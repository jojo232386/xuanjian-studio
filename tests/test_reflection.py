#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_reflection.py - 现实风险提醒与知止反思单元测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xuanjian.reflection_engine import evaluate_reflection

class TestReflectionEngine(unittest.TestCase):

    def test_credit_and_deficit_warning(self):
        """测试预算赤字与借贷消费预警"""
        data = {
            "topic": "想购买高配电脑",
            "budget_available": 2000.0,
            "cost_estimate": 12000.0,
            "uses_credit_or_loan": True
        }
        res = evaluate_reflection(data)
        self.assertEqual(res["risk_level"], "ATTENTION")
        alert_ids = [a["id"] for a in res["alerts"]]
        self.assertIn("RISK_CREDIT_BORROWING", alert_ids)
        self.assertIn("RISK_BUDGET_DEFICIT", alert_ids)
        # 核验信用额度不计入收入的警示
        borrowing_alert = next(a for a in res["alerts"] if a["id"] == "RISK_CREDIT_BORROWING")
        self.assertIn("信用额度并非实际收入", borrowing_alert["possible_impact"])

    def test_irreversible_action_alert(self):
        """测试不可逆动作警示"""
        data = {
            "topic": "清空线上生产数据库备份",
            "is_irreversible": True
        }
        res = evaluate_reflection(data)
        self.assertEqual(res["risk_level"], "HIGH_RISK")
        alert_ids = [a["id"] for a in res["alerts"]]
        self.assertIn("RISK_IRREVERSIBLE_ACTION", alert_ids)

    def test_deadline_and_exam_preservation(self):
        """测试现实客观期限（如考试、退款）优先原则"""
        data = {
            "topic": "明日全国硕士研究生入学考试",
            "impending_deadline": "2026-12-26 08:30"
        }
        res = evaluate_reflection(data)
        alert_ids = [a["id"] for a in res["alerts"]]
        self.assertIn("RISK_LEGAL_DEADLINE", alert_ids)
        deadline_alert = next(a for a in res["alerts"] if a["id"] == "RISK_LEGAL_DEADLINE")
        self.assertIn("不可因冷静期强行拖延", deadline_alert["possible_impact"])

    def test_health_and_vitality_boundary(self):
        """测试身体生理健康防线：纠偏'还精补脑/破功'焦虑"""
        data = {
            "topic": "查询某日能否同房或忍精固精"
        }
        res = evaluate_reflection(data)
        alert_ids = [a["id"] for a in res["alerts"]]
        self.assertIn("RISK_HEALTH_BOUNDARIES", alert_ids)
        health_alert = next(a for a in res["alerts"] if a["id"] == "RISK_HEALTH_BOUNDARIES")
        self.assertIn("绝非'破功'", health_alert["safer_alternative"])
        self.assertIn("严禁依据传统干支或卦象推断病情", res["boundaries_enforced"][0])

    def test_repeated_divination_mitigation(self):
        """测试反复占问纠偏机制 (初筮告，再三渎)"""
        data = {
            "topic": "这个决定到底好不好？",
            "divination_count_today": 4
        }
        res = evaluate_reflection(data)
        alert_ids = [a["id"] for a in res["alerts"]]
        self.assertIn("RISK_REPEATED_DIVINATION", alert_ids)

    def test_pause_card_structure(self):
        """测试决定前暂停卡的完整字段与灵活冷静期"""
        data = {
            "topic": "换工作辞职",
            "cost_estimate": 0,
            "budget_available": 50000,
            "is_irreversible": False
        }
        res = evaluate_reflection(data)
        pause = res["pause_card"]
        self.assertEqual(len(pause["questions"]), 5)
        # 验证5个核心自问
        labels = [q["label"] for q in pause["questions"]]
        self.assertIn("我要做什么？", labels[0])
        self.assertIn("为什么现在必须做？", labels[1])
        self.assertIn("真实成本与期限是什么？", labels[2])
        self.assertIn("最坏后果是什么，我能否坦然承受？", labels[3])
        self.assertIn("能否先做小而可逆的第一步？", labels[4])
        # 验证冷静期支持灵活选择而非死板锁定
        self.assertTrue(len(pause["pause_options"]) >= 2)

if __name__ == "__main__":
    unittest.main()
