# tests/test_server_records_api.py - 本地 SQLite 记录 API 与安全访问控制测试 (严格隔离)

import unittest
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import sys
import time
import socket
import tempfile
import shutil
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


class TestServerRecordsAPI(unittest.TestCase):
    server_proc = None
    port = None
    base_url = None
    temp_dir = None

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="xuanjian_test_records_")
        cls.port = find_free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        env = make_clean_sandbox_env({
            "PYTHONPATH": PROJECT_ROOT,
            "XUANJIAN_HOST": "127.0.0.1",
            "XUANJIAN_PORT": str(cls.port),
            "XUANJIAN_DATA_DIR": cls.temp_dir,
            "XUANJIAN_ALLOW_CLEAR_RECORDS": "1"
        })

        cls.server_proc = subprocess.Popen(
            [sys.executable, SERVER_PY],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 等待随机端口隔离服务就绪
        ready = False
        last_error = ""
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline and cls.server_proc.poll() is None:
            try:
                req = urllib.request.Request(f"{cls.base_url}/api/health")
                with LOCAL_OPENER.open(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception as exc:
                last_error = str(exc)
                time.sleep(0.15)
        if not ready:
            exit_code = cls.server_proc.poll()
            if exit_code is None:
                cls.server_proc.terminate()
            _, stderr = cls.server_proc.communicate(timeout=5)
            raise RuntimeError(
                f"随机端口测试服务启动失败: {cls.base_url}; exit={exit_code}; "
                f"last_error={last_error}; stderr={stderr[-500:]!r}"
            )

        # 严格验证实例身份与沙盒目录匹配
        if cls.server_proc.poll() is not None:
            raise RuntimeError("测试子进程意外退出")
        req_info = urllib.request.Request(f"{cls.base_url}/api/system/info")
        with LOCAL_OPENER.open(req_info, timeout=2.0) as resp:
            info = json.load(resp)
            if info.get("pid") != cls.server_proc.pid:
                cls.server_proc.terminate()
                raise RuntimeError(f"端口冲突或实例不匹配: expected PID {cls.server_proc.pid}, got {info.get('pid')}")
            if os.path.realpath(info.get("data_dir", "")) != os.path.realpath(cls.temp_dir):
                cls.server_proc.terminate()
                raise RuntimeError(f"服务数据目录脱离沙盒: {info.get('data_dir')}")
            if not os.path.realpath(info.get("db_path", "")).startswith(os.path.realpath(cls.temp_dir)):
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

    def setUp(self):
        # 发送清空请求前严格前置检查：确认子进程存活且实例身份匹配沙盒
        self.assertIsNone(self.server_proc.poll(), "测试子进程已异常退出，禁止发送清空请求")
        req_info = urllib.request.Request(f"{self.base_url}/api/system/info")
        with LOCAL_OPENER.open(req_info, timeout=2.0) as resp:
            info = json.load(resp)
            self.assertEqual(info.get("pid"), self.server_proc.pid, "端口响应进程 PID 不匹配，拒绝发送清空请求")
            self.assertEqual(os.path.realpath(info.get("data_dir", "")), os.path.realpath(self.temp_dir), "服务数据目录脱离测试沙盒，拒绝发送清空请求")
            self.assertTrue(os.path.realpath(info.get("db_path", "")).startswith(os.path.realpath(self.temp_dir)), "数据库路径脱离测试沙盒，拒绝发送清空请求")

        # 清除临时隔离实例中的记录
        req = urllib.request.Request(
            f"{self.base_url}/api/records/clear",
            data=b"{}",
            headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{self.port}"},
            method="POST"
        )
        LOCAL_OPENER.open(req)

    def test_post_get_and_delete_record(self):
        """测试通过 HTTP API 新建、查询、更新与删除记录"""
        payload = {
            "record_type": "divination",
            "title": "API测试卦例：既济之贲",
            "topic": "测试HTTP接口保存",
            "tags": ["测试", "既济"],
            "calculation_result": {"hexagram": "既济"},
            "review_data": {"notes": "初始测试笔记"}
        }

        # 1. POST /api/records
        req = urllib.request.Request(
            f"{self.base_url}/api/records",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{self.port}"},
            method="POST"
        )
        with LOCAL_OPENER.open(req) as resp:
            self.assertEqual(resp.status, 201)
            created = json.loads(resp.read().decode("utf-8"))
            rec_id = created["id"]
            self.assertEqual(created["title"], "API测试卦例：既济之贲")

        # 2. GET /api/records/<id>
        with LOCAL_OPENER.open(f"{self.base_url}/api/records/{rec_id}") as resp:
            self.assertEqual(resp.status, 200)
            fetched = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(fetched["id"], rec_id)

        # 3. GET /api/records (带中文关键词搜索)
        query_url = f"{self.base_url}/api/records?query=" + urllib.parse.quote("既济")
        with LOCAL_OPENER.open(query_url) as resp:
            list_res = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(list_res["total"], 1)
            self.assertEqual(list_res["records"][0]["id"], rec_id)

        # 4. PUT /api/records/<id> (更新复盘内容)
        update_payload = {
            "review_data": {
                "original_thought": "原先以为一次通过",
                "actual_outcome": "实测接口非常稳定",
                "notes": "更新成功"
            }
        }
        put_req = urllib.request.Request(
            f"{self.base_url}/api/records/{rec_id}",
            data=json.dumps(update_payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{self.port}"},
            method="PUT"
        )
        with LOCAL_OPENER.open(put_req) as resp:
            self.assertEqual(resp.status, 200)
            updated = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(updated["review_data"]["actual_outcome"], "实测接口非常稳定")

        # 5. DELETE /api/records/<id>
        del_req = urllib.request.Request(
            f"{self.base_url}/api/records/{rec_id}",
            headers={"Host": f"127.0.0.1:{self.port}"},
            method="DELETE"
        )
        with LOCAL_OPENER.open(del_req) as resp:
            self.assertEqual(resp.status, 200)

        # 再次获取应该 404
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            LOCAL_OPENER.open(f"{self.base_url}/api/records/{rec_id}")
        self.assertEqual(ctx.exception.code, 404)

    def test_dns_rebinding_and_cross_origin_blocked(self):
        """核心安全防线：拦截伪造非本地 Host 及跨站 Origin 的写入请求 (403)"""
        payload = {"title": "恶意攻击者试图注入的数据"}

        # 1. 非法 Host 请求 (例如攻击者域名 attacker-domain.com)
        req_bad_host = urllib.request.Request(
            f"{self.base_url}/api/records",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Host": "attacker-domain.com"
            },
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            LOCAL_OPENER.open(req_bad_host)
        self.assertEqual(ctx.exception.code, 403)

        # 2. 跨站 Origin 请求 (例如来自 https://malicious-site.org)
        req_bad_origin = urllib.request.Request(
            f"{self.base_url}/api/records",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Host": f"127.0.0.1:{self.port}",
                "Origin": "https://malicious-site.org"
            },
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            LOCAL_OPENER.open(req_bad_origin)
        self.assertEqual(ctx.exception.code, 403)

    def test_clear_records_safeguard_forbidden_without_env_flag(self):
        """测试安全防护：若未显式声明 XUANJIAN_ALLOW_CLEAR_RECORDS=1，接口坚决返回 403 拒绝清空"""
        temp_dir2 = tempfile.mkdtemp(prefix="xuanjian_test_safeguard_")
        port2 = find_free_port()
        base_url2 = f"http://127.0.0.1:{port2}"

        env = make_clean_sandbox_env({
            "PYTHONPATH": PROJECT_ROOT,
            "XUANJIAN_HOST": "127.0.0.1",
            "XUANJIAN_PORT": str(port2),
            "XUANJIAN_DATA_DIR": temp_dir2
        })

        proc = subprocess.Popen(
            [sys.executable, SERVER_PY],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            # 等待启动
            ready2 = False
            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline and proc.poll() is None:
                try:
                    with LOCAL_OPENER.open(f"{base_url2}/api/health", timeout=1.0) as resp:
                        if resp.status == 200:
                            ready2 = True
                            break
                except Exception:
                    time.sleep(0.15)

            self.assertTrue(ready2, f"临时测试服务未能启动: {base_url2}; exit={proc.poll()}")
            self.assertIsNone(proc.poll(), "临时测试子进程已意外退出")
            req_info = urllib.request.Request(f"{base_url2}/api/system/info")
            with LOCAL_OPENER.open(req_info, timeout=2.0) as resp:
                info = json.load(resp)
                self.assertEqual(info.get("pid"), proc.pid, "PID 不匹配")
                self.assertEqual(os.path.realpath(info.get("data_dir", "")), os.path.realpath(temp_dir2))
                self.assertTrue(os.path.realpath(info.get("db_path", "")).startswith(os.path.realpath(temp_dir2)))

            req = urllib.request.Request(
                f"{base_url2}/api/records/clear",
                data=b"{}",
                headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{port2}"},
                method="POST"
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                LOCAL_OPENER.open(req)
            self.assertEqual(ctx.exception.code, 403)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()
            if os.path.exists(temp_dir2):
                shutil.rmtree(temp_dir2, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
