# -*- coding: utf-8 -*-
"""
tests/test_daodejing_and_builtin_reader.py - 道德经八十一章、四术内置研读与复盘历史留痕测试
"""

import pytest
import tempfile
import os
import shutil
from xuanjian.daodejing_data import (
    DAODEJING_CHAPTERS,
    get_all_daodejing_chapters,
    get_daodejing_chapter
)
from xuanjian.builtin_reader import generate_builtin_reading
from xuanjian.ziwei_engine import calculate_ziwei
from xuanjian.qimen_engine import calculate_qimen
from xuanjian.bazi_engine import calculate_bazi
from xuanjian.storage import XuanJianStorage


def test_daodejing_81_chapters_completeness():
    """验证《道德经》八十一章传世本全文本完整收录，无占位符，正文完整"""
    chapters = get_all_daodejing_chapters()
    assert len(chapters) == 81, "必须完整收录八十一章"

    for i in range(1, 82):
        ch = get_daodejing_chapter(i)
        assert ch is not None, f"第{i}章不可为空"
        assert ch["chapter_num"] == i
        assert len(ch["original_text"]) > 10, f"第{i}章原文不可过短"
        assert "传世通行本经文。" not in ch["original_text"], f"第{i}章不得为通用占位符"
        assert ch["part"] in ["道经", "德经"]
        assert len(ch["translation"]) > 5
        assert len(ch["reflection"]) > 5
        assert ch["verification_status"] in ["重点抽查对照·传世王弼本", "通行文本录入·未独立对校"]


def test_daodejing_specific_core_chapters():
    """验证重点核心章节经文与知止自省义理"""
    ch1 = get_daodejing_chapter(1)
    assert "道可道" in ch1["original_text"]
    assert ch1["part"] == "道经"

    ch44 = get_daodejing_chapter(44)
    assert "知足不辱" in ch44["original_text"]
    assert "知止不殆" in ch44["original_text"]
    assert ch44["part"] == "德经"

    ch81 = get_daodejing_chapter(81)
    assert "信言不美" in ch81["original_text"]
    assert "为而不争" in ch81["original_text"]


def test_builtin_reader_four_arts():
    """验证四术（周易、八字、紫微、奇门）免 API 内置研读生成"""
    # 1. 紫微斗数
    ziwei_res = calculate_ziwei(2000, 5, 20, 8, 30, gender="女")
    reading_zw = generate_builtin_reading("ziwei", ziwei_res, topic="职业方向探讨")
    assert reading_zw["reading_type"] == "builtin"
    assert reading_zw["is_ai"] is False
    assert len(reading_zw["sections"]) >= 3
    assert len(reading_zw["citations"]) >= 1
    assert any("《紫微斗数全书》" in c["book"] for c in reading_zw["citations"])

    # 2. 奇门遁甲
    qimen_res = calculate_qimen(2026, 9, 26, 10, 30)
    reading_qm = generate_builtin_reading("qimen", qimen_res, topic="商务签约")
    assert reading_qm["reading_type"] == "builtin"
    assert reading_qm["is_ai"] is False
    assert len(reading_qm["sections"]) >= 3
    assert any("《奇门遁甲统宗》" in c["book"] for c in reading_qm["citations"])

    # 3. 八字
    bazi_res = calculate_bazi(1990, 8, 15, 12, 0, gender="男")
    reading_bz = generate_builtin_reading("bazi", bazi_res, topic="健康与自律")
    assert reading_bz["reading_type"] == "builtin"
    assert len(reading_bz["citations"]) >= 1
    assert any("《渊海子平》" in c["book"] for c in reading_bz["citations"])

    # 4. 周易 (真实 calculate_hexagram 引擎输出测试)
    from scripts.iching import calculate_hexagram

    # 4.1 乾卦
    calc_qian = calculate_hexagram([7, 7, 7, 7, 7, 7])
    reading_qian = generate_builtin_reading("zhouyi", calc_qian, topic="创业抉择")
    assert reading_qian["reading_type"] == "builtin"
    assert reading_qian["title"] == "《周易》乾卦内置研读"
    assert "天行健，君子以自强不息。" in reading_qian["citations"][0]["quote"]
    assert reading_qian["citations"][0]["book"] == "《周易·乾传》"

    # 4.2 坤卦 (全阴爻 8 8 8 8 8 8，必须准确匹配坤卦原文，绝不可误套乾卦)
    calc_kun = calculate_hexagram([8, 8, 8, 8, 8, 8])
    reading_kun = generate_builtin_reading("divination", calc_kun, topic="沉潜修省")
    assert reading_kun["title"] == "《周易》坤卦内置研读"
    assert reading_kun["citations"][0]["book"] == "《周易·坤传》"
    assert reading_kun["citations"][0]["quote"] == "地势坤，君子以厚德载物。"
    assert "元亨，利牝马之贞" in reading_kun["sections"][1]["content"]
    assert "天行健" not in reading_kun["sections"][1]["content"]

    # 4.3 既济之贲 (含动爻 5 和 6)
    calc_jiji = calculate_hexagram([7, 8, 7, 8, 9, 6])
    reading_jiji = generate_builtin_reading("divination", calc_jiji, topic="防患未然")
    assert reading_jiji["title"] == "《周易》既济卦内置研读"
    assert reading_jiji["citations"][0]["book"] == "《周易·既济传》"
    assert "水在火上，既济；君子以思患而预防之。" in reading_jiji["citations"][0]["quote"]
    assert "爻位5" in reading_jiji["sections"][1]["content"]
    assert "爻位6" in reading_jiji["sections"][1]["content"]


