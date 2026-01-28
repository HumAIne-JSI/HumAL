FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Keep backend paths predictable inside the container
ENV TEAM_CLASSIFIER_PATH=/app/models/perfect_team_classifier \
    TICKET_CLASSIFIER_PATH=/app/models/ticket_classifier_model \
    KNOWLEDGE_BASE_PATH=/app/data/User_Request_last_team_ANON.csv \
    LLM_MODEL=gpt-3.5-turbo \
    LLM_MAX_TOKENS=800 \
    LLM_TEMPERATURE=0.2 \
    SENTENCE_MODEL=all-MiniLM-L6-v2 \
    EMBEDDING_CACHE_DIR=embeddings_cache \
    DEFAULT_TOP_K=3 \
    DISABLE_EMBEDDING_CACHE=0

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
COPY models /app/models
COPY data /app/data

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
