// frontend/src/components/QimenCalculator.tsx - 奇门遁甲九宫排盘与运筹研读组件

import React, { useState } from 'react';
import {
  Grid3X3,
  Clock,
  BookOpen,
  Save,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { calculateQimenAPI, fetchBuiltinReadingAPI, createRecordAPI } from '../api';
import type { QimenResult, QimenPalace, BuiltinReadingResponse } from '../types';

export const QimenCalculator: React.FC = () => {
  const now = new Date();
  const [year, setYear] = useState<number>(now.getFullYear());
  const [month, setMonth] = useState<number>(now.getMonth() + 1);
  const [day, setDay] = useState<number>(now.getDate());
  const [hour, setHour] = useState<number>(now.getHours());
  const [minute, setMinute] = useState<number>(now.getMinutes());
  const [topic, setTopic] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QimenResult | null>(null);
  const [selectedPalace, setSelectedPalace] = useState<QimenPalace | null>(null);

  const [builtinReading, setBuiltinReading] = useState<BuiltinReadingResponse | null>(null);
  const [readingLoading, setReadingLoading] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  // 一键同步为此时此刻 (冻结输入)
  const setToCurrentTime = () => {
    const d = new Date();
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setDay(d.getDate());
    setHour(d.getHours());
    setMinute(d.getMinutes());
    setResult(null);
    setBuiltinReading(null);
    setSelectedPalace(null);
    setError(null);
  };

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setSavedSuccess(false);
    setBuiltinReading(null);
    try {
      const res = await calculateQimenAPI({
        year,
        month,
        day,
        hour,
        minute,
        topic
      });
      setResult(res);
      if (res.palaces && res.palaces.length > 0) {
        // 默认选中值使门或值符所在宫位
        const defaultPalace = res.palaces.find(p => p.isZhiShi) || res.palaces.find(p => p.isZhiFu) || res.palaces[0];
        setSelectedPalace(defaultPalace);
      }
    } catch (err: any) {
      setError(err?.message || '奇门排盘失败，请核验输入时间');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchBuiltinReading = async () => {
    if (!result) return;
    setReadingLoading(true);
    try {
      const res = await fetchBuiltinReadingAPI({
        record_type: 'qimen',
        calculation: result,
        topic: topic || '奇门时家转盘研习'
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
      const title = `奇门遁甲·【${result.meta.dun}${result.meta.juNumber}局·${result.meta.zhiShiDoor}值使】（${result.input.solar_date || ''}）`;
      await createRecordAPI({
        record_type: 'qimen',
        title,
        topic: topic || '奇门时家运筹研读',
        tags: ['奇门遁甲', result.meta.dun, `${result.meta.juNumber}局`, result.meta.zhiShiDoor, result.meta.solarTerm],
        params: {
          year,
          month,
          day,
          hour,
          minute,
          topic
        },
        calculation_result: result,
        review_data: {
          original_thought: '探讨时方运筹、知止避险与客观现实条理',
          observation_window: '近期行事观察'
        }
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      setError(err?.message || '保存手记记录失败');
    }
  };

  // 经典九宫南上北下顺序:
  // 第一排: 4 (巽四·东南), 9 (离九·正南), 2 (坤二·西南)
  // 第二排: 3 (震三·正东), 5 (中五·中央), 7 (兑七·正西)
  // 第三排: 8 (艮八·东北), 1 (坎一·正北), 6 (乾六·西北)
  const NINE_GRID_LAYOUT = [
    [4, 9, 2],
    [3, 5, 7],
    [8, 1, 6]
  ];

  const getPalaceByNumber = (num: number): QimenPalace | undefined => {
    return result?.palaces.find(p => p.palaceNumber === num);
  };

  return (
    <div className="space-y-6">
      {/* 顶部标题与原则卡片 */}
      <div className="bg-amber-50/50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200 dark:border-stone-800">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2 text-stone-800 dark:text-stone-100">
              <Grid3X3 className="w-5 h-5 text-amber-700 dark:text-amber-500" />
              时家转盘奇门遁甲 · 运筹研读
            </h2>
            <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">
              遵循经典拆补定局与洛书九宫南上北下排盘规则。天盘、地盘、八门、九星、八神完备。纯本地免 API 运行。
            </p>
          </div>
          <button
            onClick={setToCurrentTime}
            className="px-3 py-1.5 text-xs border border-stone-300 dark:border-stone-700 rounded hover:bg-stone-100 dark:hover:bg-stone-800 flex items-center gap-1.5 self-start sm:self-auto"
          >
            <Clock className="w-3.5 h-3.5 text-amber-700" />
            设为此时此刻 (冻结时间)
          </button>
        </div>

        {/* 输入参数表单 */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-4">
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">公历年</label>
            <input
              type="number"
              min={1900}
              max={2100}
              value={year}
              onChange={e => setYear(parseInt(e.target.value) || 2026)}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">公历月</label>
            <input
              type="number"
              min={1}
              max={12}
              value={month}
              onChange={e => setMonth(parseInt(e.target.value) || 1)}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">公历日</label>
            <input
              type="number"
              min={1}
              max={31}
              value={day}
              onChange={e => setDay(parseInt(e.target.value) || 1)}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">小时 (0-23)</label>
            <input
              type="number"
              min={0}
              max={23}
              value={hour}
              onChange={e => setHour(parseInt(e.target.value) || 0)}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">分钟 (0-59)</label>
            <input
              type="number"
              min={0}
              max={59}
              value={minute}
              onChange={e => setMinute(parseInt(e.target.value) || 0)}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-stone-600 dark:text-stone-400 mb-1">求测/反思主题</label>
            <input
              type="text"
              placeholder="可选主题"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              className="w-full text-sm bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded px-2.5 py-1.5"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 mt-3 border-t border-stone-200 dark:border-stone-800">
          <div className="text-xs text-stone-500">
            <span>定局法：时家转盘拆补法 ｜ 寄宫：中五寄坤二 ｜ 方位：南上北下</span>
          </div>
          <button
            onClick={handleCalculate}
            disabled={loading}
            className="px-5 py-2 bg-amber-700 hover:bg-amber-800 text-white rounded font-medium shadow-sm transition-colors flex items-center gap-2"
          >
            {loading ? <span className="animate-spin">⏳</span> : <Grid3X3 className="w-4 h-4" />}
            生成奇门盘面
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 完整奇门盘面 */}
      {result && result.palaces && (
        <div className="space-y-6">
          {/* 局况核心概要条 */}
          <div className="bg-stone-100 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs">
            <div>
              <span className="text-stone-500 block">阴阳遁 / 局数:</span>
              <span className="font-bold text-amber-700 dark:text-amber-400 text-sm">
                {result.meta.dun} {result.meta.juNumber}局 · {result.meta.yuan}
              </span>
            </div>
            <div>
              <span className="text-stone-500 block">节气与时刻:</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">
                {result.meta.solarTerm} ({result.input.solar_date})
              </span>
            </div>
            <div>
              <span className="text-stone-500 block">值符星 (落宫):</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">
                {result.meta.zhiFuStar} (落{result.meta.zhiFuPalace}宫)
              </span>
            </div>
            <div>
              <span className="text-stone-500 block">值使门 (落宫):</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">
                {result.meta.zhiShiDoor} (落{result.meta.zhiShiPalace}宫)
              </span>
            </div>
            <div>
              <span className="text-stone-500 block">时辰空亡:</span>
              <span className="font-bold text-stone-800 dark:text-stone-200 text-sm">
                {result.meta.kongWang.length > 0 ? result.meta.kongWang.join('、') : '无'}
              </span>
            </div>
            <div>
              <span className="text-stone-500 block">天乙贵人星:</span>
              <span className="text-stone-700 dark:text-stone-300 text-sm">
                {result.meta.tianYiStar || '天禽'} (落{result.meta.tianYiPalace || 2}宫)
              </span>
            </div>
          </div>

          {/* 3x3 洛书九宫盘面与右侧详情卡 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 九宫格 (南上北下) */}
            <div className="lg:col-span-2 space-y-2">
              <div className="flex items-center justify-between text-xs text-stone-500 px-1">
                <span>洛书九宫格局 (南上北下，点击宫位研读):</span>
                <span>离九南 ｜ 坎一北 ｜ 震三东 ｜ 兑七西</span>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {NINE_GRID_LAYOUT.flat().map(palaceNum => {
                  const p = getPalaceByNumber(palaceNum);
                  if (!p) return null;

                  const isSelected = selectedPalace?.palaceNumber === p.palaceNumber;
                  const isCenter = p.palaceNumber === 5;

                  return (
                    <button
                      key={p.palaceNumber}
                      onClick={() => setSelectedPalace(p)}
                      className={`text-left p-3 rounded-lg border transition-all relative min-h-[120px] flex flex-col justify-between ${
                        isSelected
                          ? 'border-amber-600 bg-amber-50 dark:bg-amber-950/40 shadow-sm ring-1 ring-amber-600'
                          : isCenter
                          ? 'border-stone-200 dark:border-stone-800 bg-stone-100/50 dark:bg-stone-900/60'
                          : 'border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 hover:border-stone-400'
                      }`}
                    >
                      {/* 宫首信息 */}
                      <div className="flex items-center justify-between pb-1 border-b border-stone-100 dark:border-stone-800 w-full text-xs">
                        <span className="font-bold text-stone-800 dark:text-stone-100 flex items-center gap-1">
                          {p.fullName}
                          {p.isZhiFu && <span className="text-[10px] bg-red-100 text-red-700 px-1 rounded">符</span>}
                          {p.isZhiShi && <span className="text-[10px] bg-blue-100 text-blue-700 px-1 rounded">使</span>}
                          {p.isKongWang && <span className="text-[10px] bg-purple-100 text-purple-700 px-1 rounded">空</span>}
                        </span>
                        <span className="text-[11px] text-stone-400">{p.direction}</span>
                      </div>

                      {/* 盘面四层: 神 / 星 / 门 / 干 */}
                      <div className="py-1.5 space-y-1 text-xs w-full">
                        <div className="flex items-center justify-between text-stone-600 dark:text-stone-300">
                          <span className="text-amber-700 dark:text-amber-400 font-medium">八神: {p.god || '―'}</span>
                          <span className="text-stone-400 text-[11px]">地神: {p.diGod || '―'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-stone-800 dark:text-stone-200">九星: {p.star || '―'}</span>
                          <span className="font-semibold text-amber-800 dark:text-amber-300">八门: {p.door || '―'}</span>
                        </div>
                        <div className="flex items-center justify-between pt-1 border-t border-stone-100 dark:border-stone-800/60 text-xs">
                          <span className="text-stone-700 dark:text-stone-300 font-mono">
                            天盘: <span className="font-bold text-amber-700">{p.tianPanGan || p.earthStem || '―'}</span>
                          </span>
                          <span className="text-stone-700 dark:text-stone-300 font-mono">
                            地盘: <span className="font-bold text-stone-700">{p.diPanGan || p.skyStem || '―'}</span>
                          </span>
                        </div>
                      </div>

                      {/* 克应标记摘要 */}
                      <div className="text-[10px] text-stone-400 truncate">
                        {p.keYing && p.keYing.length > 0 ? (
                          <span className={p.keYing[0].type === '吉' ? 'text-green-600' : p.keYing[0].type === '大凶' ? 'text-red-600' : 'text-stone-500'}>
                            [{p.keYing[0].name}] {p.keYing[0].key}
                          </span>
                        ) : (
                          '平'
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 选中宫位深度详解卡 */}
            <div className="bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-lg p-5 space-y-4">
              {selectedPalace ? (
                <>
                  <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-stone-800">
                    <div>
                      <h3 className="text-lg font-bold text-stone-800 dark:text-stone-100 flex items-center gap-2">
                        {selectedPalace.fullName} ({selectedPalace.direction})
                      </h3>
                      <p className="text-xs text-stone-500">
                        五行属{selectedPalace.element} ｜ 卦象：{selectedPalace.gua}
                        {selectedPalace.isZhiFu && ' ｜ 值符星所在'}
                        {selectedPalace.isZhiShi && ' ｜ 值使门所在'}
                        {selectedPalace.isKongWang && ' ｜ 时辰空亡'}
                      </p>
                    </div>
                  </div>

                  {/* 门星神三才配置 */}
                  <div className="space-y-2 text-xs">
                    <div className="bg-white dark:bg-stone-800 p-2.5 rounded border border-stone-200 dark:border-stone-700 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-stone-800 dark:text-stone-100">
                          门：{selectedPalace.door || '中宫无门'} ({selectedPalace.doorElement || ''})
                        </span>
                        {selectedPalace.isZhiShi && <span className="text-[10px] bg-blue-100 text-blue-700 px-1 rounded">值使令官</span>}
                      </div>
                      {result.door_cultural_info?.[selectedPalace.door] && (
                        <p className="text-stone-600 dark:text-stone-300">
                          {result.door_cultural_info[selectedPalace.door].nature}。{result.door_cultural_info[selectedPalace.door].reflection}
                        </p>
                      )}
                    </div>

                    <div className="bg-white dark:bg-stone-800 p-2.5 rounded border border-stone-200 dark:border-stone-700 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-stone-800 dark:text-stone-100">
                          星：{selectedPalace.star} ({selectedPalace.starElement || ''})
                        </span>
                        {selectedPalace.isZhiFu && <span className="text-[10px] bg-red-100 text-red-700 px-1 rounded">值符主帅</span>}
                      </div>
                      {result.star_cultural_info?.[selectedPalace.star] && (
                        <p className="text-stone-600 dark:text-stone-300">
                          {result.star_cultural_info[selectedPalace.star].character}。{result.star_cultural_info[selectedPalace.star].reflection}
                        </p>
                      )}
                    </div>

                    <div className="bg-white dark:bg-stone-800 p-2.5 rounded border border-stone-200 dark:border-stone-700">
                      <span className="font-bold text-stone-800 dark:text-stone-100">神：{selectedPalace.god || '无'}</span>
                      <span className="text-stone-400 ml-2">(地八神：{selectedPalace.diGod || '无'})</span>
                    </div>
                  </div>

                  {/* 十干克应格局 */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-stone-600 dark:text-stone-400">十干克应与格局:</h4>
                    {selectedPalace.keYing && selectedPalace.keYing.length > 0 ? (
                      selectedPalace.keYing.map((k, kIdx) => (
                        <div key={kIdx} className="bg-white dark:bg-stone-800 p-2.5 rounded border border-stone-200 dark:border-stone-700 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-stone-800 dark:text-stone-100">
                              【{k.name}】({k.key})
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                              k.type.includes('吉') ? 'bg-green-100 text-green-700' : k.type.includes('凶') ? 'bg-red-100 text-red-700' : 'bg-stone-100 text-stone-600'
                            }`}>
                              {k.type}
                            </span>
                          </div>
                          <p className="text-stone-600 dark:text-stone-300 leading-relaxed">
                            {k.desc}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-stone-400 italic">此宫无特殊显著克应格局，阴阳适中。</div>
                    )}
                  </div>
                </>
              ) : (
                <div className="py-8 text-center text-xs text-stone-400">请选择左侧九宫查看详情</div>
              )}

              {/* 操作按钮条 */}
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
                      保存奇门手记
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
