// frontend/src/views/CalendarView.tsx - 历法与宜忌考据视图 (支持墨夜主题)

import React from 'react';
import type { CalendarDayData, TabooItem } from '../types';
import { ChevronLeft, ChevronRight, RotateCcw, Calendar, ShieldCheck } from 'lucide-react';

interface CalendarViewProps {
  calendarData: CalendarDayData | null;
  currentDateStr: string;
  onChangeDate: (dateStr: string) => void;
  onOpenSource: (item: TabooItem) => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  calendarData,
  currentDateStr,
  onChangeDate,
  onOpenSource
}) => {
  const handlePrevDay = () => {
    const d = new Date(currentDateStr);
    d.setDate(d.getDate() - 1);
    onChangeDate(d.toISOString().slice(0, 10));
  };

  const handleNextDay = () => {
    const d = new Date(currentDateStr);
    d.setDate(d.getDate() + 1);
    onChangeDate(d.toISOString().slice(0, 10));
  };

  const handleToday = () => {
    const today = new Date().toISOString().slice(0, 10);
    onChangeDate(today);
  };

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto py-4">
      {/* 顶部日期切换与控制栏 */}
      <div className="card-xuan p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevDay}
            className="btn-secondary px-3 py-1.5"
            aria-label="前一天"
          >
            <ChevronLeft size={16} />
            <span>前一日</span>
          </button>
          <button
            onClick={handleNextDay}
            className="btn-secondary px-3 py-1.5"
            aria-label="后一天"
          >
            <span>后一日</span>
            <ChevronRight size={16} />
          </button>
          <button
            onClick={handleToday}
            className="btn-secondary px-3 py-1.5"
            aria-label="回到今日"
          >
            <RotateCcw size={14} />
            <span>回到今日</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Calendar size={16} className="text-[var(--daiqing)]" />
          <input
            type="date"
            value={currentDateStr}
            onChange={(e) => e.target.value && onChangeDate(e.target.value)}
            className="input-xuan py-1 px-2 text-sm w-auto cursor-pointer"
            min="1900-01-31"
            max="2100-12-31"
          />
        </div>
      </div>

      {/* 主历法展示大卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 左侧：公农历与干支看板 */}
        <div className="md:col-span-1 card-xuan p-6 flex flex-col justify-between bg-[var(--xuanzhi-light)] border-t-4 border-t-[var(--daiqing)]">
          <div>
            <div className="text-xs text-[var(--ink-muted)] flex items-center justify-between mb-2">
              <span className="seal-tag">时宪历法</span>
              <span>{calendarData?.solar.weekday}</span>
            </div>
            <div className="font-song text-4xl font-bold text-[var(--ink)] my-2">
              {calendarData?.solar.day}
            </div>
            <div className="text-sm font-medium text-[var(--ink)]">
              {calendarData?.solar.year}年 {calendarData?.solar.month}月
            </div>

            <div className="my-4 pt-4 border-t border-[var(--border-light)]">
              <div className="font-song text-lg font-bold text-[var(--daiqing)]">
                {calendarData?.lunar.month_chinese}月{calendarData?.lunar.day_chinese}
              </div>
              <div className="text-xs text-[var(--ink-muted)] mt-1">
                {calendarData?.lunar.ganzhi_year} · {calendarData?.lunar.ganzhi_month} · {calendarData?.lunar.ganzhi_day}
              </div>
              <div className="text-xs text-[var(--ink-subtle)] mt-0.5">
                生肖：{calendarData?.lunar.animal} ｜ 纳音：{calendarData?.lunar.nayin}
              </div>
              {calendarData?.lunar.is_leap_month && (
                <span className="mt-2 inline-block px-2 py-0.5 text-[11px] bg-[var(--daiqing-light)] text-[var(--daiqing)] rounded">
                  本月为闰月
                </span>
              )}
            </div>
          </div>

          {/* 节气与时区 */}
          <div className="pt-4 border-t border-[var(--border-light)] text-xs text-[var(--ink-muted)]">
            {calendarData?.solar_term.current ? (
              <div className="text-[var(--daiqing)] font-bold font-song">
                ● 今日节气：{calendarData.solar_term.current}
              </div>
            ) : (
              <div>
                下一节气：{calendarData?.solar_term.next_term?.name || '待算'} ({calendarData?.solar_term.next_term?.date || ''})
              </div>
            )}
            <div className="text-[11px] text-[var(--ink-subtle)] mt-1">
              口径：北京时间 UTC+8（换日以子正 00:00 为准）
            </div>
          </div>
        </div>

        {/* 右侧：传统宜忌与彭祖百忌考据 */}
        <div className="md:col-span-2 flex flex-col gap-5">
          {/* 宜与忌两列 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* 宜 (Yi) */}
            <div className="card-xuan p-5 bg-[var(--xuanzhi-card)]">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border-light)]">
                <span className="w-5 h-5 rounded-full bg-[var(--daiqing-light)] text-[var(--daiqing)] flex items-center justify-center text-xs font-bold font-song">
                  宜
                </span>
                <span className="font-song font-bold text-sm text-[var(--ink)]">今日宜行事项</span>
                <span className="text-[10px] text-[var(--ink-subtle)] ml-auto">点击考据出处</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {calendarData?.yi && calendarData.yi.length > 0 ? (
                  calendarData.yi.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => onOpenSource(item)}
                      className="px-2.5 py-1 text-xs bg-[var(--daiqing-light)] hover:bg-[var(--border-light)] text-[var(--daiqing)] rounded transition cursor-pointer border border-[var(--border)]"
                    >
                      {item.term || item.title}
                    </button>
                  ))
                ) : (
                  <span className="text-xs text-[var(--ink-subtle)]">诸事平平，按常处之</span>
                )}
              </div>
            </div>

            {/* 忌 (Ji) */}
            <div className="card-xuan p-5 bg-[var(--xuanzhi-card)]">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border-light)]">
                <span className="w-5 h-5 rounded-full bg-[var(--zhusha-light)] text-[var(--zhusha)] flex items-center justify-center text-xs font-bold font-song">
                  忌
                </span>
                <span className="font-song font-bold text-sm text-[var(--ink)]">传统建议避忌</span>
                <span className="text-[10px] text-[var(--ink-subtle)] ml-auto">点击考据出处</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {calendarData?.ji && calendarData.ji.length > 0 ? (
                  calendarData.ji.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => onOpenSource(item)}
                      className="px-2.5 py-1 text-xs bg-[var(--zhusha-light)] hover:bg-[var(--border-light)] text-[var(--zhusha)] rounded transition cursor-pointer border border-[var(--border)]"
                    >
                      {item.term || item.title}
                    </button>
                  ))
                ) : (
                  <span className="text-xs text-[var(--ink-subtle)]">无特殊典籍避忌</span>
                )}
              </div>
            </div>
          </div>

          {/* 彭祖百忌卡片 */}
          <div className="card-xuan p-4 bg-[var(--xuanzhi-light)]">
            <div className="flex items-center gap-2 mb-2">
              <span className="seal-tag-muted">彭祖百忌</span>
              <span className="text-xs text-[var(--ink-subtle)]">《事林广记·历法门》</span>
            </div>
            <p className="font-song text-sm font-medium text-[var(--ink)]">
              {calendarData?.pengzu_baiji.full}
            </p>
            <p className="text-xs text-[var(--ink-muted)] mt-1 leading-relaxed">
              天干与地支各自配属之民俗戒慎。古人以此作为日常行事的隐喻反省，非现实物理阻隔。凡遇诉讼、治水、医病等要务，当遵法度与医学。
            </p>
          </div>

          {/* 算法来源与独立核验证据 */}
          <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] text-xs text-[var(--ink-muted)] flex flex-col gap-1.5">
            <div className="font-song font-bold text-[var(--ink)] flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-[var(--daiqing)]" />
              历法计算口径与可追溯说明
            </div>
            <p>
              1. <strong>计算引擎</strong>：{calendarData?.metadata?.engine} v{calendarData?.metadata?.version} ({calendarData?.metadata?.license} 许可)
            </p>
            <p>
              2. <strong>独立参考</strong>：{calendarData?.metadata?.verification_reference}
            </p>
            <p>
              3. <strong>节假日口径</strong>：未来年度节假日需以国务院办公厅当年年底官方发布为准，未公布前标示为“待公布”，不臆测连休。
            </p>
            <p className="text-[var(--zhusha)] mt-1">
              {calendarData?.metadata?.disclaimer}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
