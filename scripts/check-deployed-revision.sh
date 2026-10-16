#!/usr/bin/env bash
# Read-only comparison of the running production container with remote main.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${COMPOSE_PROJECT_NAME:-groceriesdeals-production}"

if [[ $# -ne 0 ]]; then
  echo "Usage: $0" >&2
  echo "Run on Lightsail. Optionally set COMPOSE_PROJECT_NAME." >&2
  exit 2
fi

fail() { echo "ERROR: $*" >&2; exit 2; }

for command in git docker; do
  command -v "$command" >/dev/null 2>&1 || fail "Required command not found: $command"
done

latest_ref=$(git -C "$ROOT" ls-remote --exit-code origin refs/heads/main) \
  || fail "Cannot read origin/main. Check network access and Git credentials."
latest=${latest_ref%%[[:space:]]*}
[[ "$latest" =~ ^[[:xdigit:]]{40}$ ]] || fail "Remote main did not return a valid commit SHA."

containers=$(docker ps -q \
  --filter "label=com.docker.compose.project=$PROJECT" \
  --filter "label=com.docker.compose.service=mcp" \
  --filter "label=com.docker.compose.oneoff=False") \
  || fail "Cannot query Docker. Check daemon access."
[[ -n "$containers" ]] || fail "No running MCP container for $PROJECT. Run this on the Lightsail host."
[[ "$containers" != *$'\n'* ]] || fail "Multiple MCP containers found; cannot identify a single deployment."

deployed=$(docker inspect \
  --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' \
  "$containers") || fail "Cannot inspect the running MCP container."
[[ "$deployed" =~ ^[[:xdigit:]]{40}$ ]] || fail "Container has no valid revision label; rebuild using the publishing workflow."

echo "Latest main: $latest"
echo "Deployed:    $deployed"
if [[ "$latest" == "$deployed" ]]; then
  echo "PASS: latest main is deployed"
else
  echo "MISMATCH: the running deployment differs from main"
  exit 1
fi
