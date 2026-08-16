#!/usr/bin/env bash
# Stop docker-compose services started for local development.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Stopping docker compose services"
docker compose down

echo "Done. If MCP or the landing site are still running in another terminal, stop them with Ctrl+C."
