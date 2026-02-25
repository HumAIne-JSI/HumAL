from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import inference_router, active_learning_router, config_router, data_router, xai_router, resolution_router

from contextlib import asynccontextmanager
from app.core.dependencies import get_startup_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_startup_service().load_data_from_minio_into_duckdb()
    yield

app = FastAPI(
    title="HumAL API",
    description="Human-in-the-loop Active Learning API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inference_router.router)
app.include_router(active_learning_router.router)
app.include_router(config_router.router)
app.include_router(data_router.router)
app.include_router(xai_router.router)
app.include_router(resolution_router.router)

# Entry point for running the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)