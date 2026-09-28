// frontend/src/components/BaziCalculator.tsx - 八字排盘与干支四柱象数计算组件 (F04)

import React, { useState } from 'react';
import type { BaziResult } from '../types';
import { calculateBaziAPI, createRecordAPI } from '../api';
import { Clock, Database, Check, Shield, AlertCircle, Info } from 'lucide-react';

export const BaziCalculator: React.FC = () => {
  const [year, setYear] = useState<number>(1990);
  const [month, setMonth] = useState<number>(5);
  const [day, setDay] = useState<number>(15);
  const [hour, setHour] = useState<number>(14);
  const [minute, setMinute] = useState<number>(30);
  const [unknownHour, setUnknownHour] = useState<boolean>(false);
  const [gender, setGender] = useState<'乾造' | '坤造'>('乾造');
  const [isLunar, setIsLunar] = useState<boolean>(false);
  const [isLeapMonth, setIsLeapMonth] = useState<boolean>(false);
  const [ziHourSect, setZiHourSect] = useState<number>(2);

  const [isLoading, setIsLoading] = useState(false);
  const [baziResult, setBaziResult] = useState<BaziResult | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isDemo, setIsDemo] = useState(true);

  // 检查生辰输入是否来源于默认预设范例 (1990年5月15日 14:30 乾造 公历)
  const checkIfBaziDefault = (
    y: number,
    m: number,
    d: number,
    h: number,
    min: number,
    unk: boolean,
    g: string,
    lunar: boolean,
    leap: boolean
  ) => {
    return (
      y === 1990 &&
      m === 5 &&
      d === 15 &&
      h === 14 &&
      min === 30 &&
      !unk &&
      g === '乾造' &&
      !lunar &&
      !leap
    );
  };

  // 默认跑一次初始化排盘作为体验示例
  React.useEffect(() => {
    handleCalculate();
  }, []);

  const handleCalculate = async () => {
    const isDefault = checkIfBaziDefault(
      year,
      month,
      day,
      hour,
      minute,
      unknownHour,
      gender,
      isLunar,
      isLeapMonth
    );
    setIsDemo(isDefault);
    setIsLoading(true);
    setErrorMsg('');
    try {
      const res = await calculateBaziAPI({
        year,
        month,
        day,
        hour: unknownHour ? null : hour,
        minute: unknownHour ? 0 : minute,
        gender,
        is_lunar: isLunar,
        is_leap_month: isLeapMonth,
        zi_hour_sect: ziHourSect
      });
      setBaziResult(res);
      setSavedSuccess(false);
    } catch (e: any) {
      setErrorMsg(e.message || '八字推算失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveToRecord = async () => {
    if (!baziResult) return;
    try {
      await createRecordAPI({
        record_type: 'bazi',
        title: `八字手记 · ${baziResult.four_pillars.year.gan_zhi} ${baziResult.four_pillars.month.gan_zhi} ${baziResult.four_pillars.day.gan_zhi} ${baziResult.four_pillars.hour.gan_zhi}`,
        topic: `日主${baziResult.day_master.gan}${baziResult.day_master.wuxing}五行研读`,
        tags: ['八字排盘', baziResult.gender, baziResult.day_master.wuxing],
        params: {
          year,
          month,
          day,
          hour: unknownHour ? null : hour,
          minute: unknownHour ? 0 : minute,
          gender,
          is_lunar: isLunar
        },
        calculation_result: baziResult
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (e: any) {
      alert(`保存失败: ${e.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* 输入控制卡片 */}
      <div className="card-xuan p-5 bg-[var(--xuanzhi-light)]">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className="seal-tag">象数</span>
            <h3 className="font-song text-lg font-bold text-[var(--ink)]">八字干支排盘</h3>
            <span className="text-xs text-[var(--ink-muted)]">基于严格节气划分 · 确定性推算 · 不作宿命定论</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setIsLunar(false);
                setIsDemo(checkIfBaziDefault(year, month, day, hour, minute, unknownHour, gender, false, isLeapMonth));
              }}
              className={`px-3 py-1 text-xs rounded border transition ${
                !isLunar
                  ? 'bg-[var(--daiqing)] text-white border-[var(--daiqing)]'
                  : 'bg-[var(--xuanzhi)] text-[var(--ink)] border-[var(--border)]'
              }`}
            >
              公历 (阳历)
            </button>
            <button
              onClick={() => {
                setIsLunar(true);
                setIsDemo(checkIfBaziDefault(year, month, day, hour, minute, unknownHour, gender, true, isLeapMonth));
              }}
              className={`px-3 py-1 text-xs rounded border transition ${
                isLunar
                  ? 'bg-[var(--daiqing)] text-white border-[var(--daiqing)]'
                  : 'bg-[var(--xuanzhi)] text-[var(--ink)] border-[var(--border)]'
              }`}
            >
              农历 (阴历)
            </button>
          </div>
        </div>

        {/* 表单输入网格 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 mb-4">
          <div>
            <label className="block text-xs text-[var(--ink-muted)] mb-1">年份</label>
            <input
              type="number"
              min={1900}
              max={2100}
              value={year}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 1990;
                setYear(v);
                setIsDemo(checkIfBaziDefault(v, month, day, hour, minute, unknownHour, gender, isLunar, isLeapMonth));
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)]"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--ink-muted)] mb-1">月份</label>
            <input
              type="number"
              min={1}
              max={12}
              value={month}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 1;
                setMonth(v);
                setIsDemo(checkIfBaziDefault(year, v, day, hour, minute, unknownHour, gender, isLunar, isLeapMonth));
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)]"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--ink-muted)] mb-1">日期</label>
            <input
              type="number"
              min={1}
              max={31}
              value={day}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 1;
                setDay(v);
                setIsDemo(checkIfBaziDefault(year, month, v, hour, minute, unknownHour, gender, isLunar, isLeapMonth));
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)]"
            />
          </div>

          <div>
            <label className="block text-xs text-[var(--ink-muted)] mb-1">出生时辰</label>
            <input
              type="number"
              min={0}
              max={23}
              disabled={unknownHour}
              value={hour}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 0;
                setHour(v);
                setIsDemo(checkIfBaziDefault(year, month, day, v, minute, unknownHour, gender, isLunar, isLeapMonth));
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)] disabled:opacity-40"
            />
          </div>

          <div>
            <label className="block text-xs text-[var(--ink-muted)] mb-1">分钟</label>
            <input
              type="number"
              min={0}
              max={59}
              disabled={unknownHour}
              value={minute}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 0;
                setMinute(v);
                setIsDemo(checkIfBaziDefault(year, month, day, hour, v, unknownHour, gender, isLunar, isLeapMonth));
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)] disabled:opacity-40"
            />
          </div>

          <div>
            <label className="block text-xs text-[var(--ink-muted)] mb-1">性别</label>
            <select
              value={gender}
              onChange={(e) => {
                const v = e.target.value as any;
                setGender(v);
                setIsDemo(checkIfBaziDefault(year, month, day, hour, minute, unknownHour, v, isLunar, isLeapMonth));
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)]"
            >
              <option value="乾造">乾造 (男)</option>
              <option value="坤造">坤造 (女)</option>
            </select>
          </div>
        </div>

        {/* 附加选项与按钮 */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-1.5 text-xs text-[var(--ink)]">
              <span className="text-[var(--ink-muted)]">子时换日口径：</span>
              <select
                value={ziHourSect}
                onChange={(e) => setZiHourSect(parseInt(e.target.value) || 2)}
                className="px-2 py-1 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)]"
              >
                <option value={2}>00:00 换日（早晚子时分立，默认）</option>
                <option value={1}>23:00 换日（子初换日派）</option>
              </select>
            </div>

            <label className="flex items-center gap-1.5 text-xs text-[var(--ink)] cursor-pointer">
              <input
                type="checkbox"
                checked={unknownHour}
                onChange={(e) => {
                  const v = e.target.checked;
                  setUnknownHour(v);
                  setIsDemo(checkIfBaziDefault(year, month, day, hour, minute, v, gender, isLunar, isLeapMonth));
                }}
                className="rounded border-[var(--border)] text-[var(--daiqing)]"
              />
              <span>时辰未知 (降级为三柱六字)</span>
            </label>

            {isLunar && (
              <label className="flex items-center gap-1.5 text-xs text-[var(--ink)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={isLeapMonth}
                  onChange={(e) => {
                    const v = e.target.checked;
                    setIsLeapMonth(v);
                    setIsDemo(checkIfBaziDefault(year, month, day, hour, minute, unknownHour, gender, isLunar, v));
                  }}
                  className="rounded border-[var(--border)] text-[var(--daiqing)]"
                />
                <span>闰月</span>
              </label>
            )}
          </div>

          <button
            onClick={() => handleCalculate()}
            disabled={isLoading}
            className="btn-antique px-5 py-2 text-xs flex items-center gap-1.5"
          >
            <Clock size={14} />
            <span>{isLoading ? '正在推算...' : '排盘推算'}</span>
          </button>
        </div>

        {errorMsg && (
          <div className="mt-3 p-2.5 bg-red-500/10 border border-red-500/30 text-red-700 dark:text-red-400 text-xs rounded flex items-center gap-2">
            <AlertCircle size={14} />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* 排盘结果展示 */}
      {baziResult && (
        <div className="flex flex-col gap-6">
          {/* 体验示例状态提示 */}
          {isDemo && (
            <div className="card-xuan p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-lg text-xs text-amber-900 dark:text-amber-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-amber-200 dark:bg-amber-800/80 font-bold">体验示例</span>
                <span>当前显示为预设示例（1990年5月15日），未录入您的真实生辰。</span>
              </div>
              <span className="text-amber-700 dark:text-amber-300">
                可修改上方生辰并点击“推算四柱八字”开始个人排盘
              </span>
            </div>
          )}

          {/* 日期概览与降级提示 */}
          <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] flex flex-col gap-2">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <span className="px-2.5 py-1 text-xs font-bold rounded bg-[var(--daiqing)] text-white">
                  {baziResult.gender}
                </span>
                <div className="text-xs text-[var(--ink)] font-song">
                  <span className="font-bold">公历：</span>{baziResult.solar_date}
                </div>
                <div className="text-xs text-[var(--ink)] font-song">
                  <span className="font-bold">农历：</span>{baziResult.lunar_date}
                </div>
              </div>

              {baziResult.degraded_to_three_pillars && (
                <span className="px-2 py-0.5 text-xs rounded bg-amber-500/20 text-amber-800 dark:text-amber-200 border border-amber-500/30">
                  已降级为三柱六字 (时柱未知)
                </span>
              )}
            </div>

            {baziResult.time_boundary_notes && (
              <div className="text-[11px] text-[var(--ink-muted)] pt-2 border-t border-[var(--border-light)] flex flex-col gap-1 font-song">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[var(--ink)]">时间口径：</span>
                  <span>{baziResult.time_boundary_notes.solar_time_system}</span>
                  <span className="text-[var(--border)]">|</span>
                  <span>{baziResult.time_boundary_notes.zi_hour_mode}</span>
                </div>
                <div className="text-[var(--ink-subtle)] leading-relaxed">
                  {baziResult.time_boundary_notes.timezone_and_dst_notice}
                </div>
              </div>
            )}
          </div>

          {/* 四柱排盘大卡片 */}
          <div className="card-xuan p-5 bg-[var(--xuanzhi-light)] overflow-x-auto">
            <div className="min-w-[500px]">
              <div className="grid grid-cols-4 gap-3 text-center">
                {/* 四柱列 */}
                {(['year', 'month', 'day', 'hour'] as const).map((key) => {
                  const p = baziResult.four_pillars[key];
                  const isHourUnknown = key === 'hour' && baziResult.degraded_to_three_pillars;

                  return (
                    <div
                      key={key}
                      className={`p-3 rounded-lg border transition ${
                        key === 'day'
                          ? 'border-[var(--daiqing)] bg-[var(--xuanzhi)] shadow-sm'
                          : 'border-[var(--border)] bg-[var(--xuanzhi-light)]'
                      }`}
                    >
                      <div className="text-xs font-bold text-[var(--ink-muted)] mb-2 flex items-center justify-center gap-1">
                        <span>{p.pillar_name}</span>
                        <span className="font-serif font-bold text-[var(--ink)]">({p.gan_zhi})</span>
                        {key === 'day' && <span className="text-[10px] text-[var(--daiqing)] font-normal">(日元)</span>}
                      </div>

                      {/* 主星十神 */}
                      <div className="text-xs font-song text-[var(--zhusha)] font-bold mb-2">
                        {p.ten_god}
                      </div>

                      {/* 天干 */}
                      <div className="text-2xl font-serif font-bold text-[var(--ink)] mb-1">
                        {p.gan}
                      </div>

                      {/* 地支 */}
                      <div className="text-2xl font-serif font-bold text-[var(--ink)] mb-3">
                        {p.zhi}
                      </div>

                      {/* 地支藏干与副星十神 */}
                      <div className="text-left text-[11px] bg-[var(--border-light)] p-2 rounded mb-2 space-y-1">
                        <div className="text-[10px] text-[var(--ink-muted)] border-b border-[var(--border)] pb-1 mb-1">
                          地支藏干
                        </div>
                        {isHourUnknown ? (
                          <div className="text-[var(--ink-muted)] text-[10px]">时辰未知</div>
                        ) : p.hidden_stems.length > 0 ? (
                          p.hidden_stems.map((h, i) => (
                            <div key={i} className="flex items-center justify-between text-[10px]">
                              <span className="font-bold text-[var(--ink)]">{h.gan} ({h.wuxing})</span>
                              <span className="text-[var(--ink-muted)]">{h.ten_god}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-[var(--ink-muted)] text-[10px]">-</div>
                        )}
                      </div>

                      {/* 纳音 */}
                      <div className="text-[11px] text-[var(--ink-muted)] mb-1">
                        纳音：<span className="text-[var(--ink)]">{p.nayin}</span>
                      </div>

                      {/* 旬空 */}
                      <div className="text-[10px] text-[var(--ink-muted)]">
                        空亡：<span className="text-[var(--ink)]">{p.xun_kong}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 日主与五行分布卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 日主特质 */}
            <div className="card-xuan p-5 bg-[var(--xuanzhi-light)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="seal-tag">日元</span>
                <h4 className="font-song font-bold text-[var(--ink)]">日主属性分析</h4>
              </div>
              <div className="p-3 rounded bg-[var(--xuanzhi)] border border-[var(--border)] mb-3">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-xl font-bold font-serif text-[var(--daiqing)]">
                    {baziResult.day_master.gan}{baziResult.day_master.wuxing}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-[var(--daiqing)] text-white">
                    {baziResult.day_master.yinyang}{baziResult.day_master.wuxing}
                  </span>
                </div>
                <p className="text-xs text-[var(--ink)] leading-relaxed mt-2">
                  {baziResult.day_master.description}
                </p>
              </div>
              <p className="text-xs text-[var(--ink-muted)] leading-relaxed">
                在传统命理象数中，日主代表当事人之本原心性与立足基点。知止之要，在于明辨自身偏颇，刚者戒矜，柔者戒馁。
              </p>
            </div>

            {/* 五行分布 */}
            <div className="card-xuan p-5 bg-[var(--xuanzhi-light)]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="seal-tag">五行</span>
                  <h4 className="font-song font-bold text-[var(--ink)]">
                    五行数量分布 ({baziResult.wuxing_analysis.total_chars_analyzed}字干支字面计数)
                  </h4>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                {(['木', '火', '土', '金', '水'] as const).map((wx) => {
                  const count = baziResult.wuxing_analysis.counts[wx] || 0;
                  const pct = baziResult.wuxing_analysis.percentages[wx] || 0;
                  const colors: Record<string, string> = {
                    木: 'bg-emerald-600',
                    火: 'bg-rose-600',
                    土: 'bg-amber-600',
                    金: 'bg-slate-500',
                    水: 'bg-sky-600'
                  };

                  return (
                    <div key={wx} className="flex items-center gap-2 text-xs">
                      <span className="w-6 font-bold text-[var(--ink)] text-center">{wx}</span>
                      <div className="flex-1 bg-[var(--border-light)] rounded-full h-3 overflow-hidden border border-[var(--border)]">
                        <div
                          className={`h-full ${colors[wx]} transition-all duration-500`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="w-12 text-right text-[var(--ink-muted)] text-[11px]">
                        {count} ({pct}%)
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="flex items-center gap-4 text-xs text-[var(--ink-muted)] pt-2 border-t border-[var(--border)]">
                <div>
                  偏多五行：
                  <span className="font-bold text-[var(--ink)]">
                    {baziResult.wuxing_analysis.strongest.join('、') || '无'}
                  </span>
                </div>
                <div>
                  字面未现：
                  <span className="font-bold text-[var(--zhusha)]">
                    {baziResult.wuxing_analysis.missing.join('、') || '无'}
                  </span>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-[var(--ink-muted)] leading-relaxed bg-[var(--xuanzhi)] p-2 rounded border border-[var(--border)]">
                注：五行统计仅为四柱干支字面数量分布统计，绝不代表命理强弱、吉凶或缺补依据，切忌迷信附会。
              </p>
            </div>
          </div>

          {/* 大运序列卡片 */}
          <div className="card-xuan p-5 bg-[var(--xuanzhi-light)]">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-2 border-b border-[var(--border)]">
              <div className="flex items-center gap-2">
                <span className="seal-tag">大运</span>
                <h4 className="font-song font-bold text-[var(--ink)]">十年大运流向</h4>
                <span className="text-xs px-2 py-0.5 rounded bg-[var(--border-light)] text-[var(--ink)] border border-[var(--border)]">
                  {baziResult.dayun.metadata.direction_text}
                </span>
              </div>
              <div className="text-xs text-[var(--ink-muted)]">
                起运公历：{baziResult.dayun.metadata.start_solar_date} ({baziResult.dayun.metadata.start_year_offset}岁起运)
              </div>
            </div>

            <p className="text-xs text-[var(--ink-muted)] mb-4">
              {baziResult.dayun.metadata.approx_note}
            </p>

            {/* 大运轮盘/列表 */}
            <div className="overflow-x-auto pb-2">
              <div className="flex items-center gap-3 min-w-[700px]">
                {baziResult.dayun.sequence.map((dy) => (
                  <div
                    key={dy.index}
                    className="flex-1 min-w-[75px] p-2.5 rounded border border-[var(--border)] bg-[var(--xuanzhi)] text-center transition hover:border-[var(--daiqing)] hover:shadow-sm"
                  >
                    <div className="text-[10px] text-[var(--zhusha)] font-bold mb-1">
                      {dy.ten_god}
                    </div>
                    <div className="text-base font-serif font-bold text-[var(--ink)] mb-1">
                      {dy.gan_zhi}
                    </div>
                    <div className="text-[10px] text-[var(--ink)] font-bold">
                      {dy.start_age}-{dy.end_age}岁
                    </div>
                    <div className="text-[9px] text-[var(--ink-muted)]">
                      {dy.start_year}年
                    </div>
                    <div className="text-[9px] text-[var(--ink-subtle)] mt-1 border-t border-[var(--border)] pt-1">
                      {dy.nayin}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 存为手记与防线 */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 card-xuan p-4 bg-[var(--xuanzhi-light)] border border-[var(--border)]">
            <div className="flex items-center gap-2 text-xs text-[var(--ink-muted)]">
              <Shield size={14} className="text-[var(--daiqing)]" />
              <span>数据存储于本地 SQLite (data/xuanjian.db)，绝不上报云端。</span>
            </div>

            <button
              onClick={handleSaveToRecord}
              disabled={savedSuccess}
              className={`px-4 py-2 text-xs font-song rounded flex items-center gap-1.5 transition ${
                savedSuccess
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'btn-antique'
              }`}
            >
              {savedSuccess ? <Check size={14} /> : <Database size={14} />}
              <span>{savedSuccess ? '已存为本地手记' : '存为本地手记'}</span>
            </button>
          </div>

          {/* 客观知止声明 */}
          <div className="p-3.5 rounded bg-amber-500/10 border border-amber-500/30 text-xs text-[var(--ink)] leading-relaxed flex items-start gap-2.5">
            <Info size={16} className="text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-amber-800 dark:text-amber-300">客观知止提醒：</span>
              <span>{baziResult.disclaimer}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
