import json
import os
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
root = Path(os.environ['GIIS_ROOT']).resolve()
repo = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
revision = HfApi().model_info(repo).sha
snapshot_download(repo, revision=revision, local_dir=root / 'Models/Reranker',
                  allow_patterns=['*.json', '*.txt', '*.safetensors', 'tokenizer*', 'vocab*'])
(root / 'server/reranker_manifest.json').write_text(
    json.dumps({'model': repo, 'revision': revision}, indent=2) + '\n')
# Fetch the token-count encoding during installation, not service operation.
import tiktoken
tiktoken.get_encoding('o200k_base')
