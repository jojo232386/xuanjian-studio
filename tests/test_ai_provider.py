#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_ai_provider.py - 智能研读层与 AI Provider 单元测试 (F06)
"""

import unittest
from xuanjian.ai_provider import (
    AIProviderConfig,
    mask_api_key,
    sanitize_user_input,
    build_grounded_prompt,
    TokenBudgetTracker,
    BudgetExceededError,
    generate_ai_interpretation,
    get_ai_config,
    update_ai_config
)

class TestAIProvider(unittest.TestCase):

    def test_mask_api_key(self):
        """测试 API Key 脱敏显示"""
        self.assertEqual(mask_api_key(None), "")
        self.assertEqual(mask_api_key(""), "")
        self.assertEqual(mask_api_key("12345"), "********")
        self.assertEqual(mask_api_key("sk-abcdef123456789"), "sk-****6789")

    def test_sanitize_user_input(self):
        """测试输入清洗与防注入截断"""
        dirty = "Hello\x00\x08World!\x1F" + "a" * 600
        clean = sanitize_user_input(dirty)
        self.assertNotIn("\x00", clean)
        self.assertNotIn("\x08", clean)
        self.assertNotIn("\x1F", clean)
        self.assertLessEqual(len(clean), 400)
        self.assertTrue(clean.startswith("HelloWorld!"))

    def test_build_grounded_prompt(self):
        """测试真实文献与象数计算结果注入 prompt"""
        calc_data = {
            "original_hexagram": {
                "name": "既济",
                "full_name": "水火既济",
                "guaci": "亨小，利贞，初吉终乱。",
                "xiangzhuan": "水在火上，既济；君子以思患而预防之。",
                "tuanzhuan": "既济，亨，小者亨也。"
            },
            "transformed_hexagram": {
                "name": "贲",
                "full_name": "山火贲"
            },
            "nuclear_hexagram": {
                "name": "未济"
            },
            "input_lines": [7, 8, 7, 8, 9, 6],
            "moving_lines": [5, 6]
        }
        sys_p, usr_p = build_grounded_prompt("创业项目风险防范", calc_data)

        self.assertIn("思患预防", sys_p)
        self.assertIn("严禁算命断死生", sys_p)
        self.assertIn("水火既济", usr_p)
        self.assertIn("水在火上，既济；君子以思患而预防之。", usr_p)
        self.assertIn("第 5、6 爻", usr_p)
        self.assertIn("创业项目风险防范", usr_p)

    def test_token_budget_tracker(self):
        """测试调用次数与 Token 预算熔断防线"""
        tracker = TokenBudgetTracker(daily_limit=2, monthly_limit=1500)
        status = tracker.get_status()
        self.assertTrue(status["is_budget_ok"])

        # 第 1 次调用 (500 tokens)
        tracker.check_and_increment(500)
        # 第 2 次调用 (500 tokens)
        tracker.check_and_increment(500)

        # 第 3 次调用应触发熔断
        with self.assertRaises(BudgetExceededError):
            tracker.check_and_increment(500)

    def test_offline_fallback_mode(self):
        """测试离线/无 Key 模式安全降级并输出标准任务提示词"""
        update_ai_config({"provider_type": "offline", "api_key": ""})
        calc_data = {
            "original_hexagram": {"name": "既济", "guaci": "亨小"},
            "transformed_hexagram": {"name": "未济"}
        }
        res = generate_ai_interpretation("知止反思", calc_data)

        self.assertFalse(res["connected"])
        self.assertEqual(res["status"], "BLOCKED_EXTERNAL")
        self.assertIn("copy_task_prompt", res)
        self.assertIn("既济", res["copy_task_prompt"])
        self.assertIn("本地安全模式", res["message"])

    def test_config_update_and_masking(self):
        """测试配置更新与字典导出脱敏"""
        cfg = update_ai_config({
            "provider_type": "openai_compatible",
            "base_url": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat",
            "api_key": "sk-test-fixture-123",
            "temperature": 0.5,
            "max_tokens": 800
        })
        d = cfg.to_dict(mask_key=True)
        self.assertEqual(d["provider_type"], "openai_compatible")
        self.assertEqual(d["model_name"], "deepseek-chat")
        self.assertNotIn("sk-test-fixture-123", d["api_key"])
        self.assertTrue(d["api_key"].startswith("sk-****"))

        # 还原为 offline
        update_ai_config({"provider_type": "offline", "api_key": ""})

if __name__ == "__main__":
    unittest.main()
