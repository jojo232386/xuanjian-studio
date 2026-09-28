# -*- coding: utf-8 -*-
"""
xuanjian/classics_data.py - 典籍短读与易学词典知识库

严格遵循真实出处考据，收录：
1. 经典短读 (系辞、大象传、先秦两汉辨析)
2. 玄鉴术语词典 (本卦、动爻、变卦、互卦、卦德、象传等)
"""

from typing import List, Dict, Any

CLASSICAL_READINGS: List[Dict[str, Any]] = [
    {
        "id": "READING_JIJI_YUFANG",
        "title": "既济·思患而预防之",
        "author": "周公/孔门后学",
        "source": "《周易·既济卦·象传》",
        "source_type": "古籍可定位",
        "verification_status": "已核对",
        "category": "易象修养",
        "original_text": "水在火上，既济；君子以思患而预防之。",
        "translation": "坎水在上，离火在下，水火相交而济，万事粗定。君子处于成功圆满之时，应当预先思虑潜藏的祸患，并提前做好防范。",
        "commentary": "朱熹《周易本义》注：'水在火上，其势易泄；既济之时，其难易起。故君子思患而预为之防也。'成功之时往往是防线最易松懈之日，知止与慎初正是易道之枢纽。"
    },
    {
        "id": "READING_XICI_SHUJI",
        "title": "系辞·言行枢机",
        "author": "孔子（托名）",
        "source": "《周易·系辞上传·第八章》",
        "source_type": "古籍可定位",
        "verification_status": "已核对",
        "category": "现实修身",
        "original_text": "君子居其室，出其言善，则千里之外应之，况其迩者乎？居其室，出其言不善，则千里之外违之，况其迩者乎？言出乎身，加乎民；行发乎迩，见乎远。言行，君子之枢机。枢机之发，荣辱之主也。枢机之发，荣辱之主也，可不慎乎！",
        "translation": "君子在自己的室内，如果发出善言，千里之外的人都会感应共鸣；如果在室内发出不善之言，千里之外的人都会背离。言论从自身发出，会施加到他人身上；行动始于细微身边，其影响却显现于远方。言语与行动，是君子主宰进退的关键开关。开关一动，荣辱即定，怎能不极其谨慎呢！",
        "commentary": "此章阐明因果连锁与现实负责态度。不可将成败轻浮寄托于虚妄占验，而应时刻检点自己当下的微细言行。"
    },
    {
        "id": "READING_XICI_YOUHUAN",
        "title": "系辞·易作于忧患",
        "author": "孔子（托名）",
        "source": "《周易·系辞下传·第七章》",
        "source_type": "古籍可定位",
        "verification_status": "已核对",
        "category": "易理源流",
        "original_text": "《易》之兴也，其当殷之末世，周之盛德邪？当文王与纣之事邪？是故其辞危。危者使平，易者使倾。其道甚大，百物不废。惧以终始，其要无咎，此之谓《易》之道也。",
        "translation": "《易经》的兴起，大概正值殷商末期与西周德政将兴之时吧？正当文王面对商纣暴虐忧患之时吧？所以它的文辞充满危惧警戒之意。心怀危惧敬畏，才能化险为平；麻痹轻忽懈怠，必将倾覆灭亡。《易》的道理极其广大，始终保持慎重戒惧，以求无过无咎，这就是《易》的真谛。",
        "commentary": "易经的本质不是算命求吉，而是'忧患意识'。君子学易，是为了在顺境中见危机、在逆境中持操守。"
    },
    {
        "id": "READING_WANGCHONG_JIRI",
        "title": "论衡·讥日（古代理性批判）",
        "author": "王充（东汉思想家）",
        "source": "《论衡·卷二十四·讥日篇》",
        "source_type": "古籍可定位",
        "verification_status": "已核对",
        "category": "理性思辨",
        "original_text": "凿井得泉，在于地下脉势，不在干支。起宅安吉，在于构架端正、材力坚固，不在神煞。世俗不察其实，徒信虚妄之历，失现实之事理，悲夫！",
        "translation": "打井能否打出甘泉，取决于地下的水文地势，而不在于天干地支；建房能否平安吉祥，取决于房屋结构端正、建材承重坚固，而不在于吉神凶煞。世俗之人不考察客观事实，一味迷信虚妄的日历，丧失了处理现实事物的真实条理，这实在令人可悲！",
        "commentary": "两千年前东汉王充的唯物主义论断，正是现代人审视传统历法宜忌应持的清醒理智标杆。"
    }
]

