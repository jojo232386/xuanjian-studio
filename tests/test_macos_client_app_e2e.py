# tests/test_macos_client_app_e2e.py - 玄鉴·书房 v3.0.1 macOS 客户 App 独立端到端验收套件
# 覆盖：冷启动沙箱、四术与典籍全流程、数据持久性、升级兼容性、异常与损坏隔离防护

import os
import sys
import unittest
import subprocess
import time
import json
import tempfile
import shutil
import urllib.request
import urllib.error
import socket

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(PROJECT_ROOT, "dist", "玄鉴·书房.app")
SERVER_BIN = os.path.join(APP_PATH, "Contents", "Resources", "server", "xuanjian_server")
NODE_BIN = os.path.join(APP_PATH, "Contents", "Resources", "node", "bin", "node")
WORKER_BUNDLE = os.path.join(APP_PATH, "Contents", "Resources", "scripts", "calc_worker.bundle.js")
FRONTEND_DIST = os.path.join(APP_PATH, "Contents", "Resources", "frontend", "dist")


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_request(url: str, method: str = "GET", data: dict = None, headers: dict = None, port: int = 8990) -> tuple:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    default_headers = {
        "Host": f"127.0.0.1:{port}",
        "Content-Type": "application/json"
    }
    if headers:
        default_headers.update(headers)
    req_body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_body, headers=default_headers, method=method)
    try:
        with opener.open(req, timeout=5.0) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as he:
        body = he.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"error": body}
        return he.code, parsed


