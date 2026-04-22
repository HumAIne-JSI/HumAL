"""
Minimal MinIO client.
"""

import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


# MinIO endpoint paths
AUTH_LOGIN_PATH = "/auth/auth"
UPLOAD_PATH = "/main_ops/upload"
METADATA_PATH_TMPL = "/main_ops/metadata/{bucket}/{object}"
UPDATE_METADATA_PATH_TMPL = "/main_ops/update_metadata/{bucket}/{object}"
DOWNLOAD_PATH_TMPL = "/main_ops/download/{bucket}/{object}"
DELETE_PATH_TMPL = "/main_ops/delete/{bucket}/{object}"
SEARCH_OBJECTS_PATH = "/main_ops/search/objects"


class MinioClient:
    """
    Expected env vars:
    - base_url: MINIO_BASE_URL
    - username: MINIO_USERNAME
    - password: MINIO_PASSWORD
    """

    def __init__(self, timeout_s=30, auto_reauth=True):
        base_url = os.getenv("MINIO_BASE_URL")
        username = os.getenv("MINIO_USERNAME")
        password = os.getenv("MINIO_PASSWORD")

        if not base_url:
            raise ValueError("Missing MinIO base url env var (MINIO_BASE_URL).")
        if not username or not password:
            raise ValueError("Missing MinIO credentials env vars (MINIO_USERNAME, MINIO_PASSWORD).")

        logger.info(f"Initializing MinioClient with base_url={base_url}, timeout={timeout_s}s, auto_reauth={auto_reauth}")
        
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.token = None

        # Keep credentials only to support auto re-auth on 401/403.
        self._auto_reauth = bool(auto_reauth)
        self._username = username if self._auto_reauth else None
        self._password = password if self._auto_reauth else None

        self.login(username, password)


    def headers(self):
        if not self.token:
            raise ValueError("Not authenticated (missing token).")
        return {"Authorization": f"Bearer {self.token}"}

    def _url(self, path):
        return f"{self.base_url}/{path.lstrip('/')}"

    def _reauth(self):
        if not self._username or not self._password:
            raise ValueError(
                "Cannot re-authenticate (credentials not stored). "
                "Initialize with auto_reauth=True or call login() manually."
            )
        logger.debug("Token expired, attempting to re-authenticate with MinIO")
        return self.login(self._username, self._password)

    def _request(self, method, path, *, auth=True, retry_on_unauth=True, **kwargs):
        """
        Execute a single HTTP request.

        Pattern:
        attempt request -> if 401/403 -> re-auth -> retry once
        """
        url = self._url(path)
        logger.debug(f"MinIO {method} request to {path}")

        headers = kwargs.pop("headers", None) or {}
        headers = dict(headers)
        if auth:
            headers.update(self.headers())

        def do_request():
            return requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout_s,
                **kwargs,
            )

        try:
            r = do_request()
            if (auth and retry_on_unauth and r.status_code in (401, 403) and self._auto_reauth and self._username and self._password):
                logger.warning(f"Received {r.status_code} response, attempting to re-authenticate")
                self._reauth()
                headers.update(self.headers())
                r = do_request()

            r.raise_for_status()
            logger.debug(f"MinIO {method} {path} completed with status {r.status_code}")
            return r
        except requests.RequestException as e:
            logger.error(f"MinIO {method} request to {path} failed: {e}", exc_info=True)
            raise

    def login(self, username, password):
        url = self._url(AUTH_LOGIN_PATH)
        logger.debug(f"Attempting MinIO login at {url}")
        try:
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            r = requests.post(
                url,
                headers=headers,
                data={"username": username, "password": password},
                timeout=self.timeout_s,
            )
            r.raise_for_status()
            self.token = r.json()["access_token"]
            logger.info("Successfully authenticated with MinIO")
            return self.token
        except requests.RequestException as e:
            logger.error(f"MinIO login failed: {e}", exc_info=True)
            raise

    def upload_file_path(self, bucket_name, object_name, filepath):
        filepath = Path(filepath)
        guessed_type, _ = mimetypes.guess_type(str(filepath))
        content_type = guessed_type or "application/octet-stream"
        file_size = filepath.stat().st_size

        logger.info(f"Uploading file to MinIO: bucket={bucket_name}, object={object_name}, file={filepath}, size={file_size} bytes")
        
        url = self._url(UPLOAD_PATH)
        try:
            with open(filepath, "rb") as f:
                def do_post():
                    # Ensure stream is rewound.
                    f.seek(0)
                    files = {
                        "bucket_name": (None, bucket_name),
                        "object_name": (None, object_name),
                        "file": (filepath.name, f, content_type),
                    }
                    return requests.post(url, headers=self.headers(), files=files, timeout=self.timeout_s)

                r = do_post()
                if r.status_code in (401, 403) and self._auto_reauth:
                    logger.warning(f"Received {r.status_code}, re-authenticating and retrying upload")
                    self._reauth()
                    r = do_post()

                r.raise_for_status()
                logger.info(f"Successfully uploaded to {bucket_name}/{object_name}")
                return r.json()
        except Exception as e:
            logger.error(f"Upload failed for {bucket_name}/{object_name}: {e}", exc_info=True)
            raise

    def upload_file_bytes(self, bucket_name, object_name, file_bytes, filename="file.bin"):
        """
        Same as `upload_file_path`, but reads the file from memory.
        """
        guessed_type, _ = mimetypes.guess_type(str(filename))
        content_type = guessed_type or "application/octet-stream"
        
        # Calculate size for logging
        byte_size = len(file_bytes) if isinstance(file_bytes, bytes) else (
            len(file_bytes.getvalue()) if hasattr(file_bytes, "getvalue") else 0
        )
        
        logger.info(f"Uploading bytes to MinIO: bucket={bucket_name}, object={object_name}, filename={filename}, size={byte_size} bytes")

        url = self._url(UPLOAD_PATH)

        try:
            def do_post():
                # If a file-like object is provided (e.g. io.BytesIO), rewind for retries.
                if hasattr(file_bytes, "seek"):
                    try:
                        file_bytes.seek(0)
                    except Exception:
                        pass
                files = {
                    "bucket_name": (None, bucket_name),
                    "object_name": (None, object_name),
                    "file": (filename, file_bytes, content_type),
                }
                return requests.post(url, headers=self.headers(), files=files, timeout=self.timeout_s)

            r = do_post()
            if r.status_code in (401, 403) and self._auto_reauth:
                logger.warning(f"Received {r.status_code}, re-authenticating and retrying bytes upload")
                self._reauth()
                r = do_post()

            r.raise_for_status()
            logger.info(f"Successfully uploaded bytes to {bucket_name}/{object_name}")
            return r.json()
        except Exception as e:
            logger.error(f"Bytes upload failed for {bucket_name}/{object_name}: {e}", exc_info=True)
            raise

    def get_metadata(self, bucket_name, object_name):
        logger.debug(f"Fetching metadata: bucket={bucket_name}, object={object_name}")
        b = quote(str(bucket_name), safe="")
        o = quote(str(object_name), safe="")
        try:
            r = self._request("GET", METADATA_PATH_TMPL.format(bucket=b, object=o))
            logger.debug(f"Successfully retrieved metadata for {bucket_name}/{object_name}")
            return r.json()
        except Exception as e:
            logger.error(f"Failed to get metadata for {bucket_name}/{object_name}: {e}", exc_info=True)
            raise

    def update_metadata(self, bucket_name, object_name, metadata):
        logger.debug(f"Updating metadata: bucket={bucket_name}, object={object_name}, metadata={metadata}")
        b = quote(str(bucket_name), safe="")
        o = quote(str(object_name), safe="")
        try:
            r = self._request("PATCH", UPDATE_METADATA_PATH_TMPL.format(bucket=b, object=o), json=metadata)
            logger.debug(f"Successfully updated metadata for {bucket_name}/{object_name}")
            return r.json()
        except Exception as e:
            logger.error(f"Failed to update metadata for {bucket_name}/{object_name}: {e}", exc_info=True)
            raise

    def download_object(self, bucket_name, object_name, dest_path=None):
        """
        - if dest_path is None -> returns bytes
        - else -> writes file and returns dest_path
        """
        logger.info(f"Downloading from MinIO: bucket={bucket_name}, object={object_name}, dest_path={dest_path}")
        b = quote(str(bucket_name), safe="")
        o = quote(str(object_name), safe="")
        try:
            r = self._request("GET", DOWNLOAD_PATH_TMPL.format(bucket=b, object=o))

            if dest_path is None:
                logger.debug(f"Downloaded {len(r.content)} bytes from {bucket_name}/{object_name}")
                return r.content

            dest = Path(dest_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            logger.info(f"Successfully saved download to {dest_path} ({len(r.content)} bytes)")
            return str(dest)
        except Exception as e:
            logger.error(f"Download failed for {bucket_name}/{object_name}: {e}", exc_info=True)
            raise

    def delete_object(self, bucket_name, object_name):
        logger.info(f"Deleting from MinIO: bucket={bucket_name}, object={object_name}")
        b = quote(str(bucket_name), safe="")
        o = quote(str(object_name), safe="")
        try:
            r = self._request("DELETE", DELETE_PATH_TMPL.format(bucket=b, object=o))
            logger.info(f"Successfully deleted {bucket_name}/{object_name}")
            try:
                return r.json()
            except Exception:
                return {}
        except Exception as e:
            logger.error(f"Delete failed for {bucket_name}/{object_name}: {e}", exc_info=True)
            raise

    def list_objects(
        self,
        bucket_name: str,
        *,
        prefix: Optional[str] = None,
        q: Optional[str] = None,
        metadata_key: Optional[str] = None,
        metadata_value: Optional[str] = None,
        filter_type: Optional[str] = None,
        min_value: Optional[str] = None,
        max_value: Optional[str] = None,
        limit: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ):
        """Search objects in a bucket.

        This calls the MinIO API facade's list endpoint. The endpoint path template can
        be overridden via `MINIO_LIST_OBJECTS_PATH_TMPL` if needed.

        Params are passed as query params; exact supported keys depend on the server.
        """
        logger.debug(f"Listing objects in bucket {bucket_name}, prefix={prefix}, filter_type={filter_type}")
        
        path = os.getenv("MINIO_SEARCH_OBJECTS_PATH", SEARCH_OBJECTS_PATH)

        params: Dict[str, Any] = {"bucket_name": bucket_name}
        if prefix is not None:
            params["prefix"] = prefix
        if q is not None:
            params["q"] = q
        if metadata_key is not None:
            params["metadata_key"] = metadata_key
        if metadata_value is not None:
            params["metadata_value"] = metadata_value
        if filter_type is not None:
            params["filter_type"] = filter_type
        if min_value is not None:
            params["min_value"] = min_value
        if max_value is not None:
            params["max_value"] = max_value
        if limit is not None:
            params["limit"] = int(limit)
        if extra_params:
            params.update(extra_params)

        try:
            r = self._request("GET", path, params=params)
            result = r.json()
            match_count = len(result.get("matches", [])) if result else 0
            logger.debug(f"Found {match_count} objects in {bucket_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to list objects in {bucket_name} with prefix={prefix}: {e}", exc_info=True)
            raise