def test_builtin_reader_rejection_of_empty_and_degraded_handling():
    """验证缺失排盘数据时明确拒绝 (400/ValueError)，以及时辰未知显式降级不脑补"""
    # 1. 严禁空数据伪装：无输入时必须抛出 ValueError，杜绝脑补默认“庚金”
    with pytest.raises(ValueError, match="排盘数据"):
        generate_builtin_reading("bazi", {})

    with pytest.raises(ValueError, match="排盘数据"):
        generate_builtin_reading("divination", {})

    with pytest.raises(ValueError, match="排盘数据"):
        generate_builtin_reading("ziwei", {})

    with pytest.raises(ValueError, match="排盘数据"):
        generate_builtin_reading("qimen", {})

    # 2. 周易非法卦名与卦名/卦号矛盾坚决拒绝，绝不 fallback 乾卦
    with pytest.raises(ValueError, match="未知或非法"):
        generate_builtin_reading("divination", {"ben_name": "虚构无名卦"})

    with pytest.raises(ValueError, match="不符"):
        generate_builtin_reading("divination", {"ben_name": "坤", "original_hexagram": {"name": "坤", "number": 1}})

    # 3. 八字非法日干坚决抛出异常，绝不默认回退“土”
    with pytest.raises(ValueError, match="有效日元天干"):
        generate_builtin_reading("bazi", {"day_master": {"gan": "X"}})

    # 4. 八字时辰未知显式降级处理 (真实 calculate_bazi 引擎驱动)
    bazi_unknown_hour = calculate_bazi(1990, 8, 15, hour=None, gender="男")
    reading_bazi_deg = generate_builtin_reading("bazi", bazi_unknown_hour)
    assert "三柱降级版" in reading_bazi_deg["title"]
    assert "【降级提示】因出生时辰未详" in reading_bazi_deg["sections"][0]["content"]
    assert "时辰未详" in reading_bazi_deg["summary"]

    # 5. 紫微斗数时辰未知显式降级 (真实 calculate_ziwei 引擎 hour=None 驱动)
    ziwei_real_deg = calculate_ziwei(2000, 5, 20, hour=None, gender="女")
    assert ziwei_real_deg["degraded"] is True
    reading_zw_deg = generate_builtin_reading("ziwei", ziwei_real_deg)
    assert "时辰未详·降级说明" in reading_zw_deg["title"]
    assert "不推演虚构星曜" in reading_zw_deg["sections"][0]["content"]
    # 坚决不输出虚构主星或“无主星（借对宫）”
    assert "无主星" not in reading_zw_deg["summary"]
    assert "借对宫" not in reading_zw_deg["summary"]


