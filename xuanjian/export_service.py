# -*- coding: utf-8 -*-
"""
xuanjian/export_service.py - 数据导出与溯源格式化服务

支持将问事卦象、知止反思、历法记录导出为严谨的 Markdown 与 JSON 格式，
附带版本、算法、典籍来源及边界声明，杜绝私密凭据外泄。
"""

import json
import datetime
from typing import Dict, Any

EXPORT_SCHEMA_VERSION = "2.0.0"

def export_divination_markdown(payload: Dict[str, Any]) -> str:
    """生成易学卦象考据与反思 Markdown 文本"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic = payload.get("topic", "未命名问事/研读事项")
    calc = payload.get("calculation", {})
    orig = calc.get("original_hexagram", {})
    trans = calc.get("transformed_hexagram", {})
    nuc = calc.get("nuclear_hexagram", {})
    mov = calc.get("moving_lines", [])
    mov_str = ", ".join(str(m) for m in mov) if mov else "无（静卦）"

    lines = [
        f"# 「玄鉴·书房」研究记录 · {orig.get('name', '')}之{trans.get('name', '')}",
        f"",
        f"> **起卦时间**：{calc.get('cast_at', now_str)}  ",
        f"> **起卦方式**：{calc.get('generation_mode', '历史记录')}  ",
        f"> **主题/思考事项**：{topic}  ",
        f"> **计算方法**：文王六十四卦象数确定性计算（自下而上初爻至上爻）  ",
        f"> **版本标准**：XuanJian Core v{EXPORT_SCHEMA_VERSION}  ",
        f"",
        f"---",
        f"",
        f"## 一、象数结构",
        f"",
        f"- **本卦**：第 {orig.get('number', '')} 卦 【{orig.get('name', '')}】（{orig.get('full_name', '')}）",
        f"  - 上卦：{orig.get('upper_trigram', '')} ｜ 下卦：{orig.get('lower_trigram', '')}",
        f"  - 卦辞：{orig.get('guaci', '')}",
        f"  - 大象传：{orig.get('xiangzhuan', '')}",
        f"- **动爻**：第 {mov_str} 爻",
        f"- **变卦**：第 {trans.get('number', '')} 卦 【{trans.get('name', '')}】（{trans.get('full_name', '')}）",
        f"- **互卦**：第 {nuc.get('number', '')} 卦 【{nuc.get('name', '')}】（{nuc.get('full_name', '')}）",
        f"",
        f"## 二、六爻爻辞溯源（自下而上）",
        f""
    ]

    for item in calc.get("lines", []):
        mov_tag = "【变】" if item.get("is_moving") else "【静】"
        lines.append(f"- **{item.get('yao_name')}** ({mov_tag})：{item.get('yaoci')}")
        lines.append(f"  - *性质*：{item.get('nature')}爻 ｜ 原始爻值：{item.get('value')}")

    if calc.get("coin_flips"):
        lines.extend(["", "## 原始投币记录"])
        for i, coins in enumerate(calc["coin_flips"], 1):
            lines.append(f"- 第{i}次：{' + '.join(map(str, coins))} = {sum(coins)}")
    lines.extend(["", "爻辞来源：open-iching 电子录入文本（古代公版原文），未逐条独立校订。"])

    # 分层解读
    interpretation = payload.get("interpretation", {})
    if interpretation:
        lines.extend([
            f"",
            f"## 三、分层考据与解读",
            f"",
            f"- **【传统文本】**：{interpretation.get('traditional_text', '依据《周易》卦爻辞及十翼大象传原典。')}",
            f"- **【术数计算】**：{interpretation.get('math_calculation', f'爻位变换与互卦取象，变爻位在第 {mov_str} 爻。')}",
            f"- **【象征解读】**：{interpretation.get('symbolic_insight', '以君子思患预防、修德省身之哲学启示。')}",
            f"- **【现实证据】**：{interpretation.get('real_world_evidence', '一切现实决策应当尊重客观商业、医学与法律事实。')}",
            f"- **【待核实项】**：{interpretation.get('to_verify', '任何未经实证核实之推测均保留存疑。')}"
        ])

    lines.extend([
        f"",
        f"---",
        f"",
        f"### 典籍溯源与边界声明",
        f"1. **典籍版本**：卦爻采用已登记来源的传世电子录入文本，爻辞未逐条独立校订；解释段落为现代规则解读。",
        f"2. **理智原则**：象数体验旨在澄心理性、启发反思；严禁用于健康诊断、投机交易或替代法定合约与客观事实。"
    ])

    return "\n".join(lines)

def export_reflection_markdown(payload: Dict[str, Any]) -> str:
    """生成知止反思卡与现实评估 Markdown 文本"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic = payload.get("topic", "未命名反思决策")
    eval_res = payload.get("evaluation", {})
    pause_card = eval_res.get("pause_card", {})

    lines = [
        f"# 「玄鉴·知止」现实反思手记 · {topic}",
        f"",
        f"> **记录时间**：{now_str}  ",
        f"> **风险评估等级**：{eval_res.get('risk_level', 'NORMAL')}  ",
        f"> **版本标准**：XuanJian Reflection v{EXPORT_SCHEMA_VERSION}  ",
        f"",
        f"---",
        f"",
        f"## 一、现实风险提醒条目",
        f""
    ]

    alerts = eval_res.get("alerts", [])
    if alerts:
        for idx, alert in enumerate(alerts, 1):
            lines.extend([
                f"### {idx}. [{alert.get('level', '').upper()}] {alert.get('title')}",
                f"- **触发事实**：{alert.get('trigger_fact')}",
                f"- **可能影响**：{alert.get('possible_impact')}",
                f"- **更稳妥的替代方案**：{alert.get('safer_alternative')}",
                f"- **调整建议**：{alert.get('how_to_adjust')}",
                f""
            ])
    else:
        lines.append("当前主动提供的事实中，未触发明显的透支或不可逆高危边界。\n")

    lines.extend([
        f"## 二、决定前暂停卡（澄心自问）",
        f""
    ])

    for q in pause_card.get("questions", []):
        lines.extend([
            f"**{q.get('label')}**",
            f"> 引导提示：{q.get('prompt')}",
            f"- 填写内容：{q.get('user_value')}",
            f""
        ])

    lines.extend([
        f"---",
        f"",
        f"### 现实理性声明",
        f"本反思卡仅依据用户主动填写的已知事实生成，旨在破除冲动决策幻觉。信用额度不等于自有收入，冷静期绝不可拖延法定退款与考试时效。"
    ])

    return "\n".join(lines)

def export_bundle_json(payload: Dict[str, Any]) -> str:
    """生成符合标准 Schema 的完整 JSON 导出包"""
    bundle = {
        "$schema": "https://xuanjian.studio/schemas/export-v2.json",
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": datetime.datetime.now().isoformat(),
        "application": "XuanJian Studio (玄鉴·书房)",
        "license": "MIT / Open Academic Use",
        "data": payload
    }
    return json.dumps(bundle, ensure_ascii=False, indent=2)
