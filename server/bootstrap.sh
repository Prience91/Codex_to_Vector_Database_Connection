#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/runtime.env.sh"
cd "$GIIS_ROOT"
exec 9>"$GIIS_ROOT/run/install.lock"
flock -n 9 || { echo 'Another installation is running.'; exit 1; }
python3 -m venv "$GIIS_ROOT/.venv"
"$GIIS_ROOT/.venv/bin/python" -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0
"$GIIS_ROOT/.venv/bin/python" -m pip install -r "$GIIS_ROOT/server/requirements.txt"
"$GIIS_ROOT/.venv/bin/python" "$GIIS_ROOT/server/install_models.py"
"$GIIS_ROOT/.venv/bin/python" -m pip freeze > "$GIIS_ROOT/server/requirements.resolved.txt"
"$GIIS_ROOT/.venv/bin/python" "$GIIS_ROOT/server/retriever.py" --smoke | tee "$GIIS_ROOT/logs/installation_smoke.json"
