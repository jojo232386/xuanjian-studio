#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/ziwei_engine.py - 紫微斗数排盘与宫位象数推衍引擎

依托经核验的开源 iztro (v2.6.1) 核心，由独立按需 Node 进程执行确定性星盘排布：
1. 完整排布十二宫位（命宫、兄弟、夫妻、子女、财帛、疾厄、迁移、仆役/交友、官禄/事业、田宅、福德、父母）及身宫；
2. 安置十四主星（紫微、天机、太阳、武曲、天同、廉贞、天府、太阴、贪狼、巨门、天相、天梁、七杀、破军）及其庙旺平陷状态；
3. 安置核心辅曜与煞曜（文昌、文曲、左辅、右弼、天魁、天钺、禄存、擎羊、陀罗、火星、铃星、地空、地劫等）；
4. 计算生年四化（化禄、化权、化科、化忌）、大限行运区间与选定流年；
5. 计算三方四正对宫与合宫关系；
6. 出生时辰未知时安全降级，明确提示限制，绝不臆造虚假星盘；
7. 恪守理性研读原则，明确星曜宫位为传统象征哲学模型，严禁用作宿命恐吓或医学/投资决断。
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional

from xuanjian.runtime_env import get_node_bin_path, get_worker_bundle_path

# 项目根目录与 Worker 脚本路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_BUNDLE_PATH = get_worker_bundle_path()

DISCLAIMER_TEXT = (
    "紫微斗数系中国古代将天象星宿与阴阳五行哲学相结合的人文时间符号模型。各宫星曜、四化转折与运限流转，"
    "在传统研习中主要用于修身自省、知止避险与心性观照，绝不构成个人命运定论或现实吉凶必然。"
    "现实决策应当以客观条件、合法合规、财务常识与科学验证为准，知止慎独，顺势笃行。"
)

# 核心星曜传统文化释义索引
STAR_CULTURAL_INFO: Dict[str, Dict[str, str]] = {
    "紫微": {"nature": "北斗帝王星", "element": "阴土", "keywords": "尊贵、包容、领导力、厚重", "reflection": "修己安人，慎防独断自矜"},
    "天机": {"nature": "南斗智慧星", "element": "乙木", "keywords": "机敏、思辨、运筹、变通", "reflection": "思虑宜深，慎防多思少断"},
    "太阳": {"nature": "中天至阳星", "element": "丙火", "keywords": "光明、博爱、奉献、昭彰", "reflection": "施惠天下，慎防劳碌耗神"},
    "武曲": {"nature": "北斗财帛星", "element": "辛金", "keywords": "刚毅、务实、执行力、财赋", "reflection": "刚正不阿，慎防过刚则折"},
    "天同": {"nature": "南斗福德星", "element": "壬水", "keywords": "温和、知足、修养、安乐", "reflection": "以和为贵，慎防安逸怠惰"},
    "廉贞": {"nature": "北斗次桃花星", "element": "丁火/阴木", "keywords": "清廉、秩序、洞察、专注", "reflection": "克己复礼，慎防偏执冲动"},
    "天府": {"nature": "南斗令星/库星", "element": "戊土", "keywords": "稳健、宽厚、储蓄、守成", "reflection": "海纳百川，慎防固步自封"},
    "太阴": {"nature": "中天至阴星", "element": "癸水", "keywords": "细腻、内敛、慈爱、潜藏", "reflection": "温润如玉，慎防多愁善感"},
    "贪狼": {"nature": "北斗正桃花星", "element": "甲木/癸水", "keywords": "多才多艺、进取、探索、社交", "reflection": "求知好新，慎防贪多嚼不烂"},
    "巨门": {"nature": "北斗暗曜星", "element": "癸水", "keywords": "明辨是非、口才、深究、洞微", "reflection": "深思谨言，慎防言语生隙"},
    "天相": {"nature": "南斗印星", "element": "壬水", "keywords": "诚信、佐助、公正、调和", "reflection": "辅政尽职，慎防随波逐流"},
    "天梁": {"nature": "南斗荫星/老人星", "element": "戊土", "keywords": "庇佑、原则、解厄、清高", "reflection": "尊贤乐善，慎防自视清高"},
    "七杀": {"nature": "南斗将星", "element": "庚金/丁火", "keywords": "果决、开创、勇猛、坚毅", "reflection": "临危不乱，慎防急躁冒进"},
    "破军": {"nature": "北斗耗星", "element": "癸水", "keywords": "破旧立新、求变、冒险、重塑", "reflection": "革故鼎新，慎防轻率毁弃"}
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
        raise TimeoutError("紫微斗数排盘计算超时 (5秒)")
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

def calculate_ziwei(
    year: int,
    month: int,
    day: int,
    hour: Optional[int] = None,
    calendar_type: str = "solar",
    gender: str = "男",
    is_leap_month: bool = False,
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    紫微斗数排盘核心接口

    :param year: 公历或农历年份 (如 1990)
    :param month: 月份 (1-12)
    :param day: 日期 (1-31)
    :param hour: 出生小时 (0-23)，若为 None 则触发安全降级
    :param calendar_type: 'solar' (公历) 或 'lunar' (农历)
    :param gender: '男' 或 '女'
    :param is_leap_month: 是否为农历闰月
    :param target_date: 流年大限考查日期 (如 '2026-09-26')
    :return: 包含星盘、宫位、三方四正、四化及知止释义的字典
    """
    # 参数预处理与防御性检验
    if year < 1900 or year > 2100:
        raise ValueError("年份仅支持 1900 至 2100 年范围")
    if month < 1 or month > 12:
        raise ValueError("月份必须在 1 至 12 之间")
    if day < 1 or day > 31:
        raise ValueError("日期必须在 1 至 31 之间")
    if calendar_type not in ("solar", "lunar"):
        calendar_type = "solar"
    if gender not in ("男", "女"):
        gender = "男"

    # 时辰未知降级
    if hour is None:
        return {
            "success": True,
            "degraded": True,
            "message": "出生时辰未知，紫微斗数无法安立命宫与分布十四主星。系统保留已知年月日信息，绝不随意揣测时辰。",
            "input": {
                "calendar_type": calendar_type,
                "year": year,
                "month": month,
                "day": day,
                "hour": None,
                "gender": gender
            },
            "engine_version": "iztro 2.6.1",
            "disclaimer": DISCLAIMER_TEXT
        }

    if hour < 0 or hour > 23:
        raise ValueError("出生小时必须在 0 至 23 之间")

    worker_params = {
        "calendarType": calendar_type,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "gender": gender,
        "isLeapMonth": is_leap_month,
        "targetDate": target_date
    }

    result = _run_worker("calculate_ziwei", worker_params)
    result["disclaimer"] = DISCLAIMER_TEXT
    result["star_cultural_info"] = STAR_CULTURAL_INFO

    return result
