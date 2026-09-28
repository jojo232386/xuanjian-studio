#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/qimen_engine.py - 时家转盘奇门遁甲排盘引擎

依托经核验的开源 bigfishmarquis-qimen (v1.0.0) 算法及 lunar-python 高精度节气干支：
1. 采用时家转盘奇门与拆补定局法（以节气精确交节分界，甲己符头定上中下三元）；
2. 完整排布九宫（坎一、坤二、震三、巽四、中五、乾六、兑七、艮八、离九）洛书方位；
3. 输出地盘六仪三奇、天盘三奇六仪、暗干支；
4. 排布九星（天蓬、天芮、天冲、天辅、天禽、天心、天柱、天任、天英）及天禽寄坤二宫规则；
5. 排布八门（休门、生门、伤门、杜门、景门、死门、惊门、开门）；
6. 排布八神（值符、腾蛇、太阴、六合、白虎、玄武、九地、九天）及地八神；
7. 明确计算值符星与值使门落宫、旬首、空亡与驿马；
8. 匹配十干克应传统典籍断语（青龙返首、飞鸟跌穴、玉女守门等）；
9. 恪守文化与理性防线，严禁将门星吉凶作为现实灾祸或决策通行证。
"""

import os
import sys
import json
import subprocess
import datetime
from typing import Dict, Any, List, Optional
from lunar_python import Solar, Lunar
from xuanjian.runtime_env import get_node_bin_path, get_worker_bundle_path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_BUNDLE_PATH = get_worker_bundle_path()

DISCLAIMER_TEXT = (
    "奇门遁甲系中国古代构建的兵法运筹与天时地利符号模型。局中九宫、八门、九星与八神，"
    "在传统研习中主要用于明辨时势、进退知止与思患预防，绝不构成现实人生命运的命定裁决。"
    "面对生活中的重要决策，当以现实法律、医学规律、经济常识与严谨论证为根本凭据，切忌迷信附会。"
)

# 经典八门传统人文释义与知止警示
DOOR_CULTURAL_INFO: Dict[str, Dict[str, str]] = {
    "开门": {"element": "乾金", "direction": "西北", "nature": "开创、亨通、官禄、经商", "reflection": "宜开辟进取、公开透明；慎防锋芒太露"},
    "休门": {"element": "坎水", "direction": "正北", "nature": "休整、养息、安宁、和合", "reflection": "宜蓄力静养、拜会求和；慎防消极怠慢"},
    "生门": {"element": "艮土", "direction": "东北", "nature": "生机、增益、财富、营建", "reflection": "宜务实创收、养生修德；慎防贪婪求盈"},
    "伤门": {"element": "震木", "direction": "正东", "nature": "冲决、竞争、捕猎、讨债", "reflection": "宜雷厉风行、纠正偏差；慎防斗狠好勇伤人伤己"},
    "杜门": {"element": "巽木", "direction": "东南", "nature": "防守、藏匿、保密、深潜", "reflection": "宜严守机密、固守本分；慎防闭目塞听自绝于外"},
    "景门": {"element": "离火", "direction": "正南", "nature": "昭著、文书、谋划、显耀", "reflection": "宜宣明礼乐、展现才华；慎防虚浮华而不实"},
    "死门": {"element": "坤土", "direction": "西南", "nature": "终结、固守、祭奠、收敛", "reflection": "宜止息执念、善终其事；传统忌开创，非必主现实灾殃"},
    "惊门": {"element": "兑金", "direction": "正西", "nature": "辩论、警示、词讼、震荡", "reflection": "宜居安思危、谨防欺诈；传统戒轻率，非必主现实惊祸"}
}

# 九星人文释义
STAR_CULTURAL_INFO: Dict[str, Dict[str, str]] = {
    "天蓬": {"element": "水", "original_palace": 1, "character": "大智勇略、开疆拓土", "reflection": "谋定后动，戒贪戒险"},
    "天芮": {"element": "土", "original_palace": 2, "character": "结友受业、厚德载物", "reflection": "修身求师，防疾思安"},
    "天冲": {"element": "木", "original_palace": 3, "character": "威严勇决、雷霆突破", "reflection": "勇往直前，慎防鲁莽"},
    "天辅": {"element": "木", "original_palace": 4, "character": "文教佐理、春风化雨", "reflection": "尊师崇文，修身立道"},
    "天禽": {"element": "土", "original_palace": 5, "character": "中正宽仁、统御全局", "reflection": "居中处正，允执厥中"},
    "天心": {"element": "金", "original_palace": 6, "character": "医道济世、明察秋毫", "reflection": "救难济危，慎独守正"},
    "天柱": {"element": "金", "original_palace": 7, "character": "隐忍坚毅、言辞雄辩", "reflection": "砥柱中流，戒谗防争"},
    "天任": {"element": "土", "original_palace": 8, "character": "慈祥敦厚、守信用德", "reflection": "厚德载福，戒私戒傲"},
    "天英": {"element": "火", "original_palace": 9, "character": "声华声誉、烈火鉴真", "reflection": "明德昭彰，戒躁戒虚"}
}

def _run_worker(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """通过子进程调用 Node 计算 Worker"""
    if not os.path.exists(WORKER_BUNDLE_PATH):
        raise FileNotFoundError(f"计算 Worker 脚本不存在: {WORKER_BUNDLE_PATH}")

    payload = json.dumps({"action": action, "params": params}, ensure_ascii=False)
    node_bin = get_node_bin_path()
    try:
        proc = subprocess.Popen(
            [node_bin, WORKER_BUNDLE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input=payload, timeout=5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise TimeoutError("奇门遁甲排盘计算超时 (5秒)")
    except FileNotFoundError:
        raise RuntimeError("紫微/奇门计算组件未能启动：未检测到可用的 Node 运行时。请使用官方自带独立运行时的「玄鉴·书房.app」运行。")
    except Exception as e:
        raise RuntimeError(f"紫微/奇门计算组件未能启动: {e}")

    if proc.returncode != 0:
        raise RuntimeError(f"Worker 异常退出 ({proc.returncode}): {stderr.strip()}")

    try:
        res = json.loads(stdout)
    except Exception as e:
        raise ValueError(f"Worker 返回非标准 JSON: {stdout[:200]}")

    if "error" in res:
        raise RuntimeError(res["error"])

    return res

def calculate_qimen(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    topic: str = "",
    solar_term: Optional[str] = None
) -> Dict[str, Any]:
    """
    时家转盘奇门遁甲排盘接口

    :param year: 公历年份 (1900-2100)
    :param month: 公历月份 (1-12)
    :param day: 公历日 (1-31)
    :param hour: 小时 (0-23)
    :param minute: 分钟 (0-59)
    :param topic: 求测或反思主题
    :param solar_term: 可选手动指定节气，若不提供则通过高精度历法自动提取
    :return: 包含局数、九宫、十干克应、知止释义的字典
    """
    if year < 1900 or year > 2100:
        raise ValueError("年份仅支持 1900 至 2100 年范围")
    if month < 1 or month > 12:
        raise ValueError("月份必须在 1 至 12 之间")
    if day < 1 or day > 31:
        raise ValueError("日期必须在 1 至 31 之间")
    if hour < 0 or hour > 23:
        raise ValueError("小时必须在 0 至 23 之间")
    if minute < 0 or minute > 59:
        raise ValueError("分钟必须在 0 至 59 之间")

    # 通过 lunar-python 精确计算四柱八字与节气
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()

    four_pillars = {
        "year": {"gan": eight_char.getYearGan(), "zhi": eight_char.getYearZhi()},
        "month": {"gan": eight_char.getMonthGan(), "zhi": eight_char.getMonthZhi()},
        "day": {"gan": eight_char.getDayGan(), "zhi": eight_char.getDayZhi()},
        "hour": {"gan": eight_char.getTimeGan(), "zhi": eight_char.getTimeZhi()}
    }

    if not solar_term:
        # 获取当前或最近的前一个节气
        prev_jie = lunar.getPrevJieQi(True)
        solar_term = prev_jie.getName() if prev_jie else "冬至"

    worker_params = {
        "solarTerm": solar_term,
        "fourPillars": four_pillars,
        "hourNumber": hour,
        "topic": topic
    }

    result = _run_worker("calculate_qimen", worker_params)
    result["disclaimer"] = DISCLAIMER_TEXT
    result["door_cultural_info"] = DOOR_CULTURAL_INFO
    result["star_cultural_info"] = STAR_CULTURAL_INFO
    result["input"]["solar_date"] = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"

    return result
