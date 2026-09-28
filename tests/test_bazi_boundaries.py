#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_bazi_boundaries.py - 八字子时换日跨日规则、时区平太阳时说明与五行数量分布校验 (Section C)
"""

import unittest
from xuanjian.bazi_engine import calculate_bazi

class TestBaziBoundaries(unittest.TestCase):

    def test_01_zi_hour_cross_day_convention_sect1_vs_sect2(self):
        """测试 23:00-24:00 子时跨日不同口径 (sect=1 vs sect=2)"""
        # 2026年9月26日 23:30
        # sect=2: 00:00 换日（早晚子时分立，23:00-24:00 日柱依然属当天 癸卯）
        res_sect2 = calculate_bazi(2026, 9, 26, 23, 30, zi_hour_sect=2)
        day_pillar_2 = res_sect2["four_pillars"]["day"]["gan_zhi"]
        self.assertEqual(day_pillar_2, "癸卯")
        self.assertIn("00:00", res_sect2["time_boundary_notes"]["zi_hour_mode"])
        self.assertIn("属当天", res_sect2["time_boundary_notes"]["zi_hour_mode"])

        # sect=1: 23:00 换日（子初换日，23:00 起日柱即转入次日 甲辰）
        res_sect1 = calculate_bazi(2026, 9, 26, 23, 30, zi_hour_sect=1)
        day_pillar_1 = res_sect1["four_pillars"]["day"]["gan_zhi"]
        self.assertEqual(day_pillar_1, "甲辰")
        self.assertIn("23:00", res_sect1["time_boundary_notes"]["zi_hour_mode"])
        self.assertIn("转入次日", res_sect1["time_boundary_notes"]["zi_hour_mode"])

    def test_02_timezone_and_solar_time_notices(self):
        """测试排盘返回中包含平太阳时与夏令时/经度偏差客观说明"""
        res = calculate_bazi(2024, 6, 1, 12, 0)
        notes = res.get("time_boundary_notes", {})
        self.assertIn("北京时间 (UTC+8) 平太阳时", notes.get("solar_time_system", ""))
        self.assertIn("真太阳时", notes.get("timezone_and_dst_notice", ""))
        self.assertIn("夏令时", notes.get("timezone_and_dst_notice", ""))

    def test_03_wuxing_distribution_renaming_and_disclaimer(self):
        """测试将五行分析客观命名为五行数量分布，并提供字面计数防迷信说明"""
        res = calculate_bazi(2024, 6, 1, 12, 0)
        self.assertIn("wuxing_distribution", res)
        # 向下兼容别名
        self.assertIn("wuxing_analysis", res)

        dist = res["wuxing_distribution"]
        self.assertEqual(dist["total_chars_analyzed"], 8)
        self.assertIn("note", dist)
        self.assertIn("字面数量分布", dist["note"])
        self.assertIn("切忌迷信附会", dist["note"])

if __name__ == "__main__":
    unittest.main()
