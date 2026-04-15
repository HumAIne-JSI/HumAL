import os
from pathlib import Path
from dotenv import load_dotenv

# Load project-root .env before importing modules that read os.getenv at import time
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import inference_router, active_learning_router, config_router, data_router, xai_router, resolution_router

from contextlib import asynccontextmanager
from app.core.dependencies import get_startup_service, get_xai_service, get_rabbitmq_client

if os.getenv("USE_RABBITMQ", "0") == "1":
    rabbitmq_client = get_rabbitmq_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_startup_service().load_data_from_minio_into_duckdb()
    use_rabbitmq = os.getenv("USE_RABBITMQ", "0") == "1"

    # Establish connection to RabbitMQ at startup (if enabled)
    if use_rabbitmq:
        result_queue = os.getenv("RESULT_QUEUE")
        if not result_queue:
            raise RuntimeError("RESULT_QUEUE is not configured")

        try:
            await rabbitmq_client.connect()

            # Consume the queue for XAI jobs
            await rabbitmq_client.consume(queue_name=result_queue, callback=get_xai_service().update_xai_job)
        except Exception:
            await rabbitmq_client.close()
            raise

    try:
        yield
    finally:
        # Close RabbitMQ connection on shutdown
        if use_rabbitmq:
            await rabbitmq_client.close()

app = FastAPI(
    title="HumAL API",
    description="Human-in-the-loop Active Learning API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
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