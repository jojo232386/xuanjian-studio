#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_taboos.py - 传统宜忌与禁忌考据单元测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xuanjian.taboos_data import (
    YI_JI_GLOSSARY,
    TRADITIONAL_TABOOS,
    get_taboo_by_term,
    search_taboos
)

class TestTaboosData(unittest.TestCase):

    def test_glossary_schema_integrity(self):
        """核验所有宜忌词汇具备完整考据字段"""
        required_keys = {"id", "title", "content_type", "domain", "source", "source_type", "verification_status", "meaning", "rational_handling"}
        for term, data in YI_JI_GLOSSARY.items():
            self.assertTrue(required_keys.issubset(data.keys()), f"词条 {term} 缺少必要字段")
            self.assertIn(data["source_type"], ["古籍可定位", "现代整理", "日历库规则输出", "民俗传说", "出处待核实"])
            self.assertIn(data["verification_status"], ["已核对", "考据中", "民俗口传", "未收录"])

    def test_traditional_taboos_schema_integrity(self):
        """核验传统禁忌库字段规范"""
        required_keys = {"id", "title", "content_type", "domain", "source", "source_type", "verification_status", "scope", "meaning", "rational_handling"}
        for item in TRADITIONAL_TABOOS:
            self.assertTrue(required_keys.issubset(item.keys()), f"禁忌 {item['id']} 缺少必要字段")

    def test_search_hit_verified(self):
        """测试'这是真的吗？'对收录词条检索准确性"""
        res = search_taboos("癸不词讼")
        self.assertTrue(res["found"])
        self.assertTrue(res["count"] >= 1)
        item = res["results"][0]
        self.assertEqual(item["id"], "TB_PENGZU_GUI")
        self.assertEqual(item["verification_status"], "已核对")
        self.assertIn("事林广记", item["source"])

    def test_search_miss_no_hallucination(self):
        """测试未收录词条坚决拒绝臆造古籍出处"""
        res = search_taboos("喝可乐会破坏卦象")
        self.assertFalse(res["found"])
        self.assertEqual(res["verification_status"], "未收录")
        self.assertIn("未收录", res["message"])
        self.assertIn("不使用 AI 临场伪造", res["message"])

    def test_zhushibuyi_clarification(self):
        """测试'诸事不宜'词条明确不转为现实危险警报"""
        res = search_taboos("诸事不宜")
        self.assertTrue(res["found"])
        item = next(x for x in res["results"] if x["id"] == "TB_ZHUSHIBUYI")
        self.assertIn("绝非现实灾难预警", item["rational_handling"])

if __name__ == "__main__":
    unittest.main()
