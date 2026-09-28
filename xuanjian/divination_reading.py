"""Small local reading rules shared by every Zhouyi entry point.
These are modern symbolic interpretations, never quotations or outcome probabilities.
"""
from datetime import datetime, timezone

FLOW_VERSION = 'simple-flow-20260927'

# A short editorial theme for the original hexagram, not an empirical predictor.
GROUPS = [
    ('艮节损', '宜收敛，守住界限', '收住过多的动作，先确定做到哪里就停。'),
    ('需蹇困否剥讼', '宜缓行，先解眼前阻碍', '不要把受阻当成需要加码的理由，先看条件是否成熟。'),
    ('升渐益泰晋大有', '可推进，以积累为主', '更适合分步落实，不把眼前顺利等同于一步到位。'),
    ('比同人家人萃咸恒', '重沟通，先看双方是否一致', '先确认关系与承诺，再决定下一步。'),
    ('革鼎震涣解复', '有调整之意，先小步试行', '适合重新安排方法，保留调整余地。'),
    ('坎履大过小过明夷旅', '宜谨慎，留出回旋余地', '先把不确定处讲清楚，避免一次押上全部。'),
    ('既济未济', '重收尾，别把过程当成结果', '检查最后的条件是否满足，完成后也要留意变化。'),
]

def make_reading(calc, topic=''):
    orig = calc['original_hexagram']; name = orig['name']
    headline, focus = '先看条件，再定进退', '从具体条件出发，选择眼下能落实的一步。'
    # Names are listed explicitly to avoid short-name substring matches (济/畜等).
    groups = [(['艮','节','损'],0), (['需','蹇','困','否','剥','讼'],1),
              (['升','渐','益','泰','晋','大有'],2), (['比','同人','家人','萃','咸','恒'],3),
              (['革','鼎','震','涣','解','复'],4), (['坎','履','大过','小过','明夷','旅'],5),
              (['既济','未济'],6)]
    for names, i in groups:
        if name in names: headline, focus = GROUPS[i][1:]; break
    basics = {
        '乾': ('可主动，留有分寸', '主动推进眼下能做的事，同时留意进取过度。'),
        '坤': ('宜顺势，做好承接', '先看已有条件，靠配合与持续投入推进，不急于争先。'),
        '兑': ('宜沟通，慎重承诺', '先把想法说清楚，避免只凭一时高兴作出承诺。'),
        '离': ('先看清，再行动', '辨明所依靠的条件，再决定下一步。'),
        '巽': ('循序进入，以沟通推进', '用温和而持续的方式推进，先让彼此理解。'),
    }
    if name in basics: headline, focus = basics[name]
    if any(w in topic for w in ('抽','祈愿','扭蛋')):
        context = '你问的是消费取舍。把总价、是否只想要本体、是否愿意为过程付费分开看；卦象不能换算成中奖率。'
        action = '先写下愿意承担的总花费，再比较固定价取得和随机抽取。'
    elif any(w in topic for w in ('皮肤','买','购买','消费','预算')):
        context = '你问的是购买取舍。把实际需要、总价和交付方式放在一起比较。'
        action = '先确认是否确实想要，再核对价格、交付内容与售后条件。'
    elif any(w in topic for w in ('工作','跳槽','职业','面试','项目','创业')):
        context = '你问的是工作或项目。把推进条件落到岗位、时间、资源与已确认的承诺上。'
        action = '先落实一个可验证的小步骤，再决定是否扩大投入。'
    elif any(w in topic for w in ('感情','恋爱','复合','关系','对方','相处')):
        context = '你问的是相处与关系。结合实际沟通理解卦意，不代替对方表达真实想法。'
        action = '先说清自己的期待，听取对方回应，再决定下一步。'
    else:
        context = '把这次卦意放回你的问题里：哪些条件已具备，哪些仍需要确认？'
        action = '把眼下最重要的一个条件写下来，先确认它。'
    moving = calc['moving_lines']
    movement = ('六爻皆静，本卦不变，以本卦卦辞和大象为主。' if not moving else
                f"第 {'、'.join(map(str,moving))} 爻动，变卦为「{calc['transformed_hexagram']['name']}」；具体动爻原文见下方。")
    return {'headline': headline, 'summary': f'「{name}」的象意：{focus}',
            'context': context, 'action': action,
            'basis': [orig['xiangzhuan'], movement],
            'label': '本地象意解读', 'rule_version': FLOW_VERSION,
            'boundary': '仅作传统文化与娱乐性解读，不表示实际事件的发生概率。'}

def enrich_calculation(calc, topic='', method=None):
    """One response contract for manual, full-coin, and guided casting."""
    calc['topic'] = str(topic or '').strip()[:1000]
    calc['cast_at'] = datetime.now(timezone.utc).isoformat()
    calc['flow_version'] = FLOW_VERSION
    if method: calc['generation_mode'] = method
    reading = make_reading(calc, calc['topic'])
    calc['reading'] = reading
    orig = calc['original_hexagram']
    calc['layered_interpretation'] = {
        'traditional_text': f"【{orig['name']}】卦辞：{orig['guaci']} 大象：{orig['xiangzhuan']}",
        'math_calculation': f"自下而上爻值 {calc['input_lines']}。{reading['basis'][1]}",
        'symbolic_insight': reading['summary'] + ' ' + reading['context'],
        'real_world_evidence': reading['action'],
        'to_verify': '以上是规则生成的象意解释；具体事实需另行确认。'
    }
    return calc
