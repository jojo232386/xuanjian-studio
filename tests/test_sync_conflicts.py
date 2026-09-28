#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_sync_conflicts.py - 真实本地 WebDAV 服务与双实例冲突解决闭环测试 (Section A)

物理验证：
1. 启动本地真实 WebDAV HTTP 测试服务 (127.0.0.1:端口)；
2. 两个独立数据目录 (db_a, db_b) 经由实际 HTTP PUT/GET 传输数据；
3. 同一记录两端并发离线修改，验证两版内容完整保留（主记录 + 冲突副本）；
4. 注入设备时钟相差正负五分钟 (±300s)，验证冲突副本仍然生成，不因墙上时钟抹除内容；
5. 一端删除、一端修改冲突，验证删除标记可传播且独立修改被保护性恢复；
6. 验证重复同步幂等性，不产生无限复制；
7. 验证远端被并发更新时的条件写入冲突拦截 (SyncConflictError)。
"""

import os
import shutil
import tempfile
import unittest
import threading
import base64
import json
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List

from xuanjian.storage import XuanJianStorage
from xuanjian.sync_service import (
    WebDAVSyncConfig,
    sync_push,
    sync_pull_and_merge,
    SyncConflictError,
    export_sync_snapshot
)

class MockWebDAVHandler(BaseHTTPRequestHandler):
    """用于测试的真实 HTTP WebDAV 服务端 Handler"""
    server_storage: Dict[str, bytes] = {}
    request_log: List[Dict[str, Any]] = []

    def log_message(self, format: str, *args: Any) -> None:
        pass  # 静默测试日志

    def _check_auth(self) -> bool:
        auth_header = self.headers.get("Authorization", "")
        expected = "Basic " + base64.b64encode(b"testuser:testpass").decode("ascii")
        if auth_header != expected:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="TestWebDAV"')
            self.end_headers()
            return False
        return True

    def do_OPTIONS(self):
        if not self._check_auth():
            return
        self.send_response(200)
        self.send_header("DAV", "1, 2")
        self.send_header("Allow", "GET, HEAD, POST, PUT, DELETE, OPTIONS, PROPFIND")
        self.end_headers()

    def do_PROPFIND(self):
        if not self._check_auth():
            return
        self.request_log.append({"method": "PROPFIND", "path": self.path})
        if self.path in self.server_storage:
            self.send_response(207)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<multistatus></multistatus>")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if not self._check_auth():
            return
        self.request_log.append({"method": "GET", "path": self.path})
        if self.path in self.server_storage:
            content = self.server_storage[self.path]
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if not self._check_auth():
            return
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        self.server_storage[self.path] = body
        self.request_log.append({"method": "PUT", "path": self.path, "bytes_received": len(body)})
        self.send_response(201)
        self.end_headers()


class TestSyncConflictResolution(unittest.TestCase):
    """测试 WebDAV 同步冲突解决与双端数据无损保存"""

    @classmethod
    def setUpClass(cls):
        # 启动真实后台 WebDAV HTTP 服务器
        MockWebDAVHandler.server_storage = {}
        MockWebDAVHandler.request_log = []
        cls.httpd = HTTPServer(("127.0.0.1", 0), MockWebDAVHandler)
        cls.server_port = cls.httpd.server_address[1]
        cls.server_url = f"http://127.0.0.1:{cls.server_port}"
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_a_path = os.path.join(self.temp_dir, "instance_a.db")
        self.db_b_path = os.path.join(self.temp_dir, "instance_b.db")
        self.storage_a = XuanJianStorage(self.db_a_path)
        self.storage_b = XuanJianStorage(self.db_b_path)

        self.sync_cfg_a = WebDAVSyncConfig(
            enabled=True,
            server_url=self.server_url,
            username="testuser",
            password="testpass",
            remote_path="/test_backup.enc",
            encryption_passphrase="sync_passphrase_888"
        )
        self.sync_cfg_b = WebDAVSyncConfig(
            enabled=True,
            server_url=self.server_url,
            username="testuser",
            password="testpass",
            remote_path="/test_backup.enc",
            encryption_passphrase="sync_passphrase_888"
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_1_concurrent_offline_edits_preserve_both_versions(self):
        """
        场景 1: 同一记录两端并发离线修改 -> 重新同步 -> 完整保留两版本 (主记录 + 冲突副本)
        """
        # 初始：A 端创建初始记录 R101 并通过 HTTP 推送到 WebDAV
        self.storage_a.create_record({
            "id": "REC_CONCURRENT_101",
            "record_type": "divination",
            "title": "初始基线卦例",
            "topic": "既济卦初始分析"
        })
        push_res = sync_push(self.storage_a, self.sync_cfg_a)
        self.assertTrue(push_res["success"])
        self.assertGreater(len(MockWebDAVHandler.request_log), 0)

        # B 端从 WebDAV 拉取基线
        pull_res_b = sync_pull_and_merge(self.storage_b, self.sync_cfg_b)
        self.assertTrue(pull_res_b["success"])
        self.assertEqual(pull_res_b["inserted"], 1)

        # 模拟两端离线：两端分别对 REC_CONCURRENT_101 进行独立修改
        now = datetime.now(timezone.utc)
        time_a = (now + timedelta(seconds=1)).isoformat()
        time_b = (now + timedelta(seconds=10)).isoformat()  # B 端稍新

        self.storage_a.update_record("REC_CONCURRENT_101", {
            "title": "A 端离线修改版本：强调预防违约",
            "review_data": {"notes": "A端独有见解：需查验保证金"},
            "updated_at": time_a
        })

        self.storage_b.update_record("REC_CONCURRENT_101", {
            "title": "B 端离线修改版本：强调加速交付",
            "review_data": {"notes": "B端独有见解：需调整生产排期"},
            "updated_at": time_b
        })

        # B 端先连网并推送到 WebDAV (HTTP PUT)
        push_b = sync_push(self.storage_b, self.sync_cfg_b, force=True)
        self.assertTrue(push_b["success"])

        # A 端重连，先拉取远端快照并协同合并 (HTTP GET -> merge_snapshots)
        merge_res_a = sync_pull_and_merge(self.storage_a, self.sync_cfg_a)
        self.assertTrue(merge_res_a["success"])
        self.assertGreaterEqual(merge_res_a["conflicts_resolved"], 1)
        self.assertGreaterEqual(len(merge_res_a["conflict_copies_created"]), 1)

        # 检查 A 端数据真实状态：两端修改必须全部存在于本地数据库中！
        all_recs_a, total_a = self.storage_a.list_records(limit=10)
        titles_a = [r["title"] for r in all_recs_a]

        # 验证：B 端的最新版本成为主记录
        primary_rec = self.storage_a.get_record("REC_CONCURRENT_101")
        self.assertEqual(primary_rec["title"], "B 端离线修改版本：强调加速交付")
        self.assertIn("需调整生产排期", primary_rec.get("review_data", {}).get("notes", ""))

        # 验证：A 端的离线修改被自动完整保留在 [冲突副本] 中，绝未丢失！
        conflict_rec_id = merge_res_a["conflict_copies_created"][0]
        conflict_rec = self.storage_a.get_record(conflict_rec_id)
        self.assertIsNotNone(conflict_rec)
        self.assertIn("[冲突副本]", conflict_rec["title"])
        self.assertIn("A 端离线修改版本", conflict_rec["title"])
        self.assertIn("需查验保证金", conflict_rec.get("review_data", {}).get("notes", ""))
        self.assertIn("冲突溯源", conflict_rec.get("review_data", {}).get("notes", ""))

        print("\n  [✓ 验证通过] 双端并发离线编辑：两端版本均已完整找回并以 [冲突副本] 保留。")

    def test_2_clock_skew_tolerance_preserves_both_contents(self):
        """
        场景 2: 注入设备时钟相差正负五分钟 (±300s)，冲突依然被准确捕获并双向保留
        """
        self.storage_a.create_record({
            "id": "REC_SKEW_102",
            "record_type": "reflection",
            "title": "基线知止卡",
            "topic": "时钟偏移测试"
        })
        sync_push(self.storage_a, self.sync_cfg_a, force=True)
        sync_pull_and_merge(self.storage_b, self.sync_cfg_b)

        # 模拟时钟漂移：A 端时钟落后 5 分钟 (-300s)，B 端时钟超前 5 分钟 (+300s)
        now = datetime.now(timezone.utc)
        skewed_time_a = (now - timedelta(seconds=300)).isoformat()
        skewed_time_b = (now + timedelta(seconds=300)).isoformat()

        self.storage_a.update_record("REC_SKEW_102", {
            "title": "A 端慢5分钟的笔记内容",
            "updated_at": skewed_time_a
        })
        self.storage_b.update_record("REC_SKEW_102", {
            "title": "B 端快5分钟的笔记内容",
            "updated_at": skewed_time_b
        })

        # B 端推送，A 端拉取
        sync_push(self.storage_b, self.sync_cfg_b, force=True)
        res = sync_pull_and_merge(self.storage_a, self.sync_cfg_a)

        self.assertGreaterEqual(res["conflicts_resolved"], 1)
        records_in_a, count_in_a = self.storage_a.list_records(limit=10)
        titles = [r["title"] for r in records_in_a]

        # 确认即便时钟相差10分钟，A端与B端两份文本都健在！
        self.assertTrue(any("快5分钟" in t for t in titles))
        self.assertTrue(any("慢5分钟" in t for t in titles))
        print("  [✓ 验证通过] 时钟注入 ±5 分钟漂移测试：基于实质内容差异准确触发冲突副本，无盲目抹除。")

    def test_3_delete_vs_edit_conflict_and_tombstone_propagation(self):
        """
        场景 3: 一端删除、一端修改冲突测试：
        - 若删除较新且修改端未见删除，修改内容应被保护性恢复 (抢救为独立卡片)，主记录接受删除；
        - 若修改较新，修改端胜出并保留。
        """
        # 创建公共条目
        self.storage_a.create_record({
            "id": "REC_DEL_CONFLICT_103",
            "record_type": "study_note",
            "title": "待查经义短读"
        })
        sync_push(self.storage_a, self.sync_cfg_a, force=True)
        sync_pull_and_merge(self.storage_b, self.sync_cfg_b)

        now = datetime.now(timezone.utc)
        # A 端软删除该记录
        self.storage_a.delete_record("REC_DEL_CONFLICT_103")
        # 确认 A 端已软删除
        self.assertIsNone(self.storage_a.get_record("REC_DEL_CONFLICT_103", include_deleted=False))

        # B 端在不知情下对该条目追加了关键心得 (但时间稍早于删除)
        self.storage_b.update_record("REC_DEL_CONFLICT_103", {
            "review_data": {"notes": "B 端极为重要的古籍引证笔记，绝不可丢失！"},
            "updated_at": (now - timedelta(seconds=10)).isoformat()
        })

        # A 端先推送到云端 (携带墓碑 is_deleted=1)
        sync_push(self.storage_a, self.sync_cfg_a, force=True)

        # B 端拉取 A 端的删除
        merge_res_b = sync_pull_and_merge(self.storage_b, self.sync_cfg_b)

        # 核心断言：主条目已按远端意图被标记删除
        rec_b_main = self.storage_b.get_record("REC_DEL_CONFLICT_103", include_deleted=True)
        self.assertEqual(rec_b_main["is_deleted"], 1)

        # 但是：B 端的心得笔记被保护性恢复并提取为 [恢复未删笔记]，未被无声抹去！
        b_active_records, _ = self.storage_b.list_records(limit=10, include_deleted=False)
        rescued_recs = [r for r in b_active_records if "恢复未删笔记" in r["title"]]
        self.assertEqual(len(rescued_recs), 1)
        self.assertIn("极为重要的古籍引证笔记", rescued_recs[0]["review_data"]["notes"])
        print("  [✓ 验证通过] 删除 vs 修改冲突：主记录墓碑传播成功，且未同步笔记被保护性恢复。")

    def test_4_idempotency_and_conditional_write_protection(self):
        """
        场景 4: 重复同步幂等性与远端更新条件写入保护 (SyncConflictError)
        """
        # 建立记录并推送
        self.storage_a.create_record({
            "id": "REC_IDEMP_104",
            "record_type": "divination",
            "title": "幂等性测试卡"
        })
        push_1 = sync_push(self.storage_a, self.sync_cfg_a, force=True)
        self.assertTrue(push_1["success"])

        # 连续两次拉取，记录数与冲突数不变 (幂等)
        pull_1 = sync_pull_and_merge(self.storage_b, self.sync_cfg_b)
        count_after_first = pull_1["final_local_total"]

        pull_2 = sync_pull_and_merge(self.storage_b, self.sync_cfg_b)
        self.assertEqual(pull_2["final_local_total"], count_after_first)
        self.assertEqual(pull_2["conflicts_resolved"], 0)
        self.assertEqual(pull_2["inserted"], 0)

        # 远端并发保护测试：
        # B 端推送了更新，A 端的 last_synced_remote_sha256 已经过期
        self.storage_b.update_record("REC_IDEMP_104", {"title": "B 端推进了版本"})
        sync_push(self.storage_b, self.sync_cfg_b, force=True)

        # A 端如果直接不经 pull 尝试 push (force=False)，必须被 SyncConflictError 拦截！
        with self.assertRaises(SyncConflictError):
            sync_push(self.storage_a, self.sync_cfg_a, force=False)

        print("  [✓ 验证通过] 幂等性与条件写入保护：重复同步无无限复制，远端变动拦截盲目覆盖。")

if __name__ == "__main__":
    unittest.main()