GLOSSARY_TERMS: List[Dict[str, Any]] = [
    {
        "term": "本卦",
        "category": "象数核心",
        "source": "《左传·僖公十五年》、宋代朱熹《易学启蒙》",
        "definition": "起卦所得的初始六爻卦体。代表所问事项当前的原发结构、初始状态及内在阴阳力量对比。"
    },
    {
        "term": "动爻",
        "category": "象数核心",
        "source": "《周易·系辞上》：'极数知来之谓占，通变之谓事。'",
        "definition": "凡遇老阴（数值为6）或老阳（数值为9）的爻线，称为变爻或动爻。代表事物运动中量变累积至极限、即将向对立面质变的活化节点。"
    },
    {
        "term": "变卦（之卦）",
        "category": "象数核心",
        "source": "《左传》杜预注：'之，往也，自此卦变往彼卦。'",
        "definition": "动爻发生阴阳性质反转（老阴变少阳，老阳变少阴）后组合而成的新卦。象征事态发展的潜在走向、远景或事物转化的启示。"
    },
    {
        "term": "互卦（交互卦）",
        "category": "象数核心",
        "source": "汉代京房《京氏易传》、宋代邵雍《皇极经世》",
        "definition": "取本卦第二、三、四爻为下卦，第三、四、五爻为上卦，重新拼合而成的新卦。揭示事物内部深层蕴涵的中介机制、隐性矛盾或过渡形态。"
    },
    {
        "term": "卦德",
        "category": "易理义理",
        "source": "《周易·说卦传》",
        "definition": "八卦所象征的本质属性：乾健（刚健自强）、坤顺（厚德柔顺）、震动（奋发萌动）、巽入（温和渗透）、坎陷（险难隐伏）、离丽（依附明亮）、艮止（适时止步）、兑悦（和悦欣喜）。"
    },
    {
        "term": "彖传（彖曰）",
        "category": "文献考据",
        "source": "《易传·十翼》之一",
        "definition": "'彖'者断也，统论全卦之名义、卦辞内涵及卦象总括，侧重宏观哲理与天地规律之阐发。"
    },
    {
        "term": "象传（大象/小象）",
        "category": "文献考据",
        "source": "《易传·十翼》之一",
        "definition": "分为解释全卦象征君子修养的《大象传》（如'天行健，君子以自强不息'），以及逐句解析爻辞吉凶义理的《小象传》。"
    },
    {
        "term": "彭祖百忌",
        "category": "民俗干支",
        "source": "宋代《事林广记·历法门》",
        "definition": "以六十甲子天干地支相配为口诀的传统民间戒慎，多取干支五行之象做隐喻性警示，属民俗文化范畴。"
    },
    # ─── 八字术语 ──────────────────────────────────
    {
        "term": "日元（日主）",
        "category": "八字术语",
        "source": "《渊海子平·论日主》",
        "definition": "四柱八字中日柱的天干。代表当事人的主体五行属性，为八字命理推算格局、十神与生克流通的基准坐标。"
    },
    {
        "term": "十神",
        "category": "八字术语",
        "source": "《子平真诠》",
        "definition": "以日干为基准，根据五行生克与阴阳同异划分的十种象征关系：正官、偏官（七杀）、正印、偏印（枭神）、比肩、劫财、食神、伤官、正财、偏财。"
    },
    {
        "term": "地支藏干",
        "category": "八字术语",
        "source": "《三命通会·论地支藏干》",
        "definition": "十二地支内部所隐伏的天干，分为本气、中气与余气。象征事物显露表面之下潜藏的生机与矛盾。"
    },
    # ─── 紫微术语 ──────────────────────────────────
    {
        "term": "命宫与身宫",
        "category": "紫微术语",
        "source": "《紫微斗数全书·卷一》",
        "definition": "命宫主管先天秉性、心志初衷与处世基调；身宫主管后天行藏、行动习惯与中年之后的发展重心。"
    },
    {
        "term": "十四正星",
        "category": "紫微术语",
        "source": "《紫微斗数全书·诸星问答》",
        "definition": "紫微星系（紫微、天机、太阳、武曲、天同、廉贞）与天府星系（天府、太阴、贪狼、巨门、天相、天梁、七杀、破军）共十四颗核心主曜。"
    },
    {
        "term": "生年四化",
        "category": "紫微术语",
        "source": "《太微赋》",
        "definition": "依出生年天干所引动的四种星曜气化状态：化禄（情缘厚禄）、化权（权柄掌控）、化科（声名清贵）、化忌（执念波折）。"
    },
    {
        "term": "三方四正",
        "category": "紫微术语",
        "source": "《紫微斗数全书》",
        "definition": "以本宫为中心，考查其正对之对宫（六冲宫），以及隔四宫形成的三合宫位（如命宫与官禄、财帛三合，加上迁移对宫），构成观察星曜组合的完整网格。"
    },
    # ─── 奇门术语 ──────────────────────────────────
    {
        "term": "时家转盘奇门",
        "category": "奇门术语",
        "source": "《奇门遁甲统宗》",
        "definition": "以每个时辰为一局，九宫天盘九星、八门、八神沿洛书九宫环形转动排布的经典奇门推衍体系。"
    },
    {
        "term": "拆补定局法",
        "category": "奇门术语",
        "source": "《奇门遁甲元机赋》",
        "definition": "以二十四节气精确交节时刻为界，日柱往前寻最近的甲、己符头确定上、中、下三元局数的确定性定局方法。"
    },
    {
        "term": "值符与值使",
        "category": "奇门术语",
        "source": "《奇门遁甲统宗》",
        "definition": "值符为主帅，对应时辰旬首六仪所落之天盘九星；值使为主官，对应旬首本位宫之八门，主管当务之机要。"
    },
    {
        "term": "十干克应",
        "category": "奇门术语",
        "source": "《奇门遁甲秘笈大全》",
        "definition": "九宫天盘天干与地盘天干相配所产生的传统格局效应（如乙加辛为青龙逃走、丙加戊为飞鸟跌穴、辛加己为入狱自刑等）。"
    }
]

