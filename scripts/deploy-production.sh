#!/usr/bin/env bash
# Pull and deploy an immutable Groceries Deals image on the production host.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT/compose.production.yaml}"
GROCERIES_ENV_FILE="${GROCERIES_ENV_FILE:-/etc/groceriesdeals/groceriesdeals.env}"

usage() {
  echo "Usage: $0 <image-tag>"
  echo "Example: $0 9a97f855472f28a2a294dc610ce53329d8fbe3e3"
}

if [[ $# -ne 1 || -z "$1" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -r "$GROCERIES_ENV_FILE" ]]; then
  echo "Cannot read production environment file: $GROCERIES_ENV_FILE" >&2
  exit 1
fi

for command in docker; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Required command not found: $command" >&2
    exit 1
  fi
done

if ! docker compose version >/dev/null 2>&1; then
  echo "The Docker Compose plugin is required." >&2
  exit 1
fi

export GROCERIES_ENV_FILE
export IMAGE_TAG="$1"

compose=(docker compose --env-file "$GROCERIES_ENV_FILE" -f "$COMPOSE_FILE")

echo "==> Validating production Compose configuration"
"${compose[@]}" config --quiet

echo "==> Pulling application image ${IMAGE_TAG} and the proxy image"
"${compose[@]}" pull mcp caddy

echo "==> Starting application and proxy"
"${compose[@]}" up \
  --detach \
  --remove-orphans \
  --wait \
  --wait-timeout 120 \
  mcp caddy

echo "==> Deployment status"
"${compose[@]}" ps
