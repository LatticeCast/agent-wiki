FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
WORKDIR /app
COPY wikic/pyproject.toml ./
RUN uv sync --no-install-project
ENV PATH="/opt/venv/bin:$PATH"
