# -*- coding: utf-8 -*-
"""
xuanjian/reflection_engine.py - 现实风险提醒与决定前暂停卡引擎

依据用户主动提供的事实条件进行理性边界评估：
- 预算不足 / 借贷消费 / 信用卡透支
- 不可逆操作 (删除、辞职、退学、极端决策)
- 真实法定或商业期限 (考试、退款、维权截止)
- 医疗健康边界 (禁止依赖卦象诊断、纠正伪科学绝欲/破功焦虑)
- 反复占问纠偏 (杜绝'抽到吉才罢休'的心态)
"""

from typing import Dict, List, Any, Optional

def evaluate_reflection(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    现实风险与知止反思评估
    :param data: 用户主动提供的事实字典
    """
    topic = str(data.get("topic", "")).strip()
    budget_available = float(data.get("budget_available", 0.0) or 0.0)
    cost_estimate = float(data.get("cost_estimate", 0.0) or 0.0)
    uses_credit = bool(data.get("uses_credit_or_loan", False))
    is_irreversible = bool(data.get("is_irreversible", False))
    deadline = str(data.get("impending_deadline", "")).strip()
    divination_count = int(data.get("divination_count_today", 0) or 0)
    has_medical_conflict = bool(data.get("has_medical_conflict", False))

    alerts = []
    boundaries = []

    # 1. 预算与借贷规则 (信用额度绝对不等于可支配收入)
    if cost_estimate > 0:
        if uses_credit:
            alerts.append({
                "id": "RISK_CREDIT_BORROWING",
                "level": "warning",
                "title": "透支与借贷消费预警",
                "trigger_fact": f"此项支出预算为 ¥{cost_estimate:.2f}，且计划使用借贷或信用卡分期。",
                "possible_impact": "利息与分期手续费将推高真实综合资金成本，且可能削弱未来数月的现金流抵御风险能力。信用额度并非实际收入！",
                "safer_alternative": "将非必需消费搁置至纯现金储蓄充足时；若为生产力刚需工具，先评估二手或开源可逆替代品。",
                "how_to_adjust": "若属于已全额备付的正常免息周转，可在确认现金账户充足后在设置中关闭该项。"
            })
            boundaries.append("信贷与分期额度不作为自有可支配收入核算。")
        if budget_available < cost_estimate:
            shortfall = cost_estimate - budget_available
            alerts.append({
                "id": "RISK_BUDGET_DEFICIT",
                "level": "warning",
                "title": "自有可用预算缺口",
                "trigger_fact": f"可用流动资金为 ¥{budget_available:.2f}，预估支出 ¥{cost_estimate:.2f}，缺口达 ¥{shortfall:.2f}。",
                "possible_impact": "动用紧急备用金将导致突发变故时缺乏缓冲，造成现实焦虑。",
                "safer_alternative": "削减非核心附加选配件，或将决策拆分为多期小额验证。",
                "how_to_adjust": "如已有独立专项储蓄已就绪，可更新可用资金数值。"
            })

    # 2. 不可逆操作规则
    if is_irreversible:
        alerts.append({
            "id": "RISK_IRREVERSIBLE_ACTION",
            "level": "danger",
            "title": "高风险不可逆动作警示",
            "trigger_fact": "当前拟执行的动作为不可逆操作（如彻底删除数据、断绝重要协议或冲动辞退）。",
            "possible_impact": "一旦执行无法回滚撤回，事后补救成本极高且容易陷入决策懊悔。",
            "safer_alternative": "先执行归档、冷备份或阶段性静默观察，设定为期数天的只读冷静期。",
            "how_to_adjust": "若已完成多地多介质完整备份且已通过演练验证，方可继续执行。"
        })
        boundaries.append("不可逆操作前必须具备独立快照或可逆退出路线。")

    # 3. 考试、就医、维权与真实期限规则
    if deadline:
        alerts.append({
            "id": "RISK_LEGAL_DEADLINE",
            "level": "info",
            "title": "真实客观期限约束",
            "trigger_fact": f"存在明确法定或商业截止期限：{deadline}。",
            "possible_impact": "任何反思或传统忌讳切勿导致错过报名、退款或法定时效！不可因冷静期强行拖延。",
            "safer_alternative": "先提交可修改的草案或可全额退款的申请，锁定资格后再行细化调整。",
            "how_to_adjust": "在规定时限前完成必要操作，系统不强制锁定。"
        })
        boundaries.append("现实法律时效、考试与退款截止日绝对优先于任何择日或反思流程。")

    # 4. 医疗健康与生理迷信纠偏
    health_keywords = ["同房", "射精", "破功", "还精", "绝育", "禁食", "辟谷", "断药", "就医", "生病"]
    is_health_related = any(k in topic for k in health_keywords) or has_medical_conflict
    if is_health_related:
        alerts.append({
            "id": "RISK_HEALTH_BOUNDARIES",
            "level": "warning",
            "title": "生理与医疗健康科学界限",
            "trigger_fact": "咨询事项涉及身体健康、用药、生理机能或传统养生戒慎。",
            "possible_impact": "迷信传统'固精破功'或根据黄历择日停药就诊，会导致泌尿器质性损伤或延误疾病黄金治疗期。",
            "safer_alternative": "急症慢病请立即前往正规三甲医院就诊并遵医嘱；正常性冲动与遗精属于自然生理代谢，绝非'破功'，切勿练习任何憋气忍精之法。",
            "how_to_adjust": "本系统永久禁止利用卦象替代医学诊断与处方。"
        })
        boundaries.append("严禁依据传统干支或卦象推断病情，坚决反对'破功'恐吓与极端伪养生。")

    # 5. 反复占问纠偏
    if divination_count >= 3:
        alerts.append({
            "id": "RISK_REPEATED_DIVINATION",
            "level": "info",
            "title": "反复占问警惕 (初筮告，再三渎)",
            "trigger_fact": f"今日对同类事项已连续起卦 {divination_count} 次。",
            "possible_impact": "试图通过反复刷新直到抽到'大吉'，属于心理投射与概率游戏，不仅无法改变客观事实，反而加剧决策内耗。",
            "safer_alternative": "停止占问，转向'决定前暂停'卡，列出可控事实、沉没成本与最小可验证步骤。",
            "how_to_adjust": "可随时关闭起卦界面，进入知止模块查看历史记录与现实分析。"
        })
        boundaries.append("不提供'重抽转运'机制，不把吉凶当成现实胜率。")

    # 决定前暂停卡 (Pause Before Deciding)
    pause_card = {
        "title": "决定前暂停 · 澄心自问",
        "questions": [
            {
                "id": "q1",
                "label": "我要做什么？",
                "prompt": "用客观中立的一句话描述即将采取的具体动作，不带情绪化形容词。",
                "user_value": topic or "（未填写具体操作）"
            },
            {
                "id": "q2",
                "label": "为什么现在必须做？",
                "prompt": "区分'真正的时间窗口限制'与'当下冲动导致的急迫幻觉'。",
                "user_value": f"截止期限说明: {deadline}" if deadline else "当前并无不可逆的外界时效催促"
            },
            {
                "id": "q3",
                "label": "真实成本与期限是什么？",
                "prompt": "除直接支出外，计入时间占用、机会成本、分期利息及注意力损耗；信用额度不等于收入。",
                "user_value": f"预估直接成本: ¥{cost_estimate:.2f} (可用自有现金: ¥{budget_available:.2f})"
            },
            {
                "id": "q4",
                "label": "最坏后果是什么，我能否坦然承受？",
                "prompt": "假设本次行动完全失败、资金归零或合作破裂，我的生活底线是否受损？",
                "user_value": "如果后果涉及不可逆失业、严重负债或身体器质损伤，应立即中止。" if is_irreversible else "风险边界在可控范围，但需注意防范次生连带成本。"
            },
            {
                "id": "q5",
                "label": "能否先做小而可逆的第一步？",
                "prompt": "能否先试用原型、购买最小装、签署试行条款或先做局部备份？",
                "user_value": "建议采取可撤销的沙盒试验或最小可行步骤（MVP），保留退路。"
            }
        ],
        "pause_options": [
            {"label": "暂停15分钟深呼吸", "duration_minutes": 15},
            {"label": "稍后决定（今晚复核）", "duration_minutes": 240},
            {"label": "期限临近·按最小稳妥方案立即推进", "duration_minutes": 0}
        ]
    }

    # 判定总体风险等级 (纯现实逻辑)
    overall_level = "NORMAL"
    if any(a["level"] == "danger" for a in alerts):
        overall_level = "HIGH_RISK"
    elif any(a["level"] == "warning" for a in alerts):
        overall_level = "ATTENTION"

    return {
        "status": "success",
        "risk_level": overall_level,
        "alerts_count": len(alerts),
        "alerts": alerts,
        "pause_card": pause_card,
        "boundaries_enforced": boundaries
    }
