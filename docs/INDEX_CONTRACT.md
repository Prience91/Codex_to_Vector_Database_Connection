# Connect an existing index package

This repository does not explain or run index construction. Supply a compatible existing GIIS package separately, on the server's local filesystem:

```text
GIIS_RAG/
  active_index.json
  READY.json
  source_manifest.json
  Vector_Index/
    chroma/
    lexical.<version>.sqlite3
  Embedding_Model/
  server/                     # copied from this repository
  Models/Reranker/             # installation downloads this small model
  .venv/                      # created on Ubuntu
  cache/ logs/ run/            # folder-contained runtime state
```

The index must already include passage text and source metadata. Original PDFs and parsed-corpus registries are not required for the service's live retrieval calls, though the pre-existing package may contain them.

`active_index.json` supplies `chroma_dir`, `collection_name`, `chunk_count`, `lexical_db`, `embedding_model_path` and `corpus_version`. Paths are relative to the dedicated root; resolved paths that escape it are refused. Do not use a historical nested binding with another machine's absolute paths.

`READY.json` must contain `source_manifest_sha256`; the service compares it to the digest of the supplied `source_manifest.json`. This verifies the manifest binding, not all data bytes at each service startup. An operator must have completed and retained the original file-transfer/integrity verification. The Chroma collection count is checked against the binding; this is not a full integrity audit of every embedding or metadata field.

The Chroma collection must use cosine distances with normalized384-dimensional Granite embeddings from the compatible `ibm-granite/granite-embedding-30m-english` snapshot and source query settings. A dimension match alone does not establish model compatibility. The service embeds queries using the supplied local snapshot; it does not re-embed documents.

The lexical SQLite database contains:

- `chunks(chunk_id, document_id, payload_json, ...)` with unique stable chunk IDs;
- `chunks_fts` with `chunk_id` and indexed text, searchable using SQLite FTS and `bm25(chunks_fts)`;
- payload JSON containing `chunk_id`, `document_id`, `text`, and available source fields such as `title`, `authors`, `year`, `doi`, `journal`, `publisher`, `volume`, `issue`, `document_type`, `page_start` and `page_end`.

Missing optional bibliography fields remain absent; they are not filled by guesses. Each ranked vector/keyword hit is resolved against the same keyword payload database. A vector ID absent from that database fails retrieval instead of manufacturing text.
