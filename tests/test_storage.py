# tests/test_storage.py - SQLite 本地存储引擎与中文搜索、复盘、容灾测试

import unittest
import os
import shutil
import tempfile
import json
from xuanjian.storage import StorageManager, StorageError


class TestStorageManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="xuanjian_storage_test_")
        self.db_path = os.path.join(self.test_dir, "test_xuanjian.db")
        self.storage = StorageManager(self.db_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_and_get_record(self):
        """测试新建与读取记录，验证象数结果与复盘结构完整性"""
        sample_data = {
            "record_type": "divination",
            "title": "既济之贲研读卦例",
            "topic": "研读水火既济变山火贲之象",
            "tags": ["既济", "义理", "思患预防"],
            "params": {"lines": [7, 8, 7, 8, 9, 6]},
            "calculation_result": {
                "primary_hexagram": {"name": "既济", "number": 63},
                "transformed_hexagram": {"name": "贲", "number": 22},
                "moving_lines": [5, 6]
            },
            "review_data": {
                "original_thought": "初时以为已济大吉，当可高枕无忧",
                "actual_outcome": "实则次月突发细节失误，幸早有备选方案",
                "missing_evidence": "当时未充分考量外部供应链交期变动",
                "notes": "君子以思患而预防之，确为克治疏忽之良箴。"
            }
        }

        created = self.storage.create_record(sample_data)
        self.assertIsNotNone(created.get("id"))
        self.assertEqual(created["title"], "既济之贲研读卦例")
        self.assertEqual(created["record_type"], "divination")
        self.assertEqual(created["calculation_result"]["primary_hexagram"]["name"], "既济")
        self.assertEqual(created["review_data"]["original_thought"], "初时以为已济大吉，当可高枕无忧")

        # 读取记录
        fetched = self.storage.get_record(created["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], created["id"])
        self.assertEqual(fetched["tags"], "既济,义理,思患预防")

    def test_chinese_search_capabilities(self):
        """核心验收：中文全文多字段模糊搜索测试 (标题、主题、标签、复盘内容)"""
        # 插入若干记录
        self.storage.create_record({
            "record_type": "divination",
            "title": "测试乾卦全动",
            "topic": "乾为天研读用九群龙无首",
            "tags": ["乾卦", "用九"],
            "review_data": {"notes": "群龙无首，吉。乃见天则。"}
        })
        self.storage.create_record({
            "record_type": "reflection",
            "title": "分期借贷购车现实知止卡",
            "topic": "计划通过信用消费贷款购买新能源汽车",
            "tags": ["预算", "借贷赤字"],
            "review_data": {"notes": "冷静期后决定以公共交通与现有结余为主，避免现金流断裂。"}
        })
        self.storage.create_record({
            "record_type": "study_note",
            "title": "宋明理学知止格物笔记",
            "topic": "大学知止而后有定考据",
            "tags": ["哲学", "格物"],
            "review_data": {"notes": "知止非固步自封，乃明事理之止所也。"}
        })

        # 1. 搜标题中文关键词
        res1, total1 = self.storage.list_records(query="乾卦")
        self.assertEqual(total1, 1)
        self.assertEqual(res1[0]["title"], "测试乾卦全动")

        # 2. 搜复盘内容里的中文
        res2, total2 = self.storage.list_records(query="现金流断裂")
        self.assertEqual(total2, 1)
        self.assertEqual(res2[0]["title"], "分期借贷购车现实知止卡")

        # 3. 搜标签里的中文
        res3, total3 = self.storage.list_records(query="格物")
        self.assertEqual(total3, 1)
        self.assertEqual(res3[0]["title"], "宋明理学知止格物笔记")

        # 4. 搜多个中文词联合匹配 (AND 语义)
        res4, total4 = self.storage.list_records(query="借贷 购车")
        self.assertEqual(total4, 1)
        self.assertEqual(res4[0]["title"], "分期借贷购车现实知止卡")

        # 5. 未匹配中文
        res5, total5 = self.storage.list_records(query="完全不存在的火星文词汇")
        self.assertEqual(total5, 0)

    def test_update_review_without_mutating_calculation(self):
        """测试事后复盘更新，绝不覆盖原始象数计算结果"""
        rec = self.storage.create_record({
            "record_type": "divination",
            "title": "原始问事记录",
            "calculation_result": {"hexagram": "既济", "code": 63},
            "review_data": {}
        })

        updated = self.storage.update_review(rec["id"], {
            "original_thought": "当时以为必定成功",
            "actual_outcome": "实测需要两轮迭代",
            "missing_evidence": "当时缺少第三方测试报告",
            "notes": "复盘已完成"
        })

        self.assertEqual(updated["review_data"]["original_thought"], "当时以为必定成功")
        # 原始计算结果完好无损
        self.assertEqual(updated["calculation_result"]["hexagram"], "既济")
        self.assertEqual(updated["calculation_result"]["code"], 63)

    def test_soft_and_hard_delete(self):
        """测试软删除与物理删除"""
        rec = self.storage.create_record({"title": "待删除手记"})
        rec_id = rec["id"]

        # 软删除
        self.storage.delete_record(rec_id, permanent=False)
        self.assertIsNone(self.storage.get_record(rec_id))
        # 包含已删除时可查到
        soft_deleted = self.storage.get_record(rec_id, include_deleted=True)
        self.assertIsNotNone(soft_deleted)
        self.assertEqual(soft_deleted["is_deleted"], 1)

        # 物理硬删除
        self.storage.delete_record(rec_id, permanent=True)
        self.assertIsNone(self.storage.get_record(rec_id, include_deleted=True))

    def test_corrupted_file_safe_recovery(self):
        """测试数据库文件损坏或截断时安全隔离并重新初始化，绝不导致服务崩溃"""
        # 先写一条记录
        self.storage.create_record({"title": "正常记录"})

        # 故意制造损坏：向 db 及其 wal 写入非 SQLite 的垃圾字节
        for ext in ["", "-wal", "-shm"]:
            target = self.db_path + ext
            if os.path.exists(target):
                with open(target, "wb") as f:
                    f.write(b"CORRUPTED_TRUNCATED_GARBAGE_DATA_1234567890")

        # 重新创建 StorageManager 实例，必须自愈
        recovered_storage = StorageManager(self.db_path)
        # 应该能正常写入新记录
        new_rec = recovered_storage.create_record({"title": "自愈后的新记录"})
        self.assertIsNotNone(new_rec)
        self.assertEqual(new_rec["title"], "自愈后的新记录")

        # 确认生成了 .corrupted.*.bak 备份文件
        bak_files = [fn for fn in os.listdir(self.test_dir) if ".corrupted." in fn]
        self.assertGreaterEqual(len(bak_files), 1)

    def test_export_markdown(self):
        """测试 Markdown 导出能力"""
        self.storage.create_record({
            "title": "导出测试记录",
            "topic": "周易既济",
            "calculation_result": {
                "primary_hexagram": {"name": "既济"},
                "transformed_hexagram": {"name": "贲"},
                "moving_lines": [5]
            },
            "review_data": {
                "original_thought": "初时以为万事大吉",
                "notes": "宜慎始敬终"
            }
        })

        md = self.storage.export_records_as_markdown()
        self.assertIn("# 玄鉴·书房 ｜ 本地记录与复盘手记导出", md)
        self.assertIn("导出测试记录", md)
        self.assertIn("【当时象数推算】", md)
        self.assertIn("【事后复盘思考】", md)


if __name__ == "__main__":
    unittest.main()
