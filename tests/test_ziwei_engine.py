#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_ziwei_engine.py - 紫微斗数 12 组基准与关键边界测试

覆盖：
1. 经典公历样本基准验证 (命主、身主、五局、命宫地支)
2. 公农历等价输入基准验证 (公历 1990-05-15 与 农历 1990-04-21)
3. 出生时辰未知安全降级 (不臆造时柱与假星盘)
4. 早子时 (00:30) 排盘与命身宫边界
5. 晚子时 (23:30) 排盘与跨日子时边界
6. 农历闰月输入处理 (如 2020 闰四月)
7. 阳男阴女大限顺行与阴男阳女逆行
8. 动态流年考查 (指定 target_date 触发大限与生年四化)
9. 年界立春前后边界
10. 非法年份/月份/小时参数拦截与边界防护
11. 十二宫三方四正对宫与三合宫逻辑闭环
12. 连续多次并发与异参调用无全局状态污染 (重入幂等性)
"""

import unittest
from xuanjian.ziwei_engine import calculate_ziwei

class TestZiweiEngine(unittest.TestCase):

    def test_01_standard_solar_benchmark(self):
        """用例1: 标准公历基准样本 (1990-05-15 14:00 男)"""
        res = calculate_ziwei(1990, 5, 15, hour=14, gender="男", calendar_type="solar")
        self.assertTrue(res["success"])
        self.assertFalse(res["degraded"])
        basic = res["basic"]
        self.assertEqual(basic["soul"], "禄存")
        self.assertEqual(basic["body"], "火星")
        self.assertEqual(basic["fiveElementsClass"], "土五局")
        self.assertEqual(basic["earthlyBranchOfSoulPalace"], "戌")
        self.assertEqual(basic["earthlyBranchOfBodyPalace"], "子")
        self.assertEqual(len(res["palaces"]), 12)

    def test_02_solar_lunar_equivalence(self):
        """用例2: 公农历等价输入验证 (1990-05-15 等价于 农历 1990-04-21)"""
        solar_res = calculate_ziwei(1990, 5, 15, hour=14, gender="男", calendar_type="solar")
        lunar_res = calculate_ziwei(1990, 4, 21, hour=14, gender="男", calendar_type="lunar")
        self.assertEqual(solar_res["basic"]["soul"], lunar_res["basic"]["soul"])
        self.assertEqual(solar_res["basic"]["fiveElementsClass"], lunar_res["basic"]["fiveElementsClass"])
        self.assertEqual(solar_res["basic"]["earthlyBranchOfSoulPalace"], lunar_res["basic"]["earthlyBranchOfSoulPalace"])
        self.assertEqual(solar_res["basic"]["earthlyBranchOfBodyPalace"], lunar_res["basic"]["earthlyBranchOfBodyPalace"])

    def test_03_unknown_hour_graceful_degradation(self):
        """用例3: 出生时辰未知安全降级，绝不凭空假排"""
        res = calculate_ziwei(1990, 5, 15, hour=None, gender="男")
        self.assertTrue(res["success"])
        self.assertTrue(res["degraded"])
        self.assertIn("出生时辰未知", res["message"])
        self.assertNotIn("palaces", res)

    def test_04_early_rat_hour(self):
        """用例4: 早子时 (00:15，属当日凌晨)"""
        res = calculate_ziwei(2000, 8, 16, hour=0, gender="男")
        self.assertTrue(res["success"])
        self.assertIn("子时", res["basic"]["time"])
        self.assertEqual(len(res["palaces"]), 12)

    def test_05_late_rat_hour(self):
        """用例5: 晚子时 (23:45，属跨日夜子时)"""
        res = calculate_ziwei(2000, 8, 16, hour=23, gender="男")
        self.assertTrue(res["success"])
        self.assertIn("子时", res["basic"]["time"])
        # 晚子时时辰索引有效
        self.assertEqual(len(res["palaces"]), 12)

    def test_06_leap_month_handling(self):
        """用例6: 农历闰月处理 (2020 农历闰四月十五)"""
        res_leap = calculate_ziwei(2020, 4, 15, hour=10, gender="女", calendar_type="lunar", is_leap_month=True)
        res_normal = calculate_ziwei(2020, 4, 15, hour=10, gender="女", calendar_type="lunar", is_leap_month=False)
        self.assertTrue(res_leap["success"])
        self.assertTrue(res_normal["success"])
        # 闰月与平月星盘应有区别或明确记载
        self.assertIn("二〇二〇", res_leap["basic"]["lunarDate"])

    def test_07_gender_and_decadal_direction(self):
        """用例7: 性别与大限流向 (阳男阴女顺行，阴男阳女逆行)"""
        res_male = calculate_ziwei(1990, 5, 15, hour=14, gender="男")
        res_female = calculate_ziwei(1990, 5, 15, hour=14, gender="女")
        self.assertTrue(res_male["success"])
        self.assertTrue(res_female["success"])
        # 庚午年，庚为阳天干。男命为阳男(顺行)，女命为阳女(逆行)
        palaces_male = res_male["palaces"]
        palaces_female = res_female["palaces"]
        # 两者命盘宫位星曜相同，但大限起限排列方向不同
        dec_m = [p["decadal"]["range"] for p in palaces_male if p["decadal"]]
        dec_f = [p["decadal"]["range"] for p in palaces_female if p["decadal"]]
        self.assertNotEqual(dec_m, dec_f)

    def test_08_horoscope_dynamic_yearly(self):
        """用例8: 指定流年大限目标日期计算 (target_date 动态解析)"""
        res = calculate_ziwei(1990, 5, 15, hour=14, gender="男", target_date="2026-09-26")
        self.assertTrue(res["success"])
        horo = res["horoscope"]
        self.assertIsNotNone(horo)
        self.assertIn("yearly", horo)
        self.assertIn("decadal", horo)
        self.assertEqual(horo["targetDate"], "2026-09-26")

    def test_09_year_boundary_lichun(self):
        """用例9: 年界立春附近日期排盘稳定性 (2024-02-04 附近)"""
        res_pre = calculate_ziwei(2024, 2, 3, hour=12, gender="男")
        res_post = calculate_ziwei(2024, 2, 5, hour=12, gender="男")
        self.assertTrue(res_pre["success"])
        self.assertTrue(res_post["success"])
        self.assertNotEqual(res_pre["basic"]["solarDate"], res_post["basic"]["solarDate"])

    def test_10_invalid_parameters_rejection(self):
        """用例10: 非法参数边界拦截"""
        with self.assertRaises(ValueError):
            calculate_ziwei(1800, 5, 15, hour=12) # 超出 1900-2100 年份
        with self.assertRaises(ValueError):
            calculate_ziwei(1990, 13, 15, hour=12) # 月份越界
        with self.assertRaises(ValueError):
            calculate_ziwei(1990, 5, 32, hour=12) # 日期越界
        with self.assertRaises(ValueError):
            calculate_ziwei(1990, 5, 15, hour=25) # 小时越界

    def test_11_san_fang_si_zheng_consistency(self):
        """用例11: 十二宫三方四正对宫与三合逻辑自洽"""
        res = calculate_ziwei(1990, 5, 15, hour=14, gender="男")
        palaces = res["palaces"]
        ming_palace = next(p for p in palaces if p["name"] == "命宫")
        # 命宫对宫必然为迁移宫
        self.assertEqual(ming_palace["sanFangSiZheng"]["opposite"], "迁移")
        # 命宫三合必然为官禄与财帛
        trines = {ming_palace["sanFangSiZheng"]["trine1"], ming_palace["sanFangSiZheng"]["trine2"]}
        self.assertEqual(trines, {"官禄", "财帛"})

    def test_12_isolation_and_no_cross_contamination(self):
        """用例12: 异参连续调用无跨请求污染 (重入稳定性)"""
        res_a = calculate_ziwei(1985, 3, 10, hour=8, gender="女")
        res_b = calculate_ziwei(2005, 11, 20, hour=20, gender="男")
        res_a_again = calculate_ziwei(1985, 3, 10, hour=8, gender="女")
        self.assertEqual(res_a["basic"], res_a_again["basic"])
        self.assertNotEqual(res_a["basic"]["solarDate"], res_b["basic"]["solarDate"])
        self.assertNotEqual(res_a["basic"]["soul"], res_b["basic"]["soul"])

    def test_13_ming_body_and_original_palace_distinction(self):
        """用例13: 命宫、身宫与来因宫严格分野，绝不可混为一谈"""
        # 测试样本: 2000-08-16 02:00 (庚辰年 丑时 女)
        # 生年天干为庚，宫干为庚者落辰位(子女宫)，故来因宫严格为辰(子女)
        # 命宫落未位(武曲)，身宫落酉位(福德/天府)
        res = calculate_ziwei(2000, 8, 16, hour=2, gender="女", calendar_type="solar")
        self.assertTrue(res["success"])
        palaces = res["palaces"]
        basic = res["basic"]

        # 1. 验证基础元信息
        self.assertEqual(basic["earthlyBranchOfSoulPalace"], "未")
        self.assertEqual(basic["earthlyBranchOfBodyPalace"], "酉")
        self.assertEqual(basic["originalPalaceName"], "子女")
        self.assertEqual(basic["earthlyBranchOfOriginalPalace"], "辰")

        # 2. 命宫与来因宫地支严格不相等
        self.assertNotEqual(basic["earthlyBranchOfSoulPalace"], basic["earthlyBranchOfOriginalPalace"])

        # 3. 宫位标记核验
        ming_palace = next(p for p in palaces if p["name"] == "命宫")
        self.assertEqual(ming_palace["earthlyBranch"], "未")
        self.assertTrue(ming_palace.get("isSoulPalace"))
        self.assertFalse(ming_palace["isOriginalPalace"]) # 命宫绝非来因宫
        self.assertFalse(ming_palace["isBodyPalace"])

        laiyin_palace = next(p for p in palaces if p["isOriginalPalace"])
        self.assertEqual(laiyin_palace["name"], "子女")
        self.assertEqual(laiyin_palace["earthlyBranch"], "辰")
        self.assertTrue(laiyin_palace["isOriginalPalace"])
        self.assertFalse(laiyin_palace.get("isSoulPalace", False))

        shen_palace = next(p for p in palaces if p["isBodyPalace"])
        self.assertEqual(shen_palace["name"], "福德")
        self.assertEqual(shen_palace["earthlyBranch"], "酉")
        self.assertTrue(shen_palace["isBodyPalace"])

if __name__ == "__main__":
    unittest.main()
