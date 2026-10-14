# Recover a disconnected GIIS session

There are two independent processes: the **server retrieval service** and the **PC SSH tunnel**. Ordinary SSH login proves neither is running. Do not reinstall dependencies, rebuild the index or change Tailscale to address a missing process.

## Check the company service in Ubuntu

After a normal SSH login, run the installed read-only helper:

```bash
bash /path/to/GIIS_RAG/server/status.sh
```

For an older deployment without the helper:

```bash
ss -ltn 'sport = :8765'
curl --max-time 5 -sS -o /dev/null -w 'HTTP status: %{http_code}\n' http://127.0.0.1:8765/mcp
tail -n 12 /path/to/GIIS_RAG/logs/service.log
```

HTTP000 and connection refused indicate no reachable HTTP service. An HTTP405,406 or other response proves reachability, not full MCP readiness. Old log entries alone do not prove current liveness. If no listener exists, report it to the operator; researcher onboarding does not authorize a server restart.

## Choose foreground or detached operation

The authorized operator uses `server/start.sh` for foreground operation. Its SSH terminal must remain alive. A blinking cursor is normal because output goes to the log, but it does not prove successful initialization.

For operation that survives SSH logout, use `server/start-detached.sh`. It creates only a dedicated `giis-rag` tmux session on the socket `GIIS_RAG/run/tmux.sock`. It does not register a global service, automatically restart crashes or survive server reboots.

To switch a running foreground instance, the operator presses Ctrl+C in **that instance's terminal**, verifies it stopped, then runs:

```bash
bash /path/to/GIIS_RAG/server/start-detached.sh
bash /path/to/GIIS_RAG/server/status.sh
```

The helper refuses to interrupt an instance holding the service lock. Do not kill guessed PIDs or use generic `tmux kill-server`. To inspect the dedicated session:

```bash
tmux -S /path/to/GIIS_RAG/run/tmux.sock attach -t giis-rag
```

Detach with Ctrl+B, then D. Ctrl+C stops the service. Session existence is not readiness: if unhealthy, inspect its pane and service log. Restart only through an explicit operator action.

## Open the tunnel on the PC, not in Ubuntu

In a separate **local PowerShell window**:

```powershell
./client/Connect-GiisRag.ps1 -ServerHost 'HOST_FROM_ADMIN' -SshUser 'USER_FROM_ADMIN'
```

Alternatively use `client/Open-GiisTunnel.ps1` with those parameters to open a dedicated interactive window. Enter the company password privately there and leave it open. Blank output after authentication is normal for `ssh -N`; test the protocol instead of assuming blank output means success.

Manual equivalent:

```powershell
ssh -N -L 127.0.0.1:18765:127.0.0.1:8765 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 USER_FROM_ADMIN@HOST_FROM_ADMIN
```

Reopen the tunnel after closing its window, restarting the PC or an unrecovered network interruption. One tunnel per PC can serve multiple chats; another teammate needs their own PC's tunnel.

## Verify and resume

```powershell
./client/Test-GiisMcp.ps1 -Query 'How does climate change affect biodiversity?'
```

Expect `basic_retrieval_passed`, three GIIS tools and passages. `connected_but_no_qualifying_evidence` proves connectivity but not evidence availability for that question. Reuse the saved configuration; do not add duplicate tables. Restart Codex only if it has not loaded the restored connection.

Connectivity is not semantic coverage certification. Resume the normal obligation–evidence validation protocol before writing claims.
