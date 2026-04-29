FROM python:3.13-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt


FROM python:3.13-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/sarteta/pgvector-rag-starter"
LABEL org.opencontainers.image.description="Multi-tenant RAG starter on Postgres + pgvector with FastAPI"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --create-home app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=app:app app ./app

USER app

EXPOSE 8000

# Defaults to in-memory store; set DATABASE_URL to use Postgres + pgvector.
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
