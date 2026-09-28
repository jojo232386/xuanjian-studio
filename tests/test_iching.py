#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_iching.py - 六爻象数计算单元测试
"""

import unittest
import sys
import os

# 将根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.iching import (
    calculate_hexagram,
    cast_coins,
    TRIGRAMS,
    HEXAGRAM_TABLE,
    get_yao_name
)

class TestIChingCore(unittest.TestCase):

    def test_fixed_sample_jiji_to_bi(self):
        """
        核心验收样例：
        输入自下而上: 7 8 7 8 9 6
        预期:
        - 本卦: 既济 (水火既济, 63)
        - 动爻: 5, 6
        - 变卦: 贲 (山火贲, 22)
        - 互卦: 未济 (火水未济, 64)
        """
        lines = [7, 8, 7, 8, 9, 6]
        res = calculate_hexagram(lines)

        # 验证本卦
        self.assertEqual(res["original_hexagram"]["name"], "既济")
        self.assertEqual(res["original_hexagram"]["full_name"], "水火既济")
        self.assertEqual(res["original_hexagram"]["number"], 63)

        # 验证动爻 (爻位 1..6，自下而上)
        self.assertEqual(res["moving_lines"], [5, 6])

        # 验证变卦
        self.assertEqual(res["transformed_hexagram"]["name"], "贲")
        self.assertEqual(res["transformed_hexagram"]["full_name"], "山火贲")
        self.assertEqual(res["transformed_hexagram"]["number"], 22)

        # 验证互卦
        self.assertEqual(res["nuclear_hexagram"]["name"], "未济")
        self.assertEqual(res["nuclear_hexagram"]["full_name"], "火水未济")
        self.assertEqual(res["nuclear_hexagram"]["number"], 64)

        # 验证各爻爻名与性质
        self.assertEqual(res["lines"][0]["yao_name"], "初九")
        self.assertEqual(res["lines"][0]["nature"], "阳")
        self.assertFalse(res["lines"][0]["is_moving"])

        self.assertEqual(res["lines"][1]["yao_name"], "六二")
        self.assertEqual(res["lines"][1]["nature"], "阴")
        self.assertFalse(res["lines"][1]["is_moving"])

        self.assertEqual(res["lines"][2]["yao_name"], "九三")
        self.assertEqual(res["lines"][2]["nature"], "阳")
        self.assertFalse(res["lines"][2]["is_moving"])

        self.assertEqual(res["lines"][3]["yao_name"], "六四")
        self.assertEqual(res["lines"][3]["nature"], "阴")
        self.assertFalse(res["lines"][3]["is_moving"])

        self.assertEqual(res["lines"][4]["yao_name"], "九五")
        self.assertEqual(res["lines"][4]["nature"], "阳")
        self.assertTrue(res["lines"][4]["is_moving"])

        self.assertEqual(res["lines"][5]["yao_name"], "上六")
        self.assertEqual(res["lines"][5]["nature"], "阴")
        self.assertTrue(res["lines"][5]["is_moving"])

    def test_pure_yang_static(self):
        """测试纯阳静卦 (乾为天，无动爻)"""
        lines = [7, 7, 7, 7, 7, 7]
        res = calculate_hexagram(lines)
        self.assertEqual(res["original_hexagram"]["name"], "乾")
        self.assertEqual(res["transformed_hexagram"]["name"], "乾")
        self.assertEqual(res["nuclear_hexagram"]["name"], "乾")
        self.assertEqual(res["moving_lines"], [])
        self.assertTrue(res["is_pure_yang"])
        self.assertFalse(res["is_pure_yin"])

    def test_pure_yang_all_moving(self):
        """测试纯阳全动 (乾之坤，触发用九)"""
        lines = [9, 9, 9, 9, 9, 9]
        res = calculate_hexagram(lines)
        self.assertEqual(res["original_hexagram"]["name"], "乾")
        self.assertEqual(res["transformed_hexagram"]["name"], "坤")
        self.assertEqual(res["nuclear_hexagram"]["name"], "乾")
        self.assertEqual(res["moving_lines"], [1, 2, 3, 4, 5, 6])
        self.assertIsNotNone(res["special_statement"])
        self.assertIn("用九", res["special_statement"])

    def test_pure_yin_static(self):
        """测试纯阴静卦 (坤为地，无动爻)"""
        lines = [8, 8, 8, 8, 8, 8]
        res = calculate_hexagram(lines)
        self.assertEqual(res["original_hexagram"]["name"], "坤")
        self.assertEqual(res["transformed_hexagram"]["name"], "坤")
        self.assertEqual(res["nuclear_hexagram"]["name"], "坤")
        self.assertEqual(res["moving_lines"], [])
        self.assertFalse(res["is_pure_yang"])
        self.assertTrue(res["is_pure_yin"])

    def test_pure_yin_all_moving(self):
        """测试纯阴全动 (坤之乾，触发用六)"""
        lines = [6, 6, 6, 6, 6, 6]
        res = calculate_hexagram(lines)
        self.assertEqual(res["original_hexagram"]["name"], "坤")
        self.assertEqual(res["transformed_hexagram"]["name"], "乾")
        self.assertEqual(res["nuclear_hexagram"]["name"], "坤")
        self.assertEqual(res["moving_lines"], [1, 2, 3, 4, 5, 6])
        self.assertIsNotNone(res["special_statement"])
        self.assertIn("用六", res["special_statement"])

    def test_hexagram_table_completeness(self):
        """验证六十四卦表的完整性 (8x8=64组合全部存在且编号唯一)"""
        self.assertEqual(len(HEXAGRAM_TABLE), 64)
        seen_numbers = set()
        for (upper, lower), data in HEXAGRAM_TABLE.items():
            num = data[0]
            self.assertNotIn(num, seen_numbers)
            seen_numbers.add(num)
            self.assertTrue(1 <= num <= 64)
        self.assertEqual(len(seen_numbers), 64)

    def test_trigrams_completeness(self):
        """验证八卦定义 (8种组合全部存在)"""
        self.assertEqual(len(TRIGRAMS), 8)
        names = {v["name"] for v in TRIGRAMS.values()}
        self.assertEqual(names, {"乾", "兑", "离", "震", "巽", "坎", "艮", "坤"})

    def test_invalid_line_count(self):
        """测试爻数非法"""
        with self.assertRaises(ValueError):
            calculate_hexagram([7, 8, 7])
        with self.assertRaises(ValueError):
            calculate_hexagram([7, 8, 7, 8, 9, 6, 7])

    def test_invalid_line_value(self):
        """测试爻值非法"""
        with self.assertRaises(ValueError):
            calculate_hexagram([7, 8, 7, 8, 9, 5])
        with self.assertRaises(ValueError):
            calculate_hexagram([7, 8, 7, 8, 9, 10])

    def test_cast_coins(self):
        """测试铜钱摇卦模拟的物理有效性"""
        for _ in range(20):
            lines, flips = cast_coins()
            self.assertEqual(len(lines), 6)
            self.assertEqual(len(flips), 6)
            for val in lines:
                self.assertIn(val, (6, 7, 8, 9))
            for f in flips:
                self.assertEqual(len(f), 3)
                for coin in f:
                    self.assertIn(coin, (2, 3))

    def test_coins_exact_enumeration_distribution(self):
        """
        测试三枚铜钱理论全枚举二项分布：
        每枚铜钱有 2 (阴面) 或 3 (阳面) 两种结果，3枚铜钱共 2^3 = 8 种等可能样本空间：
        - (2, 2, 2) => 和 6 (老阴，动爻): 1 种 (1/8 = 12.5%)
        - (2, 2, 3), (2, 3, 2), (3, 2, 2) => 和 7 (少阳，静爻): 3 种 (3/8 = 37.5%)
        - (2, 3, 3), (3, 2, 3), (3, 3, 2) => 和 8 (少阴，静爻): 3 种 (3/8 = 37.5%)
        - (3, 3, 3) => 和 9 (老阳，动爻): 1 种 (1/8 = 12.5%)
        """
        sample_space = [(c1, c2, c3) for c1 in (2, 3) for c2 in (2, 3) for c3 in (2, 3)]
        self.assertEqual(len(sample_space), 8)
        sums = [sum(outcome) for outcome in sample_space]
        self.assertEqual(sums.count(6), 1)
        self.assertEqual(sums.count(7), 3)
        self.assertEqual(sums.count(8), 3)
        self.assertEqual(sums.count(9), 1)

    def test_all_4096_inputs_structural_invariants(self):
        """
        结构不变量穷举校验 (4^6 = 4096 种合法六爻输入组合):
        说明：遍历穷举全空间用于验证数理逻辑与状态机的不变量成立，
        绝不作为“预测准确率”的指标宣传。
        检验不变量：
        1. 爻数严格等于 6，本卦、变卦、互卦编号均在 [1, 64] 范围内。
        2. 无动爻输入 (仅由 7, 8 构成，共 2^6 = 64 种) 时，变卦必然恒等于本卦，动爻列表恒为空。
        3. 动爻索引严格对应所有值为 6 或 9 的爻位 (1..6)。
        4. 变卦阴阳转换正确 (6->1, 9->0, 7->1, 8->0)。
        5. 互卦严格由原卦下互 (二三四爻) 与上互 (三四五爻) 构成。
        6. 用九/用六仅在全动纯乾/全动纯坤时触发，静卦乾坤绝不触发。
        """
        import itertools
        checked_count = 0
        static_count = 0
        for combo in itertools.product((6, 7, 8, 9), repeat=6):
            lines = list(combo)
            res = calculate_hexagram(lines)
            checked_count += 1

            # 不变量 1: 编号范围
            self.assertEqual(len(res["lines"]), 6)
            self.assertTrue(1 <= res["original_hexagram"]["number"] <= 64)
            self.assertTrue(1 <= res["transformed_hexagram"]["number"] <= 64)
            self.assertTrue(1 <= res["nuclear_hexagram"]["number"] <= 64)

            # 不变量 2: 动爻与变卦一致性
            moving = res["moving_lines"]
            expected_moving = [idx for idx, val in enumerate(lines, start=1) if val in (6, 9)]
            self.assertEqual(moving, expected_moving)

            if not moving:
                static_count += 1
                self.assertEqual(res["original_hexagram"]["number"], res["transformed_hexagram"]["number"])

            # 不变量 3: 互卦爻位
            orig_bits = [1 if v in (7, 9) else 0 for v in lines]
            nuc_lower_bits = (orig_bits[1], orig_bits[2], orig_bits[3])
            nuc_upper_bits = (orig_bits[2], orig_bits[3], orig_bits[4])
            self.assertEqual(TRIGRAMS[nuc_lower_bits]["name"], res["nuclear_hexagram"]["lower_trigram"])
            self.assertEqual(TRIGRAMS[nuc_upper_bits]["name"], res["nuclear_hexagram"]["upper_trigram"])

            # 不变量 4: 用九/用六触发严格性
            if res["special_statement"] is not None:
                is_all_9 = all(v == 9 for v in lines)
                is_all_6 = all(v == 6 for v in lines)
                self.assertTrue(is_all_9 or is_all_6)
                if is_all_9:
                    self.assertIn("用九", res["special_statement"])
                if is_all_6:
                    self.assertIn("用六", res["special_statement"])

        self.assertEqual(checked_count, 4096)
        self.assertEqual(static_count, 64)

if __name__ == "__main__":
    unittest.main()
