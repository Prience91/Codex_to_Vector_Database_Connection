#!/usr/bin/env bash
# Opt-in operator action: survive SSH logout without creating a global service.
set -euo pipefail
source "$(dirname -- "$0")/runtime.env.sh"
command -v tmux >/dev/null || { echo 'tmux is unavailable; ask the operator.' >&2; exit 1; }
socket="$GIIS_ROOT/run/tmux.sock"
session=giis-rag
if tmux -S "$socket" has-session -t "$session" 2>/dev/null; then
    echo 'Dedicated GIIS session already exists. Check server/status.sh; no new process started.'
    exit 0
fi
exec 8>"$GIIS_ROOT/run/service.lock"
if ! flock -n 8; then
    echo 'A GIIS service already holds the lock. The operator must stop its foreground instance before switching to detached mode.' >&2
    exit 1
fi
flock -u 8
exec 8>&-
printf -v launch 'exec bash %q' "$GIIS_ROOT/server/start.sh"
tmux -S "$socket" new-session -d -s "$session" -c "$GIIS_ROOT" "$launch"
echo 'Detached session launched; verify server/status.sh and the client MCP test after initialization.'
echo 'This survives SSH logout, not a reboot or process crash.'
