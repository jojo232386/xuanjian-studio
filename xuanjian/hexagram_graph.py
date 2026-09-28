#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/hexagram_graph.py - 六十四卦关系网与典籍研读象数引擎 (F05)

构建文王六十四卦全息关系网络：
1. 本卦（上下卦象、六爻阴阳序列、卦名、卦辞、彖传、象传）；
2. 错卦（对卦）：六爻皆变（阴变阳、阳变阴），呈现截然相反之镜像考量；
3. 综卦（反卦）：上下颠倒（初爻至上爻倒置），呈现换位思考与逆向视角；
4. 互卦（重卦中爻）：取二三四爻为下卦、三四五爻为上卦，洞悉事物内在潜藏趋势；
5. 之卦（单爻变卦）：自下而上六爻各自变动所成之六个衍生卦；
6. 序卦邻卦：文王卦序前承与后继。
"""

from typing import Dict, Any, List, Optional, Union
from scripts.iching import HEXAGRAM_TABLE, TRIGRAMS, get_yao_name

# 辅助查找映射表
NAME_TO_TRIGRAM = {v["name"]: k for k, v in TRIGRAMS.items()}
TRIGRAM_TO_NAME = {k: v["name"] for k, v in TRIGRAMS.items()}

# (King Wen Number) -> (upper_name, lower_name)
NUM_TO_TRIGRAM_NAMES: Dict[int, tuple] = {}
NAME_TO_NUM: Dict[str, int] = {}
TABLE_BY_NUM: Dict[int, tuple] = {}

for (upper_name, lower_name), entry in HEXAGRAM_TABLE.items():
    num = entry[0]
    short_name = entry[1]
    NUM_TO_TRIGRAM_NAMES[num] = (upper_name, lower_name)
    NAME_TO_NUM[short_name] = num
    NAME_TO_NUM[entry[2]] = num  # full_name 也能索引
    TABLE_BY_NUM[num] = entry

def _lines_from_trigrams(upper_name: str, lower_name: str) -> List[int]:
    """根据上下卦获取自下而上的6个二进制爻 (0=阴, 1=阳)"""
    lower_bits = list(NAME_TO_TRIGRAM[lower_name])
    upper_bits = list(NAME_TO_TRIGRAM[upper_name])
    return lower_bits + upper_bits

def _get_hex_brief_by_bits(lines: List[int]) -> Dict[str, Any]:
    """根据6个爻获取简要卦信息"""
    lower_tuple = tuple(lines[0:3])
    upper_tuple = tuple(lines[3:6])
    lower_name = TRIGRAM_TO_NAME[lower_tuple]
    upper_name = TRIGRAM_TO_NAME[upper_tuple]
    entry = HEXAGRAM_TABLE[(upper_name, lower_name)]
    return {
        "number": entry[0],
        "name": entry[1],
        "full_name": entry[2],
        "upper_trigram": upper_name,
        "lower_trigram": lower_name
    }

def get_hexagram_node(identifier: Union[int, str]) -> Dict[str, Any]:
    """
    根据卦编号 (1-64) 或卦名获取该卦的完整象数关系网节点
    """
    if isinstance(identifier, int):
        num = identifier
    elif isinstance(identifier, str):
        if identifier.isdigit():
            num = int(identifier)
        elif identifier in NAME_TO_NUM:
            num = NAME_TO_NUM[identifier]
        else:
            raise ValueError(f"未识别的卦名或编号: {identifier}")
    else:
        raise ValueError(f"无效的标识符类型: {type(identifier)}")

    if num < 1 or num > 64:
        raise ValueError(f"卦象编号必须在 1 至 64 之间，当前为: {num}")

    upper_name, lower_name = NUM_TO_TRIGRAM_NAMES[num]
    entry = TABLE_BY_NUM[num]
    lines = _lines_from_trigrams(upper_name, lower_name)

    # 1. 错卦 (对卦): 阴阳全翻转
    opposite_lines = [1 - b for b in lines]
    opposite_info = _get_hex_brief_by_bits(opposite_lines)
    opposite_info["relation_type"] = "错卦 (对卦)"
    opposite_info["meaning"] = "阴阳易位，立场反转。从截然相反的极端审视事物利弊与潜在盲区。"

    # 2. 综卦 (反卦): 上下颠倒 (lines[::-1])
    reverse_lines = lines[::-1]
    is_self_reversed = (reverse_lines == lines)
    reverse_info = _get_hex_brief_by_bits(reverse_lines)
    reverse_info["relation_type"] = "综卦 (反卦)"
    reverse_info["is_self_reversed"] = is_self_reversed
    if is_self_reversed:
        reverse_info["meaning"] = "本卦上下对称（正卦），倒看仍为自身。示现立身持正、表里如一之象。"
    else:
        reverse_info["meaning"] = "上下颠倒，视角逆转。从对方感受、后来者视角或终局换位思考。"

    # 3. 互卦 (重卦中爻): 下互取2,3,4爻，上互取3,4,5爻
    nuclear_lines = list(lines[1:4]) + list(lines[2:5])
    nuclear_info = _get_hex_brief_by_bits(nuclear_lines)
    nuclear_info["relation_type"] = "互卦 (交互卦)"
    nuclear_info["meaning"] = "剔除初爻之始与上爻之终，观照事物内部蕴育的核心动力与潜在质变。"

    # 4. 单爻变卦 (之卦): 1至6爻发动
    changes = []
    for line_idx in range(1, 7):
        ch_lines = list(lines)
        ch_lines[line_idx - 1] = 1 - ch_lines[line_idx - 1]
        ch_info = _get_hex_brief_by_bits(ch_lines)
        yao_name = get_yao_name(line_idx, lines[line_idx - 1])
        changes.append({
            "line_index": line_idx,
            "line_name": yao_name,
            "line_bit": lines[line_idx - 1],
            "target_hexagram": ch_info
        })

    # 5. 序卦前后卦
    prev_num = 64 if num == 1 else num - 1
    next_num = 1 if num == 64 else num + 1
    prev_info = _get_hex_brief_by_bits(_lines_from_trigrams(*NUM_TO_TRIGRAM_NAMES[prev_num]))
    next_info = _get_hex_brief_by_bits(_lines_from_trigrams(*NUM_TO_TRIGRAM_NAMES[next_num]))

    # 爻体详细（自下而上）
    line_structures = []
    for idx, bit in enumerate(lines, start=1):
        line_structures.append({
            "index": idx,
            "bit": bit,
            "nature": "阳" if bit == 1 else "阴",
            "name": get_yao_name(idx, bit),
            "symbol": "—" if bit == 1 else "- -"
        })

    return {
        "number": num,
        "name": entry[1],
        "full_name": entry[2],
        "upper_trigram": {
            "name": upper_name,
            "nature": TRIGRAMS[NAME_TO_TRIGRAM[upper_name]]["nature"],
            "symbol": TRIGRAMS[NAME_TO_TRIGRAM[upper_name]]["symbol"],
            "attr": TRIGRAMS[NAME_TO_TRIGRAM[upper_name]]["attr"]
        },
        "lower_trigram": {
            "name": lower_name,
            "nature": TRIGRAMS[NAME_TO_TRIGRAM[lower_name]]["nature"],
            "symbol": TRIGRAMS[NAME_TO_TRIGRAM[lower_name]]["symbol"],
            "attr": TRIGRAMS[NAME_TO_TRIGRAM[lower_name]]["attr"]
        },
        "lines": lines,
        "line_structures": line_structures,
        "texts": {
            "guaci": entry[3],
            "xiangzhuan": entry[4],
            "tuanzhuan": entry[5]
        },
        "relationships": {
            "opposite": opposite_info,
            "reverse": reverse_info,
            "nuclear": nuclear_info,
            "changes": changes,
            "prev_hexagram": prev_info,
            "next_hexagram": next_info
        }
    }

def get_all_hexagrams_summary() -> List[Dict[str, Any]]:
    """获取文王六十四卦全表概览（供关系网概览与快速筛选）"""
    res = []
    for num in range(1, 65):
        upper_name, lower_name = NUM_TO_TRIGRAM_NAMES[num]
        entry = TABLE_BY_NUM[num]
        lines = _lines_from_trigrams(upper_name, lower_name)
        res.append({
            "number": num,
            "name": entry[1],
            "full_name": entry[2],
            "upper_trigram": upper_name,
            "lower_trigram": lower_name,
            "lines": lines,
            "guaci_summary": entry[3][:30] + ("..." if len(entry[3]) > 30 else ""),
            "xiangzhuan": entry[4]
        })
    return res

def search_hexagrams(keyword: str) -> List[Dict[str, Any]]:
    """检索卦象（支持编号、单字名、全名、上下卦、卦辞或大象传模糊检索）"""
    kw = keyword.strip()
    if not kw:
        return get_all_hexagrams_summary()

    all_hex = get_all_hexagrams_summary()
    matched = []
    for h in all_hex:
        if (
            (kw.isdigit() and h["number"] == int(kw)) or
            kw in h["name"] or
            kw in h["full_name"] or
            kw in h["upper_trigram"] or
            kw in h["lower_trigram"] or
            kw in h["guaci_summary"] or
            kw in h["xiangzhuan"]
        ):
            matched.append(h)
    return matched
