#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_calendar.py - 独立历法核验与临界样本测试

根据香港天文台 (HKO) 公农历对照表及紫金山天文台历表建立基准测试用例，
覆盖：
1. 公农历互转
2. 闰月处理 (2020 闰四月、2025 闰六月)
3. 年界换岁 (除夕与正月初一)
4. 二十四节气临界推算
5. 彭祖百忌与干支对齐
6. 边界与非法日期防御
7. 可注入时钟支持
"""

import unittest
import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xuanjian.calendar_engine import get_calendar_day, ENGINE_METADATA

class TestCalendarEngine(unittest.TestCase):

    def test_spring_festival_year_boundary(self):
        """
        年界测试：核验 2026 年春节交界
        2026-02-16: 乙巳年 (蛇年) 腊月廿九
        2026-02-17: 丙午年 (马年) 正月初一 (春季元旦)
        """
        day_eve = get_calendar_day(target_date=datetime.date(2026, 2, 16))
        self.assertIn("乙巳", day_eve["lunar"]["ganzhi_year"])
        self.assertIn("腊", day_eve["lunar"]["month_chinese"])
        self.assertIn("廿九", day_eve["lunar"]["day_chinese"])

        day_new_year = get_calendar_day(target_date=datetime.date(2026, 2, 17))
        self.assertIn("丙午", day_new_year["lunar"]["ganzhi_year"])
        self.assertIn("正", day_new_year["lunar"]["month_chinese"])
        self.assertIn("初一", day_new_year["lunar"]["day_chinese"])

    def test_autumn_equinox_solar_term(self):
        """节气临界测试：2026-09-23 为秋分"""
        day = get_calendar_day(target_date=datetime.date(2026, 9, 23))
        self.assertEqual(day["solar_term"]["current"], "秋分")

    def test_mid_autumn_festival(self):
        """传统大节测试：2026-09-25 为农历八月十五 (中秋节)"""
        day = get_calendar_day(target_date=datetime.date(2026, 9, 25))
        self.assertEqual(day["lunar"]["month_chinese"], "八")
        self.assertEqual(day["lunar"]["day_chinese"], "十五")

    def test_target_date_2026_09_26(self):
        """当前基准日期测试：2026-09-26 为八月十六，癸卯日"""
        day = get_calendar_day(target_date=datetime.date(2026, 9, 26))
        self.assertEqual(day["lunar"]["month_chinese"], "八")
        self.assertEqual(day["lunar"]["day_chinese"], "十六")
        self.assertIn("癸卯", day["lunar"]["ganzhi_day"])
        self.assertIn("癸不词讼", day["pengzu_baiji"]["full"])
        self.assertIn("卯不穿井", day["pengzu_baiji"]["full"])

    def test_historical_benchmark_1949_10_01(self):
        """外部权威历史基准测试：1949-10-01 为己丑年八月初十，甲子日"""
        day = get_calendar_day(target_date=datetime.date(1949, 10, 1))
        self.assertEqual(day["solar"]["weekday"], "星期六")
        self.assertEqual(day["lunar"]["month_chinese"], "八")
        self.assertEqual(day["lunar"]["day_chinese"], "初十")
        self.assertIn("己丑", day["lunar"]["ganzhi_year"])
        self.assertIn("甲子", day["lunar"]["ganzhi_day"])
        self.assertIn("甲不开仓", day["pengzu_baiji"]["full"])
        self.assertIn("子不问卜", day["pengzu_baiji"]["full"])

    def test_leap_months(self):
        """
        闰月样本测试：
        1. 2020-05-23 为 庚子年 闰四月初一
        2. 2025-07-25 为 乙巳年 闰六月初一
        """
        day_2020 = get_calendar_day(target_date=datetime.date(2020, 5, 23))
        self.assertTrue(day_2020["lunar"]["is_leap_month"])
        self.assertIn("闰四", day_2020["lunar"]["month_chinese"])
        self.assertEqual(day_2020["lunar"]["day_chinese"], "初一")

        day_2025 = get_calendar_day(target_date=datetime.date(2025, 7, 25))
        self.assertTrue(day_2025["lunar"]["is_leap_month"])
        self.assertIn("闰六", day_2025["lunar"]["month_chinese"])
        self.assertEqual(day_2025["lunar"]["day_chinese"], "初一")

    def test_out_of_range_handling(self):
        """超出支持范围 (1900-2100) 必须明确报错"""
        with self.assertRaises(ValueError):
            get_calendar_day(year=1899, month=12, day=31)
        with self.assertRaises(ValueError):
            get_calendar_day(year=2101, month=1, day=1)

    def test_invalid_dates_handling(self):
        """公历无效日期必须防御"""
        with self.assertRaises(ValueError):
            get_calendar_day(year=2026, month=2, day=30)
        with self.assertRaises(ValueError):
            get_calendar_day(year=2026, month=13, day=1)

    def test_injected_clock_isolation(self):
        """核验支持显式注入日期，不依赖物理时钟"""
        day_a = get_calendar_day(target_date=datetime.date(2024, 1, 1))
        day_b = get_calendar_day(target_date=datetime.date(2024, 1, 2))
        self.assertNotEqual(day_a["solar"]["date"], day_b["solar"]["date"])

    def test_metadata_provenance(self):
        """核验元数据包含版本、时区、独立参考与免责说明"""
        meta = ENGINE_METADATA
        self.assertEqual(meta["engine"], "lunar-python")
        self.assertIn("UTC+8", meta["timezone"])
        self.assertIn("香港天文台", meta["verification_reference"])
        self.assertIn("免责", meta["disclaimer"] + "文化记录")

if __name__ == "__main__":
    unittest.main()
