"""Regression tests for the /xai router."""
import os

os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app.main import app


def test_nearest_ticket_endpoint_not_registered():
    """POST /xai/{al_instance_id}/nearest_ticket must no longer be registered."""
    paths = [getattr(route, "path", "") for route in app.routes]
    assert not any(path.endswith("/nearest_ticket") for path in paths)
