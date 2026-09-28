// frontend/src/views/ArchiveView.tsx - 典藏：古籍短读、术语词典与本地手记复盘 (F03)

import { useState, useEffect } from 'react';
import type { ClassicReading, GlossaryTerm } from '../types';
import { fetchClassicsAPI, exportDataAPI } from '../api';
import { BookOpen, Search, FileDown, Shield, Database, Bookmark, Network } from 'lucide-react';
import { LocalRecordsManager } from '../components/LocalRecordsManager';
import { HexagramBrowser } from '../components/HexagramBrowser';
import { DaodejingReader } from '../components/DaodejingReader';

export const ArchiveView = ({initialTab = 'classics'}: {initialTab?: 'classics'|'records'}) => {
  const [archiveTab, setArchiveTab] = useState<'classics' | 'daodejing' | 'hexagrams' | 'records'>(initialTab);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [readings, setReadings] = useState<ClassicReading[]>([]);
  const [glossary, setGlossary] = useState<GlossaryTerm[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [allowPersistence, setAllowPersistence] = useState(false);

  useEffect(() => {
    loadClassics();
    const storedPref = localStorage.getItem('xuanjian_allow_persist');
    if (storedPref === 'true') {
      setAllowPersistence(true);
    }
  }, []);

  const loadClassics = async () => {
    setIsLoading(true);
    try {
      const res = await fetchClassicsAPI(query, category);
      setReadings(res.readings);
      setGlossary(res.glossary);
    } catch (e: any) {
      console.error('载入典藏失败:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePersistence = (checked: boolean) => {
    setAllowPersistence(checked);
    localStorage.setItem('xuanjian_allow_persist', checked ? 'true' : 'false');
  };

  const handleExportJSON = async () => {
    try {
      const bundle = await exportDataAPI('bundle', 'json', {
        readings_count: readings.length,
        glossary_count: glossary.length,
        allow_persistence: allowPersistence,
        readings,
        glossary
      });
      const blob = new Blob([bundle], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `玄鉴典藏备份_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`导出 JSON 失败: ${e.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto py-4">
      {/* 顶部主副标签切换 */}
      <div className="card-xuan p-4 bg-[var(--xuanzhi-light)] flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="seal-tag">典藏</span>
            <h2 className="font-song text-xl font-bold text-[var(--ink)]">手记与经典</h2>
          </div>
          <p className="text-xs text-[var(--ink-muted)]">
            留住此刻的思考，也读读前人的文字。
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1 bg-[var(--border-light)] p-1 rounded border border-[var(--border)]">
          <button
            onClick={() => setArchiveTab('classics')}
            className={`px-3 min-h-10 py-2 text-sm font-song rounded transition flex items-center gap-1.5 ${
              archiveTab === 'classics'
                ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            <BookOpen size={13} />
            <span>经典与词典</span>
          </button>
          <button
            onClick={() => setArchiveTab('daodejing')}
            className={`px-3 min-h-10 py-2 text-sm font-song rounded transition flex items-center gap-1.5 ${
              archiveTab === 'daodejing'
                ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            <Bookmark size={13} />
            <span>道德经</span>
          </button>
          <button
            onClick={() => setArchiveTab('hexagrams')}
            className={`px-3 min-h-10 py-2 text-sm font-song rounded transition flex items-center gap-1.5 ${
              archiveTab === 'hexagrams'
                ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            <Network size={13} />
            <span>六十四卦</span>
          </button>
          <button
            onClick={() => setArchiveTab('records')}
            className={`px-3 min-h-10 py-2 text-sm font-song rounded transition flex items-center gap-1.5 ${
              archiveTab === 'records'
                ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            <Database size={13} />
            <span>我的手记</span>
          </button>
        </div>
      </div>

      {/* 选项一：本地 SQLite 手记与事后复盘 */}
      {archiveTab === 'records' && (
        <LocalRecordsManager />
      )}

      {/* 选项二：六十四卦全息关系网与双栏研读 */}
      {archiveTab === 'hexagrams' && (
        <HexagramBrowser />
      )}

      {/* 选项三：道德经研读 */}
      {archiveTab === 'daodejing' && (
        <DaodejingReader />
      )}

      {/* 选项四：经传短读与四术词典 */}
      {archiveTab === 'classics' && (
        <div className="flex flex-col gap-6">
          {/* 典籍检索与分类筛选 */}
          <div className="card-xuan p-5 bg-[var(--xuanzhi-card)] flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 w-full md:w-auto">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadClassics()}
                placeholder="搜索典籍名篇或四术术语（如：既济、十神、化忌、天冲星、知止）..."
                className="input-xuan text-xs py-2 pl-8 pr-16"
              />
              <Search size={14} className="absolute left-2.5 top-3 text-[var(--ink-subtle)]" />
              <button
                onClick={loadClassics}
                disabled={isLoading}
                className="absolute right-1.5 top-1.5 px-3 py-1 bg-[var(--daiqing)] text-white text-xs rounded"
              >
                检索
              </button>
            </div>

            {/* 分类快捷筛选 */}
            <div className="flex flex-wrap items-center gap-1 text-xs">
              <span className="text-[var(--ink-muted)]">分类：</span>
              {[
                { id: '', label: '全部' },
                { id: '易经象数', label: '易经' },
                { id: '八字命理', label: '八字' },
                { id: '紫微斗数', label: '紫微' },
                { id: '奇门遁甲', label: '奇门' },
                { id: '知止反思', label: '知止' },
                { id: '易象修养', label: '修养' },
                { id: '现实修身', label: '修身' }
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    setCategory(cat.id);
                    fetchClassicsAPI(query, cat.id).then(res => {
                      setReadings(res.readings);
                      setGlossary(res.glossary);
                    });
                  }}
                  className={`px-2 py-1 rounded text-xs transition ${
                    category === cat.id
                      ? 'bg-[var(--daiqing)] text-white font-medium'
                      : 'bg-[var(--xuanzhi-light)] hover:bg-[var(--border-light)] border border-[var(--border)] text-[var(--ink)]'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* 隐私与存储边界说明 */}
          <div className="card-xuan p-4 bg-[var(--xuanzhi-light)] border-l-4 border-l-[var(--daiqing)] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-3">
              <Shield size={18} className="text-[var(--daiqing)] shrink-0" />
              <div>
                <div className="font-bold text-[var(--ink)] flex items-center gap-2">
                  隐私保护与存储规则
                  <span className="seal-tag-muted text-[10px]">
                    {allowPersistence ? '允许主动落盘' : '默认不保存私人数据'}
                  </span>
                </div>
                <p className="text-[var(--ink-muted)] mt-0.5">
                  所有问事与反思记录默认仅留存在当前内存中。仅当您主动开启或点击“存为手记”时保存在本机私有档案库中。
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <label className="flex items-center gap-1.5 cursor-pointer text-[var(--ink)]">
                <input
                  type="checkbox"
                  checked={allowPersistence}
                  onChange={(e) => handleTogglePersistence(e.target.checked)}
                  className="rounded text-[var(--daiqing)]"
                />
                <span>允许主动保存</span>
              </label>

              <button
                onClick={handleExportJSON}
                className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1"
              >
                <FileDown size={13} />
                <span>导出典籍库</span>
              </button>
            </div>
          </div>

          {/* 核心板块 1: 经部短读 */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between px-1">
              <h3 className="font-song text-base font-bold text-[var(--ink)] flex items-center gap-2">
                <BookOpen size={16} className="text-[var(--daiqing)]" />
                经典篇章短读（含出处校勘）
              </h3>
              <span className="text-xs text-[var(--ink-subtle)]">收录 {readings.length} 篇正文</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {readings.map((r) => (
                <div key={r.id} className="card-xuan p-5 bg-[var(--xuanzhi-light)] flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="seal-tag">{r.category}</span>
                      <span className="text-xs text-[var(--ink-subtle)] font-serif">{r.source}</span>
                    </div>
                    <h4 className="font-song text-base font-bold text-[var(--ink)] mb-2">
                      {r.title}
                    </h4>
                    <blockquote className="pl-3 border-l-2 border-[var(--daiqing)] font-song text-xs text-[var(--ink)] italic mb-3 leading-relaxed bg-[var(--xuanzhi-card)] p-2 rounded">
                      “{r.original_text}”
                    </blockquote>
                    <p className="text-xs text-[var(--ink-muted)] leading-relaxed mb-3">
                      <strong>【白话诠释】</strong>：{r.translation}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[var(--border-light)] text-xs text-[var(--ink-subtle)] flex items-center justify-between">
                    <span>作者/源流：{r.author}</span>
                    <span className="seal-tag-muted text-[10px]">{r.verification_status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 核心板块 2: 玄鉴术语词典 */}
          <div className="flex flex-col gap-3 mt-2">
            <div className="flex items-center justify-between px-1">
              <h3 className="font-song text-base font-bold text-[var(--ink)] flex items-center gap-2">
                <Bookmark size={16} className="text-[var(--daiqing)]" />
                玄鉴易学象数术语词典
              </h3>
              <span className="text-xs text-[var(--ink-subtle)]">收录 {glossary.length} 核心术语</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {glossary.map((g, idx) => (
                <div key={idx} className="card-xuan p-4 bg-[var(--xuanzhi-card)]">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-song font-bold text-sm text-[var(--ink)]">{g.term}</span>
                    <span className="text-[10px] bg-[var(--daiqing-light)] text-[var(--daiqing)] px-1.5 py-0.5 rounded">
                      {g.category}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--ink-muted)] leading-relaxed mb-2 line-clamp-3">
                    {g.definition}
                  </p>
                  <div className="text-[10px] text-[var(--ink-subtle)] font-serif border-t border-[var(--border-light)] pt-1">
                    出处：{g.source}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
