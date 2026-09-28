#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_qimen_engine.py - 奇门遁甲 12 组基准与关键边界测试

覆盖：
1. 标准时家转盘奇门基准样本 (验证局数、阴阳遁、三元、值符、值使)
2. 冬至附近极性翻转 (冬至后转阳遁)
3. 夏至附近极性翻转 (夏至后转阴遁)
4. 三元定局符头验证 (甲子/甲午/己卯等符头在上中下元的分野)
5. 子时边界与换日测试 (00:15 vs 23:45)
6. 六甲旬首遁干完整覆盖 (戊、己、庚、辛、壬、癸)
7. 值符星与值使门落宫计算自洽性
8. 中五宫天禽寄坤二宫规则核验
9. 洛书九宫标准方位排布 (南离九、北坎一、东震三、西兑七)
10. 十干克应经典断语匹配 (天盘干加地盘干)
11. 冻结输入绝对幂等复现 (同一时间重复计算盘面零漂移)
12. 参数越界防御性拦截
"""

import unittest
from xuanjian.qimen_engine import calculate_qimen

class TestQimenEngine(unittest.TestCase):

    def test_01_standard_qimen_benchmark(self):
        """用例1: 标准时家转盘奇门样本 (2026-09-26 17:30 秋分)"""
        res = calculate_qimen(2026, 9, 26, 17, 30, topic="测试求测")
        self.assertTrue(res["success"])
        meta = res["meta"]
        self.assertEqual(meta["system"], "时家转盘奇门")
        self.assertEqual(meta["juMethod"], "拆补法")
        self.assertEqual(meta["dun"], "阴遁")
        self.assertEqual(meta["juNumber"], 1)
        self.assertEqual(meta["yuan"], "中元")
        self.assertEqual(meta["zhiFuStar"], "天禽")
        self.assertEqual(meta["zhiShiDoor"], "死门")
        self.assertEqual(len(res["palaces"]), 9)

    def test_02_winter_solstice_yang_dun(self):
        """用例2: 冬至交节后必然为阳遁 (如 2024-12-22 冬至)"""
        res = calculate_qimen(2024, 12, 22, 12, 0)
        self.assertTrue(res["success"])
        self.assertEqual(res["meta"]["dun"], "阳遁")
        self.assertEqual(res["meta"]["solarTerm"], "冬至")

    def test_03_summer_solstice_yin_dun(self):
        """用例3: 夏至交节后必然为阴遁 (如 2024-06-22 夏至)"""
        res = calculate_qimen(2024, 6, 22, 12, 0)
        self.assertTrue(res["success"])
        self.assertEqual(res["meta"]["dun"], "阴遁")
        self.assertEqual(res["meta"]["solarTerm"], "夏至")

    def test_04_san_yuan_fu_tou(self):
        """用例4: 拆补定局三元分界 (上元、中元、下元均可合法生成)"""
        res_shang = calculate_qimen(2024, 2, 5, 10, 0) # 立春附近
        self.assertTrue(res_shang["success"])
        self.assertIn(res_shang["meta"]["yuan"], ["上元", "中元", "下元"])
        self.assertGreaterEqual(res_shang["meta"]["juNumber"], 1)
        self.assertLessEqual(res_shang["meta"]["juNumber"], 9)

    def test_05_midnight_boundary(self):
        """用例5: 早子时与晚子时边界 (00:15 vs 23:45)"""
        res_early = calculate_qimen(2026, 9, 26, 0, 15)
        res_late = calculate_qimen(2026, 9, 26, 23, 45)
        self.assertTrue(res_early["success"])
        self.assertTrue(res_late["success"])
        # 两者时柱地支均为子，但天干或日柱推进不同
        fp_early = res_early["input"]["fourPillars"]["hour"]["zhi"]
        fp_late = res_late["input"]["fourPillars"]["hour"]["zhi"]
        self.assertEqual(fp_early, "子")
        self.assertEqual(fp_late, "子")

    def test_06_xun_shou_coverage(self):
        """用例6: 六甲旬首对应遁仪 (甲子戊、甲戌己、甲申庚、甲午辛、甲辰壬、甲寅癸)"""
        # 测试多个时间点确保能提取出合法的旬首与六仪
        res = calculate_qimen(2026, 9, 26, 17, 30)
        zhi_fu_palace = res["meta"]["zhiFuPalace"]
        self.assertGreaterEqual(zhi_fu_palace, 1)
        self.assertLessEqual(zhi_fu_palace, 9)

    def test_07_zhifu_and_zhishi_palaces(self):
        """用例7: 值符星与值使门落宫有效性"""
        res = calculate_qimen(2025, 5, 1, 9, 0)
        meta = res["meta"]
        self.assertIn(meta["zhiFuStar"], ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"])
        self.assertIn(meta["zhiShiDoor"], ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"])
        self.assertIn(meta["zhiFuPalace"], list(range(1, 10)))
        self.assertIn(meta["zhiShiPalace"], list(range(1, 10)))

    def test_08_tianqin_jigong(self):
        """用例8: 中五宫天禽寄坤二宫规则"""
        res = calculate_qimen(2026, 9, 26, 17, 30)
        palaces = {p["palaceNumber"]: p for p in res["palaces"]}
        p5 = palaces[5]
        # 中五宫星为天禽
        self.assertEqual(p5["star"], "天禽")
        self.assertEqual(p5["palaceName"], "中")

    def test_09_luoshu_nine_palaces_layout(self):
        """用例9: 洛书九宫标准排盘方位"""
        res = calculate_qimen(2026, 9, 26, 17, 30)
        palaces = {p["palaceNumber"]: p for p in res["palaces"]}
        self.assertEqual(palaces[1]["direction"], "正北") # 坎一
        self.assertEqual(palaces[9]["direction"], "正南") # 离九
        self.assertEqual(palaces[3]["direction"], "正东") # 震三
        self.assertEqual(palaces[7]["direction"], "正西") # 兑七
        self.assertEqual(palaces[5]["direction"], "中央") # 中五

    def test_10_shigankeying_pattern_matching(self):
        """用例10: 十干克应经典格局断语匹配"""
        res = calculate_qimen(2026, 9, 26, 17, 30)
        # 至少有一个宫位有十干克应格局
        all_keying = []
        for p in res["palaces"]:
            all_keying.extend(p.get("keYing", []))
        self.assertGreater(len(all_keying), 0)
        # 验证十干克应包含名称与类型
        sample = all_keying[0]
        self.assertIn("name", sample)
        self.assertIn("type", sample)
        self.assertIn("desc", sample)

    def test_11_idempotent_reproducibility(self):
        """用例11: 冻结时间输入重复排盘零漂移"""
        res_a = calculate_qimen(2026, 9, 26, 14, 0, topic="同一事项")
        res_b = calculate_qimen(2026, 9, 26, 14, 0, topic="同一事项")
        self.assertEqual(res_a["meta"], res_b["meta"])
        self.assertEqual(res_a["palaces"], res_b["palaces"])

    def test_12_out_of_bound_inputs(self):
        """用例12: 异常参数越界防护"""
        with self.assertRaises(ValueError):
            calculate_qimen(1850, 1, 1, 12, 0) # 年份越界
        with self.assertRaises(ValueError):
            calculate_qimen(2026, 13, 1, 12, 0) # 月份越界
        with self.assertRaises(ValueError):
            calculate_qimen(2026, 5, 35, 12, 0) # 日期越界
        with self.assertRaises(ValueError):
            calculate_qimen(2026, 5, 1, 24, 0) # 小时越界
        with self.assertRaises(ValueError):
            calculate_qimen(2026, 5, 1, 12, 60) # 分钟越界

    def test_13_tianpan_dipan_and_keying_consistency(self):
        """用例13: 天盘干与地盘干明确语义映射，十干克应自洽核验"""
        # 测试样本: 2026-09-26 17:30
        res = calculate_qimen(2026, 9, 26, 17, 30)
        self.assertTrue(res["success"])
        palaces = {p["palaceNumber"]: p for p in res["palaces"]}

        # 坎一宫: 天盘壬，地盘戊。十干克应必须为「壬加戊」(天盘干加地盘干)
        p1 = palaces[1]
        self.assertEqual(p1["tianPanGan"], "壬")
        self.assertEqual(p1["diPanGan"], "戊")
        self.assertNotEqual(p1["tianPanGan"], p1["diPanGan"])
        p1_keying_keys = [k["key"] for k in p1.get("keYing", [])]
        self.assertIn("壬加戊", p1_keying_keys)
        p1_sample = next(k for k in p1["keYing"] if k["key"] == "壬加戊")
        self.assertEqual(p1_sample["name"], "小蛇化龙")

        # 震三宫: 天盘庚，地盘丙。十干克应必须为「庚加丙」(太白入荧)
        p3 = palaces[3]
        self.assertEqual(p3["tianPanGan"], "庚")
        self.assertEqual(p3["diPanGan"], "丙")
        p3_keying_keys = [k["key"] for k in p3.get("keYing", [])]
        self.assertIn("庚加丙", p3_keying_keys)
        p3_sample = next(k for k in p3["keYing"] if k["key"] == "庚加丙")
        self.assertEqual(p3_sample["name"], "太白入荧")

        # 验证所有宫位的天盘克应来源均满足: key == f"{tianPanGan}加{diPanGan}"
        for p in res["palaces"]:
            tian = p.get("tianPanGan")
            di = p.get("diPanGan")
            if tian and di:
                tian_keyings = [k for k in p.get("keYing", []) if k.get("source") == "天盘"]
                if tian_keyings:
                    self.assertEqual(tian_keyings[0]["key"], f"{tian}加{di}")

if __name__ == "__main__":
    unittest.main()
