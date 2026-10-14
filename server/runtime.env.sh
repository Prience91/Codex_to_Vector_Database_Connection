#!/usr/bin/env bash
GIIS_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
export GIIS_ROOT
export XDG_CACHE_HOME="$GIIS_ROOT/cache"
export HF_HOME="$GIIS_ROOT/cache/huggingface"
export TORCH_HOME="$GIIS_ROOT/cache/torch"
export TIKTOKEN_CACHE_DIR="$GIIS_ROOT/cache/tiktoken"
export TMPDIR="$GIIS_ROOT/cache/tmp"
export PYTHONPYCACHEPREFIX="$GIIS_ROOT/cache/pycache"
export PIP_CACHE_DIR="$GIIS_ROOT/cache/pip"
export PIP_CONFIG_FILE=/dev/null
export PYTHONNOUSERSITE=1
export PYTHONPATH=""
export ANONYMIZED_TELEMETRY=False
export HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
mkdir -p "$TMPDIR" "$GIIS_ROOT/logs" "$GIIS_ROOT/run"
