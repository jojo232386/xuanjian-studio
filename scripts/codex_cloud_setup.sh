#!/usr/bin/env bash
# Run only in an isolated Codex Cloud checkout.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
cloud_python="${XUANJIAN_CLOUD_PYTHON:-python3.14}"
"${cloud_python}" -c 'import sys; assert sys.version_info[:2] == (3, 14), "Python 3.14 required"'
node -e 'if (process.versions.node.split(".")[0] !== "22") { throw new Error("Node.js 22 required"); }'
if [[ ! -e .venv ]]; then
  "${cloud_python}" -m venv .venv
fi
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 14), "Existing .venv must use Python 3.14"'
.venv/bin/python -m pip install --disable-pip-version-check -r requirements-dev.txt
npm --prefix frontend ci
npm --prefix frontend run build
