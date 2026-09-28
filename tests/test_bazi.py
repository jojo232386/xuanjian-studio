#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_bazi.py - 八字排盘引擎单元测试 (F04)
"""

import unittest
from xuanjian.bazi_engine import calculate_bazi, GAN_INFO, ZHI_INFO

class TestBaziEngine(unittest.TestCase):

    def test_standard_four_pillars(self):
        """测试标准公历四柱排盘推算"""
        # 1990-05-15 14:30 男
        res = calculate_bazi(1990, 5, 15, 14, 30, gender="乾造")
        self.assertFalse(res["degraded_to_three_pillars"])
        self.assertEqual(res["gender"], "乾造")

        # 验证四柱干支
        pillars = res["four_pillars"]
        self.assertEqual(pillars["year"]["gan_zhi"], "庚午")
        self.assertEqual(pillars["month"]["gan_zhi"], "辛巳")
        self.assertEqual(pillars["day"]["gan_zhi"], "庚辰")
        self.assertEqual(pillars["hour"]["gan_zhi"], "癸未")

        # 验证日主
        self.assertEqual(res["day_master"]["gan"], "庚")
        self.assertEqual(res["day_master"]["wuxing"], "金")

        # 验证十神
        self.assertEqual(pillars["year"]["ten_god"], "比肩")
        self.assertEqual(pillars["month"]["ten_god"], "劫财")
        self.assertEqual(pillars["day"]["ten_god"], "日主")
        self.assertEqual(pillars["hour"]["ten_god"], "伤官")

        # 验证五行统计 (总计8字)
        wuxing = res["wuxing_analysis"]
        self.assertEqual(wuxing["total_chars_analyzed"], 8)
        self.assertEqual(sum(wuxing["counts"].values()), 8)

        # 验证大运序列
        dayun = res["dayun"]
        self.assertGreater(len(dayun["sequence"]), 5)
        first_step = dayun["sequence"][0]
        self.assertEqual(first_step["gan_zhi"], "壬午")
        self.assertEqual(first_step["start_age"], 8)
        self.assertTrue(dayun["metadata"]["is_forward"])

    def test_unknown_hour_graceful_degradation(self):
        """测试时辰未知时安全降级为三柱六字"""
        res = calculate_bazi(1990, 5, 15, hour=None)
        self.assertTrue(res["degraded_to_three_pillars"])

        # 时柱应明确标注未知，绝不胡编
        hour_p = res["four_pillars"]["hour"]
        self.assertEqual(hour_p["gan"], "未知")
        self.assertEqual(hour_p["zhi"], "未知")
        self.assertEqual(hour_p["gan_zhi"], "未知")
        self.assertEqual(hour_p["ten_god"], "未知")

        # 五行统计应仅统计已知的三柱六字
        wuxing = res["wuxing_analysis"]
        self.assertEqual(wuxing["total_chars_analyzed"], 6)
        self.assertEqual(sum(wuxing["counts"].values()), 6)

        # 大运应当提示近似
        self.assertIn("出生时辰未知", res["dayun"]["metadata"]["approx_note"])

    def test_solar_term_boundary_transition(self):
        """测试节气交节时刻干支年月的严格切换 (立春)"""
        # 2024年立春交节在 2024-02-04 16:27
        # 16:27 之前为 癸卯年 乙丑月
        res_before = calculate_bazi(2024, 2, 4, 10, 0)
        self.assertEqual(res_before["four_pillars"]["year"]["gan_zhi"], "癸卯")
        self.assertEqual(res_before["four_pillars"]["month"]["gan_zhi"], "乙丑")

        # 16:27 之后为 甲辰年 丙寅月
        res_after = calculate_bazi(2024, 2, 4, 18, 0)
        self.assertEqual(res_after["four_pillars"]["year"]["gan_zhi"], "甲辰")
        self.assertEqual(res_after["four_pillars"]["month"]["gan_zhi"], "丙寅")

    def test_dayun_gender_direction(self):
        """测试大运顺逆行逻辑 (阳男阴女顺，阴男阳女逆)"""
        # 2024年是甲辰年 (甲为阳干)
        # 男命 (乾造) -> 顺行
        b_male = calculate_bazi(2024, 6, 1, 12, 0, gender="乾造")
        self.assertTrue(b_male["dayun"]["metadata"]["is_forward"])
        self.assertEqual(b_male["dayun"]["metadata"]["direction_text"], "顺行")

        # 女命 (坤造) -> 逆行
        b_female = calculate_bazi(2024, 6, 1, 12, 0, gender="坤造")
        self.assertFalse(b_female["dayun"]["metadata"]["is_forward"])
        self.assertEqual(b_female["dayun"]["metadata"]["direction_text"], "逆行")

    def test_lunar_calendar_input(self):
        """测试农历与闰月输入正确转换为四柱"""
        # 农历 2023年闰二月初一 12:00
        res = calculate_bazi(2023, 2, 1, 12, 0, is_lunar=True, is_leap_month=True)
        self.assertTrue(res["is_lunar_input"])
        self.assertTrue(res["is_leap_month"])
        self.assertIn("闰二月", res["lunar_date"])
        # 对应公历应当是 2023-03-22
        self.assertIn("2023年03月22日", res["solar_date"])

    def test_invalid_parameters_raise_error(self):
        """测试越界或无效日期抛出合法异常"""
        with self.assertRaises(ValueError):
            calculate_bazi(1850, 1, 1)  # 超出年份下限
        with self.assertRaises(ValueError):
            calculate_bazi(2024, 13, 1)  # 无效月份
        with self.assertRaises(ValueError):
            calculate_bazi(2024, 5, 35)  # 无效日期

    def test_disclaimer_present(self):
        """测试必须包含客观防线与理性声明"""
        res = calculate_bazi(2000, 1, 1, 12, 0)
        self.assertIn("时间符号模型", res["disclaimer"])
        self.assertIn("绝不构成个人宿命论", res["disclaimer"])
        self.assertIn("知止", res["disclaimer"])

if __name__ == "__main__":
    unittest.main()
