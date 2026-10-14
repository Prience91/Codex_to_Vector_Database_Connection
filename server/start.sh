#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/runtime.env.sh"
cd "$GIIS_ROOT"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
exec 9>"$GIIS_ROOT/run/service.lock"
flock -n 9 || { echo 'GIIS retrieval service already running.' >&2; exit 1; }
exec "$GIIS_ROOT/.venv/bin/python" "$GIIS_ROOT/server/mcp_server.py" >>"$GIIS_ROOT/logs/service.log" 2>&1
