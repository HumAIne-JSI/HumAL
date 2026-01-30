# Pre-downloading Models for Offline Use

To ensure the Docker container works without internet access in Kubernetes:

## Step 1: Download the model locally

Before building the Docker image, run:

```bash
cd backend
python download_models.py
```

This will create a `sentence_transformers_cache/` directory containing the pre-downloaded model.

## Step 2: Build the Docker image

The Dockerfile now includes the cached model:

```bash
docker build -t rokklancic/humaine-al-api:v0.2.0 ./backend
```

The model will be bundled inside the image at `/app/sentence_transformers_cache`.

## How it works

- The environment variable `SENTENCE_TRANSFORMERS_HOME=/app/sentence_transformers_cache` tells sentence-transformers to use the local cache
- When `SentenceTransformer("all-MiniLM-L6-v2")` is instantiated, it checks this directory first
- No internet connection is needed at runtime

## File sizes

The `all-MiniLM-L6-v2` model is approximately 80-90 MB, which will add to your Docker image size.
