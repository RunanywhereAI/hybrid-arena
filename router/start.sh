#!/usr/bin/env bash
# Launch the hybrid router proxy. Reads OPEN_AI_API_KEY from ../.env if present.
set -euo pipefail

cd "$(dirname "$0")"

# Load env if present.
if [[ -f ../.env ]]; then
  # Export every line that looks like KEY=VALUE.
  set -a
  # shellcheck disable=SC1091
  source ../.env
  set +a
fi

# Some defaults.
: "${PORT:=8787}"
: "${LOCAL_BASE:=http://127.0.0.1:11434/v1}"
: "${LOCAL_MODEL:=qwen3.6:27b-coding-mxfp8}"
: "${ROUTER_MODEL:=qwen3:0.6b}"
: "${CLOUD_BASE:=https://api.openai.com/v1}"
: "${CLOUD_MODEL:=gpt-5.5}"
: "${CLOUD_FALLBACK_MODEL:=gpt-5}"
: "${ROUTER_BANNER:=1}"

# Make .env's OPEN_AI_API_KEY visible to the server (it accepts either spelling).
if [[ -z "${OPENAI_API_KEY:-}" && -n "${OPEN_AI_API_KEY:-}" ]]; then
  export OPENAI_API_KEY="$OPEN_AI_API_KEY"
fi

export PORT LOCAL_BASE LOCAL_MODEL ROUTER_MODEL CLOUD_BASE CLOUD_MODEL CLOUD_FALLBACK_MODEL ROUTER_BANNER

echo "Starting opencode hybrid router on http://127.0.0.1:${PORT}"
echo "  local  : ${LOCAL_BASE}  model=${LOCAL_MODEL}"
echo "  cloud  : ${CLOUD_BASE}  model=${CLOUD_MODEL}  key=${OPENAI_API_KEY:+present}"
echo "  router : ${ROUTER_MODEL}"
echo

exec node server.mjs
