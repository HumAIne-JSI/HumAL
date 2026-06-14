from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import (
    create_access_token,
    get_current_user,
    get_duckdb_persistence_service,
)
from app.data_models.active_learning_dm import (
    LoginRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.persistence.duckdb import DuckDbPersistenceService

router = APIRouter(prefix="/users", tags=["users"])
duckdb_service = get_duckdb_persistence_service()


@router.post("/register", response_model=UserResponse)
def register_user(request: UserRegisterRequest):
    """Register a new user."""
    existing = duckdb_service.get_user_by_username(username=request.username)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username already exists")
    user_id = duckdb_service.upsert_user(
        username=request.username,
        password=request.password,
    )
    user = duckdb_service.get_user(user_id=user_id)
    return UserResponse(
        user_id=str(user["user_id"]),
        username=user["username"],
    )


@router.post("/login", response_model=TokenResponse)
def login_user(request: LoginRequest):
    """Authenticate a user and return a JWT access token."""
    user = duckdb_service.get_user_by_username(username=request.username)
    if user is None or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        user_id=str(user["user_id"]),
        username=user["username"],
    )
    return TokenResponse(access_token=access_token)


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's identity."""
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
    }
