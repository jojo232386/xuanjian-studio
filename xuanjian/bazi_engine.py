#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/bazi_engine.py - 八字排盘与干支四柱象数计算引擎 (F04)

依托 lunar-python 库的精确节气算法进行干支推算：
1. 严格以“节气”（立春换年、节气换月）划分干支年与干支月，杜绝正月初一误换年的错漏；
2. 完整输出四柱（年、月、日、时）天干、地支、纳音五行、主星十神、地支藏干及副星十神、旬空；
3. 支持时辰未知时安全降级为三柱六字，杜绝脑内补全或胡编时柱；
4. 计算大运起运时间、起运年龄及十年大运流向（顺行/逆行）；
5. 统计五行分布与日主属性；
6. 严格恪守理性与知止原则，输出客观防线说明，明确干支为传统时间符号模型。
"""

from typing import Dict, Any, List, Optional
from lunar_python import Solar, Lunar
from lunar_python.util import LunarUtil

# 天干五行与阴阳属性
GAN_INFO = {
    "甲": {"wuxing": "木", "yinyang": "阳", "desc": "阳木，如参天巨木，主条达舒畅"},
    "乙": {"wuxing": "木", "yinyang": "阴", "desc": "阴木，如花草灌木，主柔顺随和"},
    "丙": {"wuxing": "火", "yinyang": "阳", "desc": "阳火，如普照烈阳，主热情进取"},
    "丁": {"wuxing": "火", "yinyang": "阴", "desc": "阴火，如烛火星芒，主内敛洞烛"},
    "戊": {"wuxing": "土", "yinyang": "阳", "desc": "阳土，如城墙厚土，主敦厚稳健"},
    "己": {"wuxing": "土", "yinyang": "阴", "desc": "阴土，如田园沃土，主包容含蓄"},
    "庚": {"wuxing": "金", "yinyang": "阳", "desc": "阳金，如刀剑刚金，主刚毅果决"},
    "辛": {"wuxing": "金", "yinyang": "阴", "desc": "阴金，如珠玉精金，主细腻温润"},
    "壬": {"wuxing": "水", "yinyang": "阳", "desc": "阳水，如江河汪洋，主通达智谋"},
    "癸": {"wuxing": "水", "yinyang": "阴", "desc": "阴水，如雨露泉水，主静谧润物"}
}

# 地支本气五行与阴阳属性
ZHI_INFO = {
    "子": {"wuxing": "水", "yinyang": "阳", "zodiac": "鼠"},
    "丑": {"wuxing": "土", "yinyang": "阴", "zodiac": "牛"},
    "寅": {"wuxing": "木", "yinyang": "阳", "zodiac": "虎"},
    "卯": {"wuxing": "木", "yinyang": "阴", "zodiac": "兔"},
    "辰": {"wuxing": "土", "yinyang": "阳", "zodiac": "龙"},
    "巳": {"wuxing": "火", "yinyang": "阴", "zodiac": "蛇"},
    "午": {"wuxing": "火", "yinyang": "阳", "zodiac": "马"},
    "未": {"wuxing": "土", "yinyang": "阴", "zodiac": "羊"},
    "申": {"wuxing": "金", "yinyang": "阳", "zodiac": "猴"},
    "酉": {"wuxing": "金", "yinyang": "阴", "zodiac": "鸡"},
    "戌": {"wuxing": "土", "yinyang": "阳", "zodiac": "狗"},
    "亥": {"wuxing": "水", "yinyang": "阴", "zodiac": "猪"}
}

DISCLAIMER_TEXT = (
    "八字排盘系基于中国传统干支纪年法构建的时间符号模型。各柱干支、五行生克与十神象征，"
    "在传统哲学中主要用于象数推演与修身自省，绝不构成个人宿命论或现实成就的必然结论。"
    "现实生活中的决策应当以真实条件、客观数据与自身长期努力为基石，知止慎独，顺应时势。"
)

def _get_shishen_for_gan(day_gan: str, target_gan: str) -> str:
    """计算十神"""
    return LunarUtil.SHI_SHEN.get(day_gan + target_gan, "比肩")

def _get_hidden_stems(day_gan: str, zhi: str) -> List[Dict[str, str]]:
    """获取地支藏干及其十神"""
    hidden = LunarUtil.ZHI_HIDE_GAN.get(zhi, [])
    res = []
    for g in hidden:
        shishen = _get_shishen_for_gan(day_gan, g)
        wx = GAN_INFO.get(g, {}).get("wuxing", "")
        res.append({
            "gan": g,
            "wuxing": wx,
            "ten_god": shishen
        })
    return res

def calculate_bazi(
    year: int,
    month: int,
    day: int,
    hour: Optional[int] = None,
    minute: Optional[int] = 0,
    gender: str = "乾造",
    is_lunar: bool = False,
    is_leap_month: bool = False,
    zi_hour_sect: int = 2
) -> Dict[str, Any]:
    """
    八字排盘主计算入口
    :param year: 年份 (公历 1900-2100 或对应农历年)
    :param month: 月份 (1-12)
    :param day: 日期 (1-31)
    :param hour: 时辰 (0-23，None 表示未知)
    :param minute: 分钟 (0-59)
    :param gender: 性别，"乾造" / "男" 为男，"坤造" / "女" 为女，其余默认为乾造
    :param is_lunar: 输入是否为农历日期
    :param is_leap_month: 若为农历，是否为闰月
    :param zi_hour_sect: 子时跨日口径：1 为“以 23:00 换日柱”（子初换日），2 为“以 00:00 换日柱”（早晚子时分立，默认 2）
    :return: 结构化排盘数据字典
    """
    if year < 1900 or year > 2100:
        raise ValueError(f"年份超出支持范围 (1900-2100): {year}")
    if month < 1 or month > 12:
        raise ValueError(f"月份无效: {month}")
    if day < 1 or day > 31:
        raise ValueError(f"日期无效: {day}")

    # 子时跨日口径处理
    sect = 2
    if isinstance(zi_hour_sect, str):
        sect = 1 if ("23" in zi_hour_sect or "sect1" in zi_hour_sect.lower()) else 2
    elif isinstance(zi_hour_sect, (int, float)):
        sect = 1 if int(zi_hour_sect) == 1 else 2

    has_hour = hour is not None
    calc_hour = hour if has_hour else 12  # 若未知，大运推算取正午12点折中
    calc_minute = minute if (has_hour and minute is not None) else 0

    if is_lunar:
        lunar_m = -month if is_leap_month else month
        lunar = Lunar.fromYmdHms(year, lunar_m, day, calc_hour, calc_minute, 0)
        solar = lunar.getSolar()
    else:
        solar = Solar.fromYmdHms(year, month, day, calc_hour, calc_minute, 0)
        lunar = solar.getLunar()

    eight_char = lunar.getEightChar()
    eight_char.setSect(sect)

    # 性别转换：1=男(乾造), 0=女(坤造)
    is_male = 0 if (gender in ("坤造", "女", "female", "F")) else 1
    gender_label = "坤造" if is_male == 0 else "乾造"

    # 日主
    day_gan = eight_char.getDayGan()
    day_master_info = GAN_INFO.get(day_gan, {"wuxing": "未知", "yinyang": "", "desc": ""})

    # 1. 年柱
    year_gan = eight_char.getYearGan()
    year_zhi = eight_char.getYearZhi()
    year_pillar = {
        "pillar_name": "年柱",
        "gan": year_gan,
        "zhi": year_zhi,
        "gan_zhi": eight_char.getYear(),
        "wuxing": eight_char.getYearWuXing(),
        "nayin": eight_char.getYearNaYin(),
        "ten_god": eight_char.getYearShiShenGan(),
        "hidden_stems": _get_hidden_stems(day_gan, year_zhi),
        "xun_kong": eight_char.getYearXunKong()
    }

    # 2. 月柱
    month_gan = eight_char.getMonthGan()
    month_zhi = eight_char.getMonthZhi()
    month_pillar = {
        "pillar_name": "月柱",
        "gan": month_gan,
        "zhi": month_zhi,
        "gan_zhi": eight_char.getMonth(),
        "wuxing": eight_char.getMonthWuXing(),
        "nayin": eight_char.getMonthNaYin(),
        "ten_god": eight_char.getMonthShiShenGan(),
        "hidden_stems": _get_hidden_stems(day_gan, month_zhi),
        "xun_kong": eight_char.getMonthXunKong()
    }

    # 3. 日柱
    day_zhi = eight_char.getDayZhi()
    day_pillar = {
        "pillar_name": "日柱",
        "gan": day_gan,
        "zhi": day_zhi,
        "gan_zhi": eight_char.getDay(),
        "wuxing": eight_char.getDayWuXing(),
        "nayin": eight_char.getDayNaYin(),
        "ten_god": "日主",
        "hidden_stems": _get_hidden_stems(day_gan, day_zhi),
        "xun_kong": eight_char.getDayXunKong()
    }

    # 4. 时柱 (若未知则安全降级)
    if has_hour:
        time_gan = eight_char.getTimeGan()
        time_zhi = eight_char.getTimeZhi()
        hour_pillar = {
            "pillar_name": "时柱",
            "gan": time_gan,
            "zhi": time_zhi,
            "gan_zhi": eight_char.getTime(),
            "wuxing": eight_char.getTimeWuXing(),
            "nayin": eight_char.getTimeNaYin(),
            "ten_god": eight_char.getTimeShiShenGan(),
            "hidden_stems": _get_hidden_stems(day_gan, time_zhi),
            "xun_kong": eight_char.getTimeXunKong()
        }
    else:
        hour_pillar = {
            "pillar_name": "时柱",
            "gan": "未知",
            "zhi": "未知",
            "gan_zhi": "未知",
            "wuxing": "未知",
            "nayin": "未知",
            "ten_god": "未知",
            "hidden_stems": [],
            "xun_kong": "未知"
        }

    # 5. 五行统计
    active_pillars = [year_pillar, month_pillar, day_pillar]
    if has_hour:
        active_pillars.append(hour_pillar)

    wuxing_counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    total_chars = 0

    # 统计天干与地支本气五行
    for p in active_pillars:
        g = p["gan"]
        z = p["zhi"]
        if g in GAN_INFO:
            wuxing_counts[GAN_INFO[g]["wuxing"]] += 1
            total_chars += 1
        if z in ZHI_INFO:
            wuxing_counts[ZHI_INFO[z]["wuxing"]] += 1
            total_chars += 1

    wuxing_percentages = {}
    if total_chars > 0:
        for wx, cnt in wuxing_counts.items():
            wuxing_percentages[wx] = round((cnt / total_chars) * 100, 1)

    # 6. 大运序列计算
    yun = eight_char.getYun(is_male)
    dayun_raw = yun.getDaYun()
    dayun_list = []

    # getDaYun() 索引 0 为起运前童限，实际大运从 index 1 开始
    for dy in dayun_raw[1:10]:
        gz = dy.getGanZhi()
        if not gz:
            continue
        g = gz[0]
        z = gz[1]
        dy_ten_god = _get_shishen_for_gan(day_gan, g)
        dy_nayin = LunarUtil.NAYIN.get(gz, "")
        dy_hidden = _get_hidden_stems(day_gan, z)
        dayun_list.append({
            "index": dy.getIndex(),
            "gan_zhi": gz,
            "gan": g,
            "zhi": z,
            "ten_god": dy_ten_god,
            "nayin": dy_nayin,
            "hidden_stems": dy_hidden,
            "start_age": dy.getStartAge(),
            "end_age": dy.getEndAge(),
            "start_year": dy.getStartYear(),
            "end_year": dy.getEndYear()
        })

    start_solar = yun.getStartSolar()
    dayun_meta = {
        "is_forward": yun.isForward(),
        "direction_text": "顺行" if yun.isForward() else "逆行",
        "start_year_offset": yun.getStartYear(),
        "start_month_offset": yun.getStartMonth(),
        "start_day_offset": yun.getStartDay(),
        "start_solar_date": start_solar.toYmd(),
        "approx_note": (
            "出生时辰未知，起运公历与岁数系基于当日正午推算之近似参考，可能存在数月浮动。"
            if not has_hour else "起运时间系由最近节气严格推算精确所得。"
        )
    }

    # 7. 格式化公历与农历文本
    solar_fmt = f"{solar.getYear()}年{solar.getMonth():02d}月{solar.getDay():02d}日"
    if has_hour:
        solar_fmt += f" {hour:02d}:{minute:02d}"
    else:
        solar_fmt += " (时辰未知)"

    lunar_fmt = f"{lunar.getYearInGanZhi()}年 农历{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"
    if has_hour:
        lunar_fmt += f" {eight_char.getTimeZhi()}时"
    else:
        lunar_fmt += " (时辰未知)"

    wuxing_dist = {
        "total_chars_analyzed": total_chars,
        "counts": wuxing_counts,
        "percentages": wuxing_percentages,
        "strongest": [k for k, v in wuxing_counts.items() if v == max(wuxing_counts.values())],
        "missing": [k for k, v in wuxing_counts.items() if v == 0],
        "note": "五行统计仅为四柱干支字面数量分布统计，不代表强弱或缺补之命理结论，切忌迷信附会。"
    }

    return {
        "solar_date": solar_fmt,
        "lunar_date": lunar_fmt,
        "gender": gender_label,
        "is_lunar_input": is_lunar,
        "is_leap_month": is_leap_month,
        "degraded_to_three_pillars": not has_hour,
        "time_boundary_notes": {
            "zi_hour_sect": sect,
            "zi_hour_mode": "以 00:00 换日柱（早晚子时分立，23:00-24:00 日柱属当天）" if sect == 2 else "以 23:00 换日柱（子初换日，23:00 起日柱即转入次日）",
            "solar_time_system": "北京时间 (UTC+8) 平太阳时",
            "timezone_and_dst_notice": "本排盘基于北京时间平太阳时计算。如遇历史夏令时年份（如 1986-1991 年夏令时）或出生地远离东经 120 度产生的经度时差及真太阳时差（通常在数分钟至数十分钟），需由研究者自行比对校准当地真太阳时。"
        },
        "day_master": {
            "gan": day_gan,
            "wuxing": day_master_info["wuxing"],
            "yinyang": day_master_info["yinyang"],
            "description": f"{day_gan}{day_master_info['wuxing']} ({day_master_info['desc']})"
        },
        "four_pillars": {
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "hour": hour_pillar
        },
        "wuxing_distribution": wuxing_dist,
        "wuxing_analysis": wuxing_dist,  # 兼容旧代码引用
        "dayun": {
            "metadata": dayun_meta,
            "sequence": dayun_list
        },
        "disclaimer": DISCLAIMER_TEXT
    }
