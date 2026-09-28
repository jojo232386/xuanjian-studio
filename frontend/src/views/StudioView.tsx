import type { NavTab, CalendarDayData } from '../types';
import { ArrowRight, BookOpen, NotebookPen, CalendarDays, Compass, ShieldCheck } from 'lucide-react';
interface Props {calendarData: CalendarDayData|null;onNavigate:(tab:NavTab)=>void;onOpenSource:(term:string)=>void;onOpenRecords?:()=>void;onOpenClassics?:()=>void;}
export const StudioView=({calendarData,onNavigate,onOpenSource,onOpenRecords,onOpenClassics}:Props)=>{
 const day=calendarData?.solar;
 return <div className="studio-page max-w-5xl mx-auto space-y-7 py-3 md:py-5">
   <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-[var(--ink-muted)]">
     <p className="flex items-center gap-2"><CalendarDays size={17}/>{day?`${day.date} ${day.weekday}`:'正在读取今日历法'}<span className="hidden sm:inline">· {calendarData?.lunar.full_string}</span></p>
     <button onClick={()=>onNavigate('calendar')} className="text-link">查看历法 <ArrowRight size={14}/></button>
   </div>
   <section className="studio-welcome">
     <div className="max-w-2xl"><p className="text-sm tracking-[.18em] text-[var(--accent-ink)] mb-4">玄鉴 · 今日书房</p>
       <h2 className="font-song text-3xl sm:text-4xl leading-snug">留一刻清静，<br/>看清眼前事。</h2>
       <p className="mt-5 text-base leading-7 text-[var(--ink-muted)] max-w-lg">第一次来？从一件小事开始。写下问题，软件会模拟投币，再给你一段可供思考的传统文化解读。</p>
       <div className="mt-7 flex flex-wrap items-center gap-4"><button className="btn-primary" onClick={()=>onNavigate('divination')}><Compass size={18}/>从这里开始<ArrowRight size={16}/></button><span className="text-sm text-[var(--ink-muted)]">不需要准备硬币，也不用填写个人资料</span></div>
     </div>
   </section>
   <section className="card-xuan p-5 sm:p-7" aria-labelledby="first-visit-title">
     <p className="text-sm text-[var(--accent-ink)]">第一次使用</p>
     <h3 id="first-visit-title" className="font-song text-xl mt-1">照着这三步试一次</h3>
     <ol className="grid sm:grid-cols-3 gap-4 mt-5">
       <li><span className="text-sm text-[var(--accent-ink)]">01 · 写问题</span><p className="text-sm leading-6 mt-1 text-[var(--ink-muted)]">选一个页面里的例子，再改成你自己的话。</p></li>
       <li><span className="text-sm text-[var(--accent-ink)]">02 · 起卦</span><p className="text-sm leading-6 mt-1 text-[var(--ink-muted)]">点按钮让软件模拟投币，逐次进行或一次完成。</p></li>
       <li><span className="text-sm text-[var(--accent-ink)]">03 · 看解读</span><p className="text-sm leading-6 mt-1 text-[var(--ink-muted)]">先看简短结果；想以后再看，就主动保存到手记。</p></li>
     </ol>
     <p className="text-xs leading-5 text-[var(--ink-muted)] mt-5">这是帮助整理想法的文化研读，不会预测事情一定怎样发生。</p>
   </section>
   <div className="grid md:grid-cols-2 gap-4">
     <button onClick={onOpenRecords || (()=>onNavigate('archive'))} className="studio-shortcut group"><NotebookPen size={23} strokeWidth={1.6}/><span className="flex-1"><span className="block font-song text-xl">我的手记</span><span className="block text-sm text-[var(--ink-muted)] mt-1">回看当时的问题，记下后来的变化。</span></span><ArrowRight size={18}/></button>
     <button onClick={onOpenClassics || (()=>onNavigate('archive'))} className="studio-shortcut group"><BookOpen size={23} strokeWidth={1.6}/><span className="flex-1"><span className="block font-song text-xl">读一段经典</span><span className="block text-sm text-[var(--ink-muted)] mt-1">从《周易》到《道德经》，随手翻一页。</span></span><ArrowRight size={18}/></button>
   </div>
   <section className="card-xuan p-6 sm:p-7">
     <div className="flex items-center justify-between gap-3"><span className="text-sm text-[var(--ink-muted)]">今日短读</span><span className="text-xs text-[var(--ink-muted)]">《周易》既济 · 象传</span></div>
     <blockquote className="font-song text-xl sm:text-2xl leading-relaxed mt-4">君子以思患而预防之。</blockquote>
     <p className="text-sm leading-7 text-[var(--ink-muted)] mt-3">事情初成，也值得留一点余地。将担心写下来，往往能看清下一步。</p>
     <div className="mt-5 flex flex-wrap gap-5"><button className="text-link" onClick={()=>onOpenSource('既济')}>查看出处<ArrowRight size={14}/></button><button className="text-link" onClick={()=>onNavigate('restraint')}>做一次现实反思<ArrowRight size={14}/></button></div>
   </section>
   <p className="flex items-center justify-center gap-2 text-xs text-[var(--ink-muted)]"><ShieldCheck size={15}/>问事默认不保存，手记由你主动留存。</p>
 </div>;
};
