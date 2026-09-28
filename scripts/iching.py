#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/iching.py - 六爻象数计算核心模块 (Pure Python Standard Library)

遵循宋式易学与文王六十四卦体系，严格自下而上（初爻至上爻）排卦。
提供确定性计算：本卦、动爻、变卦（之卦）、互卦（交互卦）。
无任何外部依赖，确保跨环境与长期维护稳定。
"""

import sys
import json
import random
from scripts.yaoci_data import YAOCI, SOURCE_URL, TEXT_STATUS
from typing import List, Dict, Any, Tuple, Optional

# 八卦定义 (三爻自下而上: 0=阴, 1=阳)
# 乾(1,1,1), 兑(1,1,0), 离(1,0,1), 震(1,0,0), 巽(0,1,1), 坎(0,1,0), 艮(0,0,1), 坤(0,0,0)
TRIGRAMS = {
    (1, 1, 1): {"name": "乾", "nature": "天", "symbol": "☰", "attr": "健"},
    (1, 1, 0): {"name": "兑", "nature": "泽", "symbol": "☱", "attr": "悦"},
    (1, 0, 1): {"name": "离", "nature": "火", "symbol": "☲", "attr": "丽"},
    (1, 0, 0): {"name": "震", "nature": "雷", "symbol": "☳", "attr": "动"},
    (0, 1, 1): {"name": "巽", "nature": "风", "symbol": "☴", "attr": "入"},
    (0, 1, 0): {"name": "坎", "nature": "水", "symbol": "☵", "attr": "陷"},
    (0, 0, 1): {"name": "艮", "nature": "山", "symbol": "☶", "attr": "止"},
    (0, 0, 0): {"name": "坤", "nature": "地", "symbol": "☷", "attr": "顺"},
}

# 六十四卦对照表 (Upper, Lower) -> (King Wen Number, Short Name, Full Name, Guaci, Xiangzhuan, Tuanzhuan)
HEXAGRAM_TABLE = {
    ("乾", "乾"): (1, "乾", "乾为天", "元亨利贞。", "天行健，君子以自强不息。", "大哉乾元，万物资始，乃统天。"),
    ("坤", "坤"): (2, "坤", "坤为地", "元亨，利牝马之贞。君子有攸往，先迷后得主，利西南得朋，东北丧朋。安贞，吉。", "地势坤，君子以厚德载物。", "至哉坤元，万物资生，乃顺承天。"),
    ("坎", "震"): (3, "屯", "水雷屯", "元亨利贞。勿用有攸往，利建侯。", "云雷，屯；君子以经纶。", "屯，刚柔始交而难生。动乎险中，大亨贞。"),
    ("艮", "坎"): (4, "蒙", "山水蒙", "亨。匪我求童蒙，童蒙求我。初筮告，再三渎，渎则不告。利贞。", "山下出泉，蒙；君子以果行育德。", "蒙，山下有险，险而止，蒙。"),
    ("坎", "乾"): (5, "需", "水天需", "有孚，光亨，贞吉。利涉大川。", "云上于天，需；君子以饮食宴乐。", "需，须也；险在前也。刚健而不陷，其义不困穷矣。"),
    ("乾", "坎"): (6, "讼", "天水讼", "有孚，窒惕，中吉，终凶。利见大人，不利涉大川。", "天与水违行，讼；君子以作事谋始。", "讼，上刚下险，险而健，讼。"),
    ("坤", "坎"): (7, "师", "地水师", "贞，丈人，吉无咎。", "地中有水，师；君子以容民畜众。", "师，众也；贞，正也。能以众正，可以王矣。"),
    ("坎", "坤"): (8, "比", "水地比", "吉。原筮，元永贞，无咎。不宁方来，后夫凶。", "地上有水，比；先王以建万国，亲诸侯。", "比，吉也；比，辅也，下顺从也。"),
    ("巽", "乾"): (9, "小畜", "风天小畜", "亨。密云不雨，自我西郊。", "风行天上，小畜；君子以懿文德。", "小畜，柔得位而上下应之，曰小畜。"),
    ("乾", "兑"): (10, "履", "天泽履", "履虎尾，不咥人，亨。", "上天下泽，履；君子以辩上下，定民志。", "履，柔履刚也。说而应乎乾，是以履虎尾，不咥人，亨。"),
    ("坤", "乾"): (11, "泰", "地天泰", "小往大来，吉亨。", "天地交，泰；后以财成天地之道，辅相天地之宜，以左右民。", "泰，小往大来，吉亨。则是天地交而万物通也。"),
    ("乾", "坤"): (12, "否", "天地否", "否之匪人，不利君子贞，大往小来。", "天地不交，否；君子以俭德辟难，不可荣以禄。", "否之匪人，不利君子贞，大往小来。则是天地不交而万物不通也。"),
    ("乾", "离"): (13, "同人", "天火同人", "同人于野，亨。利涉大川，利君子贞。", "天与火，同人；君子以类族辨物。", "同人，柔得位得中而应乎乾，曰同人。"),
    ("离", "乾"): (14, "大有", "火天大有", "元亨。", "火在天上，大有；君子以遏恶扬善，顺天休命。", "大有，柔得尊位大中，而上下应之，曰大有。"),
    ("坤", "艮"): (15, "谦", "地山谦", "亨，君子有终。", "地中有山，谦；君子以裒多益寡，称物平施。", "谦，亨，天道下济而光明，地道卑而上行。"),
    ("震", "坤"): (16, "豫", "雷地豫", "利建侯行师。", "雷出地奋，豫；先王以作乐崇德，殷荐之上帝，以配祖考。", "豫，刚应而志行，顺以动，豫。"),
    ("兑", "震"): (17, "随", "泽雷随", "元亨利贞，无咎。", "泽中有雷，随；君子以向晦入宴息。", "随，刚来而下柔，动而说，随。"),
    ("艮", "巽"): (18, "蛊", "山风蛊", "元亨，利涉大川。先甲三日，后甲三日。", "山下有风，蛊；君子以振民育德。", "蛊，刚上而柔下，巽而止，蛊。"),
    ("坤", "兑"): (19, "临", "地泽临", "元亨利贞。至于八月有凶。", "泽上有地，临；君子以教思无穷，容保民无疆。", "临，刚浸而长。说而顺，刚中而应。"),
    ("巽", "坤"): (20, "观", "风地观", "盥而不荐，有孚颙若。", "风行地上，观；先王以省方，观民设教。", "大观在上，顺而巽，中正以观天下。"),
    ("离", "震"): (21, "噬嗑", "火雷噬嗑", "亨。利用狱。", "雷电，噬嗑；先王以明罚敕法。", "颐中有物，曰噬嗑。噬嗑而亨，刚柔分，动而明，雷电合而章。"),
    ("艮", "离"): (22, "贲", "山火贲", "亨。小利有攸往。", "山下有火，贲；君子以明庶政，无敢折狱。", "贲，亨。柔来而文刚，故亨；分刚上而文柔，故小利有攸往。"),
    ("艮", "坤"): (23, "剥", "山地剥", "不利有攸往。", "山附地上，剥；上以厚下，安宅。", "剥，剥也，柔变刚也。不利有攸往，小人长也。"),
    ("坤", "震"): (24, "复", "地雷复", "亨。出入无疾，朋来无咎。反复其道，七日来复，利有攸往。", "雷在地中，复；先王以至日闭关，商旅不行，后不省方。", "复亨，刚反，动而以顺行。"),
    ("乾", "震"): (25, "无妄", "天雷无妄", "元亨利贞。其匪正有眚，不利有攸往。", "天下雷行，物与无妄；先王以茂对时，育万物。", "无妄，刚自外来而为主于内。动而健，刚中而应，大亨以正，天之命也。"),
    ("艮", "乾"): (26, "大畜", "山天大畜", "利贞。不家食，吉。利涉大川。", "天在山中，大畜；君子以多识前言往行，以畜其德。", "大畜，刚健笃实辉光，日新其德，刚上而尚贤。"),
    ("艮", "震"): (27, "颐", "山雷颐", "贞吉。观颐，自求口实。", "山下有雷，颐；君子以慎言语，节饮食。", "颐贞吉，养正则吉也。观颐，观其所养也。"),
    ("兑", "巽"): (28, "大过", "泽风大过", "栋桡。利有攸往，亨。", "泽灭木，大过；君子以独立不惧，遁世无闷。", "大过，大者过也。栋桡，本末弱也。刚过而中，巽而说行，利有攸往，乃亨。"),
    ("坎", "坎"): (29, "坎", "坎为水", "习坎，有孚，维心亨，行有尚。", "水洊至，习坎；君子以常德行，习教事。", "习坎，重险也。水流而不盈，行险而不失其信。"),
    ("离", "离"): (30, "离", "离为火", "利贞，亨。畜牝牛，吉。", "明两作，离；大人以继明照于四方。", "离，丽也；日月丽乎天，百谷草木丽乎土，重明以丽乎正，乃化成天下。"),
    ("兑", "艮"): (31, "咸", "泽山咸", "亨，利贞。取女吉。", "山上有泽，咸；君子以虚受人。", "咸，感也。柔上而刚下，二气感应以相与。"),
    ("震", "巽"): (32, "恒", "雷风恒", "亨，无咎，利贞。利有攸往。", "雷风，恒；君子以立不易方。", "恒，久也。刚上而柔下，雷风相与，巽而动，刚柔皆应，恒。"),
    ("乾", "艮"): (33, "遁", "天山遁", "亨，小利贞。", "天下有山，遁；君子以远小人，不恶而严。", "遁亨，遁而亨也。刚当位而应，与时行也。"),
    ("震", "乾"): (34, "大壮", "雷天大壮", "利贞。", "雷在天上，大壮；君子以非礼弗履。", "大壮，大者壮也。刚以动，故壮。"),
    ("离", "坤"): (35, "晋", "火地晋", "康侯用锡马蕃庶，昼日三接。", "明出地上，晋；君子以自昭明德。", "晋，进也。明出地上，顺而丽乎大明，柔进而上行。"),
    ("坤", "离"): (36, "明夷", "地火明夷", "利艰贞。", "明入地中，明夷；君子以莅众，用晦而明。", "明入地中，明夷。内文明而外柔顺，以蒙大难，文王以之。"),
    ("巽", "离"): (37, "家人", "风火家人", "利女贞。", "风自火出，家人；君子以言有物而行有恒。", "家人，女正位乎内，男正位乎外，男女正，天地之大义也。"),
    ("离", "兑"): (38, "睽", "火泽睽", "小事吉。", "上火下泽，睽；君子以同而异。", "睽，火动而上，泽动而下；二女同居，其志不同行。"),
    ("坎", "艮"): (39, "蹇", "水山蹇", "利西南，不利东北；利见大人，贞吉。", "山上有水，蹇；君子以反身修德。", "蹇，难也，险在前也。见险而能止，知矣哉。"),
    ("震", "坎"): (40, "解", "雷水解", "利西南。无所往，其来复吉。有攸往，夙吉。", "雷雨作，解；君子以赦过宥罪。", "解，险以动，动而免乎险，解。"),
    ("艮", "兑"): (41, "损", "山泽损", "有孚，元吉，无咎，可贞，利有攸往。曷之用，二簋可用享。", "山下有泽，损；君子以惩忿窒欲。", "损，损下益上，其道上行。"),
    ("巽", "震"): (42, "益", "风雷益", "利有攸往，利涉大川。", "风雷，益；君子以见善则迁，有过则改。", "益，损上益下，民说无疆，自上下下，其道大光。"),
    ("兑", "乾"): (43, "夬", "泽天夬", "扬于王庭，孚号有厉，告自邑，不利即戎，利有攸往。", "泽上于天，夬；君子以施禄及下，居德则忌。", "夬，决也，刚决柔也。健而说，决而和。"),
    ("乾", "巽"): (44, "姤", "天风姤", "女壮，勿用取女。", "天下有风，姤；后以施命诰四方。", "姤，遇也，柔遇刚也。勿用取女，不可与长也。"),
    ("兑", "坤"): (45, "萃", "泽地萃", "亨。王假有庙，利见大人，亨，利贞。用大牲吉，利有攸往。", "泽上于地，萃；君子以除戎器，戒不虞。", "萃，聚也。顺以说，刚中而应，故聚也。"),
    ("坤", "巽"): (46, "升", "地风升", "元亨，用见大人，勿恤，南征吉。", "地中生木，升；君子以顺德，积小以高大。", "柔以时升，巽而顺，刚中而应，是以大亨。"),
    ("兑", "坎"): (47, "困", "泽水困", "亨，贞，大人吉，无咎，有言不信。", "泽无水，困；君子以致命遂志。", "困，刚掩也。险以说，困而不失其所亨，其唯君子乎。"),
    ("坎", "巽"): (48, "井", "水风井", "改邑不改井，无丧无得，往来井井。汔至，亦未繘井，羸其瓶，凶。", "木上有水，井；君子以劳民劝相。", "巽乎水而上水，井；井养而不穷也。"),
    ("兑", "离"): (49, "革", "泽火革", "巳日乃孚，元亨利贞，悔亡。", "泽中有火，革；君子以治历明时。", "革，水火相息，二女同居，其志不相得，曰革。"),
    ("离", "巽"): (50, "鼎", "火风鼎", "元吉，亨。", "木上有火，鼎；君子以正位凝命。", "鼎，象也。以木巽火，亨饪也。圣人亨以享上帝，而大亨以养圣贤。"),
    ("震", "震"): (51, "震", "震为雷", "亨。震来虩虩，笑言哑哑。震惊百里，不丧匕鬯。", "洊雷，震；君子以恐惧修省。", "震，亨。震来虩虩，恐致福也。笑言哑哑，后有则也。震惊百里，惊远而惧迩也。"),
    ("艮", "艮"): (52, "艮", "艮为山", "艮其背，不获其身，行其庭，不见其人，无咎。", "兼山，艮；君子以思不出其位。", "艮，止也。时止则止，时行则行，动静不失其时，其道光明。"),
    ("巽", "艮"): (53, "渐", "风山渐", "女归吉，利贞。", "山上有木，渐；君子以居贤德，善俗。", "渐之进也，女归吉也。进得位，往有功也。进以正，可以正邦也。"),
    ("震", "兑"): (54, "归妹", "雷泽归妹", "征凶，无攸利。", "泽上有雷，归妹；君子以永终知敝。", "归妹，天地之大义也。天地不交，而万物不兴。归妹，人之终始也。"),
    ("震", "离"): (55, "丰", "雷火丰", "亨，王假之，勿忧，宜日中。", "雷电皆至，丰；君子以折狱致刑。", "丰，大也。明以动，故丰。王假之，尚大也。勿忧宜日中，宜照天下也。"),
    ("离", "艮"): (56, "旅", "火山旅", "小亨，旅贞吉。", "山上有火，旅；君子以明慎用刑，而不留狱。", "旅，小亨，柔得中乎外，而顺乎刚，止而丽乎明，是以小亨旅贞吉也。"),
    ("巽", "巽"): (57, "巽", "巽为风", "小亨，利攸往，利见大人。", "随风，巽；君子以申命行事。", "重巽以申命，刚巽乎中正而志行。柔皆顺乎刚，是以小亨，利有攸往，利见大人。"),
    ("兑", "兑"): (58, "兑", "兑为泽", "亨，利贞。", "丽泽，兑；君子以朋友讲习。", "兑，说也。刚中而柔外，说以利贞，是以顺乎天，而应乎人。"),
    ("巽", "坎"): (59, "涣", "风水涣", "亨。王假有庙，利涉大川，利贞。", "风行水上，涣；先王以享于上帝立庙。", "涣亨，刚来而不穷，柔得位乎外而上同。"),
    ("坎", "兑"): (60, "节", "水泽节", "亨。苦节不可贞。", "泽上有水，节；君子以制数度，议德行。", "节亨，刚柔分，而刚得中。苦节不可贞，其道穷也。"),
    ("巽", "兑"): (61, "中孚", "风泽中孚", "豚鱼吉，利涉大川，利贞。", "泽上有风，中孚；君子以议狱缓死。", "中孚，柔在内而刚得中。说而巽，孚，乃化邦也。"),
    ("震", "艮"): (62, "小过", "雷山小过", "亨，利贞，可小事，不可大事。飞鸟遗之音，不宜上，宜下，大吉。", "山上有雷，小过；君子以行过乎恭，丧过乎哀，用过乎俭。", "小过，小者过而亨也。过以利贞，与时行也。"),
    ("坎", "离"): (63, "既济", "水火既济", "亨小，利贞，初吉终乱。", "水在火上，既济；君子以思患而预防之。", "既济，亨，小者亨也。利贞，刚柔正而位当也。初吉，柔得中也。终止则乱，其道穷也。"),
    ("离", "坎"): (64, "未济", "火水未济", "亨，小狐汔济，濡其尾，无攸利。", "火在水上，未济；君子以慎辨物居方。", "未济，亨，柔得中也。小狐汔济，未出中也。濡其尾，无攸利，不续终也。虽不当位，刚柔应也。")
}

# 爻辞关键库 (支持六十四卦标准爻辞索引)
YAOCI_SPECIAL = {
    (1, 0): "用九：见群龙无首，吉。",
    (2, 0): "用六：利永贞。",
    (63, 1): "初九：曳其轮，濡其尾，无咎。",
    (63, 2): "六二：妇丧其茀，勿逐，七日得。",
    (63, 3): "九三：高宗伐鬼方，三年克之，小人勿用。",
    (63, 4): "六四：繻有衣袡，终日戒。",
    (63, 5): "九五：东邻杀牛，不如西邻之禴祭，实受其福。",
    (63, 6): "上六：濡其首，厉。",
    (22, 1): "初九：贲其趾，舍车而徒。",
    (22, 2): "六二：贲其须。",
    (22, 3): "九三：贲如濡如，永贞吉。",
    (22, 4): "六四：贲如皤如，白马翰如，匪寇婚媾。",
    (22, 5): "六五：贲于丘园，束帛戋戋，吝，终吉。",
    (22, 6): "上九：白贲，无咎。",
}

YAOCI_SPECIAL = {**YAOCI, **YAOCI_SPECIAL}

def get_yao_name(line_index: int, bit: int) -> str:
    """获取爻位名称 (line_index: 1..6 自下而上, bit: 0=阴, 1=阳)"""
    pos_names = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}
    pos = pos_names[line_index]
    nature = "九" if bit == 1 else "六"
    if line_index == 1:
        return f"初{nature}"
    elif line_index == 6:
        return f"上{nature}"
    else:
        return f"{nature}{pos}"

def get_hexagram_by_trigrams(upper_trigram: str, lower_trigram: str) -> Dict[str, Any]:
    """通过上下卦名称获取卦体数据"""
    key = (upper_trigram, lower_trigram)
    if key not in HEXAGRAM_TABLE:
        raise ValueError(f"未知卦象组合: 上卦 {upper_trigram}, 下卦 {lower_trigram}")
    num, short_name, full_name, guaci, xiang, tuan = HEXAGRAM_TABLE[key]
    return {
        "number": num,
        "name": short_name,
        "full_name": full_name,
        "upper_trigram": upper_trigram,
        "lower_trigram": lower_trigram,
        "guaci": guaci,
        "xiangzhuan": xiang,
        "tuanzhuan": tuan
    }

def calculate_hexagram(lines: List[int]) -> Dict[str, Any]:
    """
    核心象数计算函数
    :param lines: 自下而上的6个爻值 (初爻至上爻), 取值必须属于 {6, 7, 8, 9}
    :return: 包含本卦、动爻、变卦、互卦及结构化信息的字典
    """
    if len(lines) != 6:
        raise ValueError(f"爻数必须恰好为6个 (自下而上初爻至上爻)，当前传入: {len(lines)}")
    for i, val in enumerate(lines, start=1):
        if val not in (6, 7, 8, 9):
            raise ValueError(f"第 {i} 爻数值无效: {val}。爻值必须为 6 (老阴)、7 (少阳)、8 (少阴)、9 (老阳) 之一。")

    # 1. 本卦爻位 (0=阴, 1=阳)
    original_bits = [1 if val in (7, 9) else 0 for val in lines]

    # 2. 动爻 (6和9为变爻，记录爻位 1..6)
    moving_lines = [i for i, val in enumerate(lines, start=1) if val in (6, 9)]

    # 3. 变卦爻位 (老阴6变阳1，老阳9变阴0，7和8不变)
    transformed_bits = []
    for val in lines:
        if val == 6:
            transformed_bits.append(1)
        elif val == 9:
            transformed_bits.append(0)
        elif val == 7:
            transformed_bits.append(1)
        elif val == 8:
            transformed_bits.append(0)

    # 4. 下卦 (初、二、三爻) 与 上卦 (四、五、上爻)
    orig_lower_tuple = (original_bits[0], original_bits[1], original_bits[2])
    orig_upper_tuple = (original_bits[3], original_bits[4], original_bits[5])
    orig_lower = TRIGRAMS[orig_lower_tuple]["name"]
    orig_upper = TRIGRAMS[orig_upper_tuple]["name"]
    original_hex = get_hexagram_by_trigrams(orig_upper, orig_lower)

    # 5. 变卦上下卦
    trans_lower_tuple = (transformed_bits[0], transformed_bits[1], transformed_bits[2])
    trans_upper_tuple = (transformed_bits[3], transformed_bits[4], transformed_bits[5])
    trans_lower = TRIGRAMS[trans_lower_tuple]["name"]
    trans_upper = TRIGRAMS[trans_upper_tuple]["name"]
    transformed_hex = get_hexagram_by_trigrams(trans_upper, trans_lower)

    # 6. 互卦 (下互取二三四爻，上互取三四五爻)
    # original_bits 索引 1,2,3 对应二三四爻；索引 2,3,4 对应三四五爻
    nuclear_lower_tuple = (original_bits[1], original_bits[2], original_bits[3])
    nuclear_upper_tuple = (original_bits[2], original_bits[3], original_bits[4])
    nuclear_lower = TRIGRAMS[nuclear_lower_tuple]["name"]
    nuclear_upper = TRIGRAMS[nuclear_upper_tuple]["name"]
    nuclear_hex = get_hexagram_by_trigrams(nuclear_upper, nuclear_lower)

    # 7. 各爻详细信息 (自下而上)
    line_details = []
    for idx, (val, bit) in enumerate(zip(lines, original_bits), start=1):
        is_moving = val in (6, 9)
        yao_title = get_yao_name(idx, bit)
        desc = {6: "老阴 (动爻，变阳)", 7: "少阳 (静爻)", 8: "少阴 (静爻)", 9: "老阳 (动爻，变阴)"}[val]
        text = YAOCI_SPECIAL.get((original_hex["number"], idx), f"{yao_title}：此爻原文尚未收录。")
        line_details.append({
            "position": idx,
            "position_name": ["初", "二", "三", "四", "五", "上"][idx - 1],
            "value": val,
            "bit": bit,
            "nature": "阳" if bit == 1 else "阴",
            "is_moving": is_moving,
            "yao_name": yao_title,
            "description": desc,
            "yaoci": text,
            "yaoci_source": SOURCE_URL,
            "yaoci_status": TEXT_STATUS
        })

    # 特殊用九、用六
    special_statement = None
    if original_hex["number"] == 1 and all(v == 9 for v in lines):
        special_statement = YAOCI_SPECIAL.get((1, 0))
    elif original_hex["number"] == 2 and all(v == 6 for v in lines):
        special_statement = YAOCI_SPECIAL.get((2, 0))

    return {
        "input_lines": lines,
        "direction": "bottom_to_top (初爻至上爻)",
        "method": "六爻象数确定性计算 (纯标准库)",
        "original_hexagram": original_hex,
        "moving_lines": moving_lines,
        "transformed_hexagram": transformed_hex,
        "nuclear_hexagram": nuclear_hex,
        "lines": line_details,
        "special_statement": special_statement,
        "is_pure_yang": all(b == 1 for b in original_bits),
        "is_pure_yin": all(b == 0 for b in original_bits)
    }

# 概率分布元数据 (公开声明，杜绝混淆)
COINS_DISTRIBUTION = {
    "type": "three_coins",
    "description": "传统三铜钱二项分布: 6(12.5%), 7(37.5%), 8(37.5%), 9(12.5%)",
    "probabilities": {"6": 0.125, "7": 0.375, "8": 0.375, "9": 0.125}
}

UNIFORM_RANDOM_DISTRIBUTION = {
    "type": "discrete_uniform",
    "description": "纯等概率离散分布: 6(25%), 7(25%), 8(25%), 9(25%)，非传统三铜钱法分布",
    "probabilities": {"6": 0.25, "7": 0.25, "8": 0.25, "9": 0.25}
}

def cast_coins() -> Tuple[List[int], List[List[int]]]:
    """
    模拟传统三枚铜钱起卦 (正面为3，反面为2；和为6, 7, 8, 9)
    自下而上摇掷六次
    分布特征: 二项分布 (6: 12.5%, 7: 37.5%, 8: 37.5%, 9: 12.5%)
    """
    lines = []
    coin_flips = []
    for _ in range(6):
        # 3枚铜钱，每枚 2 (背/阴) 或 3 (字/阳)
        coins = [random.choice([2, 3]), random.choice([2, 3]), random.choice([2, 3])]
        val = sum(coins)
        lines.append(val)
        coin_flips.append(coins)
    return lines, coin_flips

def cast_random_uniform() -> List[int]:
    """
    纯等概率随机排爻 (独立离散均匀分布):
    每爻独立在 {6, 7, 8, 9} 中等概率抽取 (各 25% / 1/4)。
    公开声明：此模式为离散均匀分布，与传统三铜钱法的二项分布不同。
    """
    return [random.choice([6, 7, 8, 9]) for _ in range(6)]

def format_text_output(result: Dict[str, Any]) -> str:
    orig = result["original_hexagram"]
    trans = result["transformed_hexagram"]
    nuc = result["nuclear_hexagram"]
    mov = result["moving_lines"]

    mov_str = ", ".join(str(m) for m in mov) if mov else "无"

    lines = [
        f"本卦：{orig['name']} ({orig['full_name']})",
        f"动爻：{mov_str}",
        f"变卦：{trans['name']} ({trans['full_name']})",
        f"互卦：{nuc['name']} ({nuc['full_name']})",
        "",
        "【六爻自下而上】"
    ]
    for item in reversed(result["lines"]): # 显示时自上而下阅读，标明爻位
        mark = " ●" if item["is_moving"] else "  "
        symbol = "⚊ (阳)" if item["bit"] == 1 else "⚋ (阴)"
        lines.append(f"第{item['position']}爻 [{item['yao_name']}]{mark}: {symbol} 原始值={item['value']} - {item['yaoci']}")

    lines.extend([
        "",
        f"【本卦卦辞】: {orig['guaci']}",
        f"【大象传】: {orig['xiangzhuan']}",
        f"【彖传】: {orig['tuanzhuan']}"
    ])

    if result.get("distribution_info"):
        lines.append(f"【概率分布特征】: {result['distribution_info']['description']}")

    if result.get("special_statement"):
        lines.append(f"【特殊用爻】: {result['special_statement']}")

    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 scripts/iching.py lines 7 8 7 8 9 6")
        print("  python3 scripts/iching.py coins")
        print("  python3 scripts/iching.py random")
        print("  python3 scripts/iching.py lines 7 8 7 8 9 6 --json")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    is_json = "--json" in sys.argv

    try:
        if cmd == "lines":
            args = [a for a in sys.argv[2:] if a != "--json"]
            if len(args) != 6:
                print(f"错误: lines 命令需要传入正好6个爻值 (初爻至上爻)。收到: {len(args)} 个参数", file=sys.stderr)
                sys.exit(1)
            line_vals = [int(x) for x in args]
            res = calculate_hexagram(line_vals)
            res["generation_mode"] = "manual_lines"
        elif cmd == "coins":
            line_vals, flips = cast_coins()
            res = calculate_hexagram(line_vals)
            res["coin_flips"] = flips
            res["generation_mode"] = "three_coins"
            res["distribution_info"] = COINS_DISTRIBUTION
        elif cmd == "random":
            line_vals = cast_random_uniform()
            res = calculate_hexagram(line_vals)
            res["generation_mode"] = "random_uniform"
            res["distribution_info"] = UNIFORM_RANDOM_DISTRIBUTION
        else:
            print(f"未知指令: {cmd}。请使用 lines, coins 或 random。", file=sys.stderr)
            sys.exit(1)

        if is_json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(format_text_output(res))

    except Exception as e:
        print(f"计算错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
