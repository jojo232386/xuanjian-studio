#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_sync_and_backup.py - 认证加密备份与双实例合并同步测试 (F07)
"""

import os
import shutil
import tempfile
import unittest
import time
from xuanjian.backup_crypto import (
    encrypt_bytes,
    decrypt_bytes,
    create_database_backup,
    restore_database_backup,
    CryptoAuthError
)
from xuanjian.storage import XuanJianStorage
from xuanjian.sync_service import (
    WebDAVSyncConfig,
    export_sync_snapshot,
    merge_snapshots,
    update_sync_config
)

class TestSyncAndBackup(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_encrypt_decrypt_bytes_aead(self):
        """测试 AES-256-GCM 认证加密与篡改拦截"""
        data = b"Hello XuanJian Confidential Records 12345"
        passphrase = "correct_horse_battery_staple"

        # 正常加解密
        enc = encrypt_bytes(data, passphrase)
        self.assertTrue(enc.startswith(b"XUANJIAN_ENC_V1"))

        dec = decrypt_bytes(enc, passphrase)
        self.assertEqual(dec, data)

        # 错误密码拦截
        with self.assertRaises(CryptoAuthError):
            decrypt_bytes(enc, "wrong_password_attempt")

        # 密文篡改拦截 (即使只改动 1 个 bit)
        tampered = bytearray(enc)
        tampered[-1] ^= 0x01
        with self.assertRaises(CryptoAuthError):
            decrypt_bytes(bytes(tampered), passphrase)

    def test_database_backup_and_restore_cycle(self):
        """测试完整数据库快照备份与解密恢复闭环"""
        db_path = os.path.join(self.temp_dir, "original.db")
        storage = XuanJianStorage(db_path)
        storage.create_record({
            "record_type": "divination",
            "title": "既济卦研读",
            "topic": "预防",
            "tags": ["易经", "既济"]
        })
        storage.create_record({
            "record_type": "bazi",
            "title": "庚辰日元排盘",
            "tags": ["八字"]
        })

        passphrase = "secure_backup_password_888"
        backup_bytes = create_database_backup(db_path, passphrase=passphrase)
        self.assertTrue(backup_bytes.startswith(b"XUANJIAN_ENC_V1"))

        # 恢复到另一个新路径
        restored_db_path = os.path.join(self.temp_dir, "restored.db")
        result = restore_database_backup(backup_bytes, restored_db_path, passphrase=passphrase)

        self.assertTrue(result["success"])
        # 原始库含 3 条记录：1 条自动入门指引 (REC_WELCOME_001) + 2 条手动创建
        self.assertEqual(result["restored_records_count"], 3)

        # 验证恢复出来的数据库能够正常读写并查到三条记录
        restored_storage = XuanJianStorage(restored_db_path)
        records, total = restored_storage.list_records()
        self.assertEqual(total, 3)
        titles = [r["title"] for r in records]
        self.assertIn("既济卦研读", titles)
        self.assertIn("庚辰日元排盘", titles)

        # 验证错误密码无法恢复
        fake_db = os.path.join(self.temp_dir, "fail.db")
        with self.assertRaises(CryptoAuthError):
            restore_database_backup(backup_bytes, fake_db, passphrase="wrong_pass")

    def test_two_instance_lossless_merge(self):
        """测试双实例数据无损合并 (Last-Write-Wins 且双向保留)"""
        db_a_path = os.path.join(self.temp_dir, "instance_a.db")
        db_b_path = os.path.join(self.temp_dir, "instance_b.db")

        storage_a = XuanJianStorage(db_a_path)
        storage_b = XuanJianStorage(db_b_path)

        # 实例 A 创建记录 R1(v1) 和 R2(独有)
        rec1_a = storage_a.create_record({
            "id": "REC_SHARED_001",
            "record_type": "divination",
            "title": "卦例 R1 在 A 端的初始版本",
            "topic": "版本1"
        })
        storage_a.create_record({
            "id": "REC_ONLY_A_002",
            "record_type": "study_note",
            "title": "仅在 A 端建立的手记 R2"
        })

        # 稍作时间延迟保证更新时间戳递增
        time.sleep(0.01)

        # 实例 B 同步前也有 R1(但在 B 端被更新为 v2) 并有 R3(独有)
        storage_b.create_record({
            "id": "REC_SHARED_001",
            "record_type": "divination",
            "title": "卦例 R1 在 B 端被修改更新的较新版本",
            "topic": "版本2"
        })
        storage_b.create_record({
            "id": "REC_ONLY_B_003",
            "record_type": "reflection",
            "title": "仅在 B 端建立的知止卡 R3"
        })

        # 从 B 导出快照并合并至 A
        snapshot_b = export_sync_snapshot(storage_b)
        merge_res = merge_snapshots(storage_a, snapshot_b)

        # 验证合并统计：
        # REC_ONLY_B_003 应被插入 (inserted = 1)
        # REC_SHARED_001 应被更新为 B 的较新版本 (updated = 1)
        # 同时 A 端原有内容被保护性保存为冲突副本 (conflicts_resolved = 1)
        # 本地记录总数：REC_WELCOME_001 + REC_SHARED_001(updated) + REC_ONLY_A_002 + REC_ONLY_B_003 + 冲突副本 = 5
        self.assertEqual(merge_res["inserted"], 1)
        self.assertEqual(merge_res["updated"], 1)
        self.assertEqual(merge_res.get("conflicts_resolved", 0), 1)
        self.assertEqual(merge_res["final_local_total"], 5)

        # 检查 A 端数据真实状态：主记录更新为 B 端较新版本
        r1_in_a = storage_a.get_record("REC_SHARED_001")
        self.assertEqual(r1_in_a["title"], "卦例 R1 在 B 端被修改更新的较新版本")

        # 检查 A 端原内容是否作为冲突副本被完整留存 (零丢失保证)
        all_recs, _ = storage_a.list_records(limit=10)
        conflict_titles = [r["title"] for r in all_recs if "冲突副本" in r["title"]]
        self.assertEqual(len(conflict_titles), 1)
        self.assertIn("卦例 R1 在 A 端的初始版本", conflict_titles[0])

        r2_in_a = storage_a.get_record("REC_ONLY_A_002")
        self.assertIsNotNone(r2_in_a)

        r3_in_a = storage_a.get_record("REC_ONLY_B_003")
        self.assertIsNotNone(r3_in_a)

    def test_webdav_config_masking(self):
        """测试 WebDAV 密码与加密短语脱敏"""
        cfg = WebDAVSyncConfig(
            enabled=True,
            server_url="https://dav.jianguoyun.com/dav/",
            username="user@example.com",
            password="my_super_secret_dav_password",
            encryption_passphrase="my_backup_crypto_key"
        )
        d = cfg.to_dict(mask_secret=True)
        self.assertEqual(d["password"], "********")
        self.assertEqual(d["has_encryption_passphrase"], True)
        self.assertNotIn("my_super_secret_dav_password", str(d))
        self.assertNotIn("my_backup_crypto_key", str(d))

if __name__ == "__main__":
    unittest.main()
