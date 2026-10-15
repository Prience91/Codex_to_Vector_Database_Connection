# Validation record

## Founding deployment: 13 October 2026

The initial Ubuntu company-server install used a CPU-only machine with8 available cores,15GiB RAM and about14GiB available before the test. The index package contained12,976 documents and1,419,435 chunks. Granite query embedding and the canonical cross-encoder loaded successfully.

The installation smoke result was:

```json
{
  "status": "basic_retrieval_passed",
  "seconds": 15.622486670967191,
  "peak_rss_mib": 3760.46484375,
  "chunks": 1419435,
  "passages": 9,
  "semantic_coverage_certified": false
}
```

A subsequent local Codex connection exercised preliminary search, three-obligation retrieval, and exact passage fetching. The packet returned ten selected passages; an individually fetched chunk matched its packet text and source ID. Manual client assessment found support for the three test obligations. Another demonstration queried climate-change signs in Nepal's Himalayas and exercised one rescue followed by cited synthesis and coverage limitations.

These tests establish basic usability of that existing deployed connection. They do not establish full corpus correctness, automatic semantic qualification, a production concurrency limit, uninterrupted service operation or exhaustive APA metadata completeness.

## Repository checks

### Semantic handoff contract: 15 October 2026

The packet contract now labels unassessed evidence `pending_client_validation`, identifies `codex_client` as the reviewer, and states that server semantic validation has not been performed. The client must record final obligation support/gaps and refuse substantive research answers if MCP access cannot be established. Synthetic tests cover these fields in obligation packets, preliminary searches and empty-result bundles. These tests verify the handoff and instruction contract, not the semantic correctness or compliance of an external Codex model.

The company deployment was updated with in-folder backups and restarted in its dedicated tmux session. A fresh live request with two explicit obligations returned twelve passages and confirmed `semantic_validation_owner=codex_client`, `semantic_validation_status=pending_client_validation`, and `answer_policy=mcp_evidence_only`, with one pending entry for each obligation. The helper passed the MCP handshake and tool checks. This verifies that the running service loaded the amended contract; it does not claim semantic coverage approval. Users must separately replace their local writing-folder `AGENTS.md` and refresh their Codex MCP session to load current instructions.

### Connection recovery: 14 October 2026

Company SSH login succeeded while server port 8765 had no listener and a local HTTP check returned 000. The operator restarted the existing foreground service, then opened the PC tunnel separately. The repository's `client/Test-GiisMcp.ps1` completed MCP initialization, discovered all three GIIS tools and returned nine passages for the biodiversity smoke query with `state=basic_retrieval_passed`. This validates the actual helper against the restored service, not only its syntax.

The detached tmux helper and interactive window launcher were added to repository source afterward. They have not been deployed or lifecycle-tested on the live company server. Unit and syntax checks do not certify logout or reboot behavior there.

Synthetic unit tests cover selection reservations, budget rejection, duplicate/document limits, path boundaries, read-only keyword access, per-packet rescue limits, and returned coverage status. They avoid downloading models or loading the large index. Python/TOML and PowerShell syntax checks validate the shipped code and client configuration. Linux CI also checks Bash syntax.

Run live onboarding checks against the actual company service before declaring a new user's connection ready. The bundled MCP test verifies protocol and tool presence; a query test verifies preliminary retrieval only. Semantic support is still the agent's responsibility.
