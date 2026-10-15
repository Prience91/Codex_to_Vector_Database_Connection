# Operator deployment and team onboarding

## Use an already running service

For routine researcher onboarding, provide the server address and approved SSH account through company channels. Ensure SSH local forwarding to `127.0.0.1:8765` is allowed. A shared company account can be used where it is the company's existing arrangement; the same account does not provide per-user request attribution in this service. Each person's Codex account and local writing folder are independent.

Each PC opens its own tunnel, saves the MCP settings, restarts Codex when needed, and runs the connection test. Folder access alone does not establish SSH forwarding or MCP connectivity. No server install is necessary per researcher. Keep passwords out of chat, onboarding files and command arguments.

## Install only when authorized as the operator

Place `server/` under the **existing** dedicated index-package root. Do not overwrite a live deployment automatically. A repository update is not a live-server deployment instruction.

Run `bash /path/to/GIIS_RAG/server/bootstrap.sh` in Ubuntu. It creates a local venv, installs CPU PyTorch and retrieval dependencies, downloads the canonical small reranker, records its exact Hugging Face revision and resolved dependency versions, prepares the token-count encoding and performs a basic query with peak-memory measurement. Network access is needed for installation; models are used offline after setup.

The scripts place Python environment, model/cache state, temp files, bytecode, logs and lock files inside the dedicated root. No sudo, global package install, profile changes, authorized-key modifications or firewall changes are made. `requirements.txt` pins source-compatible embedding/Chroma/Transformers versions; MCP v1 and tiktoken are constrained ranges. `requirements.resolved.txt` records the installed full environment; it is runtime provenance, not a pre-certified universal lockfile.

Run `bash /path/to/GIIS_RAG/server/start.sh` only after the smoke test succeeds. It starts one foreground MCP service on server localhost8765 and redirects output to `logs/service.log`. `flock` prevents duplicate instances started with this script. Model work is serialized within the process; do not launch additional workers over the same embedded index to bypass this limit.

The foreground service remains alive only while its process remains alive. An authorized operator may opt into `server/start-detached.sh`, which uses the dedicated `run/tmux.sock` and `giis-rag` session and survives SSH logout. It refuses to interrupt a running locked instance. It does not register a system service, survive reboot or restart crashes. See [recovery instructions](RECOVERY.md) before switching an existing foreground service.

## Network boundary

The service is loopback-only and has no application OAuth flow. Authorized SSH tunnels are the initial network-access mechanism. There is no client-specific authorization within the MCP tools or per-user quota. Do not expose the loopback service directly to a shared LAN or the internet without an approved authentication/TLS design. A cloud connector cannot directly access a user's localhost tunnel.

All users have the same corpus view through this service. It does not implement per-document access filtering. Attaching a writable Samba folder can grant additional filesystem rights beyond MCP; research clients need no such write access.

## Updating

Review and test code changes in this repository first. Deploy source updates only with operator authorization, preserving existing package data and binding. Take required provenance/backups before approved replacements. Never rebuild or delete the index as part of client onboarding. Keep private hostnames, addresses, usernames, connection manifests and generated evidence outside Git.

For the semantic-handoff amendment, update `server/retriever.py` and `server/mcp_server.py`, and install `server/AGENTS.server.md` as the dedicated package root `AGENTS.md`. Preserve any unrelated live-code changes instead of replacing them blindly. Back up the previous versions inside the dedicated folder. Restart the dedicated MCP process in a controlled operator step so Python loads the changes; existing in-memory packets are lost. Reconnect/restart client MCP sessions to refresh initialization instructions. Verify a new obligation packet declares `pending_client_validation`, `semantic_validation_owner=codex_client`, `semantic_validation_performed=false`, and `answer_policy=mcp_evidence_only`. Replace the separate local writing-folder `AGENTS.md` from the updated workspace template; the server file does not automatically update users' vaults.

The client test can exercise this handoff without claiming semantic approval:

```powershell
./client/Test-GiisMcp.ps1 -Query 'How does climate change affect biodiversity?' -Obligations @('Explain observed range shifts.', 'Explain constraints on species adaptation.')
```

It verifies that the server returns one pending review entry per requested obligation and identifies Codex as reviewer. The calling Codex model must still actually read and assess the returned passages.
