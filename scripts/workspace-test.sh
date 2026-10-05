#!/usr/bin/env bash
set -euo pipefail

export PATH="/c/msys64/ucrt64/bin:/ucrt64/bin:/usr/bin:/bin:$PATH"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

venv_python=build/workspace-docs-venv/bin/python
if [[ -f build/workspace-docs-venv/Scripts/python.exe ]]; then
  venv_python=build/workspace-docs-venv/Scripts/python.exe
fi
if [[ ! -f "$venv_python" ]]; then
  echo "Build the pinned docs aggregate before running workspace tests." >&2
  exit 2
fi
"$venv_python" -m unittest discover -s tests -p '*_test.py' -v
