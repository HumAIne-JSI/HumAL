FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV SENTENCE_TRANSFORMERS_MODEL=all-MiniLM-L6-v2 \
    SENTENCE_TRANSFORMERS_CACHE_DIR=/app/sentence_transformers_cache \
    SENTENCE_TRANSFORMERS_LOCAL_ONLY=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

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
COPY data /app/data
COPY sentence_transformers_cache /app/sentence_transformers_cache

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
