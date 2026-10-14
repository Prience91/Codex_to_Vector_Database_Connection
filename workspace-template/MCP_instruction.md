# Connect this PC's Codex to GIIS RAG

Give this file to Codex and ask: **“Follow MCP_instruction.md to connect my Codex to GIIS RAG.”** Reading or storing this file alone does not execute setup or grant permission. An explicit request to follow it authorizes the client setup described below, subject to the client's filesystem and execution approvals.

## Existing company service

- Company server: `HOST_FROM_ADMIN`, reachable on the company network or another administrator-approved route.
- Company-provided shared SSH username: `USER_FROM_ADMIN`.
- Retrieval service: server-local `127.0.0.1:8765/mcp`.
- PC tunnel endpoint: `http://127.0.0.1:18765/mcp`.
- Local Codex MCP name: `giis_rag`.

Use the existing service. Do not install another server, copy the vector database to the PC, or change company server files, services, ports, firewalls, accounts or permissions. Do not contact Spark or change Tailscale. No OpenAI API key or separate OAuth login is required for this connection. Users use their own Codex/OpenAI accounts; company SSH credentials authenticate the tunnel.

## Instructions for Codex

### 1. Inspect the client and current connection

Determine the current operating system and actual Codex configuration location. On standard Windows installations it is `%USERPROFILE%\.codex\config.toml`; respect an existing custom Codex home location. Do not expose the full configuration or any credentials in chat.

Check whether `giis_rag` is already available through MCP. If so, perform a lightweight tool call before making changes. A successful call means setup is already complete.

Otherwise check whether localhost port `18765` responds as an MCP endpoint. A port accepting TCP alone is not proof of a valid GIIS service. Do not kill another process or replace an unrelated listener if the port is occupied.

### 2. Ensure the SSH tunnel exists

An ordinary interactive SSH login is NOT the tunnel. Existing shell authentication does not automatically authenticate a new SSH process.

If an already working tunnel is present, reuse it. Otherwise ask the user to run the following in a separate **local Windows PowerShell window**, not inside the Ubuntu shell:

```powershell
ssh -N -L 127.0.0.1:18765:127.0.0.1:8765 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 USER_FROM_ADMIN@HOST_FROM_ADMIN
```

The user enters the company password at the SSH password prompt and leaves the window open. Blank output after authentication is normal. Do not request the password in chat, write it to a file, place it in command arguments, or store it in Codex configuration. If SSH asks about a previously unknown host key, have the user confirm its fingerprint with the administrator; do not disable host-key verification.

If the repository's `client/Open-GiisTunnel.ps1` is available, it can open that interactive window using the administrator-supplied host and username. It does not store passwords or establish success merely by opening a window. Run `client/Test-GiisMcp.ps1` afterward. If connectivity fails, follow `docs/RECOVERY.md`: verify the server service separately from the PC tunnel. Server startup belongs to the authorized operator, not the research client. The operator may use a folder-contained detached tmux service; this is not installed by client onboarding.

If the user already has an approved SSH key/agent and Codex has permission to launch processes, Codex may establish the tunnel without another password interaction. Verify authentication and forwarding success; do not silently create SSH keys or modify authorized keys. Prefer the user's foreground terminal for the initial setup. Any background helper must have an explicit lifecycle and no visible window unless the user requested one.

If forwarding is prohibited or server-local port `8765` is unavailable, report the specific failure and refer server-side changes to the administrator. A folder-only onboarding request does not authorize restarting the company service.

### 3. Add the saved MCP configuration

Inspect only relevant configuration sections and preserve unrelated settings, plugins, models and other MCP servers. Obtain any required filesystem approval before editing the user's configuration. Make a local backup before modifying an existing file; backups may contain secrets and must never be uploaded or printed in chat.

Add the following once, or update the existing `giis_rag` table deliberately. Do not append a duplicate TOML table. If an existing entry points elsewhere, explain the difference before replacing it.

```toml
[mcp_servers.giis_rag]
url = "http://127.0.0.1:18765/mcp"
startup_timeout_sec = 60
tool_timeout_sec = 180
enabled_tools = ["search_evidence", "retrieve_obligations", "fetch_passage"]
enabled = true
required = false

[mcp_servers.giis_rag.tools.search_evidence]
output_token_limit = 10000

[mcp_servers.giis_rag.tools.retrieve_obligations]
output_token_limit = 10000
```

Merge existing per-tool tables rather than duplicating them. Validate the complete TOML after editing. Restore the backup if validation fails. Do not install an extra Python runtime just to validate TOML if an available Codex configuration command or existing parser can perform the check. Do not overwrite the file with only this block.

This is user-level configuration and makes the tools available beyond this writing project. If the user explicitly wants project-only scope, use the trusted primary project's `.codex/config.toml` instead, respecting the client's configuration rules. Do not create both scopes unnecessarily.

### 4. Load and test the connection

If the current Codex session does not discover the newly configured server, ask the user to save their work and restart Codex. Do not close or restart the app automatically while work is running. The SSH tunnel must remain open during the restart.

After restart, discover the GIIS tools and call `search_evidence` with a short test query such as **“How does climate change affect biodiversity?”** Verify:

- the tool call succeeds against the GIIS service;
- the response contains passages with stable chunk and document identifiers;
- source titles and available citation metadata are returned; and
- the response is not an authentication error or malformed MCP message.

Optionally call `fetch_passage` for one returned chunk and verify its text and source identity. Do not claim semantic obligation coverage merely because search succeeded. Report “connected and basic retrieval tested” only after a successful live call; otherwise state exactly which step remains incomplete.

### 5. Apply the writing policy

Make the user's local writing folder the primary project folder and use its reusable `AGENTS.md`. That file governs obligation planning, evidence validation, one bounded rescue, local Markdown/Obsidian writing, and APA 7 references. If it is missing, report that the connection works but the local research-writing instructions still need to be supplied. Do not invent a replacement policy or grant server-folder write access.

Direct attachment of the company GIIS_RAG folder is optional for research via MCP. Do not add it automatically. No server files need to be writable by the client's research agent.

## What persists and what does not

- The saved MCP configuration persists across chats and PC restarts.
- One running tunnel can serve multiple Codex chats on the same PC. Each teammate establishes their own PC's tunnel; the same localhost port can be used on different PCs.
- If the PC restarts, the tunnel closes, or the network breaks, re-establish the tunnel. No configuration reinstall is normally needed.
- The company retrieval service must remain running independently of the client's tunnel. Current service startup is managed by the operator; persistent operation has not yet been established by this onboarding guide.
- Requests share one retrieval process and are serialized. This guide does not certify capacity for a particular number of simultaneous users.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| SSH permission denied | Confirm the company username/password and SSH authorization with the administrator. |
| Local port already in use | Identify the existing connection; reuse a verified GIIS tunnel or obtain approval for a different local port and update the MCP URL consistently. |
| Forwarding administratively prohibited | Administrator must approve forwarding; do not change server SSH configuration yourself. |
| Tunnel reports connection refused for server port | Existing retrieval service may be stopped; contact its operator. |
| Codex has no GIIS tools | Validate config scope and syntax, keep the tunnel open, restart Codex, and inspect MCP connection status. |
| OAuth requested | This endpoint has no OAuth flow. Check that the local Streamable HTTP MCP entry is being used, not a cloud plugin-creation form. |
| Tool timeout | Report the timeout; shared retrieval may be busy. Do not launch another server or repeatedly retry to bypass the queue. |

Codex setup reference: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
SSH forwarding reference: https://man.openbsd.org/ssh
