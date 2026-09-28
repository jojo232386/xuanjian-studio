import { useState } from 'react';
import type { NavTab } from '../types';
import { Home, Calendar, Compass, ShieldAlert, BookOpen, Menu, X, Sun, Moon, Laptop, Type, Archive, Info, Settings, Sparkles } from 'lucide-react';

interface NavigationProps {
  activeTab: NavTab; onSelectTab: (tab: NavTab) => void; aiConnected: boolean;
  themeMode: 'xuanzhi' | 'moye' | 'system'; onSelectTheme: (mode:'xuanzhi'|'moye'|'system')=>void;
  fontSize: 'standard'|'large'; onToggleFontSize:()=>void;
  onOpenAISettings?:()=>void; onOpenSyncBackup?:()=>void; onOpenAbout?:()=>void;
}
const items = [
  {id:'studio',label:'书房',desc:'从这里开始',Icon:Home},
  {id:'divination',label:'问事',desc:'写下问题，起卦研读',Icon:Compass},
  {id:'archive',label:'典藏',desc:'我的手记与经典',Icon:BookOpen},
  {id:'calendar',label:'历法',desc:'日期、节气与民俗',Icon:Calendar},
  {id:'restraint',label:'知止',desc:'整理想法，做次反思',Icon:ShieldAlert},
] as const;

export const Navigation = (p:NavigationProps) => {
  const [menuOpen,setMenuOpen]=useState(false);
  const go=(tab:NavTab)=>{p.onSelectTab(tab);setMenuOpen(false);};
  const launch=(fn?:()=>void)=>{fn?.();setMenuOpen(false);};
  const preferences=<div className="space-y-4">
    <div className="grid grid-cols-3 gap-1 rounded-lg bg-[var(--border-light)] p-1" aria-label="外观主题">
      {([{id:'xuanzhi',label:'宣纸',Icon:Sun},{id:'moye',label:'墨夜',Icon:Moon},{id:'system',label:'系统',Icon:Laptop}] as const).map(({id,label,Icon})=><button key={id} aria-pressed={p.themeMode===id} onClick={()=>p.onSelectTheme(id)} className={`min-h-10 flex items-center justify-center gap-1 rounded-md text-[13px] ${p.themeMode===id?'bg-[var(--xuanzhi-card)] shadow-sm text-[var(--ink)]':'text-[var(--ink-muted)]'}`}><Icon size={14}/>{label}</button>)}
    </div>
    <button aria-pressed={p.fontSize==='large'} onClick={p.onToggleFontSize} className="utility-button"><Type size={16}/><span>阅读字号</span><span className="ml-auto">{p.fontSize==='large'?'大字':'标准'}</span></button>
    <button onClick={()=>launch(p.onOpenAISettings)} className="utility-button"><Sparkles size={16}/><span>可选 AI 研读</span><span className="ml-auto text-xs">{p.aiConnected?'已连接':'未连接'}</span></button>
  </div>;
  const nav=<nav aria-label="主导航" className="flex flex-col gap-2">{items.map(({id,label,desc,Icon})=><button key={id} aria-current={p.activeTab===id?'page':undefined} onClick={()=>go(id)} className={`nav-item ${p.activeTab===id?'is-active':''}`}><Icon size={20} strokeWidth={1.7}/><span><span className="block font-song text-base">{label}</span><span className="block mt-0.5 text-xs opacity-85">{desc}</span></span></button>)}</nav>;
  return <>
    <aside className="hidden lg:flex fixed inset-y-0 left-0 z-30 w-64 h-dvh overflow-y-auto bg-[var(--xuanzhi-light)] border-r border-[var(--border)] px-5 py-7 flex-col gap-7">
      <div className="flex items-center gap-3 px-2"><span className="seal-tag">玄鉴</span><div><h1 className="font-song text-xl font-bold tracking-widest">玄鉴·书房</h1><p className="text-xs text-[var(--ink-muted)] mt-1">一问一记 · 常读常新</p></div></div>
      {nav}
      <div className="mt-auto pt-5 border-t border-[var(--border)] space-y-2">
        <p className="text-xs text-[var(--ink-muted)] px-3 pb-2">{p.aiConnected?'云端研读已连接':'本地研读，无需注册'}</p>
        <button onClick={()=>launch(p.onOpenSyncBackup)} className="utility-button"><Archive size={16}/>备份与恢复</button>
        <details className="nav-preferences"><summary className="utility-button cursor-pointer"><Settings size={16}/>外观与设置</summary><div className="px-2 pt-3 pb-2">{preferences}</div></details>
        <button onClick={()=>launch(p.onOpenAbout)} className="utility-button"><Info size={16}/>关于玄鉴<span className="ml-auto text-xs">3.0.1</span></button>
      </div>
    </aside>
    <header className="lg:hidden sticky top-0 z-40 bg-[var(--xuanzhi-light)] border-b border-[var(--border)] px-4 py-3 flex items-center justify-between">
      <button className="flex items-center gap-2 min-h-10" onClick={()=>go('studio')} aria-label="回到书房"><span className="seal-tag">玄鉴</span><span className="font-song text-lg font-bold">玄鉴·书房</span></button>
      <button onClick={()=>setMenuOpen(!menuOpen)} aria-label={menuOpen?'关闭导航菜单':'打开导航菜单'} aria-expanded={menuOpen} aria-controls="mobile-navigation" className="min-h-11 min-w-11 flex items-center justify-center rounded-lg border border-[var(--border)]">{menuOpen?<X size={22}/>:<Menu size={22}/>}</button>
    </header>
    {menuOpen && <div id="mobile-navigation" className="lg:hidden bg-[var(--xuanzhi-light)] border-b border-[var(--border)] p-4 max-h-[calc(100dvh-69px)] overflow-y-auto" onKeyDown={e=>{if(e.key==='Escape')setMenuOpen(false);}}>
      {nav}<div className="border-t border-[var(--border)] pt-4 mt-5 space-y-3">
        <button onClick={()=>launch(p.onOpenSyncBackup)} className="utility-button"><Archive size={16}/>备份与恢复</button>
        {preferences}
        <button onClick={()=>launch(p.onOpenAbout)} className="utility-button"><Info size={16}/>关于玄鉴与退出</button>
      </div>
    </div>}
  </>;
};
