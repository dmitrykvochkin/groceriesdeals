FROM ghcr.io/astral-sh/uv:0.11.32@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c AS uv

FROM python:3.11-slim-bookworm@sha256:2e32f7d302adc1c37428355c1e646897c0c53f4fd60b6a551245fb90ee129f91 AS builder

COPY --from=uv /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev --no-editable


FROM python:3.11-slim-bookworm@sha256:2e32f7d302adc1c37428355c1e646897c0c53f4fd60b6a551245fb90ee129f91 AS runtime

ARG VCS_REF="unknown"

LABEL org.opencontainers.image.title="Groceries Deals MCP" \
      org.opencontainers.image.description="FastMCP server for Groceries Deals" \
      org.opencontainers.image.source="https://github.com/dmitrykvochkin/groceriesdeals" \
      org.opencontainers.image.revision="${VCS_REF}"

RUN groupadd --gid 10001 groceries \
    && useradd --uid 10001 --gid groceries --create-home --home-dir /home/groceries groceries

WORKDIR /app

COPY --from=builder --chown=groceries:groceries /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER groceries

EXPOSE 8438

CMD ["groceries-mcp-http"]
