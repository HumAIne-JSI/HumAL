FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

ENV SENTENCE_TRANSFORMERS_MODEL=all-MiniLM-L6-v2 \
    SENTENCE_TRANSFORMERS_CACHE_DIR=/app/cache/sentence_transformers \
    SENTENCE_TRANSFORMERS_LOCAL_ONLY=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    MINIO_DATA_BUCKET=smart-finance-data \
    MINIO_MODELS_BUCKET=smart-finance-models \
    MINIO_RESULTS_BUCKET=smart-finance-results \
    MINIO_BASE_URL=https://humaine-minio-api.euprojects.net \
    RABBIT_URL=amqp://guest:guest@localhost:5672 \
    TASK_QUEUE=xai_jobs \
    RESULT_QUEUE=xai_results
    

# Install Python dependencies first for better Docker layer caching
COPY requirements.txt /app/requirements.txt

# Faster installs: use uv (https://github.com/astral-sh/uv) + BuildKit cache.
# Note: cache mounts require BuildKit (enabled by default in Docker Desktop).
RUN pip install --upgrade pip \
    && pip install uv

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
        uv pip install --system -r /app/requirements.txt \
      --index-url https://download.pytorch.org/whl/cpu \
            --extra-index-url https://pypi.org/simple \
            --index-strategy unsafe-best-match

# Copy backend code + bundled artifacts
COPY app /app/app
COPY sentence_transformers_cache /app/cache/sentence_transformers
COPY humal_vectorizer /app/humal_vectorizer

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