class TestMacOSClientAppE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 确保 .app 已编译生成
        if not os.path.exists(SERVER_BIN):
            subprocess.check_call([sys.executable, os.path.join(PROJECT_ROOT, "scripts", "build_macos_client_app.py")])

    def test_00_bundled_license_notices(self):
        licenses = os.path.join(APP_PATH, "Contents", "Resources", "LICENSES")
        required = (
            "XuanJian-LICENSE",
            "Node-LICENSE",
            "Python-LICENSE",
            "iztro-LICENSE",
            "bigfishmarquis-qimen-LICENSE",
            "python-packages/lunar_python/LICENSE",
            "python-packages/cryptography/LICENSE",
            "npm-packages/react/LICENSE",
            "npm-packages/lucide-react/LICENSE",
        )
        for path in required:
            self.assertTrue(os.path.isfile(os.path.join(licenses, path)), path)
        with open(os.path.join(licenses, "LICENSE_SUMMARY.md"), encoding="utf-8") as stream:
            self.assertIn("Node.js distribution LICENSE", stream.read())

    def test_01_cold_machine_simulation_and_persistence(self):
        """
        1. Cold Machine Simulation:
        在一个彻底屏蔽系统 Node/Python、没有项目依赖、纯隔离沙箱环境中启动 App。
        验证：
        - 打开并使用私有 runtime
        - 历法 / 书房
        - 周易象数起卦
        - 八字排盘
        - 紫微斗数排盘 (私有 Node Worker 驱动)
        - 奇门遁甲排盘 (私有 Node Worker 驱动)
        - 道德经全息研读
        - 记录保存与时间轴
        - 加密备份导出
        - 服务停止
        - 再次启动，数据完好无损持久化
        """
        with tempfile.TemporaryDirectory() as td:
            isolated_data = os.path.join(td, "XuanJianData")
            os.makedirs(isolated_data, exist_ok=True)
            port = find_free_port()

            # 屏蔽外部开发环境，仅保留基础系统工具目录，显式剔除外部数据库变量
            clean_env = {
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "XUANJIAN_DATA_DIR": isolated_data,
                "XUANJIAN_HOST": "127.0.0.1",
                "XUANJIAN_PORT": str(port),
                "XUANJIAN_NODE_PATH": NODE_BIN,
                "XUANJIAN_WORKER_PATH": WORKER_BUNDLE,
                "XUANJIAN_FRONTEND_DIST": FRONTEND_DIST,
                "XUANJIAN_APP_MODE": "1"
            }

            # 启动 App 内部编译的独立服务端
            proc = subprocess.Popen(
                [SERVER_BIN],
                env=clean_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                # 等待服务就绪
                ready = False
                for _ in range(30):
                    time.sleep(0.4)
                    try:
                        st, res = make_request(f"http://127.0.0.1:{port}/api/health", port=port)
                        if st == 200 and res.get("status") == "healthy":
                            ready = True
                            break
                    except Exception:
                        pass
                self.assertTrue(ready, "独立客户端服务在屏蔽外部环境中未能正常就绪")
                self.assertIsNone(proc.poll(), "独立客户端服务已异常退出")

                # (1) 系统信息自检：确认使用的是内置私有运行时与隔离数据目录，核对实例 PID 避免端口混淆
                st, sys_info = make_request(f"http://127.0.0.1:{port}/api/system/info", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(sys_info.get("pid"), proc.pid, "端口响应服务 PID 不匹配，拒绝继续测试")
                self.assertEqual(sys_info["version"], "3.0.1")
                self.assertEqual(os.path.realpath(sys_info["data_dir"]), os.path.realpath(isolated_data))
                self.assertTrue(os.path.realpath(sys_info["db_path"]).startswith(os.path.realpath(isolated_data)))
                self.assertTrue(sys_info["node_runtime"]["is_bundled"])

                # (2) 历法查询
                st, cal = make_request(f"http://127.0.0.1:{port}/api/calendar?date=2026-09-26", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(cal["solar"]["year"], 2026)

                # (3) 周易起卦
                st, iching_res = make_request(
                    f"http://127.0.0.1:{port}/api/iching/calculate",
                    method="POST",
                    data={"lines": [7, 8, 7, 8, 9, 6]},
                    port=port
                )
                self.assertEqual(st, 200)
                self.assertIn("original_hexagram", iching_res)

                # (4) 八字推算
                st, bazi_res = make_request(
                    f"http://127.0.0.1:{port}/api/bazi/calculate",
                    method="POST",
                    data={"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "男"},
                    port=port
                )
                self.assertEqual(st, 200)
                self.assertEqual(bazi_res["four_pillars"]["year"]["gan_zhi"], "庚午")

                # (5) 紫微斗数 (通过私有 Node 执行)
                st, ziwei_res = make_request(
                    f"http://127.0.0.1:{port}/api/ziwei/calculate",
                    method="POST",
                    data={"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "男"},
                    port=port
                )
                self.assertEqual(st, 200)
                self.assertIn("basic", ziwei_res)
                self.assertIn("palaces", ziwei_res)
                self.assertIn("soul", ziwei_res["basic"])

                # (6) 奇门遁甲 (通过私有 Node 执行)
                st, qimen_res = make_request(
                    f"http://127.0.0.1:{port}/api/qimen/calculate",
                    method="POST",
                    data={"year": 2026, "month": 9, "day": 26, "hour": 10, "minute": 30},
                    port=port
                )
                self.assertEqual(st, 200)
                self.assertIn("palaces", qimen_res)
                self.assertIn("meta", qimen_res)

                # (7) 道德经查询
                st, dao_res = make_request(
                    f"http://127.0.0.1:{port}/api/classics/daodejing?chapter=1",
                    port=port
                )
                self.assertEqual(st, 200)
                self.assertIn("道可道，非常道", dao_res["original_text"])

                # (8) 新建手记记录
                rec_payload = {
                    "record_type": "divination",
                    "title": "冷启动验证手记：既济之象",
                    "topic": "独立客户版端到端全流程验收",
                    "tags": ["验收", "冷启动", "既济"],
                    "calculation_result": iching_res,
                    "review_data": {"notes": "沙箱持久化测试"}
                }
                st, created_rec = make_request(
                    f"http://127.0.0.1:{port}/api/records",
                    method="POST",
                    data=rec_payload,
                    port=port
                )
                self.assertEqual(st, 201)
                rec_id = created_rec["id"]

                # (9) 导出 AES-256 加密备份
                st, backup_res = make_request(
                    f"http://127.0.0.1:{port}/api/backup/export",
                    method="POST",
                    data={"passphrase": "StrongClientPassword123!"},
                    port=port
                )
                self.assertEqual(st, 200)
                self.assertIn("data", backup_res)

                # (10) 安全停止服务
                st, shut_res = make_request(
                    f"http://127.0.0.1:{port}/api/system/shutdown",
                    method="POST",
                    data={},
                    port=port
                )
                self.assertEqual(st, 200)
                proc.wait(timeout=3.0)
                self.assertEqual(proc.returncode, 0)

            finally:
                if proc.poll() is None:
                    proc.kill()

            # (11) 再次启动服务，验证数据完好无损持久化
            port2 = find_free_port()
            clean_env["XUANJIAN_PORT"] = str(port2)
            proc2 = subprocess.Popen([SERVER_BIN], env=clean_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                ready2 = False
                for _ in range(30):
                    time.sleep(0.3)
                    try:
                        st, res = make_request(f"http://127.0.0.1:{port2}/api/health", port=port2)
                        if st == 200:
                            ready2 = True
                            break
                    except Exception:
                        pass
                self.assertTrue(ready2, f"二次启动客户端服务未能就绪: {port2}")
                self.assertIsNone(proc2.poll(), "二次启动客户端服务已异常退出")

                st, sys_info2 = make_request(f"http://127.0.0.1:{port2}/api/system/info", port=port2)
                self.assertEqual(st, 200)
                self.assertEqual(sys_info2.get("pid"), proc2.pid, "PID 不匹配，可能误连他人实例")
                self.assertEqual(os.path.realpath(sys_info2["data_dir"]), os.path.realpath(isolated_data))
                self.assertTrue(os.path.realpath(sys_info2["db_path"]).startswith(os.path.realpath(isolated_data)))

                # 检索先前创建的手记
                st, fetched_rec = make_request(f"http://127.0.0.1:{port2}/api/records/{rec_id}", port=port2)
                self.assertEqual(st, 200)
                self.assertEqual(fetched_rec["title"], "冷启动验证手记：既济之象")
                self.assertEqual(fetched_rec["topic"], "独立客户版端到端全流程验收")

                # 验证统计接口
                st, stats = make_request(f"http://127.0.0.1:{port2}/api/records/statistics", port=port2)
                self.assertEqual(st, 200)
                self.assertGreaterEqual(stats["total_records"], 1)

                # 停止服务
                make_request(f"http://127.0.0.1:{port2}/api/system/shutdown", method="POST", data={}, port=port2)
                proc2.wait(timeout=3.0)
            finally:
                if proc2.poll() is None:
                    proc2.kill()

    def test_02_upgrade_data_migration_safety(self):
        """
        2. 更新测试：
        模拟旧版 v3.0 客户数据目录存在历史数据库，
        用新 v3.0.1 客户端启动，验证历史数据 100% 完整保留，不被清空。
        """
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "xuanjian.db")

            # 模拟创建旧版数据
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL
            );
            """)
            conn.execute("INSERT INTO schema_migrations VALUES (1, '2026-09-25T00:00:00Z', 'v3.0.0 baseline');")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL, record_type TEXT NOT NULL,
                title TEXT NOT NULL, topic TEXT, tags TEXT, calculation_result_json TEXT,
                layered_interpretation_json TEXT, review_data_json TEXT, engine_version TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, is_deleted INTEGER DEFAULT 0,
                sync_version INTEGER DEFAULT 1
            );
            """)
            conn.execute("""
            INSERT INTO records VALUES (
                'REC_UPGRADE_TEST', 1, 'divination', '旧版历史卦例：乾为天', '升级保护验证',
                '["旧版", "乾卦"]', '{}', '{}', '{"notes": "珍贵历史笔记勿丢失"}', '3.0.0',
                '2026-09-25T10:00:00Z', '2026-09-25T10:00:00Z', 0, 1
            );
            """)
            conn.commit()
            conn.close()

            # 使用 v3.0.1 启动
            port = find_free_port()
            env = {
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "XUANJIAN_DATA_DIR": td,
                "XUANJIAN_HOST": "127.0.0.1",
                "XUANJIAN_PORT": str(port),
                "XUANJIAN_NODE_PATH": NODE_BIN,
                "XUANJIAN_WORKER_PATH": WORKER_BUNDLE,
                "XUANJIAN_FRONTEND_DIST": FRONTEND_DIST,
                "XUANJIAN_APP_MODE": "1"
            }
            proc = subprocess.Popen([SERVER_BIN], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                ready = False
                for _ in range(30):
                    time.sleep(0.3)
                    try:
                        st, res = make_request(f"http://127.0.0.1:{port}/api/health", port=port)
                        if st == 200:
                            ready = True
                            break
                    except Exception:
                        pass
                self.assertTrue(ready, f"升级保护测试服务未能就绪: {port}")
                self.assertIsNone(proc.poll(), "升级保护测试服务已异常退出")

                st, sys_info = make_request(f"http://127.0.0.1:{port}/api/system/info", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(sys_info.get("pid"), proc.pid, "PID 不匹配，可能误连他人实例")
                self.assertEqual(os.path.realpath(sys_info["data_dir"]), os.path.realpath(td))
                self.assertTrue(os.path.realpath(sys_info["db_path"]).startswith(os.path.realpath(td)))

                # 验证旧记录依然完好
                st, rec = make_request(f"http://127.0.0.1:{port}/api/records/REC_UPGRADE_TEST", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(rec["title"], "旧版历史卦例：乾为天")
                self.assertEqual(rec["review_data"]["notes"], "珍贵历史笔记勿丢失")

                make_request(f"http://127.0.0.1:{port}/api/system/shutdown", method="POST", data={}, port=port)
                proc.wait(timeout=3.0)
            finally:
                if proc.poll() is None:
                    proc.kill()

    def test_03_damage_and_fault_tolerance(self):
        """
        3. 损坏测试：
        模拟数据库文件损坏、密码错误、Node丢失等极端场景，
        均给出明确中文提示，绝不静默崩溃。
        """
        # (A) 数据库损坏隔离测试
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "xuanjian.db")
            with open(db_path, "wb") as f:
                f.write(b"CORRUPTED_GARBAGE_DATA_SQLITE_CANNOT_READ")

            port = find_free_port()
            env = {
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "XUANJIAN_DATA_DIR": td,
                "XUANJIAN_HOST": "127.0.0.1",
                "XUANJIAN_PORT": str(port),
                "XUANJIAN_NODE_PATH": NODE_BIN,
                "XUANJIAN_WORKER_PATH": WORKER_BUNDLE,
                "XUANJIAN_FRONTEND_DIST": FRONTEND_DIST,
                "XUANJIAN_APP_MODE": "1"
            }
            proc = subprocess.Popen([SERVER_BIN], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                ready = False
                for _ in range(30):
                    time.sleep(0.3)
                    try:
                        st, res = make_request(f"http://127.0.0.1:{port}/api/health", port=port)
                        if st == 200:
                            ready = True
                            break
                    except Exception:
                        pass
                self.assertTrue(ready, f"损坏隔离测试服务未能就绪: {port}")
                self.assertIsNone(proc.poll(), "损坏隔离测试服务已异常退出")

                st, sys_info = make_request(f"http://127.0.0.1:{port}/api/system/info", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(sys_info.get("pid"), proc.pid, "PID 不匹配")
                self.assertEqual(os.path.realpath(sys_info["data_dir"]), os.path.realpath(td))

                # 接口仍能正常访问，调用 records 触发存储管理器初始化与受损隔离
                st, rec_list = make_request(f"http://127.0.0.1:{port}/api/records", port=port)
                self.assertEqual(st, 200)

                # 数据库自动隔离备份，并重建干净库，生成安全提示记录
                bak_files = [f for f in os.listdir(td) if "corrupted" in f]
                self.assertGreaterEqual(len(bak_files), 1, "未生成损坏文件隔离备份")
                self.assertGreaterEqual(rec_list["total"], 1)
                self.assertIn("已隔离", rec_list["records"][0]["title"])

                make_request(f"http://127.0.0.1:{port}/api/system/shutdown", method="POST", data={}, port=port)
                proc.wait(timeout=3.0)
            finally:
                if proc.poll() is None:
                    proc.kill()

        # (B) 备份口令错误测试
        with tempfile.TemporaryDirectory() as td:
            port = find_free_port()
            env = {
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "XUANJIAN_DATA_DIR": td,
                "XUANJIAN_HOST": "127.0.0.1",
                "XUANJIAN_PORT": str(port),
                "XUANJIAN_NODE_PATH": NODE_BIN,
                "XUANJIAN_WORKER_PATH": WORKER_BUNDLE,
                "XUANJIAN_FRONTEND_DIST": FRONTEND_DIST,
                "XUANJIAN_APP_MODE": "1"
            }
            proc = subprocess.Popen([SERVER_BIN], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                ready = False
                for _ in range(30):
                    time.sleep(0.3)
                    try:
                        st, res = make_request(f"http://127.0.0.1:{port}/api/health", port=port)
                        if st == 200:
                            ready = True
                            break
                    except Exception:
                        pass
                self.assertTrue(ready, f"备份口令测试服务未能就绪: {port}")
                self.assertIsNone(proc.poll(), "备份口令测试服务已异常退出")

                st, sys_info = make_request(f"http://127.0.0.1:{port}/api/system/info", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(sys_info.get("pid"), proc.pid, "PID 不匹配")
                self.assertEqual(os.path.realpath(sys_info["data_dir"]), os.path.realpath(td))

                # 导出真实加密备份
                st, backup_res = make_request(
                    f"http://127.0.0.1:{port}/api/backup/export",
                    method="POST",
                    data={"passphrase": "CorrectPassword123"},
                    port=port
                )
                self.assertEqual(st, 200)
                enc_data = backup_res["data"]

                # 用错误口令尝试恢复
                st, err_res = make_request(
                    f"http://127.0.0.1:{port}/api/backup/restore",
                    method="POST",
                    data={"data": enc_data, "passphrase": "WrongPassword999"},
                    port=port
                )
                self.assertEqual(st, 401)
                self.assertIn("密码错误", err_res.get("message", ""))

                make_request(f"http://127.0.0.1:{port}/api/system/shutdown", method="POST", data={}, port=port)
                proc.wait(timeout=3.0)
            finally:
                if proc.poll() is None:
                    proc.kill()

        # (C) 私有 Node 缺失场景测试
        with tempfile.TemporaryDirectory() as td:
            port = find_free_port()
            env = {
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "XUANJIAN_DATA_DIR": td,
                "XUANJIAN_HOST": "127.0.0.1",
                "XUANJIAN_PORT": str(port),
                "XUANJIAN_NODE_PATH": "/nonexistent/path/to/node",
                "XUANJIAN_WORKER_PATH": WORKER_BUNDLE,
                "XUANJIAN_FRONTEND_DIST": FRONTEND_DIST,
                "XUANJIAN_APP_MODE": "1"
            }
            proc = subprocess.Popen([SERVER_BIN], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                ready = False
                for _ in range(30):
                    time.sleep(0.3)
                    try:
                        st, res = make_request(f"http://127.0.0.1:{port}/api/health", port=port)
                        if st == 200:
                            ready = True
                            break
                    except Exception:
                        pass
                self.assertTrue(ready, f"Node缺失测试服务未能就绪: {port}")
                self.assertIsNone(proc.poll(), "Node缺失测试服务已异常退出")

                st, sys_info = make_request(f"http://127.0.0.1:{port}/api/system/info", port=port)
                self.assertEqual(st, 200)
                self.assertEqual(sys_info.get("pid"), proc.pid, "PID 不匹配")
                self.assertEqual(os.path.realpath(sys_info["data_dir"]), os.path.realpath(td))

                # 调用紫微斗数排盘，断言返回友好中文错误，不泄露 traceback
                st, err_res = make_request(
                    f"http://127.0.0.1:{port}/api/ziwei/calculate",
                    method="POST",
                    data={"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "男"},
                    port=port
                )
                self.assertNotEqual(st, 200)
                err_msg = err_res.get("message", "")
                self.assertIn("紫微/奇门计算组件未能启动", err_msg)
                self.assertNotIn("Traceback", err_msg)

                make_request(f"http://127.0.0.1:{port}/api/system/shutdown", method="POST", data={}, port=port)
                proc.wait(timeout=3.0)
            finally:
                if proc.poll() is None:
                    proc.kill()


if __name__ == "__main__":
    unittest.main()
