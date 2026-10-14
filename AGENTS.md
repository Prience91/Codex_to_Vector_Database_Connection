# Repository maintenance

This repository connects an existing compatible hybrid index to Codex through MCP. It does not build the index or perform SFT. Keep source code, tests, documentation and portable examples only; never commit corpus passages, database files, models, credentials, local connection details or generated reports.

The writing-vault instructions are `workspace-template/AGENTS.md`; copy them into a user's primary writing folder. They are not a command to write research reports in this code repository.

Do not edit the live company deployment, restart services, contact Spark or change SSH/Tailscale as part of repository maintenance. Publishing repository changes requires the user's authorization. Test boundary enforcement, evidence selection, rescue limits and MCP configuration when modifying them. Server retrieval ranks candidates; only the client agent can make semantic coverage and final answer decisions.
