"""A stalled local connection must not block the health endpoint."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_idle_local_client_does_not_block_health():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    with tempfile.TemporaryDirectory(prefix="xuanjian-http-test-") as data_dir:
        env = {
            key: value for key, value in os.environ.items()
            if key not in {
                "XUANJIAN_DB_PATH", "XUANJIAN_APP_MODE", "OPENAI_API_KEY",
                "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "HTTP_PROXY",
                "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy",
            }
        }
        env.update({
            "PYTHONPATH": str(ROOT),
            "XUANJIAN_DATA_DIR": data_dir,
            "XUANJIAN_HOST": "127.0.0.1",
            "XUANJIAN_PORT": str(port),
        })
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "backend" / "server.py")],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        idle = None
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    with opener.open(f"http://127.0.0.1:{port}/api/system/info", timeout=1) as response:
                        info = json.load(response)
                    break
                except Exception:
                    time.sleep(0.1)
            else:
                raise AssertionError("isolated server did not start")

            assert info["pid"] == process.pid
            assert info["data_dir"] == data_dir
            idle = socket.create_connection(("127.0.0.1", port), timeout=2)
            idle.sendall(b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1")
            time.sleep(0.1)
            with opener.open(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
                assert json.load(response)["status"] == "healthy"
        finally:
            if idle is not None:
                idle.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
