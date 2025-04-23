from fastapi import FastAPI

from app.routers import inference_router, active_learning_router, label_creation_router

app = FastAPI()

app.include_router(inference_router.router)
app.include_router(active_learning_router.router)
app.include_router(label_creation_router.router)

# Entry point for running the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


