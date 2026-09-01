# ---------- Stage 1: build the virtual environment ----------
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, so this layer is cached unless the lockfile changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Then the source, and install the project itself.
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim-bookworm

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_ANALYTICS_ENABLED=False

USER appuser
EXPOSE 7860

CMD ["cy590-half-marathon-planner"]