#!/usr/bin/env bash
set -euo pipefail

export PATH="/c/msys64/ucrt64/bin:/ucrt64/bin:/usr/bin:/bin:$PATH"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
mkdir -p build

python_cmd="${SAGAN_PYTHON_EXECUTABLE:-}"
if [[ -z "$python_cmd" ]]; then
  python_cmd="$(command -v python3 || command -v python)"
fi

"$python_cmd" -m venv build/workspace-docs-venv
venv_python=build/workspace-docs-venv/bin/python
if [[ -f build/workspace-docs-venv/Scripts/python.exe ]]; then
  venv_python=build/workspace-docs-venv/Scripts/python.exe
fi
"$venv_python" -m pip install -r requirements-docs.txt
"$venv_python" scripts/bootstrap_docs_sources.py --root build/sources
aggregate_root="$(mktemp -d "$repo_root/build/workspace-docs.XXXXXX")"
"$venv_python" scripts/assemble_docs.py --source-root build/sources --output "$aggregate_root/assembled"
"$venv_python" -m mkdocs build --strict --clean -f "$aggregate_root/assembled/mkdocs.yml"
