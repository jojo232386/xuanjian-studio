#!/usr/bin/env bash
# Source and HTTP tests; macOS packaging remains a separate platform gate.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 14), "Python 3.14 required"'
node -e 'if (process.versions.node.split(".")[0] !== "22") { throw new Error("Node.js 22 required"); }'
export NO_PROXY="127.0.0.1,localhost,::1${NO_PROXY:+,${NO_PROXY}}"
export no_proxy="${NO_PROXY}"
npm --prefix frontend run build
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest -q -p no:cacheprovider --ignore=tests/test_macos_client_app_e2e.py
