#!/usr/bin/env bash
# Read-only: do not source runtime.env.sh, which creates directories.
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
socket="$root/run/tmux.sock"
if command -v tmux >/dev/null && tmux -S "$socket" has-session -t giis-rag 2>/dev/null; then
    echo 'Dedicated tmux session: present'
else
    echo 'Dedicated tmux session: absent (foreground service may still run)'
fi
echo 'Server port 8765:'
ss -ltn 'sport = :8765'
if command -v curl >/dev/null; then
    code=$(curl --max-time 5 -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/mcp) || code=000
    printf 'Local MCP HTTP status: %s\n' "$code"
    echo 'HTTP reachability alone is not MCP readiness. Run the client handshake.'
fi
if [[ -f "$root/logs/service.log" ]]; then
    echo 'Recent service log:'
    tail -n 12 "$root/logs/service.log"
fi
