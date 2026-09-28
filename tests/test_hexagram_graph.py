#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_hexagram_graph.py - 六十四卦关系网与象数引擎单元测试 (F05)
"""

import unittest
from xuanjian.hexagram_graph import (
    get_hexagram_node,
    get_all_hexagrams_summary,
    search_hexagrams,
    HEXAGRAM_TABLE
)

class TestHexagramGraph(unittest.TestCase):

    def test_64_hexagrams_completeness(self):
        """测试文王六十四卦全表覆盖无遗漏"""
        all_hex = get_all_hexagrams_summary()
        self.assertEqual(len(all_hex), 64)
        numbers = [h["number"] for h in all_hex]
        self.assertEqual(numbers, list(range(1, 65)))

    def test_opposite_hexagram_symmetry(self):
        """测试错卦（对卦，六爻阴阳全反转）数学对称性"""
        # 乾 (1, 纯阳) 的错卦为 坤 (2, 纯阴)
        qian = get_hexagram_node(1)
        self.assertEqual(qian["relationships"]["opposite"]["number"], 2)
        self.assertEqual(qian["relationships"]["opposite"]["name"], "坤")

        # 坤 (2) 的错卦为 乾 (1)
        kun = get_hexagram_node(2)
        self.assertEqual(kun["relationships"]["opposite"]["number"], 1)

        # 既济 (63) 的错卦为 未济 (64)
        jiji = get_hexagram_node(63)
        self.assertEqual(jiji["relationships"]["opposite"]["number"], 64)

        # 验证对所有64卦：错卦之错卦必为自身
        for num in range(1, 65):
            node = get_hexagram_node(num)
            opp_num = node["relationships"]["opposite"]["number"]
            opp_node = get_hexagram_node(opp_num)
            self.assertEqual(opp_node["relationships"]["opposite"]["number"], num)

    def test_reverse_hexagram_properties(self):
        """测试综卦（反卦，上下颠倒倒置）属性与正卦自身对称性"""
        # 屯 (3, 水雷屯) 倒过来是 蒙 (4, 山水蒙)
        tun = get_hexagram_node(3)
        self.assertEqual(tun["relationships"]["reverse"]["number"], 4)
        self.assertEqual(tun["relationships"]["reverse"]["name"], "蒙")
        self.assertFalse(tun["relationships"]["reverse"]["is_self_reversed"])

        meng = get_hexagram_node(4)
        self.assertEqual(meng["relationships"]["reverse"]["number"], 3)

        # 易学八正卦 (乾、坤、坎、离、颐、大过、小过、中孚) 综卦为自身
        self_reversed_nums = {1, 2, 27, 28, 29, 30, 61, 62}
        for num in range(1, 65):
            node = get_hexagram_node(num)
            is_self = node["relationships"]["reverse"]["is_self_reversed"]
            if num in self_reversed_nums:
                self.assertTrue(is_self, f"卦 {num} {node['name']} 应为正卦自反")
                self.assertEqual(node["relationships"]["reverse"]["number"], num)
            else:
                self.assertFalse(is_self, f"卦 {num} {node['name']} 不应自反")

    def test_nuclear_hexagram_properties(self):
        """测试互卦（重卦中爻：下互234，上互345）"""
        # 乾 (1) 的互卦为 乾 (1)
        qian = get_hexagram_node(1)
        self.assertEqual(qian["relationships"]["nuclear"]["number"], 1)

        # 坤 (2) 的互卦为 坤 (2)
        kun = get_hexagram_node(2)
        self.assertEqual(kun["relationships"]["nuclear"]["number"], 2)

        # 既济 (63) 101010: 二三四为010(坎)，三四五为101(离)，上离下坎为未济(64)
        jiji = get_hexagram_node(63)
        self.assertEqual(jiji["relationships"]["nuclear"]["number"], 64)

        # 屯 (3) 100010: 二三四为000(坤)，三四五为001(艮)，上艮下坤为山地剥(23)
        tun = get_hexagram_node(3)
        self.assertEqual(tun["relationships"]["nuclear"]["number"], 23)

    def test_single_line_changes(self):
        """测试单爻变动之卦推算"""
        jiji = get_hexagram_node(63)
        changes = jiji["relationships"]["changes"]
        self.assertEqual(len(changes), 6)

        # 既济第5爻（九五，阳爻变阴爻）-> 地火明夷 (36)
        line5_change = changes[4]
        self.assertEqual(line5_change["line_index"], 5)
        self.assertEqual(line5_change["line_name"], "九五")
        self.assertEqual(line5_change["target_hexagram"]["number"], 36)
        self.assertEqual(line5_change["target_hexagram"]["name"], "明夷")

    def test_search_hexagrams(self):
        """测试卦象多维度检索"""
        res_by_num = search_hexagrams("63")
        self.assertEqual(len(res_by_num), 1)
        self.assertEqual(res_by_num[0]["name"], "既济")

        res_by_name = search_hexagrams("未济")
        self.assertTrue(any(h["name"] == "未济" for h in res_by_name))

        res_by_xiang = search_hexagrams("预防")
        self.assertTrue(any(h["name"] == "既济" for h in res_by_xiang))

    def test_invalid_identifier_raises_error(self):
        """测试非法卦号抛出异常"""
        with self.assertRaises(ValueError):
            get_hexagram_node(0)
        with self.assertRaises(ValueError):
            get_hexagram_node(65)
        with self.assertRaises(ValueError):
            get_hexagram_node("不存在的神秘卦")

if __name__ == "__main__":
    unittest.main()
