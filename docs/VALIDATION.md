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

Synthetic unit tests cover selection reservations, budget rejection, duplicate/document limits, path boundaries, read-only keyword access, per-packet rescue limits, and returned coverage status. They avoid downloading models or loading the large index. Python/TOML and PowerShell syntax checks validate the shipped code and client configuration. Linux CI also checks Bash syntax.

Run live onboarding checks against the actual company service before declaring a new user's connection ready. The bundled MCP test verifies protocol and tool presence; a query test verifies preliminary retrieval only. Semantic support is still the agent's responsibility.