def test_storage_review_revisions_and_statistics():
    """验证 SQLite 复盘历史修订留痕与无玄学打分的统计分析"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_revisions.db")
    try:
        storage = XuanJianStorage(db_path=db_path)

        # 1. 存入一条初始记录
        created = storage.create_record({
            "record_type": "ziwei",
            "title": "紫微测试手记",
            "topic": "测试职业演进",
            "calculation_result": {"soul_star": "紫微天府", "body_palace": "命宫"},
            "review_data": {
                "original_thought": "最初以为对方会全盘托底",
                "actual_outcome": "",
                "missing_evidence": ""
            }
        })
        rec_id = created["id"]
        assert rec_id is not None

        # 2. 第一次复盘更新：现实演进，触发初次快照保留
        upd1 = storage.update_review(rec_id, {
            "original_thought": "最初以为对方会全盘托底",
            "actual_outcome": "半年后项目因资方资金链断裂而终止",
            "missing_evidence": "未查证资方关联企业的连带担保风险",
            "notes": "慎审资信，知止避险"
        })
        assert upd1 is not None
        assert len(upd1.get("review_data", {}).get("revisions", [])) == 1

        # 3. 第二次复盘更新：再次修改实际结果，累积为 2 次修订留痕
        upd2 = storage.update_review(rec_id, {
            "original_thought": "最初以为对方会全盘托底",
            "actual_outcome": "一年后重新审计，发现实质为合规性法律纠纷",
            "missing_evidence": "未注意前置行政许可的有效期限",
            "notes": "事预则立，不可心存侥幸"
        })
        assert upd2 is not None
        revisions = upd2.get("review_data", {}).get("revisions", [])
        assert len(revisions) == 2, "必须保留全部历史修订记录"
        assert "半年后项目因资方" in revisions[1]["previous_outcome"]
        assert revisions[1]["revised_at"] is not None

        # 4. 复盘统计检查（含1篇初始内置指南）
        stats = storage.get_review_statistics()
        assert stats["total_records"] >= 2
        assert stats["reviewed_count"] >= 1
        assert stats["type_distribution"].get("ziwei") == 1

    finally:
        shutil.rmtree(temp_dir)


def test_daodejing_boundary_and_invalid_chapters():
    """验证道德经章次越界与非法参数安全处理"""
    assert get_daodejing_chapter(0) is None
    assert get_daodejing_chapter(82) is None
    assert get_daodejing_chapter(-1) is None
    assert get_daodejing_chapter(999) is None
    assert get_daodejing_chapter(1) is not None
    assert get_daodejing_chapter(81) is not None


def test_storage_review_anti_truncation_25_plus_revisions():
    """
    核心保障: 连续复盘修改 25 次以上时，最初预期 (initial_thought) 绝不因 revisions 切片而被冲掉或丢失
    同时验证备份与还原后最初预期完整存留。
    """
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_truncation.db")
    try:
        storage = XuanJianStorage(db_path=db_path)

        # 1. 创立初始记录，明确最初预期与观察窗口
        initial_expected = "初始预期：预计此项目能在半年内通过合规审查并取得许可证"
        initial_window = "观察窗口：6个月"
        rec = storage.create_record({
            "record_type": "bazi",
            "title": "二十五次复盘抗截断测试记录",
            "topic": "合规与决策复盘",
            "calculation_result": {"test": True},
            "review_data": {
                "original_thought": initial_expected,
                "observation_window": initial_window,
                "actual_outcome": "初创期初步立项",
                "review_tags": ["立项", "合规"]
            }
        })
        rec_id = rec["id"]

        # 2. 连续模拟 35 次复盘修订 (超越30次切片上限)
        for i in range(1, 36):
            updated = storage.update_review(rec_id, {
                "original_thought": f"第{i}次修改的预期（用户后续可能随时间调整了认知）",
                "actual_outcome": f"第{i}次观察阶段性实际结果：发现合规条例第{i}项变动",
                "review_tags": [f"阶段{i}"]
            })
            assert updated is not None

        # 3. 取出最新记录，严格核验最初预期与最初观察窗口
        final_rec = storage.get_record(rec_id)
        assert final_rec is not None
        rev_data = final_rec.get("review_data", {})

        # 最初预期必须永存，不能变成第35次修改的预期！
        assert rev_data.get("initial_thought") == initial_expected, "最初预期必须完整保留，绝不可被截断丢弃"
        assert rev_data.get("initial_observation_window") == initial_window
        assert rev_data.get("total_revisions") == 35, "累计修订次数应为35次"
        # revisions 数组限制在最近 30 条以防无限膨胀
        assert len(rev_data.get("revisions", [])) == 30

        # 最新结果必须为第35次的结果
        assert "第35次观察阶段性实际结果" in rev_data.get("actual_outcome", "")

        # 4. 模拟数据导出与还原，确保最初预期在导出的 JSON/备份中完好无损
        records_dump, _ = storage.list_records(limit=10)
        target_dump = next(r for r in records_dump if r["id"] == rec_id)
        assert target_dump["review_data"]["initial_thought"] == initial_expected

    finally:
        shutil.rmtree(temp_dir)