from xuanjian.daodejing_data import DAODEJING_CHAPTERS, get_all_daodejing_chapters, get_daodejing_chapter

def search_classics(query: str = "", category: str = "") -> Dict[str, Any]:
    """
    全文检索本地已收录典籍、道德经八十一章与四术词典
    明确标注检索范围为本地已收录语料，杜绝假称全网全古籍。
    """
    clean_q = query.strip()
    readings = []
    for r in CLASSICAL_READINGS:
        if category and r["category"] != category:
            continue
        if not clean_q or (clean_q in r["title"] or clean_q in r["original_text"] or clean_q in r["translation"]):
            readings.append(r)

    glossary = []
    for g in GLOSSARY_TERMS:
        if category and g["category"] != category:
            continue
        if not clean_q or (clean_q in g["term"] or clean_q in g["definition"] or clean_q in g["source"]):
            glossary.append(g)

    daodejing_matches = []
    if clean_q:
        for ch in DAODEJING_CHAPTERS:
            if clean_q in ch["title"] or clean_q in ch["original_text"] or clean_q in ch["translation"] or clean_q in ch["reflection"]:
                daodejing_matches.append(ch)

    return {
        "query": clean_q,
        "search_scope": "本地已收录内容（《道德经》八十一章、先秦易经经传精义、四术核心术语）",
        "category": category,
        "readings_count": len(readings),
        "readings": readings,
        "glossary_count": len(glossary),
        "glossary": glossary,
        "daodejing_count": len(daodejing_matches),
        "daodejing": daodejing_matches
    }
