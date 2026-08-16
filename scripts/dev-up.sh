#!/usr/bin/env bash
# Start local dev services: Postgres, MCP HTTP, and the landing site.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Non-default ports so they don't clash with other local projects.
# Same *438 suffix as Postgres (5438) for this repo.
MCP_PORT="${MCP_PORT:-8438}"
LANDING_PORT="${LANDING_PORT:-3438}"
MCP_PID=""
LANDING_PID=""

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "$LANDING_PID" ]] && kill -0 "$LANDING_PID" 2>/dev/null; then
    kill "$LANDING_PID" 2>/dev/null || true
    wait "$LANDING_PID" 2>/dev/null || true
  fi
  if [[ -n "$MCP_PID" ]] && kill -0 "$MCP_PID" 2>/dev/null; then
    kill "$MCP_PID" 2>/dev/null || true
    wait "$MCP_PID" 2>/dev/null || true
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM

echo "==> Starting Postgres (docker compose)"
docker compose up -d --wait

echo "==> Starting MCP HTTP on http://localhost:${MCP_PORT}/mcp"
uv run fastmcp run src/groceriesdeals/mcp_server.py:mcp \
  --transport http \
  --port "$MCP_PORT" &
MCP_PID=$!

echo "==> Starting landing site on http://localhost:${LANDING_PORT}"
(
  cd apps/landing
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run dev -- --port "$LANDING_PORT"
) &
LANDING_PID=$!

echo
echo "Services running:"
echo "  Postgres  docker compose (port ${POSTGRES_PORT:-5438})"
echo "  MCP       http://localhost:${MCP_PORT}/mcp"
echo "  Landing   http://localhost:${LANDING_PORT}"
echo
echo "Press Ctrl+C to stop MCP and the landing site."
echo "Postgres keeps running; use 'make down' to stop it."

wait
