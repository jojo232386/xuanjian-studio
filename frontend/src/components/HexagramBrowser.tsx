// frontend/src/components/HexagramBrowser.tsx - 六十四卦关系网与典籍研读双栏 (F05)

import React, { useState, useEffect } from 'react';
import type { HexagramSummary, HexagramNode } from '../types';
import { fetchHexagramsAPI, fetchHexagramDetailAPI } from '../api';
import { Search, BookOpen, ArrowRight, RotateCw, GitCommit, Shield, Info, ArrowLeftRight } from 'lucide-react';

export const HexagramBrowser: React.FC = () => {
  const [query, setQuery] = useState('');
  const [hexagrams, setHexagrams] = useState<HexagramSummary[]>([]);
  const [selectedHexId, setSelectedHexId] = useState<number | null>(63); // 默认选 63 既济卦
  const [hexDetail, setHexDetail] = useState<HexagramNode | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  useEffect(() => {
    loadHexagramList(query);
  }, []);

  useEffect(() => {
    if (selectedHexId !== null) {
      loadHexDetail(selectedHexId);
    }
  }, [selectedHexId]);

  const loadHexagramList = async (q: string) => {
    setIsLoadingList(true);
    try {
      const res = await fetchHexagramsAPI(q);
      setHexagrams(res.hexagrams);
    } catch (e: any) {
      console.error('加载卦象列表失败:', e);
    } finally {
      setIsLoadingList(false);
    }
  };

  const loadHexDetail = async (id: number) => {
    setIsLoadingDetail(true);
    try {
      const node = await fetchHexagramDetailAPI(id);
      setHexDetail(node);
    } catch (e: any) {
      console.error('加载卦象详情失败:', e);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadHexagramList(query);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* 搜索与说明 */}
      <div className="card-xuan p-4 bg-[var(--xuanzhi-light)] flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="seal-tag">易象</span>
            <h3 className="font-song text-lg font-bold text-[var(--ink)]">六十四卦象数全息关系网</h3>
          </div>
          <p className="text-xs text-[var(--ink-muted)]">
            本卦 · 错卦（对卦）· 综卦（反卦）· 互卦（重卦中爻）· 六爻之卦演化 · 经典双栏研读
          </p>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-2.5 top-2.5 text-[var(--ink-muted)]" size={14} />
            <input
              type="text"
              placeholder="搜索卦名/编号/卦辞..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[var(--xuanzhi)] border border-[var(--border)] rounded text-[var(--ink)]"
            />
          </div>
          <button type="submit" className="btn-antique px-3 py-1.5 text-xs">
            检索
          </button>
        </form>
      </div>

      {/* 主布局：左侧卦象选择器（网格），右侧关系网与双栏研读 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 左侧：六十四卦速览索引 (4列/12) */}
        <div className="lg:col-span-4 card-xuan p-4 bg-[var(--xuanzhi-light)] flex flex-col h-[650px]">
          <div className="text-xs font-bold text-[var(--ink-muted)] mb-3 pb-2 border-b border-[var(--border)] flex items-center justify-between">
            <span>文王卦序索引 ({hexagrams.length} 卦)</span>
            {query && (
              <button
                onClick={() => {
                  setQuery('');
                  loadHexagramList('');
                }}
                className="text-[10px] text-[var(--daiqing)] hover:underline"
              >
                重置检索
              </button>
            )}
          </div>

          <div className="overflow-y-auto flex-1 space-y-1.5 pr-1">
            {isLoadingList ? (
              <div className="text-center py-10 text-xs text-[var(--ink-muted)]">加载索引中...</div>
            ) : hexagrams.length === 0 ? (
              <div className="text-center py-10 text-xs text-[var(--ink-muted)]">未找到匹配卦象</div>
            ) : (
              hexagrams.map((h) => {
                const isSelected = selectedHexId === h.number;
                return (
                  <button
                    key={h.number}
                    onClick={() => setSelectedHexId(h.number)}
                    className={`w-full text-left p-2.5 rounded border transition flex items-center justify-between ${
                      isSelected
                        ? 'border-[var(--daiqing)] bg-[var(--daiqing)]/10 shadow-sm'
                        : 'border-[var(--border)] bg-[var(--xuanzhi)] hover:border-[var(--daiqing)]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 text-right font-mono text-[11px] text-[var(--ink-muted)]">
                        {h.number}.
                      </span>
                      <span className="font-serif font-bold text-sm text-[var(--ink)]">
                        {h.name}
                      </span>
                      <span className="text-[11px] text-[var(--ink-muted)]">
                        ({h.full_name})
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-[10px] text-[var(--ink-subtle)]">
                      <span>{h.upper_trigram}/{h.lower_trigram}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* 右侧：单卦详情、全息关系网与双栏研读 (8列/12) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {isLoadingDetail ? (
            <div className="card-xuan p-12 text-center text-xs text-[var(--ink-muted)] bg-[var(--xuanzhi-light)]">
              正在展开卦象关系网...
            </div>
          ) : !hexDetail ? (
            <div className="card-xuan p-12 text-center text-xs text-[var(--ink-muted)] bg-[var(--xuanzhi-light)]">
              请在左侧选择卦象以研读
            </div>
          ) : (
            <>
              {/* 核心卦体与上下卦 */}
              <div className="card-xuan p-5 bg-[var(--xuanzhi-light)]">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-[var(--border)]">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-full bg-[var(--daiqing)] text-white flex items-center justify-center font-bold text-sm font-mono">
                      {hexDetail.number}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl font-serif font-bold text-[var(--ink)]">
                          {hexDetail.name}卦 · {hexDetail.full_name}
                        </h3>
                      </div>
                      <p className="text-xs text-[var(--ink-muted)]">
                        上卦：{hexDetail.upper_trigram.name} ({hexDetail.upper_trigram.nature} · {hexDetail.upper_trigram.symbol}) ｜ 下卦：{hexDetail.lower_trigram.name} ({hexDetail.lower_trigram.nature} · {hexDetail.lower_trigram.symbol})
                      </p>
                    </div>
                  </div>

                  {/* 序卦前后快捷跳转 */}
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setSelectedHexId(hexDetail.relationships.prev_hexagram.number)}
                      className="px-2 py-1 text-xs border border-[var(--border)] rounded bg-[var(--xuanzhi)] text-[var(--ink)] hover:border-[var(--daiqing)]"
                      title="前一序卦"
                    >
                      ← {hexDetail.relationships.prev_hexagram.name}
                    </button>
                    <button
                      onClick={() => setSelectedHexId(hexDetail.relationships.next_hexagram.number)}
                      className="px-2 py-1 text-xs border border-[var(--border)] rounded bg-[var(--xuanzhi)] text-[var(--ink)] hover:border-[var(--daiqing)]"
                      title="后一序卦"
                    >
                      {hexDetail.relationships.next_hexagram.name} →
                    </button>
                  </div>
                </div>

                {/* 六爻视觉符号体 */}
                <div className="flex items-center justify-center gap-8 py-2 mb-2">
                  <div className="flex flex-col-reverse gap-1.5 items-center">
                    {hexDetail.line_structures.map((ls) => (
                      <div key={ls.index} className="flex items-center gap-2">
                        <span className="w-8 text-[11px] text-[var(--ink-muted)] text-right font-song">
                          {ls.name}
                        </span>
                        <div className="flex items-center w-28 justify-center h-4">
                          {ls.bit === 1 ? (
                            <div className="w-full h-2 rounded-sm bg-[var(--daiqing)]" />
                          ) : (
                            <div className="w-full flex items-center justify-between">
                              <div className="w-[45%] h-2 rounded-sm bg-[var(--daiqing)]" />
                              <div className="w-[45%] h-2 rounded-sm bg-[var(--daiqing)]" />
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 核心关系网 (错、综、互) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 错卦 (对卦) */}
                <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] flex flex-col justify-between border-t-2 border-t-rose-500">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold font-song text-rose-700 dark:text-rose-400 flex items-center gap-1">
                        <ArrowLeftRight size={13} />
                        <span>错卦 (对卦)</span>
                      </span>
                      <span className="text-[10px] text-[var(--ink-muted)]">阴阳全变</span>
                    </div>

                    <div className="text-base font-serif font-bold text-[var(--ink)] mb-1">
                      {hexDetail.relationships.opposite.name} ({hexDetail.relationships.opposite.full_name})
                    </div>
                    <p className="text-[11px] text-[var(--ink-muted)] leading-relaxed mb-3">
                      {hexDetail.relationships.opposite.meaning}
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedHexId(hexDetail.relationships.opposite.number)}
                    className="w-full py-1.5 text-xs font-song rounded border border-[var(--border)] bg-[var(--xuanzhi)] text-[var(--ink)] hover:border-[var(--daiqing)] flex items-center justify-center gap-1 transition"
                  >
                    <span>跳转研读 {hexDetail.relationships.opposite.name}</span>
                    <ArrowRight size={12} />
                  </button>
                </div>

                {/* 综卦 (反卦) */}
                <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] flex flex-col justify-between border-t-2 border-t-sky-500">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold font-song text-sky-700 dark:text-sky-400 flex items-center gap-1">
                        <RotateCw size={13} />
                        <span>综卦 (反卦)</span>
                      </span>
                      {hexDetail.relationships.reverse.is_self_reversed ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-800 dark:text-sky-200">正卦自反</span>
                      ) : (
                        <span className="text-[10px] text-[var(--ink-muted)]">上下颠倒</span>
                      )}
                    </div>

                    <div className="text-base font-serif font-bold text-[var(--ink)] mb-1">
                      {hexDetail.relationships.reverse.name} ({hexDetail.relationships.reverse.full_name})
                    </div>
                    <p className="text-[11px] text-[var(--ink-muted)] leading-relaxed mb-3">
                      {hexDetail.relationships.reverse.meaning}
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedHexId(hexDetail.relationships.reverse.number)}
                    className="w-full py-1.5 text-xs font-song rounded border border-[var(--border)] bg-[var(--xuanzhi)] text-[var(--ink)] hover:border-[var(--daiqing)] flex items-center justify-center gap-1 transition"
                  >
                    <span>跳转研读 {hexDetail.relationships.reverse.name}</span>
                    <ArrowRight size={12} />
                  </button>
                </div>

                {/* 互卦 (交互卦) */}
                <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] flex flex-col justify-between border-t-2 border-t-emerald-500">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold font-song text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                        <GitCommit size={13} />
                        <span>互卦 (交互卦)</span>
                      </span>
                      <span className="text-[10px] text-[var(--ink-muted)]">核二三四/三四五</span>
                    </div>

                    <div className="text-base font-serif font-bold text-[var(--ink)] mb-1">
                      {hexDetail.relationships.nuclear.name} ({hexDetail.relationships.nuclear.full_name})
                    </div>
                    <p className="text-[11px] text-[var(--ink-muted)] leading-relaxed mb-3">
                      {hexDetail.relationships.nuclear.meaning}
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedHexId(hexDetail.relationships.nuclear.number)}
                    className="w-full py-1.5 text-xs font-song rounded border border-[var(--border)] bg-[var(--xuanzhi)] text-[var(--ink)] hover:border-[var(--daiqing)] flex items-center justify-center gap-1 transition"
                  >
                    <span>跳转研读 {hexDetail.relationships.nuclear.name}</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              </div>

              {/* 单爻之卦演化 (1-6爻发动) */}
              <div className="card-xuan p-4 bg-[var(--xuanzhi-light)]">
                <div className="flex items-center gap-2 mb-3">
                  <span className="seal-tag">之卦</span>
                  <h4 className="font-song font-bold text-xs text-[var(--ink)]">
                    单爻动变 · 六之卦谱系
                  </h4>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                  {hexDetail.relationships.changes.map((ch) => (
                    <button
                      key={ch.line_index}
                      onClick={() => setSelectedHexId(ch.target_hexagram.number)}
                      className="p-2 rounded border border-[var(--border)] bg-[var(--xuanzhi)] text-center transition hover:border-[var(--daiqing)] hover:shadow-sm"
                    >
                      <div className="text-[10px] text-[var(--zhusha)] font-bold">
                        {ch.line_name}动
                      </div>
                      <div className="text-xs font-serif font-bold text-[var(--ink)] my-0.5">
                        之 {ch.target_hexagram.name}
                      </div>
                      <div className="text-[9px] text-[var(--ink-muted)]">
                        {ch.target_hexagram.full_name}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* 典籍研读双栏对照卡片 */}
              <div className="card-xuan p-5 bg-[var(--xuanzhi-light)]">
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-[var(--border)]">
                  <span className="seal-tag">研读</span>
                  <h4 className="font-song font-bold text-[var(--ink)]">
                    典籍原文与义理考据双栏对照
                  </h4>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* 左栏：古籍传世原文 */}
                  <div className="p-4 rounded-lg bg-[var(--xuanzhi)] border border-[var(--border)] flex flex-col gap-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-[var(--daiqing)] pb-2 border-b border-[var(--border)]">
                      <BookOpen size={14} />
                      <span>《周易》传世原文</span>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-[var(--ink-muted)] mb-1">【卦辞】</div>
                      <p className="text-sm font-serif text-[var(--ink)] leading-relaxed">
                        {hexDetail.texts.guaci}
                      </p>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-[var(--ink-muted)] mb-1">【大象传】</div>
                      <p className="text-sm font-serif text-[var(--ink)] leading-relaxed">
                        {hexDetail.texts.xiangzhuan}
                      </p>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-[var(--ink-muted)] mb-1">【彖传】</div>
                      <p className="text-xs font-serif text-[var(--ink-muted)] leading-relaxed">
                        {hexDetail.texts.tuanzhuan}
                      </p>
                    </div>
                  </div>

                  {/* 右栏：义理考据与现实知止 */}
                  <div className="p-4 rounded-lg bg-[var(--xuanzhi-card)] border border-[var(--border)] flex flex-col gap-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-[var(--zhusha)] pb-2 border-b border-[var(--border)]">
                      <Shield size={14} />
                      <span>义理考据与知止审视</span>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-[var(--ink-muted)] mb-1">【象数修己】</div>
                      <p className="text-xs text-[var(--ink)] leading-relaxed">
                        《大象传》以上下卦象启迪君子修为。{hexDetail.name}卦之启示在于：“{hexDetail.texts.xiangzhuan}”。象由心生，行由德立。
                      </p>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-[var(--ink-muted)] mb-1">【换位与反思】</div>
                      <p className="text-xs text-[var(--ink)] leading-relaxed">
                        结合错卦【{hexDetail.relationships.opposite.name}】与综卦【{hexDetail.relationships.reverse.name}】，提醒研读者不执于一端。从极端对立面察察所忽，从后来者视角预为谋始。
                      </p>
                    </div>

                    <div className="mt-auto p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-[11px] text-[var(--ink-muted)] leading-relaxed flex items-start gap-2">
                      <Info size={13} className="text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
                      <span>卦象作为古代哲学隐喻，旨在启迪慎思；现实决断切忌机械代入，始终以客观证据与法律现金流为最高依据。</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
