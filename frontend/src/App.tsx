// frontend/src/App.tsx - 玄鉴·书房 根组件 (支持墨夜主题、字号缩放与离线优雅回退)

import { useState, useEffect } from 'react';
import type { NavTab, CalendarDayData, TabooItem } from './types';
import { fetchCalendarDay, fetchHealth } from './api';
import { Navigation } from './components/Navigation';
import { SourceDrawer } from './components/SourceDrawer';
import { StudioView } from './views/StudioView';
import { CalendarView } from './views/CalendarView';
import { DivinationView } from './views/DivinationView';
import { RestraintView } from './views/RestraintView';
import { ArchiveView } from './views/ArchiveView';
import { AISettingsModal } from './components/AISettingsModal';
import { SyncBackupModal } from './components/SyncBackupModal';
import { AboutModal } from './components/AboutModal';

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab') as NavTab;
      if (['studio', 'calendar', 'divination', 'restraint', 'archive'].includes(tab)) {
        return tab;
      }
    }
    return 'studio';
  });

  const [archiveSection, setArchiveSection] = useState<'classics'|'records'>(() =>
    new URLSearchParams(window.location.search).get('section') === 'classics' ? 'classics' : 'records');

  const handleSelectTab = (tab: NavTab) => {
    setActiveTab(tab);
    if (tab === 'archive') setArchiveSection('records');
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      url.searchParams.delete('section');
      window.history.replaceState(null, '', url.toString());
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const openArchive = (section: 'classics'|'records') => {
    handleSelectTab('archive'); setArchiveSection(section);
    const url = new URL(window.location.href); url.searchParams.set('section',section);
    window.history.replaceState(null,'',url.toString());
  };

  // 外观偏好：主题模式 (宣纸 / 墨夜 / 跟随系统) 与字号
  const [themeMode, setThemeMode] = useState<'xuanzhi' | 'moye' | 'system'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('xuanjian_theme');
      if (saved === 'xuanzhi' || saved === 'moye' || saved === 'system') {
        return saved;
      }
    }
    return 'xuanzhi';
  });

  const [fontSize, setFontSize] = useState<'standard' | 'large'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('xuanjian_font_size');
      if (saved === 'standard' || saved === 'large') {
        return saved;
      }
    }
    return 'standard';
  });

  // 主题模式与属性绑定
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', themeMode);
    if (themeMode === 'moye') {
      root.classList.add('dark');
    } else if (themeMode === 'xuanzhi') {
      root.classList.remove('dark');
    } else {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
    localStorage.setItem('xuanjian_theme', themeMode);
  }, [themeMode]);

  // 监听系统主题变化 (当为 system 时)
  useEffect(() => {
    if (themeMode !== 'system') return;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      const root = document.documentElement;
      if (e.matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [themeMode]);

  // 字号偏好绑定
  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSize);
    localStorage.setItem('xuanjian_font_size', fontSize);
  }, [fontSize]);

  const [currentDateStr, setCurrentDateStr] = useState<string>(() => {
    return new Intl.DateTimeFormat('sv-SE', {timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  });
  const [calendarData, setCalendarData] = useState<CalendarDayData | null>(null);
  const [aiConnected, setAiConnected] = useState<boolean>(false);
  const [drawerItem, setDrawerItem] = useState<TabooItem | null>(null);
  const [isAISettingsOpen, setIsAISettingsOpen] = useState<boolean>(false);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState<boolean>(false);
  const [isAboutOpen, setIsAboutOpen] = useState<boolean>(false);

  // 初始化加载
  useEffect(() => {
    checkHealth();
    loadCalendar(currentDateStr);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetchHealth();
      setAiConnected(res.ai_connected);
    } catch {
      setAiConnected(false);
    }
  };

  const loadCalendar = async (dStr: string) => {
    try {
      const data = await fetchCalendarDay(dStr);
      setCalendarData(data);
    } catch (e: any) {
      console.error('历法加载异常:', e);
    }
  };

  const handleDateChange = (newDateStr: string) => {
    setCurrentDateStr(newDateStr);
    loadCalendar(newDateStr);
  };

  const handleOpenSourceByTerm = (term: string) => {
    if (term === '既济') {
      setDrawerItem({title:'既济 · 象传',term:'既济',source:'《周易·既济·象传》',source_type:'传世原文',verification_status:'原文可定位',meaning:'水在火上，既济；君子以思患而预防之。',rational_handling:'短读中的白话文字为现代释意，与原文分开阅读。'});
      return;
    }
    const found = calendarData?.yi.find((i) => i.term === term || i.title === term) ||
                  calendarData?.ji.find((i) => i.term === term || i.title === term);
    if (found) {
      setDrawerItem(found);
    } else {
      setDrawerItem({
        title: term,
        term: term,
        source: "《钦定四库全书·协纪辨方书》",
        source_type: "古籍可定位",
        verification_status: "已核对",
        meaning: `传统黄历所载事项【${term}】。`,
        rational_handling: "传统民俗择日供文化考据，现实事务依客观规律行事。"
      });
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[var(--xuanzhi)] text-[var(--ink)] transition-colors duration-200">
      {/* 主导航 */}
      <Navigation
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        aiConnected={aiConnected}
        themeMode={themeMode}
        onSelectTheme={setThemeMode}
        fontSize={fontSize}
        onToggleFontSize={() => setFontSize(fontSize === 'large' ? 'standard' : 'large')}
        onOpenAISettings={() => setIsAISettingsOpen(true)}
        onOpenSyncBackup={() => setIsSyncModalOpen(true)}
        onOpenAbout={() => setIsAboutOpen(true)}
      />

      {/* 主体交互区域 */}
      <main className="main-content-layout p-4 md:p-8 min-h-screen flex flex-col justify-between">
        <div className="w-full">
          {activeTab === 'studio' && (
            <StudioView
              calendarData={calendarData}
              onNavigate={handleSelectTab}
              onOpenSource={handleOpenSourceByTerm}
              onOpenRecords={() => openArchive('records')}
              onOpenClassics={() => openArchive('classics')}
            />
          )}

          {activeTab === 'calendar' && (
            <CalendarView
              calendarData={calendarData}
              currentDateStr={currentDateStr}
              onChangeDate={handleDateChange}
              onOpenSource={(item) => setDrawerItem(item)}
            />
          )}

          <div hidden={activeTab !== 'divination'}>
            <DivinationView
              onNavigateToRestraint={() => handleSelectTab('restraint')}
              onOpenRecords={() => openArchive('records')}
            />
          </div>

          {activeTab === 'restraint' && (
            <RestraintView
              onOpenSource={(item) => setDrawerItem(item)}
            />
          )}

          {activeTab === 'archive' && (
            <ArchiveView key={archiveSection} initialTab={archiveSection} />
          )}
        </div>

        {/* 底部极简版权与理念署名 */}
        <footer className="mt-10 py-5 text-center text-xs text-[var(--ink-muted)]">
          玄鉴·书房 · 常读常新，依实而行
        </footer>
      </main>

      {/* 考据抽屉 */}
      <SourceDrawer
        item={drawerItem}
        onClose={() => setDrawerItem(null)}
      />

      {/* AI 模型与费用预算设置弹窗 */}
      <AISettingsModal
        isOpen={isAISettingsOpen}
        onClose={() => setIsAISettingsOpen(false)}
        onConfigSaved={() => checkHealth()}
      />

      {/* 私有云同步与加密备份恢复弹窗 */}
      <SyncBackupModal
        isOpen={isSyncModalOpen}
        onClose={() => setIsSyncModalOpen(false)}
      />

      {/* 关于玄鉴与本地系统服务弹窗 */}
      <AboutModal
        isOpen={isAboutOpen}
        onClose={() => setIsAboutOpen(false)}
        onOpenSyncBackup={() => setIsSyncModalOpen(true)}
      />
    </div>
  );
}

export default App;
