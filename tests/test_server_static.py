#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_server_static.py - 静态资源路径穿越与安全回归测试

严格验证：
1. 正常资源访问 (200)
2. ../ 路径穿越拦截 (403)
3. URL 编码路径穿越拦截 (%2e%2e%2f -> 403)
4. 同名前缀兄弟目录拦截 (dist vs dist_fake -> 403)
5. 越界符号链接拦截 (指向 dist 外部的 symlink -> 403)
全部使用临时虚构文件，测试完毕自动清理。
"""

import unittest
import urllib.request
import urllib.error
import os
import sys
import shutil
import socket
import time
import tempfile
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SERVER_PY = os.path.join(PROJECT_ROOT, "backend", "server.py")
LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_clean_sandbox_env(extra_env=None):
    """
    采用极简纯白名单机制构造测试子进程环境：
    只保留运行必需 PATH，加 PYTHONPATH 与明确临时路径，剥离外部 AI 凭据、代理与 XUANJIAN_DB_PATH。
    不继承宿主杂质，绝不更改默认/用户环境变量。
    """
    clean = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "PYTHONPATH": PROJECT_ROOT
    }
    if "HOME" in os.environ:
        clean["HOME"] = os.environ["HOME"]
    if "TMPDIR" in os.environ:
        clean["TMPDIR"] = os.environ["TMPDIR"]
    if "LANG" in os.environ:
        clean["LANG"] = os.environ["LANG"]

    if extra_env:
        clean.update(extra_env)

    blacklist = [
        "XUANJIAN_DB_PATH", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY",
        "XUANJIAN_OPERATOR_API_KEY"
    ]
    for b in blacklist:
        clean.pop(b, None)

    return clean


class TestServerStaticSecurity(unittest.TestCase):
    server_proc = None
    port = None
    base_url = None
    temp_dir = None
    mock_dist = None
    mock_sibling = None
    outside_file = None
    normal_file = None
    symlink_file = None

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="xuanjian_test_static_")
        cls.mock_dist = os.path.join(cls.temp_dir, "dist")
        cls.mock_sibling = os.path.join(cls.temp_dir, "dist_fake")
        cls.outside_file = os.path.join(cls.temp_dir, "temp_outside_secret.txt")
        cls.normal_file = os.path.join(cls.mock_dist, "temp_mock_normal.txt")
        cls.symlink_file = os.path.join(cls.mock_dist, "temp_mock_symlink.txt")
        cls.temp_data = os.path.join(cls.temp_dir, "data")

        os.makedirs(cls.mock_dist, exist_ok=True)
        os.makedirs(cls.mock_sibling, exist_ok=True)
        os.makedirs(cls.temp_data, exist_ok=True)

        # 1. 正常临时文件
        with open(cls.normal_file, "w", encoding="utf-8") as f:
            f.write("CANARY_NORMAL_CONTENT_OK")

        # 2. 外部私密文件
        with open(cls.outside_file, "w", encoding="utf-8") as f:
            f.write("CANARY_OUTSIDE_SECRET_LEAK")

        # 3. 同名前缀兄弟目录与文件 (dist_fake)
        with open(os.path.join(cls.mock_sibling, "secret.txt"), "w", encoding="utf-8") as f:
            f.write("CANARY_SIBLING_SECRET")

        # 4. 越界软链接 (在 dist 内指向 dist 外部)
        try:
            os.symlink(cls.outside_file, cls.symlink_file)
        except OSError:
            pass

        cls.port = find_free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        env = make_clean_sandbox_env({
            "PYTHONPATH": PROJECT_ROOT,
            "XUANJIAN_HOST": "127.0.0.1",
            "XUANJIAN_PORT": str(cls.port),
            "XUANJIAN_FRONTEND_DIST": cls.mock_dist,
            "XUANJIAN_DATA_DIR": cls.temp_data
        })

        cls.server_proc = subprocess.Popen(
            [sys.executable, SERVER_PY],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        ready = False
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline and cls.server_proc.poll() is None:
            try:
                with LOCAL_OPENER.open(f"{cls.base_url}/api/health", timeout=1.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.15)
        if not ready:
            exit_code = cls.server_proc.poll()
            cls.server_proc.terminate()
            raise RuntimeError(f"随机端口静态安全测试服务启动失败: {cls.base_url}; exit={exit_code}")

        if cls.server_proc.poll() is not None:
            raise RuntimeError("静态安全测试子进程意外退出")
        with LOCAL_OPENER.open(f"{cls.base_url}/api/system/info", timeout=2.0) as resp:
            import json
            info = json.load(resp)
            if info.get("pid") != cls.server_proc.pid:
                cls.server_proc.terminate()
                raise RuntimeError(f"端口冲突或实例不匹配: expected PID {cls.server_proc.pid}, got {info.get('pid')}")
            if os.path.realpath(info.get("data_dir", "")) != os.path.realpath(cls.temp_data):
                cls.server_proc.terminate()
                raise RuntimeError(f"服务数据目录脱离沙盒: {info.get('data_dir')}")
            if not os.path.realpath(info.get("db_path", "")).startswith(os.path.realpath(cls.temp_data)):
                cls.server_proc.terminate()
                raise RuntimeError(f"数据库路径脱离沙盒: {info.get('db_path')}")

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc:
            cls.server_proc.terminate()
            try:
                cls.server_proc.wait(timeout=3.0)
            except Exception:
                cls.server_proc.kill()
        if cls.temp_dir and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _get_url(self, relative_url: str):
        url = f"{self.base_url}{relative_url}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SecurityTest/1.0",
                "Host": f"127.0.0.1:{self.port}"
            }
        )
        try:
            with LOCAL_OPENER.open(req) as resp:
                return resp.status, resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="ignore")

    def test_1_normal_resource_access(self):
        """测试正常合法静态资源访问，必须返回 200 并包含预期内容"""
        status, body = self._get_url("/temp_mock_normal.txt")
        self.assertEqual(status, 200)
        self.assertIn("CANARY_NORMAL_CONTENT_OK", body)

    def test_2_dot_dot_traversal_blocked(self):
        """测试 ../ 路径穿越，必须返回 403 禁止访问"""
        status, body = self._get_url("/../temp_outside_secret.txt")
        self.assertEqual(status, 403)
        self.assertIn("禁止越界访问", body)
        self.assertNotIn("CANARY_OUTSIDE_SECRET_LEAK", body)

    def test_3_encoded_path_traversal_blocked(self):
        """测试 URL 编码的路径穿越 (%2e%2e%2f)，必须解码并返回 403"""
        status, body = self._get_url("/%2e%2e%2ftemp_outside_secret.txt")
        self.assertEqual(status, 403)
        self.assertIn("禁止越界访问", body)
        self.assertNotIn("CANARY_OUTSIDE_SECRET_LEAK", body)

    def test_4_same_prefix_sibling_dir_blocked(self):
        """测试同名前缀兄弟目录攻击 (dist_fake)，必须返回 403，绝不因 startswith 误判"""
        status, body = self._get_url("/../dist_fake/secret.txt")
        self.assertEqual(status, 403)
        self.assertIn("禁止越界访问", body)
        self.assertNotIn("CANARY_SIBLING_SECRET", body)

    def test_5_symlink_out_of_bounds_blocked(self):
        """测试越界符号链接，解析 realpath 发现目标在 dist 外部时必须返回 403"""
        if not os.path.islink(self.symlink_file):
            self.skipTest("当前系统环境不支持创建符号链接，跳过")
        status, body = self._get_url("/temp_mock_symlink.txt")
        self.assertEqual(status, 403)
        self.assertIn("禁止越界访问", body)
        self.assertNotIn("CANARY_OUTSIDE_SECRET_LEAK", body)

if __name__ == "__main__":
    unittest.main()
