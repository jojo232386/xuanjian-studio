// frontend/src/components/ZiweiCalculator.tsx - 紫微斗数十二宫星盘可视化与研读组件

import React, { useState } from 'react';
import {
  Compass,
  BookOpen,
  Save,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  ArrowRightLeft
} from 'lucide-react';
import { calculateZiweiAPI, fetchBuiltinReadingAPI, createRecordAPI } from '../api';
import type { ZiweiResult, ZiweiPalace, BuiltinReadingResponse } from '../types';

export const ZiweiCalculator: React.FC = () => {
  // 表单状态
  const getTodayStr = () => {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const dayStr = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${dayStr}`;
  };

  const [calendarType, setCalendarType] = useState<'solar' | 'lunar'>('solar');
  const [year, setYear] = useState<number>(1990);
  const [month, setMonth] = useState<number>(5);
  const [day, setDay] = useState<number>(15);
  const [hour, setHour] = useState<number | null>(14); // null 为未知
  const [gender, setGender] = useState<'男' | '女'>('男');
  const [isLeapMonth, setIsLeapMonth] = useState<boolean>(false);
  const [targetDate, setTargetDate] = useState<string>(getTodayStr);

  // 计算结果与交互状态
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ZiweiResult | null>(null);
  const [selectedPalace, setSelectedPalace] = useState<ZiweiPalace | null>(null);
  const [isDemo, setIsDemo] = useState<boolean>(true);

  // 内置研读与保存状态
  const [builtinReading, setBuiltinReading] = useState<BuiltinReadingResponse | null>(null);
  const [readingLoading, setReadingLoading] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  // 判断生辰参数是否来源于预设范例
  const checkIfPreset = (
    cType: string,
    y: number,
    m: number,
    d: number,
    h: number | null,
    g: string,
    leap: boolean
  ) => {
    const isP1 = cType === 'solar' && y === 1990 && m === 5 && d === 15 && h === 14 && g === '男' && !leap;
    const isP2 = cType === 'solar' && y === 2000 && m === 8 && d === 16 && h === 2 && g === '女' && !leap;
    return isP1 || isP2;
  };

  // 快捷虚构样例
  const setPreset = (preset: 'preset1' | 'preset2') => {
    setIsDemo(true);
    if (preset === 'preset1') {
      setCalendarType('solar');
      setYear(1990);
      setMonth(5);
      setDay(15);
      setHour(14);
      setGender('男');
      setIsLeapMonth(false);
    } else {
      setCalendarType('solar');
      setYear(2000);
      setMonth(8);
      setDay(16);
      setHour(2);
      setGender('女');
      setIsLeapMonth(false);
    }
    setResult(null);
    setBuiltinReading(null);
    setSelectedPalace(null);
    setError(null);
  };

  const handleCalculate = async () => {
    // 按实际生辰来源维持示例标识，不无条件清除；仅当用户修改非范例参数时方为个人排盘
    setIsDemo(checkIfPreset(calendarType, year, month, day, hour, gender, isLeapMonth));
    setLoading(true);
    setError(null);
    setSavedSuccess(false);
    setBuiltinReading(null);
    try {
      const res = await calculateZiweiAPI({
        year,
        month,
        day,
        hour,
        gender,
        calendar: calendarType,
        is_leap_month: isLeapMonth,
        target_date: targetDate
      });
      setResult(res);
      if (res.palaces && res.palaces.length > 0) {
        const ming = res.palaces.find(p => p.name === '命宫') || res.palaces[0];
        setSelectedPalace(ming);
      }
    } catch (err: any) {
      setError(err?.message || '紫微星盘推算失败，请核对输入参数');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchBuiltinReading = async () => {
    if (!result) return;
    setReadingLoading(true);
    try {
      const res = await fetchBuiltinReadingAPI({
        record_type: 'ziwei',
        calculation: result,
        topic: '紫微斗数象数研习'
      });
      setBuiltinReading(res);
    } catch (err: any) {
      setError(err?.message || '获取内置研读失败');
    } finally {
      setReadingLoading(false);
    }
  };

  const handleSaveRecord = async () => {
    if (!result) return;
    try {
      const mingPalace = result.palaces?.find(p => p.name === '命宫');
      const majorNames = mingPalace?.majorStars.map(s => s.name).join('、') || '无主星';
      const title = `紫微星盘·命宫【${majorNames}】（${result.basic?.chineseDate || ''}）`;

      await createRecordAPI({
        record_type: 'ziwei',
        title,
        topic: '紫微斗数命宫与三方四正研读',
        tags: ['紫微斗数', '星盘', majorNames, result.basic?.soul || ''],
        params: {
          calendarType,
          year,
          month,
          day,
          hour,
          gender,
          isLeapMonth
        },
        calculation_result: result,
        review_data: {
          original_thought: '探讨主星秉性在现代处世中的优势与盲点',
          observation_window: '长期修身自省'
        }
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      setError(err?.message || '保存手记记录失败');
    }
  };

  // 高亮三方四正的辅助函数
  const isSanFangSiZheng = (palaceName: string): boolean => {
    if (!selectedPalace || !selectedPalace.sanFangSiZheng) return false;
    const { opposite, trine1, trine2 } = selectedPalace.sanFangSiZheng;
    return palaceName === selectedPalace.name || palaceName === opposite || palaceName === trine1 || palaceName === trine2;
  };

  return (
    <div className="space-y-6">
      {/* 顶部标题与原则卡片 */}
      <div className="bg-amber-50/50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200 dark:border-stone-800">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2 text-stone-800 dark:text-stone-100">
              <Compass className="w-5 h-5 text-amber-700 dark:text-amber-500" />
              紫微斗数 · 十二宫星盘研读
            </h2>
            <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">
              基于开源 iztro (v2.6.1) 确定性算法，完整呈现十二宫位、十四主星、生年四化与大限流年。纯本地免 API 运行。
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-stone-500">参考范例(非默认):</span>
            <button
              onClick={() => setPreset('preset1')}
              className="px-2.5 py-1 text-xs border border-stone-300 dark:border-stone-700 rounded hover:bg-stone-100 dark:hover:bg-stone-800"
            >
              范例一(庚午男)
            </button>
            <button
              onClick={() => setPreset('preset2')}
              className="px-2.5 py-1 text-xs border border-stone-300 dark:border-stone-700 rounded hover:bg-stone-100 dark:hover:bg-stone-800"
            >
              范例二(庚辰女)
            </button>
          </div>
        </div>

        {/* 输入参数表单 */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-4">
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">历法类型</label>
            <select
              value={calendarType}
              onChange={e => {
                const val = e.target.value as any;
                setCalendarType(val);
                setIsDemo(checkIfPreset(val, year, month, day, hour, gender, isLeapMonth));
              }}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            >
              <option value="solar">公历 (阳历)</option>
              <option value="lunar">农历 (阴历)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">年份 (年)</label>
            <input
              type="number"
              min={1900}
              max={2100}
              value={year}
              onChange={e => {
                const val = parseInt(e.target.value) || 2000;
                setYear(val);
                setIsDemo(checkIfPreset(calendarType, val, month, day, hour, gender, isLeapMonth));
              }}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>

          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">月份 (月)</label>
            <input
              type="number"
              min={1}
              max={12}
              value={month}
              onChange={e => {
                const val = parseInt(e.target.value) || 1;
                setMonth(val);
                setIsDemo(checkIfPreset(calendarType, year, val, day, hour, gender, isLeapMonth));
              }}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>

          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">日期 (日)</label>
            <input
              type="number"
              min={1}
              max={31}
              value={day}
              onChange={e => {
                const val = parseInt(e.target.value) || 1;
                setDay(val);
                setIsDemo(checkIfPreset(calendarType, year, month, val, hour, gender, isLeapMonth));
              }}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>

          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">出生时辰</label>
            <select
              value={hour === null ? 'unknown' : hour}
              onChange={e => {
                const val = e.target.value === 'unknown' ? null : parseInt(e.target.value);
                setHour(val);
                setIsDemo(checkIfPreset(calendarType, year, month, day, val, gender, isLeapMonth));
              }}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            >
              <option value="unknown">未知时辰 (安全降级)</option>
              <option value={0}>早子时 (00:00-01:00)</option>
              <option value={2}>丑时 (01:00-03:00)</option>
              <option value={4}>寅时 (03:00-05:00)</option>
              <option value={6}>卯时 (05:00-07:00)</option>
              <option value={8}>辰时 (07:00-09:00)</option>
              <option value={10}>巳时 (09:00-11:00)</option>
              <option value={12}>午时 (11:00-13:00)</option>
              <option value={14}>未时 (13:00-15:00)</option>
              <option value={16}>申时 (15:00-17:00)</option>
              <option value={18}>酉时 (17:00-19:00)</option>
              <option value={20}>戌时 (19:00-21:00)</option>
              <option value={22}>亥时 (21:00-23:00)</option>
              <option value={23}>夜子时 (23:00-00:00)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">性别</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setGender('男');
                  setIsDemo(checkIfPreset(calendarType, year, month, day, hour, '男', isLeapMonth));
                }}
                className={`flex-1 py-1.5 text-xs rounded border ${gender === '男' ? 'bg-amber-100 dark:bg-amber-950/50 border-amber-600 font-bold text-amber-800 dark:text-amber-200' : 'border-stone-300 dark:border-stone-700'}`}
              >
                乾造(男)
              </button>
              <button
                type="button"
                onClick={() => {
                  setGender('女');
                  setIsDemo(checkIfPreset(calendarType, year, month, day, hour, '女', isLeapMonth));
                }}
                className={`flex-1 py-1.5 text-xs rounded border ${gender === '女' ? 'bg-amber-100 dark:bg-amber-950/50 border-amber-600 font-bold text-amber-800 dark:text-amber-200' : 'border-stone-300 dark:border-stone-700'}`}
              >
                坤造(女)
              </button>
            </div>
          </div>
        </div>

        {/* 农历闰月与流年考查 */}
        <div className="flex flex-wrap items-center justify-between gap-4 mt-4 pt-3 border-t border-stone-200 dark:border-stone-800 text-xs">
          <div className="flex items-center gap-4">
            {calendarType === 'lunar' && (
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isLeapMonth}
                  onChange={e => {
                    const val = e.target.checked;
                    setIsLeapMonth(val);
                    setIsDemo(checkIfPreset(calendarType, year, month, day, hour, gender, val));
                  }}
                  className="rounded text-amber-600"
                />
                <span>是否农历闰月</span>
              </label>
            )}
            <div className="flex items-center gap-1.5">
              <span className="text-stone-500">流年考查日期:</span>
              <input
                type="date"
                value={targetDate}
                onChange={e => setTargetDate(e.target.value)}
                className="bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2 py-0.5"
              />
            </div>
          </div>

          <button
            onClick={handleCalculate}
            disabled={loading}
            className="px-5 py-2 bg-amber-700 hover:bg-amber-800 text-white rounded font-medium shadow-sm transition-colors flex items-center gap-2"
          >
            {loading ? <span className="animate-spin">⏳</span> : <Compass className="w-4 h-4" />}
            排布紫微星盘
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 降级提示卡片 */}
      {result && result.degraded && (
        <div className="p-4 bg-amber-50/70 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800 rounded-lg">
          <h3 className="font-bold text-amber-800 dark:text-amber-200 flex items-center gap-2 mb-2">
            <ShieldAlert className="w-5 h-5 text-amber-600" />
            时辰未知 · 安全降级说明
          </h3>
          <p className="text-sm text-stone-700 dark:text-stone-300 leading-relaxed">
            {result.message}
          </p>
          <div className="mt-3 text-xs text-stone-500 dark:text-stone-400">
            紫微斗数安命宫与五行立局严格依赖出生时辰。若无法确认准确时辰，建议仅参考八字前三柱六字，切忌随意虚构时柱避免误导决策。
          </div>
        </div>
      )}

      {/* 正常完整星盘 */}
      {result && !result.degraded && result.palaces && (
        <div className="space-y-6">
          {/* 体验示例状态提示 */}
          {isDemo && (
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-lg p-3 text-xs text-amber-900 dark:text-amber-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-amber-200 dark:bg-amber-800/80 font-bold">演示示例</span>
                <span>当前显示为预设体验星盘，非您的个人生辰排盘。</span>
              </div>
              <span className="text-amber-700 dark:text-amber-300">
                可修改上方生辰并点击“排布紫微星盘”推算个人星盘
              </span>
            </div>
          )}

          {/* 星盘核心概要条 */}
          <div className="bg-stone-100 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-4 grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 text-xs">
            <div>
              <span className="text-stone-500 block">四柱干支:</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">{result.basic?.chineseDate}</span>
            </div>
            <div>
              <span className="text-stone-500 block">命主 / 身主:</span>
              <span className="font-bold text-amber-700 dark:text-amber-400 text-sm">{result.basic?.soul} / {result.basic?.body}</span>
            </div>
            <div>
              <span className="text-stone-500 block">五行局:</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">{result.basic?.fiveElementsClass}</span>
            </div>
            <div>
              <span className="text-stone-500 block">命宫 / 身宫 / 来因宫:</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-xs">
                命宫({result.basic?.earthlyBranchOfSoulPalace}位) / 身宫({result.basic?.earthlyBranchOfBodyPalace}位) / 来因({result.basic?.originalPalaceName || '夫妻'}·{result.basic?.earthlyBranchOfOriginalPalace || ''})
              </span>
            </div>
            <div>
              <span className="text-stone-500 block">生肖 / 星座:</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">{result.basic?.zodiac} / {result.basic?.sign}</span>
            </div>
            <div>
              <span className="text-stone-500 block">早晚子时口径:</span>
              <span className="text-stone-600 dark:text-stone-400">{result.rules?.zi_hour_mode ? '早晚子分立' : '标准'}</span>
            </div>
          </div>

          {/* 十二宫位网格与选中详情 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 十二宫网格展示 (按地支顺序或传统宫位) */}
            <div className="lg:col-span-2 space-y-2">
              <div className="flex items-center justify-between text-xs text-stone-500 px-1">
                <span>十二宫位一览 (点击宫位查看三方四正与星曜释义):</span>
                <span className="text-amber-700 dark:text-amber-400">金色高亮为选中宫位及其三方四正</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
                {result.palaces.map(palace => {
                  const isSelected = selectedPalace?.index === palace.index;
                  const inSanFang = isSanFangSiZheng(palace.name);
                  const isMing = palace.name === '命宫';
                  const isShen = palace.isBodyPalace;
                  const isLaiYin = palace.isOriginalPalace;

                  return (
                    <button
                      key={palace.index}
                      onClick={() => setSelectedPalace(palace)}
                      className={`text-left p-3 rounded-lg border transition-all relative ${
                        isSelected
                          ? 'border-amber-600 bg-amber-50 dark:bg-amber-950/40 shadow-sm ring-1 ring-amber-600'
                          : inSanFang
                          ? 'border-amber-300 dark:border-amber-800 bg-amber-50/30 dark:bg-amber-950/20'
                          : 'border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 hover:border-stone-400'
                      }`}
                    >
                      {/* 宫位标头 */}
                      <div className="flex items-center justify-between pb-1 border-b border-stone-100 dark:border-stone-800 mb-1.5">
                        <span className="font-bold text-sm text-stone-800 dark:text-stone-100 flex items-center gap-1">
                          {palace.name}
                          {isMing && <span className="text-[10px] bg-red-100 text-red-700 px-1 rounded font-medium">命</span>}
                          {isShen && <span className="text-[10px] bg-blue-100 text-blue-700 px-1 rounded font-medium">身</span>}
                          {isLaiYin && <span className="text-[10px] bg-purple-100 text-purple-700 px-1 rounded font-medium" title="来因宫（生年天干所在宫位）">来因</span>}
                        </span>
                        <span className="text-xs text-stone-400 font-mono">
                          {palace.heavenlyStem}{palace.earthlyBranch}
                        </span>
                      </div>

                      {/* 主星列表 */}
                      <div className="space-y-1 min-h-[44px]">
                        {palace.majorStars.length > 0 ? (
                          palace.majorStars.map((star, sIdx) => (
                            <div key={sIdx} className="flex items-center justify-between text-xs">
                              <span className="font-semibold text-stone-800 dark:text-stone-200">{star.name}</span>
                              <div className="flex items-center gap-1">
                                {star.brightness && (
                                  <span className="text-[10px] text-stone-400">({star.brightness})</span>
                                )}
                                {star.mutagen && (
                                  <span className="text-[10px] bg-amber-600 text-white font-bold px-1 rounded">
                                    {star.mutagen}
                                  </span>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <span className="text-xs text-stone-400 italic">借对宫星</span>
                        )}
                      </div>

                      {/* 大限岁数 */}
                      {palace.decadal && (
                        <div className="mt-2 pt-1 border-t border-stone-100 dark:border-stone-800/60 flex items-center justify-between text-[11px] text-stone-400">
                          <span>大限: {palace.decadal.range[0]}-{palace.decadal.range[1]}</span>
                          <span>{palace.changsheng12}</span>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 选中宫位深度详解与三方四正 */}
            <div className="bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-5 space-y-4">
              {selectedPalace ? (
                <>
                  <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-stone-800">
                    <div>
                      <h3 className="text-lg font-bold text-stone-800 dark:text-stone-100 flex items-center gap-2">
                        {selectedPalace.name} ({selectedPalace.heavenlyStem}{selectedPalace.earthlyBranch})
                      </h3>
                      <p className="text-xs text-stone-500">
                        {selectedPalace.name === '命宫' ? '本命核心（命宫）' : selectedPalace.isOriginalPalace ? '来因宫位（飞星四化根基）' : selectedPalace.isBodyPalace ? '身宫宿位（后天依托）' : '人事宫位'} ｜ 长生状态：{selectedPalace.changsheng12} ｜ 博士十二神：{selectedPalace.boshi12}
                      </p>
                    </div>
                    {selectedPalace.decadal && (
                      <span className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 px-2 py-1 rounded font-medium">
                        大限 {selectedPalace.decadal.range[0]}-{selectedPalace.decadal.range[1]} 岁
                      </span>
                    )}
                  </div>

                  {/* 三方四正网络 */}
                  <div className="bg-white dark:bg-stone-800/60 p-3 rounded border border-stone-200 dark:border-stone-700/60 space-y-1.5 text-xs">
                    <span className="font-semibold text-stone-700 dark:text-stone-300 block flex items-center gap-1">
                      <ArrowRightLeft className="w-3.5 h-3.5 text-amber-600" />
                      三方四正对映宫位:
                    </span>
                    <div className="grid grid-cols-3 gap-2 text-stone-600 dark:text-stone-400 pt-1">
                      <div className="bg-stone-50 dark:bg-stone-800 p-1.5 rounded">
                        <span className="text-stone-400 block text-[10px]">正对宫(六冲)</span>
                        <span className="font-medium text-amber-700 dark:text-amber-400">{selectedPalace.sanFangSiZheng?.opposite || '无'}</span>
                      </div>
                      <div className="bg-stone-50 dark:bg-stone-800 p-1.5 rounded">
                        <span className="text-stone-400 block text-[10px]">三合宫一</span>
                        <span className="font-medium text-stone-700 dark:text-stone-300">{selectedPalace.sanFangSiZheng?.trine1 || '无'}</span>
                      </div>
                      <div className="bg-stone-50 dark:bg-stone-800 p-1.5 rounded">
                        <span className="text-stone-400 block text-[10px]">三合宫二</span>
                        <span className="font-medium text-stone-700 dark:text-stone-300">{selectedPalace.sanFangSiZheng?.trine2 || '无'}</span>
                      </div>
                    </div>
                  </div>

                  {/* 宫内星曜详情 */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-stone-600 dark:text-stone-400">坐守星曜:</h4>
                    <div className="space-y-1.5">
                      {selectedPalace.majorStars.map((star, sIdx) => {
                        const cult = result.star_cultural_info?.[star.name];
                        return (
                          <div key={sIdx} className="bg-white dark:bg-stone-800 p-2.5 rounded border border-stone-200 dark:border-stone-700 text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-stone-800 dark:text-stone-100 text-sm flex items-center gap-1.5">
                                {star.name}
                                {star.mutagen && (
                                  <span className="text-xs bg-amber-600 text-white px-1.5 py-0.5 rounded">
                                    生年化{star.mutagen}
                                  </span>
                                )}
                              </span>
                              <span className="text-stone-400">庙旺: {star.brightness || '平'}</span>
                            </div>
                            {cult && (
                              <div className="text-stone-600 dark:text-stone-300 space-y-0.5 pt-1">
                                <p><span className="text-stone-400">特质:</span> {cult.keywords}</p>
                                <p className="text-amber-800 dark:text-amber-300"><span className="text-stone-400">自省:</span> {cult.reflection}</p>
                              </div>
                            )}
                          </div>
                        );
                      })}
                      {selectedPalace.minorStars.length > 0 && (
                        <div className="text-xs text-stone-500 pt-1">
                          <span>辅煞星: </span>
                          {selectedPalace.minorStars.map(s => s.name + (s.mutagen ? `(化${s.mutagen})` : '')).join('、')}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 流年/大限当前状态 */}
                  {result.horoscope && (
                    <div className="bg-amber-50/40 dark:bg-stone-800/40 p-3 rounded border border-amber-200 dark:border-stone-700 text-xs space-y-1">
                      <span className="font-semibold text-stone-700 dark:text-stone-300">
                        流年 ({result.horoscope.targetDate}):
                      </span>
                      <p className="text-stone-600 dark:text-stone-400">
                        流年岁建: {result.horoscope.yearly?.name}（{result.horoscope.yearly?.heavenlyStem}{result.horoscope.yearly?.earthlyBranch}）｜ 虚岁: {result.horoscope.age?.nominalAge}岁
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="py-8 text-center text-xs text-stone-400">请选择左侧宫位查看详情</div>
              )}

              {/* 动作按钮条 */}
              <div className="pt-2 flex flex-col gap-2">
                <button
                  onClick={handleFetchBuiltinReading}
                  disabled={readingLoading}
                  className="w-full py-2 bg-stone-800 hover:bg-stone-900 text-white rounded text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  {readingLoading ? '正在检索典籍...' : '生成内置传统研读 (免 API)'}
                </button>
                <button
                  onClick={handleSaveRecord}
                  disabled={savedSuccess}
                  className="w-full py-2 border border-stone-300 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 rounded text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                >
                  {savedSuccess ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                      <span className="text-green-600">已保存至本地记录</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-3.5 h-3.5" />
                      保存星盘手记
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 内置研读展示区 */}
          {builtinReading && (
            <div className="bg-amber-50/30 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-stone-800">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-amber-700 dark:text-amber-500" />
                  <h3 className="font-bold text-stone-800 dark:text-stone-100 text-base">{builtinReading.title}</h3>
                </div>
                <span className="text-xs bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 px-2 py-0.5 rounded">
                  {builtinReading.reading_label}
                </span>
              </div>

              <div className="space-y-4 text-sm text-stone-700 dark:text-stone-300">
                {builtinReading.sections.map((sec, idx) => (
                  <div key={idx} className="space-y-1">
                    <h4 className="font-bold text-stone-800 dark:text-stone-200 text-xs">{sec.heading}</h4>
                    <p className="leading-relaxed whitespace-pre-line text-xs sm:text-sm pl-2 border-l-2 border-amber-600/40">
                      {sec.content}
                    </p>
                  </div>
                ))}
              </div>

              {/* 典籍出处 */}
              {builtinReading.citations.length > 0 && (
                <div className="pt-3 border-t border-stone-200 dark:border-stone-800 text-xs text-stone-500 space-y-1">
                  <span className="font-semibold block text-stone-600 dark:text-stone-400">考据出处与适用说明:</span>
                  {builtinReading.citations.map((c, cIdx) => (
                    <div key={cIdx} className="bg-white dark:bg-stone-800 p-2 rounded border border-stone-200 dark:border-stone-700">
                      <span className="font-medium text-amber-700 dark:text-amber-400">[{c.book}·{c.chapter}]</span>: {c.quote}
                      <p className="text-[11px] text-stone-400 mt-0.5">{c.applicability}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 理性知止防线声明 */}
          <div className="text-xs text-stone-400 p-3 bg-stone-50 dark:bg-stone-900/50 rounded border border-stone-200 dark:border-stone-800 leading-relaxed">
            <span className="font-semibold text-stone-500">【防线说明】</span> {result.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
