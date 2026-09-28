#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_ai_budget_and_grounding.py - AI 预算持久化、并发预扣锁与接地性校验测试 (Section B)
"""

import os
import json
import tempfile
import threading
import unittest
from xuanjian.ai_provider import (
    TokenBudgetTracker,
    BudgetExceededError,
    build_grounded_prompt,
    verify_grounding_and_integrity,
    generate_ai_interpretation,
    update_ai_config,
    AIProviderConfig
)

class TestAIBudgetAndGrounding(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.budget_file = os.path.join(self.temp_dir.name, "test_budget.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_budget_persistence_across_restart(self):
        """测试 AI 预算落盘持久化及服务重启后历史用量自动恢复"""
        tracker1 = TokenBudgetTracker(daily_limit=10, monthly_limit=5000, storage_path=self.budget_file)
        # 预扣并结算 2 次调用
        res1 = tracker1.reserve(500)
        tracker1.settle(res1, 450, 500)
        res2 = tracker1.reserve(600)
        tracker1.settle(res2, 550, 600)

        status1 = tracker1.get_status()
        self.assertEqual(status1["daily_calls_used"], 2)
        self.assertEqual(status1["monthly_tokens_used"], 1000)
        self.assertTrue(os.path.exists(self.budget_file))

        # 模拟服务重启：重新实例化 Tracker，指向相同持久化路径
        tracker2 = TokenBudgetTracker(daily_limit=10, monthly_limit=5000, storage_path=self.budget_file)
        status2 = tracker2.get_status()
        self.assertEqual(status2["daily_calls_used"], 2)
        self.assertEqual(status2["monthly_tokens_used"], 1000)
        self.assertTrue(status2["is_budget_ok"])

    def test_02_concurrency_reservation_lock(self):
        """测试并发预扣锁 (Reservation Lock)：高并发下严格防穿透"""
        # 设置每日限额仅剩 1 次
        tracker = TokenBudgetTracker(daily_limit=1, monthly_limit=5000, storage_path=self.budget_file)

        success_reservations = []
        rejected_reservations = []

        def worker():
            try:
                res_id = tracker.reserve(500)
                success_reservations.append(res_id)
            except BudgetExceededError as be:
                rejected_reservations.append(str(be))

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 仅有 1 个请求能成功获得配额锁，其余 4 个全部被拦截
        self.assertEqual(len(success_reservations), 1)
        self.assertEqual(len(rejected_reservations), 4)

    def test_03_reservation_rollback_on_failure(self):
        """测试调用失败或异常时预占额度安全回滚"""
        tracker = TokenBudgetTracker(daily_limit=2, monthly_limit=5000, storage_path=self.budget_file)
        res_id = tracker.reserve(500)
        status_in_flight = tracker.get_status()
        self.assertEqual(status_in_flight["daily_calls_reserved"], 1)

        # 模拟网络异常回滚
        tracker.release(res_id, 500)
        status_after_rollback = tracker.get_status()
        self.assertEqual(status_after_rollback["daily_calls_reserved"], 0)
        self.assertEqual(status_after_rollback["daily_calls_used"], 0)
        self.assertTrue(status_after_rollback["is_budget_ok"])

    def test_04_grounding_citation_check_and_sanitization(self):
        """测试接地性引用校验：有效编号通过，非法/越界引用编号告警并安全替换"""
        calc_data = {
            "original_hexagram": {"name": "既济", "full_name": "水火既济", "guaci": "亨小，利贞"},
            "transformed_hexagram": {"name": "贲", "full_name": "山火贲"},
            "input_lines": [7, 8, 7, 8, 9, 6],
            "moving_lines": [5, 6]
        }
        valid_ids = [1, 2, 3]

        # 案例 A: 包含合法引用 [1] 和越界虚构引用 [8]、[9]
        ai_output = "研读卦辞 [1] 可知初吉终乱。此外参考 [8] 与 [9] 属于虚构文献。"
        check_res = verify_grounding_and_integrity(ai_output, calc_data, valid_ids)

        self.assertFalse(check_res["citations_valid"])
        self.assertEqual(check_res["invalid_citations"], [8, 9])
        self.assertIn("[1]", check_res["cleaned_content"])
        self.assertIn("[未核验引用8]", check_res["cleaned_content"])
        self.assertIn("[未核验引用9]", check_res["cleaned_content"])
        self.assertTrue(len(check_res["warnings"]) > 0)

        # 案例 B: 仅包含合法引用 [1]、[2]
        clean_ai_output = "依据大象传 [2] 思患预防，卦辞 [1] 提示慎终如始。"
        clean_res = verify_grounding_and_integrity(clean_ai_output, calc_data, valid_ids)
        self.assertTrue(clean_res["citations_valid"])
        self.assertEqual(len(clean_res["invalid_citations"]), 0)
        self.assertEqual(clean_res["cleaned_content"], clean_ai_output)

    def test_05_hexagram_core_integrity_protection(self):
        """测试大模型篡改/纠正底层象数判定时的防护与物理锁定"""
        calc_data = {
            "original_hexagram": {"name": "既济", "full_name": "水火既济"},
            "transformed_hexagram": {"name": "贲", "full_name": "山火贲"},
            "input_lines": [7, 8, 7, 8, 9, 6],
            "moving_lines": [5, 6]
        }

        # 模拟大模型擅自纠正卦名
        tampered_output = "你输入的并非既济，应该纠正为未济卦。"
        check_res = verify_grounding_and_integrity(tampered_output, calc_data, [1, 2, 3])

        self.assertTrue(check_res["model_tampered_core"])
        self.assertTrue(any("异常纠正" in w for w in check_res["warnings"]))
        # 验证权威核心计算结果被物理锁定
        core = check_res["authoritative_core"]
        self.assertEqual(core["original_name"], "既济")
        self.assertTrue(core["locked"])
        self.assertEqual(core["input_lines"], [7, 8, 7, 8, 9, 6])

    def test_06_generate_ai_offline_fallback_includes_authoritative_core(self):
        """测试离线/无 API 模式下权威象数核心数据完整返回"""
        update_ai_config({"provider_type": "offline", "api_key": ""})
        calc_data = {
            "original_hexagram": {"name": "既济", "full_name": "水火既济"},
            "transformed_hexagram": {"name": "未济", "full_name": "火水未济"},
            "input_lines": [7, 8, 7, 8, 9, 6],
            "moving_lines": [5, 6]
        }
        res = generate_ai_interpretation("项目合规审核", calc_data)
        self.assertEqual(res["status"], "BLOCKED_EXTERNAL")
        self.assertIn("authoritative_calculation", res)
        self.assertEqual(res["authoritative_calculation"]["original_name"], "既济")
        self.assertTrue(res["authoritative_calculation"]["locked"])

if __name__ == "__main__":
    unittest.main()
