// frontend/src/components/SourceDrawer.tsx - 典籍出处与考据抽屉

import React from 'react';
import type { TabooItem } from '../types';
import { X, BookOpen, AlertCircle, ShieldCheck } from 'lucide-react';

interface SourceDrawerProps {
  item: TabooItem | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ item, onClose }) => {
  if (!item) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end bg-black/40 backdrop-blur-[2px] transition-opacity">
      <div className="w-full max-w-md bg-[var(--xuanzhi-light)] h-full shadow-2xl border-l border-[var(--border)] flex flex-col p-6 overflow-y-auto animate-in slide-in-from-right duration-200">
        {/* 顶部标题与关闭 */}
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className="seal-tag">考据</span>
            <h3 className="font-song text-lg font-bold text-[var(--ink)]">
              {item.title || item.term}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-[var(--ink-muted)] hover:bg-[var(--border-light)] transition"
            aria-label="关闭抽屉"
          >
            <X size={20} />
          </button>
        </div>

        {/* 属性标签区 */}
        <div className="flex flex-wrap gap-2 my-4">
          <span className="seal-tag-muted flex items-center gap-1">
            <BookOpen size={12} />
            {item.source_type}
          </span>
          <span className="seal-tag-muted flex items-center gap-1">
            <ShieldCheck size={12} />
            核验状态: {item.verification_status}
          </span>
          {item.domain && (
            <span className="px-2 py-0.5 text-xs bg-[var(--border-light)] text-[var(--ink)] rounded border border-[var(--border)]">
              领域: {item.domain}
            </span>
          )}
        </div>

        {/* 核心内容区 */}
        <div className="flex flex-col gap-5 text-sm text-[var(--ink)]">
          {/* 原文与白话释义 */}
          <div>
            <h4 className="font-song font-semibold text-xs text-[var(--ink-muted)] mb-1">【原典含义】</h4>
            <p className="bg-[var(--xuanzhi-card)] p-3 rounded border border-[var(--border)] leading-relaxed">
              {item.meaning}
            </p>
          </div>

          {/* 出处来源 */}
          <div>
            <h4 className="font-song font-semibold text-xs text-[var(--ink-muted)] mb-1">【文献出处】</h4>
            <p className="text-xs text-[var(--daiqing)] bg-[var(--daiqing-light)] p-2.5 rounded border border-[var(--border)] font-serif">
              {item.source}
            </p>
          </div>

          {/* 历史流派分歧 */}
          {item.divergent_opinions && (
            <div>
              <h4 className="font-song font-semibold text-xs text-[var(--ink-muted)] mb-1">【考据与流派分歧】</h4>
              <p className="text-xs text-[var(--ink-muted)] bg-[var(--xuanzhi-card)] p-3 rounded border border-[var(--border)] leading-relaxed">
                {item.divergent_opinions}
              </p>
            </div>
          )}

          {/* 现代现实理性建议 */}
          <div className="mt-2 p-3 bg-[var(--zhusha-light)] border border-[var(--zhusha)]/30 rounded">
            <div className="flex items-center gap-1.5 font-song font-semibold text-xs text-[var(--zhusha)] mb-1">
              <AlertCircle size={14} />
              现实理性准则与科学界限
            </div>
            <p className="text-xs text-[var(--ink)] leading-relaxed">
              {item.rational_handling}
            </p>
          </div>
        </div>

        {/* 底部关闭 */}
        <div className="mt-auto pt-6 border-t border-[var(--border)]">
          <button
            onClick={onClose}
            className="w-full btn-secondary"
          >
            返回阅读
          </button>
        </div>
      </div>
    </div>
  );
};
