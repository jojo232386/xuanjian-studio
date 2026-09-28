// frontend/src/components/DaodejingReader.tsx - 《道德经》八十一章逐章研读与生活反思
import React, { useState, useEffect } from 'react';
import type { DaodejingChapter } from '../types';
import { fetchDaodejingChapterAPI } from '../api';
import { BookOpen, Search, ChevronLeft, ChevronRight, ShieldCheck, Sparkles, Compass } from 'lucide-react';

export const DaodejingReader: React.FC = () => {
  const [allChapters, setAllChapters] = useState<DaodejingChapter[]>([]);
  const [currentChapterNum, setCurrentChapterNum] = useState<number>(1);
  const [currentChapter, setCurrentChapter] = useState<DaodejingChapter | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activePart, setActivePart] = useState<'all' | 'dao' | 'de'>('all');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    loadAllChapters();
  }, []);

  const loadAllChapters = async () => {
    setIsLoading(true);
    try {
      const res = await fetchDaodejingChapterAPI();
      const list = Array.isArray(res) ? res : (res?.chapters || []);
      if (list.length > 0) {
        setAllChapters(list);
        setCurrentChapter(list[0]);
      }
    } catch (e) {
      console.error('载入道德经全本失败:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectChapter = (chNum: number) => {
    setCurrentChapterNum(chNum);
    const found = allChapters.find((c) => c.chapter_num === chNum);
    if (found) {
      setCurrentChapter(found);
    }
  };

  const handlePrev = () => {
    if (currentChapterNum > 1) {
      handleSelectChapter(currentChapterNum - 1);
    }
  };

  const handleNext = () => {
    if (currentChapterNum < 81) {
      handleSelectChapter(currentChapterNum + 1);
    }
  };

  const filteredChapters = allChapters.filter((ch) => {
    if (activePart === 'dao' && ch.chapter_num > 37) return false;
    if (activePart === 'de' && ch.chapter_num <= 37) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.trim().toLowerCase();
    return (
      ch.title.toLowerCase().includes(q) ||
      ch.original_text.toLowerCase().includes(q) ||
      ch.translation.toLowerCase().includes(q) ||
      ch.reflection.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex flex-col gap-5 w-full">
      {/* 顶部导言卡 */}
      <div className="card-xuan p-5 bg-[var(--xuanzhi-light)] border-l-4 border-l-[var(--daiqing)] flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-[var(--ink)] font-song text-base">
            <BookOpen size={18} className="text-[var(--daiqing)]" />
            <span>《道德经》八十一章通行本研读</span>
            <span className="seal-tag text-[10px]">传世正本收录</span>
          </div>
          <span className="text-xs text-[var(--ink-subtle)] font-mono">共八十一章 · 道经1-37 · 德经38-81</span>
        </div>
        <p className="text-xs text-[var(--ink-muted)] leading-relaxed">
          道家宗纲典籍。全篇五千言，微言大义，阐述顺应自然、守静处下、物极必反与知足知止之道。
          每章配以原文、白话诠释及面向现实生活与理性决策的反思启示。
        </p>
      </div>

      {/* 检索与篇章导航控制区 */}
      <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] flex flex-col gap-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* 搜索框 */}
          <div className="relative flex-1 w-full">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索道德经原文名句、白话或知止感悟（如：知止、上善若水、反者道之动）..."
              className="input-xuan text-xs py-2 pl-8 pr-10 w-full"
            />
            <Search size={14} className="absolute left-2.5 top-3 text-[var(--ink-subtle)]" />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2.5 text-xs text-[var(--ink-subtle)] hover:text-[var(--ink)]"
              >
                ✕
              </button>
            )}
          </div>

          {/* 分部筛选 */}
          <div className="flex items-center gap-1.5 shrink-0 text-xs">
            <button
              onClick={() => setActivePart('all')}
              className={`px-3 py-1.5 rounded transition ${
                activePart === 'all'
                  ? 'bg-[var(--daiqing)] text-white font-medium'
                  : 'bg-[var(--xuanzhi-light)] text-[var(--ink)] border border-[var(--border)]'
              }`}
            >
              全部 (81章)
            </button>
            <button
              onClick={() => setActivePart('dao')}
              className={`px-3 py-1.5 rounded transition ${
                activePart === 'dao'
                  ? 'bg-[var(--daiqing)] text-white font-medium'
                  : 'bg-[var(--xuanzhi-light)] text-[var(--ink)] border border-[var(--border)]'
              }`}
            >
              道经 (1-37)
            </button>
            <button
              onClick={() => setActivePart('de')}
              className={`px-3 py-1.5 rounded transition ${
                activePart === 'de'
                  ? 'bg-[var(--daiqing)] text-white font-medium'
                  : 'bg-[var(--xuanzhi-light)] text-[var(--ink)] border border-[var(--border)]'
              }`}
            >
              德经 (38-81)
            </button>
          </div>
        </div>

        {/* 章次快捷方格导航 */}
        <div className="flex flex-col gap-1.5 pt-2 border-t border-[var(--border-light)]">
          <div className="flex items-center justify-between text-[11px] text-[var(--ink-subtle)]">
            <span>章次跳转 ({filteredChapters.length} 章匹配)：</span>
            {searchQuery && <span className="text-[var(--daiqing)]">已过滤显示检索结果</span>}
          </div>
          <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto p-1 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)]">
            {filteredChapters.map((ch) => (
              <button
                key={ch.chapter_num}
                onClick={() => handleSelectChapter(ch.chapter_num)}
                title={ch.title}
                className={`w-7 h-7 text-xs font-mono rounded flex items-center justify-center transition ${
                  currentChapterNum === ch.chapter_num
                    ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm ring-2 ring-[var(--daiqing)]/30'
                    : 'bg-[var(--xuanzhi-card)] text-[var(--ink-muted)] hover:bg-[var(--border)] border border-[var(--border-light)]'
                }`}
              >
                {ch.chapter_num}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 当前章节研读卡片 */}
      {currentChapter ? (
        <div className="card-xuan p-6 bg-[var(--xuanzhi-card)] flex flex-col gap-6 shadow-sm">
          {/* 章节标题与翻页 */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-light)] pb-4">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="seal-tag">{currentChapter.part}</span>
                <span className="seal-tag-muted text-[10px] flex items-center gap-1">
                  <ShieldCheck size={12} className="text-emerald-600" />
                  {currentChapter.verification_status}
                </span>
                <span className="text-xs text-[var(--ink-subtle)] font-serif">{currentChapter.source}</span>
              </div>
              <h3 className="font-song text-xl font-bold text-[var(--ink)] tracking-wide">
                {currentChapter.title}
              </h3>
            </div>

            {/* 上一章 / 下一章切换 */}
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrev}
                disabled={currentChapterNum <= 1}
                className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1 disabled:opacity-40"
              >
                <ChevronLeft size={14} />
                <span>上一章</span>
              </button>
              <span className="text-xs font-mono font-bold text-[var(--ink)] px-1">
                {currentChapterNum} / 81
              </span>
              <button
                onClick={handleNext}
                disabled={currentChapterNum >= 81}
                className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1 disabled:opacity-40"
              >
                <span>下一章</span>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>

          {/* 经典正文古风排版 */}
          <div className="flex flex-col gap-2">
            <div className="text-xs font-song font-bold text-[var(--daiqing)] flex items-center gap-1.5">
              <Compass size={14} />
              <span>【传世原文】</span>
            </div>
            <div className="p-4 sm:p-5 bg-[var(--xuanzhi-light)] rounded-md border border-[var(--border)] shadow-inner">
              <p className="font-song text-base sm:text-lg text-[var(--ink)] leading-relaxed sm:leading-loose tracking-widest text-justify select-text">
                {currentChapter.original_text}
              </p>
            </div>
          </div>

          {/* 白话义理与现代诠释 */}
          <div className="flex flex-col gap-2">
            <div className="text-xs font-song font-bold text-[var(--ink)] flex items-center gap-1.5">
              <Sparkles size={14} className="text-[var(--zhusha)]" />
              <span>【白话通解】</span>
            </div>
            <div className="p-4 bg-[var(--xuanzhi-light)]/60 rounded-md border border-[var(--border-light)] text-xs sm:text-sm text-[var(--ink)] leading-relaxed">
              {currentChapter.translation}
            </div>
          </div>

          {/* 现实决策与知止反思 */}
          <div className="p-4 bg-[var(--daiqing)]/5 border-l-4 border-l-[var(--daiqing)] rounded-r-md flex flex-col gap-1.5">
            <div className="text-xs font-song font-bold text-[var(--daiqing)] flex items-center gap-1.5">
              <BookOpen size={14} />
              <span>【现实知止与生活反思】</span>
            </div>
            <p className="text-xs text-[var(--ink)] leading-relaxed italic font-song">
              “{currentChapter.reflection}”
            </p>
          </div>
        </div>
      ) : (
        <div className="card-xuan p-8 bg-[var(--xuanzhi-light)] text-center text-xs text-[var(--ink-muted)]">
          {isLoading ? '正在载入《道德经》...' : '未找到匹配的章节。请尝试清除检索关键词。'}
        </div>
      )}
    </div>
  );
};
