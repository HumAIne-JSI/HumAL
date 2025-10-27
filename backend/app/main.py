from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import inference_router, active_learning_router, label_creation_router, config_router, data_router, xai_router

app = FastAPI(
    title="HumAL API",
    description="Human-in-the-loop Active Learning API",
    version="1.0.0"
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
app.include_router(label_creation_router.router)
app.include_router(config_router.router)
app.include_router(data_router.router)
app.include_router(xai_router.router)

# Entry point for running the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)