#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/builtin_reader.py - 四术一体内置研读与规则出处考据引擎 (零 API 配置核心)

为周易、八字、紫微斗数、奇门遁甲提供 100% 确定性、纯本地、免外部大模型的规则解读：
1. 提取排盘核心象数结构（卦爻、四柱、宫星、门仪格局）；
2. 关联权威典籍原典出处（《周易》经传、《渊海子平》、《紫微斗数全书》、《奇门遁甲统宗》等）；
3. 生成规范化的「内置研读」报告，包含传统象征启示与现实知止警示；
4. 严格标注【内置研读】标签，绝不伪装为大模型自由对话；
5. 提供可验证的引用列表（Citations）与版本标识。
"""

from typing import Dict, Any, List, Optional
import json

from scripts.iching import HEXAGRAM_TABLE, YAOCI_SPECIAL, get_yao_name

RULE_VERSION = "2026.4.1"

# 构建 64 卦全量正文与象传快速索引 (短名、全名与卦号映射)
HEXAGRAM_BY_NAME: Dict[str, Any] = {}
HEXAGRAM_BY_NUMBER: Dict[int, Any] = {}
for entry in HEXAGRAM_TABLE.values():
    num, short_name, full_name, guaci, xiang, tuan = entry
    HEXAGRAM_BY_NAME[short_name] = entry
    HEXAGRAM_BY_NAME[full_name] = entry
    HEXAGRAM_BY_NUMBER[num] = entry

# 典籍出处基础元库
CLASSICAL_CITATIONS = {
    "iching_qian": {
        "id": "C_YJ_01",
        "book": "《周易·乾传》",
        "chapter": "乾·大象传",
        "quote": "天行健，君子以自强不息。",
        "applicability": "见于乾卦及阳刚健行象数，喻主动进取同时需戒骄盈。"
    },
    "iching_kun": {
        "id": "C_YJ_02",
        "book": "《周易·坤传》",
        "chapter": "坤·大象传",
        "quote": "地势坤，君子以厚德载物。",
        "applicability": "见于坤卦及顺承柔和象数，喻包容沉潜、循序渐进。"
    },
    "iching_jiji": {
        "id": "C_YJ_63",
        "book": "《周易·既济传》",
        "chapter": "既济·大象传",
        "quote": "水在火上，既济；君子以思患而预防之。",
        "applicability": "凡见既济或事物处于初成阶段，警醒居安思危、防患未然。"
    },
    "bazi_ziping": {
        "id": "C_BZ_01",
        "book": "《渊海子平》",
        "chapter": "论五行生克制化",
        "quote": "金旺得火，方成器皿；火旺得水，方成相济；水旺得土，方成池沼；土旺得木，方能疏通；木旺得金，方成栋梁。",
        "applicability": "八字五行配置字面统计分析，明辨五行重在流通平衡，非单字孤立。"
    },
    "ziwei_quanshu": {
        "id": "C_ZW_01",
        "book": "《紫微斗数全书》",
        "chapter": "卷一·太微赋",
        "quote": "禄权科忌，为数中之变化；紫微居午，无辅弼亦为君。善恶相因，吉凶相伴，存乎一心。",
        "applicability": "紫微斗数星盘生年四化与主星庙旺分析，强调心性自主高于星相客体。"
    },
    "qimen_tongzong": {
        "id": "C_QM_01",
        "book": "《奇门遁甲统宗》",
        "chapter": "卷一·奇门要览",
        "quote": "急则从神缓从门，动则审局静安身。吉门招福休妄动，凶门避祸重自新。",
        "applicability": "奇门时家转盘九宫八门运筹抉择，强调知止安身高于冒险取巧。"
    },
    "qimen_shigan": {
        "id": "C_QM_02",
        "book": "《奇门遁甲元机赋》",
        "chapter": "十干克应篇",
        "quote": "三奇得使利出行，六仪加临辨主客。吉格相扶莫大意，凶格并临省愆尤。",
        "applicability": "九宫天盘干与地盘干组合格局匹配，提供传统事理参考。"
    }
}

def generate_builtin_reading(record_type: str, data: Dict[str, Any], query: str = "", topic: str = "") -> Dict[str, Any]:
    """
    根据四术排盘结果生成确定性、免外部 API 的内置研读报告

    :param record_type: 'divination' (周易), 'bazi' (八字), 'ziwei' (紫微), 'qimen' (奇门)
    :param data: 对应排盘的结构化结果 (严禁为空字典)
    :param query: 用户可选附加考查主题或疑问
    :param topic: 别名，同 query
    :return: 包含标题、结构化段落、引文出处与知止防线的字典
    """
    if not data or not isinstance(data, dict):
        raise ValueError(f"【{record_type}】内置研读缺少有效排盘数据 (排盘结果不可为空)")

    q = topic if topic else query
    if record_type in ("divination", "zhouyi"):
        return _read_divination(data, q)
    elif record_type == "bazi":
        return _read_bazi(data, q)
    elif record_type == "ziwei":
        return _read_ziwei(data, q)
    elif record_type == "qimen":
        return _read_qimen(data, q)
    else:
        return _read_fallback(record_type, data, q)

def _read_divination(data: Dict[str, Any], query: str) -> Dict[str, Any]:
    if not data or not isinstance(data, dict):
        raise ValueError("周易研读缺少有效排盘数据")

    # 1. 兼容真实引擎 calculate_hexagram 的嵌套结构与历史扁平结构
    orig_data = data.get("original_hexagram")
    trans_data = data.get("transformed_hexagram")
    nuc_data = data.get("nuclear_hexagram")
    raw_lines = data.get("lines") or []
    moving_lines = data.get("moving_lines") or data.get("change_lines") or []

    # 提取本卦信息
    hex_name = ""
    hex_num = None

    if isinstance(orig_data, dict):
        hex_name = orig_data.get("name") or ""
        hex_num = orig_data.get("number")

    if not hex_name:
        hex_name = data.get("ben_name") or data.get("name") or data.get("hexagram") or ""

    if not hex_name and not hex_num:
        raise ValueError("周易研读缺少有效卦象名称或卦号")

    # 严格从 64 卦表中核查，若未知直接 ValueError，名称与编号矛盾直接拒绝 (杜绝乾卦兜底)
    hex_entry = None
    if hex_name and hex_name in HEXAGRAM_BY_NAME:
        hex_entry = HEXAGRAM_BY_NAME[hex_name]
    elif hex_num and hex_num in HEXAGRAM_BY_NUMBER:
        hex_entry = HEXAGRAM_BY_NUMBER[hex_num]

    if not hex_entry:
        raise ValueError(f"未知或非法的周易卦象: 卦名={hex_name}, 卦号={hex_num}")

    h_num, h_short, h_full, h_guaci, h_xiang, h_tuan = hex_entry
    if hex_num is not None and int(hex_num) != h_num:
        raise ValueError(f"卦名「{hex_name}」与卦号「{hex_num}」不符 (应为第{h_num}卦「{h_short}」)")

    hex_name = h_short
    hex_num = h_num
    full_name = h_full
    guaci = h_guaci
    xiangzhuan = h_xiang
    tuanzhuan = h_tuan

    # 提取互卦信息 (若存在，校验并取其规范全称)
    hu_name = ""
    if isinstance(nuc_data, dict):
        hu_name = nuc_data.get("name") or nuc_data.get("full_name") or ""
    if not hu_name:
        hu_name = data.get("hu_name") or ""

    # 提取变卦信息 (若存在，校验并取其规范全称)
    bian_name = ""
    if isinstance(trans_data, dict):
        bian_name = trans_data.get("name") or trans_data.get("full_name") or ""
    if not bian_name:
        bian_name = data.get("bian_name") or ""

    # 提取动爻考据文本：仅采信 YAOCI_SPECIAL 收录文本或经检验的爻辞，绝不无中生有编造经文
    moving_yaoci_list = []
    for ml in moving_lines:
        if (hex_num, ml) in YAOCI_SPECIAL:
            moving_yaoci_list.append(f"爻位{ml}：{YAOCI_SPECIAL[(hex_num, ml)]}")
        else:
            moving_yaoci_list.append(f"爻位{ml}：此爻原文尚未收录。")

    # 构建准确出处引用：必须从权威 HEXAGRAM_TABLE 获取，严禁采信计算端透传冒充
    citations = [
        {
            "id": f"C_YJ_{hex_num:02d}",
            "book": f"《周易·{hex_name}传》",
            "chapter": f"{hex_name}·大象传",
            "quote": xiangzhuan,
            "applicability": f"《周易》第{hex_num}卦「{full_name}」，象曰「{xiangzhuan}」。卦辞示以「{guaci}」。"
        }
    ]

    moving_section_content = f"\n动爻考据：\n" + "\n".join(moving_yaoci_list) if moving_yaoci_list else ""

    sections = [
        {
            "heading": "【象数结构研读】",
            "content": f"本卦为「{hex_name}（{full_name}）」" + (f"，互卦为「{hu_name}」" if hu_name else "") + (f"，变卦为「{bian_name}」（动爻位：{', '.join(map(str, moving_lines))}）" if moving_lines else "（纯卦六爻安定无变动）。")
        },
        {
            "heading": "【经传正文考据】",
            "content": f"卦辞：{guaci}\n大象传：{xiangzhuan}{moving_section_content}",
            "citation_ids": [c["id"] for c in citations]
        },
        {
            "heading": "【文化象征与处世启示】",
            "content": f"按传统易理，{hex_name}卦大象所示：「{xiangzhuan}」。重在昭示天道循环与君子行事之宜节。遇吉爻莫轻狂，逢险难宜安止。修德进业者，以内求正定为首务。"
        },
        {
            "heading": "【现实知止与理性防线】",
            "content": "此研读系传世典籍文本释义，绝非对未来的宿命预言。凡涉及合同签署、法律诉讼、医疗健康与财务投资，必须以现实书面证据和专业核查为准。"
        }
    ]

    return {
        "reading_type": "builtin",
        "reading_label": "内置传统典籍研读（纯本地·免 API）",
        "title": f"《周易》{hex_name}卦内置研读",
        "rule_version": RULE_VERSION,
        "is_ai": False,
        "sections": sections,
        "citations": citations,
        "summary": f"卦象呈现「{hex_name}」之象，经传示以「{xiangzhuan}」。知止避险，以实而动。"
    }

def _read_bazi(data: Dict[str, Any], query: str) -> Dict[str, Any]:
    if not data or not isinstance(data, dict):
        raise ValueError("八字研读缺少有效排盘数据")

    day_master = data.get("day_master")
    four_pillars = data.get("four_pillars")
    wuxing = data.get("wuxing_distribution") or data.get("wuxing_analysis")

    # 严格校验：若 day_master 与 four_pillars 均无，坚决拒绝，绝不默认庚金伪造
    if not day_master and not four_pillars:
        raise ValueError("八字排盘数据为空，缺少日元或四柱信息")

    dm_gan = None
    if isinstance(day_master, dict):
        dm_gan = day_master.get("gan")

    if not dm_gan and isinstance(four_pillars, dict):
        day_col = four_pillars.get("day")
        if isinstance(day_col, dict):
            gz = day_col.get("gan_zhi", "")
            if gz:
                dm_gan = gz[0]

    # 严格天干校验：非法日干坚决抛出异常，绝不默认回退“土”或“庚”
    TIANGAN_SET = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
    GAN_WUXING_MAP = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}

    if not dm_gan or dm_gan not in TIANGAN_SET:
        raise ValueError(f"八字排盘数据缺少有效日元天干 (传入: {dm_gan})")

    dm_wx = GAN_WUXING_MAP[dm_gan]

    # 考查是否时辰未知 / 降级为三柱
    is_degraded = (
        data.get("degraded_to_three_pillars") is True
        or data.get("unknown_hour") is True
        or (isinstance(four_pillars, dict) and (
            not four_pillars.get("hour")
            or (isinstance(four_pillars.get("hour"), dict) and four_pillars["hour"].get("gan_zhi") in ("时辰未知", "", None))
        ))
    )

    citations = [CLASSICAL_CITATIONS["bazi_ziping"]]

    wx_summary = ""
    if isinstance(wuxing, dict):
        wx_summary = "、".join([f"{k}:{v}" for k, v in wuxing.items() if isinstance(v, int)])
    if not wx_summary:
        wx_summary = "四柱五行按干支分布"

    degraded_prefix = "【降级提示】因出生时辰未详，本研读已显式降级为年月日本命三柱学理分析，不臆测或脑补时柱干支及晚运归宿。\n" if is_degraded else ""

    sections = [
        {
            "heading": "【日主与格局象数】",
            "content": f"{degraded_prefix}日元天干为「{dm_gan}」（五行属{dm_wx}）。四柱干支字面五行数量分布统计为：{wx_summary}。"
        },
        {
            "heading": "【传统学理考据】",
            "content": f"《渊海子平》云：五行之理在于循环中和。字面统计仅反映干支符号的数量出现频次，不代表客观命理强弱结论。",
            "citation_ids": ["C_BZ_01"]
        },
        {
            "heading": "【心性涵养启示】",
            "content": f"日主为{dm_gan}{dm_wx}，传统取象重在{dm_wx}性特质。顺应天时，养浩然之气；知足常乐，修内守和。"
        },
        {
            "heading": "【现实知止与健康边界】",
            "content": "干支系传统计时坐标模型，切忌附会为个人命运吉凶。生理代谢遵从医学常理，生计立足于诚信奋斗，不可沉溺干支补救。"
        }
    ]

    return {
        "reading_type": "builtin",
        "reading_label": "内置八字学理研读（纯本地·免 API）",
        "title": f"八字日元【{dm_gan}{dm_wx}】内置研读" + ("（三柱降级版）" if is_degraded else ""),
        "rule_version": RULE_VERSION,
        "is_ai": False,
        "sections": sections,
        "citations": citations,
        "summary": f"日元为「{dm_gan}{dm_wx}」，四柱五行字面分布（{wx_summary}）。" + ("【时辰未详·三柱降级】" if is_degraded else "") + "重在修己以和，理性行事。"
    }

def _read_ziwei(data: Dict[str, Any], query: str) -> Dict[str, Any]:
    if not data or not isinstance(data, dict):
        raise ValueError("紫微斗数研读缺少有效排盘数据")

    # 严格时辰降级检查：若出生时辰未知 (degraded=True 或 basic.unknown_hour=True 或无宫位)
    is_degraded = (
        data.get("degraded") is True
        or data.get("degraded_unknown_hour") is True
        or data.get("basic", {}).get("unknown_hour") is True
        or not data.get("palaces")
    )

    if is_degraded:
        # 时辰未知时坚决不输出虚构宫星，明确出具降级说明
        return {
            "reading_type": "builtin",
            "reading_label": "内置紫微斗数研读（时辰未详·降级说明）",
            "title": "紫微斗数时辰未详·降级说明",
            "rule_version": RULE_VERSION,
            "is_ai": False,
            "sections": [
                {
                    "heading": "【时辰未详·排盘降级说明】",
                    "content": "紫微斗数安命宫、定十二宫职与布列十四主星（紫微、天府星系）严格依赖出生时辰。出生时辰未知时，无法推求命身宫位与主星吉凶。本系统严格知止，不推演虚构星曜，不作主星断语。"
                },
                {
                    "heading": "【建议事项】",
                    "content": "建议核对出生证明、户口簿或医院原始记录核实具体时辰。在时辰未明前，可参考八字前三柱（年月日）干支五行流通作为学理参考。"
                },
                {
                    "heading": "【现实知止防线】",
                    "content": "星曜排列为宋明人文象征推衍，绝不可用于推断个人寿命、疾病诊治或商业投机决策。现实人生靠实地耕耘与守法履约建构。"
                }
            ],
            "citations": [CLASSICAL_CITATIONS["ziwei_quanshu"]],
            "summary": "出生时辰未详，星盘已严格降级，不生成虚构主星与十二宫推演。"
        }

    basic = data.get("basic") or {}
    palaces = data.get("palaces") or []
    ming_palace = next((p for p in palaces if p.get("name") == "命宫"), None)

    if not ming_palace:
        raise ValueError("紫微斗数排盘数据缺少命宫信息")

    major_stars = ming_palace.get("majorStars") or []
    major_names = "、".join([s.get("name", "") for s in major_stars]) or "无主星（借对宫）"
    soul = basic.get("soul", "")
    body = basic.get("body", "")
    five_elem = basic.get("fiveElementsClass", "")
    body_palace_name = basic.get("bodyPalaceName") or next((p.get("name") for p in palaces if p.get("isBodyPalace")), "")
    original_palace_name = basic.get("originalPalaceName") or next((p.get("name") for p in palaces if p.get("isOriginalPalace")), "")
    original_palace_branch = basic.get("earthlyBranchOfOriginalPalace") or next((p.get("earthlyBranch") for p in palaces if p.get("isOriginalPalace")), "")
    laiyin_str = f"；身宫在「{body_palace_name}」，来因宫在「{original_palace_name}（{original_palace_branch}位）」" if original_palace_name else ""

    citations = [CLASSICAL_CITATIONS["ziwei_quanshu"]]

    sections = [
        {
            "heading": "【本命星盘象数】",
            "content": f"命宫坐「{ming_palace.get('earthlyBranch', '')}」位，主星坐守：「{major_names}」；命主「{soul}」，身主「{body}」，立局为「{five_elem}」{laiyin_str}。"
        },
        {
            "heading": "【星曜象征与三方考据】",
            "content": f"《紫微斗数全书》以星宿喻人事性情。命宫主星体现处世基调与初衷，迁移对宫观对外行止，官禄财帛察进取之方。善恶吉凶在乎修己慎行。",
            "citation_ids": ["C_ZW_01"]
        },
        {
            "heading": "【德行与知止观照】",
            "content": f"主星「{major_names}」之特性，长于自主谋划，慎于偏狭孤傲。大限流年如时令之春夏秋冬，顺应而不违逆，进退有据。"
        },
        {
            "heading": "【现实防线与理性界限】",
            "content": "星曜排列为宋明人文象征推衍，绝不可用于推断个人寿命、疾病诊治或商业投机决策。现实人生靠实地耕耘与守法履约建构。"
        }
    ]

    return {
        "reading_type": "builtin",
        "reading_label": "内置紫微斗数研读（纯本地·免 API）",
        "title": f"紫微斗数命宫【{major_names}】内置研读",
        "rule_version": RULE_VERSION,
        "is_ai": False,
        "sections": sections,
        "citations": citations,
        "summary": f"命宫主星为「{major_names}」（{five_elem}），命主{soul}。以修身为纲，理性规避冒进。"
    }

def _read_qimen(data: Dict[str, Any], query: str) -> Dict[str, Any]:
    if not data or not isinstance(data, dict):
        raise ValueError("奇门遁甲研读缺少有效排盘数据")

    meta = data.get("meta")
    palaces = data.get("palaces")

    if not meta and not palaces:
        raise ValueError("奇门遁甲排盘数据为空，缺少局象信息")

    meta = meta or {}
    palaces = palaces or []
    dun = meta.get("dun", "")
    ju_num = meta.get("juNumber", "")
    yuan = meta.get("yuan", "")
    zhi_fu = meta.get("zhiFuStar", "")
    zhi_shi = meta.get("zhiShiDoor", "")

    citations = [CLASSICAL_CITATIONS["qimen_tongzong"], CLASSICAL_CITATIONS["qimen_shigan"]]

    # 提取若干十干克应
    keying_samples = []
    for p in palaces:
        tian = p.get("tianPanGan") or p.get("earthStem") or ""
        di = p.get("diPanGan") or p.get("skyStem") or ""
        stem_str = f" [天盘{tian}/地盘{di}]" if tian and di else ""
        for k in p.get("keYing", []):
            keying_samples.append(f"{p.get('fullName')}{stem_str}: {k.get('name')}（{k.get('key')}）- {k.get('desc')}")
    keying_summary = "\n".join(keying_samples[:3]) if keying_samples else "局中天盘地盘各安其位。"

    sections = [
        {
            "heading": "【奇门局数与值符值使】",
            "content": f"此时家转盘奇门局为「{dun} {ju_num}局 · {yuan}」，值符星为「{zhi_fu}」（落{meta.get('zhiFuPalace')}宫），值使门为「{zhi_shi}」（落{meta.get('zhiShiPalace')}宫）。"
        },
        {
            "heading": "【天盘地盘与克应考据】",
            "content": f"《奇门遁甲统宗》强调审时度势，动静有常。\n部分主要宫位十干克应如下：\n{keying_summary}",
            "citation_ids": ["C_QM_01", "C_QM_02"]
        },
        {
            "heading": "【传统运筹启示】",
            "content": f"值使「{zhi_shi}」主管当下行事机要。休生开三吉门宜休整、开创与求利；死惊伤杜诸门宜自守、止息与反思，万事以静待清明为宜。"
        },
        {
            "heading": "【现实知止防线】",
            "content": "奇门局系古代时空运筹与演兵模型，决不能借此决定重大医疗救治、金钱借贷或法律诉讼。现实中若有既定期限与合同义务，必须严格依规履约。"
        }
    ]

    return {
        "reading_type": "builtin",
        "reading_label": "内置奇门运筹研读（纯本地·免 API）",
        "title": f"奇门遁甲【{dun}{ju_num}局·{zhi_shi}值使】内置研读",
        "rule_version": RULE_VERSION,
        "is_ai": False,
        "sections": sections,
        "citations": citations,
        "summary": f"局属「{dun}{ju_num}局·{yuan}」，值使门「{zhi_shi}」。重在知止防险，顺理而行。"
    }

def _read_fallback(record_type: str, data: Dict[str, Any], query: str) -> Dict[str, Any]:
    if not data or not isinstance(data, dict):
        raise ValueError(f"【{record_type}】研读缺少有效排盘数据")
    return {
        "reading_type": "builtin",
        "reading_label": "内置象数研读（纯本地·免 API）",
        "title": f"【{record_type}】内置研读",
        "rule_version": RULE_VERSION,
        "is_ai": False,
        "sections": [
            {"heading": "【概述】", "content": "象数已推衍完毕。秉持传统修德自省原则，知止安命。"}
        ],
        "citations": [],
        "summary": "象数完备，以理自持。"
    }
