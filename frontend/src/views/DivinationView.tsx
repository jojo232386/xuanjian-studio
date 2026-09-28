import { useEffect, useRef, useState } from 'react';
import type { CalculationResult, AIInterpretResponse } from '../types';
import { HexagramSvg } from '../components/HexagramSvg';
import { BaziCalculator } from '../components/BaziCalculator';
import { ZiweiCalculator } from '../components/ZiweiCalculator';
import { QimenCalculator } from '../components/QimenCalculator';
import { calculateHexagramAPI, castCoinsAPI, castSingleCoinAPI, requestAiInterpretAPI, exportDataAPI, createRecordAPI } from '../api';
import { RotateCw, Check, FileDown, Save, ArrowRight, CheckCircle2 } from 'lucide-react';

type Throw = {coins: number[]; value: number};
const labels: Record<number, string> = {6:'老阴 · 动爻',7:'少阳 · 静爻',8:'少阴 · 静爻',9:'老阳 · 动爻'};

export const DivinationView = ({onNavigateToRestraint,onOpenRecords}: {onNavigateToRestraint: () => void;onOpenRecords?:()=>void}) => {
  const [mode, setMode] = useState('zhouyi');
  const [question, setQuestion] = useState('');
  const [lockedQuestion, setLockedQuestion] = useState('');
  const [throws, setThrows] = useState<Throw[]>([]);
  const [manual, setManual] = useState([7,7,7,7,7,7]);
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const working = useRef(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [ai, setAi] = useState<AIInterpretResponse | null>(null);
  const resultRegion = useRef<HTMLElement>(null);
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const el=resultRegion.current;
      if (result && el && el.getClientRects().length) {
        el.focus({preventScroll:true});
        el.scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
      }
    });
    return ()=>cancelAnimationFrame(frame);
  }, [result]);
  const locked = throws.length > 0 || !!result;
  const topic = lockedQuestion || question.trim();
  const nextStep = result
    ? saved ? '已保存。以后可到「典藏 → 我的手记」回看并补充复盘。' : '解读已经生成。想日后回看，请点「保存这次问事」。'
    : throws.length === 6 ? '六次结果已保留。点击「查看解读」继续，不会重新投币。'
    : throws.length ? `继续点击投币，完成剩下的 ${6-throws.length} 次；第六次后会自动显示解读。`
    : question.trim() ? '问题已经写好。点击「一步步起卦」模拟投币六次，或点「快速起卦」一次完成。'
    : '先写一件具体的事；不知道怎么写，可以点下面的例子。';

  async function run(action: () => Promise<void>) {
    if (working.current) return;
    working.current = true; setBusy(true); setError('');
    try { await action(); } catch(e) { setError(e instanceof Error ? e.message : '操作未完成，请重试。'); }
    finally { working.current = false; setBusy(false); }
  }
  function accept(calc: CalculationResult, method: string, trace?: number[][]) {
    const snapshot = {...calc, generation_mode: method, ...(trace ? {coin_flips:trace} : {})};
    setResult(snapshot); setSaved(false); setAi(null);
    setSelected(calc.moving_lines[0] ?? 1);
  }
  async function finish(all: Throw[], q: string) {
    const calc = await calculateHexagramAPI(all.map(t=>t.value), q);
    accept(calc, 'guided_three_coins', all.map(t=>t.coins));
  }
  function toss() {
    if (!topic || result) return;
    void run(async()=>{
      const q = topic;
      if (throws.length === 6) { await finish(throws,q); return; }
      const one = await castSingleCoinAPI();
      const all = [...throws,one];
      setLockedQuestion(q); setThrows(all);
      if (all.length === 6) await finish(all,q);
    });
  }
  function quick() {
    if (!question.trim() || locked) return;
    void run(async()=>{
      const q=question.trim();
      const calc=await castCoinsAPI(q);
      setLockedQuestion(q);
      accept(calc,'three_coins');
      setThrows(calc.input_lines.map((value,i)=>({value,coins:calc.coin_flips?.[i] ?? []})));
    });
  }
  function reset() {
    if (working.current) return;
    setQuestion(''); setLockedQuestion(''); setThrows([]); setResult(null);
    setAi(null); setError(''); setSaved(false); setManual([7,7,7,7,7,7]);
  }
  function save() {
    if (!result || saved) return;
    void run(async()=>{
      await createRecordAPI({record_type:'divination',title:`${result.original_hexagram.name} · ${result.topic}`,
        topic:result.topic, tags:[result.original_hexagram.name,'问事'],
        params:{lines:result.input_lines,coin_flips:result.coin_flips,method:result.generation_mode,cast_at:result.cast_at},
        calculation_result:result,ai_interpret:ai || {}});
      setSaved(true);
    });
  }
  function exportRecord() {
    if (!result) return;
    void run(async()=>{
      const md=await exportDataAPI('divination','markdown',{topic:result.topic,calculation:result,interpretation:result.layered_interpretation});
      const url=URL.createObjectURL(new Blob([md],{type:'text/markdown;charset=utf-8'}));
      const a=document.createElement('a');a.href=url;a.download=`玄鉴_${result.original_hexagram.name}.md`;a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
  }
  const activeLine=result?.lines.find(l=>l.position===selected);
  return <div className="flex flex-col gap-6 max-w-4xl mx-auto py-3 md:py-5 divination-flow">
    <header className="flex flex-wrap items-center justify-between gap-3">
      <div><p className="text-sm text-[var(--accent-ink)] tracking-widest mb-2">周易 · 问事</p><h2 className="font-song text-3xl text-[var(--ink)]">{result ? '留一份此刻的思考' : '把心里的事，写下来'}</h2></div>
      <label className="text-sm text-[var(--ink-muted)]">切换排盘 <select aria-label="切换排盘" value={mode} disabled={busy} onChange={e=>setMode(e.target.value)} className="input-xuan ml-2">
        <option value="zhouyi">周易起卦</option><option value="bazi">八字</option><option value="ziwei">紫微</option><option value="qimen">奇门</option>
      </select></label>
    </header>
    {mode==='bazi' ? <BaziCalculator/> : mode==='ziwei' ? <ZiweiCalculator/> : mode==='qimen' ? <QimenCalculator/> : <>
      <ol className="flow-steps" aria-label="问事进度">{['写下问题','完成起卦','阅读与留存'].map((name,i)=>{
        const stage=result?2:throws.length?1:0;
        return <li key={name} aria-current={stage===i?'step':undefined} className={stage===i?'current':''}><span>{i<stage?<Check size={13}/>:i+1}</span>{name}</li>;
      })}</ol>
      <p className="text-sm leading-6 text-[var(--ink-muted)]" role="status">下一步：{nextStep}</p>
      <section className={`card-xuan ${locked ? 'p-4 sm:p-5' : 'p-5 sm:p-7'}`}>
        {locked ? <div className="flex items-start justify-between gap-4">
          <div className="min-w-0"><p className="text-xs text-[var(--ink-muted)] mb-1">这次所问</p><p className="text-base leading-7 break-words">{topic}</p></div>
          <button className="text-link shrink-0" disabled={busy} onClick={reset}>新问题<ArrowRight size={14}/></button>
        </div> : <>
          <label htmlFor="question" className="block font-song text-xl text-[var(--ink)] mb-3">你想问什么？</label>
          <textarea id="question" value={question} disabled={busy} maxLength={200} rows={3}
            onChange={e=>setQuestion(e.target.value)} className="input-xuan w-full resize-none question-input"
            placeholder="一件具体的事，会更容易展开思考。"/>
          <p className="text-sm text-[var(--ink-muted)] mt-3">没有头绪？选一个例子，再改成自己的问题。</p>
          <div className="flex flex-wrap gap-2 mt-3">{[
            ['工作机会','这个工作机会，我该怎样把握？'],['消费取舍','这笔消费值得现在做吗？'],['相处沟通','我该怎样推进这段关系？']
          ].map(([label,q])=><button key={label} className="question-example" disabled={busy} onClick={()=>setQuestion(q)}>{label}</button>)}</div>
        </>}
        {!result && <div className="mt-4 flex flex-wrap items-center gap-3">
          <button className="btn-primary" onClick={toss} disabled={busy || !topic}><RotateCw size={16}/>{busy ? '正在起卦…' : throws.length===6 ? '查看解读' : throws.length ? `投第 ${throws.length+1} 次` : '一步步起卦'}</button>
          {!locked && <button className="btn-secondary" onClick={quick} disabled={busy || !question.trim()}>快速起卦</button>}
          {throws.length>0 && <span role="status" className="text-sm text-[var(--ink-muted)]">已投 {throws.length} / 6 次 · 自下而上</span>}
        </div>}
        {!locked && <p className="text-xs text-[var(--ink-muted)] mt-3">“起卦”就是用六次模拟投币生成一组卦象；这里的解读供文化研读和自我反思。</p>}
        {error && <p role="alert" className="mt-4 text-[var(--zhusha)]">{error}{throws.length===6 && !result ? ' 六次结果已保留，点击“查看解读”重试，不会重新投币。' : ''}</p>}
      </section>
      {!locked && <details className="card-xuan px-6 py-4">
        <summary className="cursor-pointer text-sm text-[var(--ink-muted)]">我投了实体硬币，手动录入</summary>
        <p className="text-sm text-[var(--ink-muted)] my-3">约定两面分别为 2 和 3，每次三枚相加。按第一次到第六次填写。</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">{manual.map((v,i)=><label key={i} className="text-sm">第 {i+1} 次<select aria-label={`第${i+1}次爻值`} disabled={busy} className="input-xuan w-full mt-1" value={v} onChange={e=>setManual(manual.map((x,j)=>j===i?Number(e.target.value):x))}>{[6,7,8,9].map(n=><option key={n} value={n}>{n} {labels[n]}</option>)}</select></label>)}</div>
        <button className="btn-secondary mt-4" disabled={busy || !question.trim()} onClick={()=>void run(async()=>{const q=question.trim();const calc=await calculateHexagramAPI(manual,q);setLockedQuestion(q);accept(calc,'manual_lines');})}>按我的结果排卦</button>
      </details>}
      {!result && throws.length>0 && <section className="card-xuan p-6" aria-label="投币记录"><h3 className="font-song text-lg mb-3">卦象正在形成</h3><ol className="space-y-2">{throws.map((t,i)=><li key={i} className="flex justify-between border-b border-[var(--border-light)] pb-2 text-sm"><span>第 {i+1} 次 · {t.coins.join(' + ')} = {t.value}</span><span>{labels[t.value]}</span></li>)}</ol></section>}
      {result && <>
        <section ref={resultRegion} tabIndex={-1} aria-label="本次问事解读" className="card-xuan p-5 sm:p-7 reading-card scroll-mt-20 lg:scroll-mt-8" aria-live="polite">
          <p className="text-sm text-[var(--ink-muted)]">{result.original_hexagram.full_name}{result.moving_lines.length ? ` → ${result.transformed_hexagram.full_name}` : ' · 静卦，无动爻'} · 本地象意解读</p>
          <h3 className="font-song text-2xl text-[var(--ink)] mt-3">{result.reading?.headline || result.original_hexagram.name}</h3>
          <p className="mt-4 leading-relaxed">{result.reading?.summary || result.layered_interpretation?.symbolic_insight}</p>
          <p className="mt-3 text-[var(--ink-muted)] leading-relaxed">{result.reading?.context}</p>
          <p className="mt-5 p-4 rounded-lg bg-[var(--daiqing-light)] text-[var(--ink)] leading-7">{result.reading?.action}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-primary" disabled={busy || saved} onClick={save}>{saved ? <Check size={16}/> : <Save size={16}/>} {saved ? '已存入手记' : '保存这次问事'}</button>
            {saved && <button className="btn-secondary" onClick={onOpenRecords}>查看我的手记<ArrowRight size={16}/></button>}
            <button className="text-link px-2 min-h-11" disabled={busy} onClick={exportRecord}><FileDown size={16}/>导出记录</button>
          </div>
          {saved && <p role="status" className="mt-3 flex gap-2 items-center text-sm text-[var(--accent-ink)]"><CheckCircle2 size={16}/>已保存原始问题与解读，日后可追加复盘。</p>}
          <p className="mt-4 text-xs text-[var(--ink-muted)]">{result.reading?.boundary || '传统文化与娱乐性解读，不表示实际事件的发生概率。'} 不会自动保存。</p>
        </section>
        <details className="card-xuan p-6">
          <summary className="cursor-pointer font-song text-base">为什么这样解？查看卦爻原文</summary>
          <div className="mt-5 space-y-4">{result.reading?.basis.map((b,i)=><p key={i} className="leading-relaxed">{b}</p>)}
            <div className="flex flex-wrap justify-center gap-6"><HexagramSvg hexagram={result.original_hexagram} lines={result.lines} title="本卦" selectedLine={selected} onSelectLine={setSelected}/>
              {result.moving_lines.length>0 && <div className="max-w-sm self-center"><h4 className="font-song text-lg">变卦 · {result.transformed_hexagram.full_name}</h4><p className="mt-2">{result.transformed_hexagram.guaci}</p></div>}
            </div>
            <label className="text-sm block">查看爻辞 <select aria-label="查看爻辞" className="input-xuan ml-2" value={selected ?? 1} onChange={e=>setSelected(Number(e.target.value))}>{result.lines.map(l=><option key={l.position} value={l.position}>{l.yao_name}{l.is_moving?' · 动爻':''}</option>)}</select></label>
            <p>{activeLine?.yaoci}</p><p className="text-xs text-[var(--ink-muted)]">{activeLine?.yaoci_status} · <a className="underline" href={activeLine?.yaoci_source} target="_blank" rel="noreferrer">查看文本来源</a></p>
            <p className="text-sm">互卦：{result.nuclear_hexagram.full_name}</p>
          </div>
        </details>
        <details className="card-xuan px-6 py-4"><summary className="cursor-pointer text-sm">起卦记录与更多选项</summary>
          <div className="mt-4 space-y-3 text-sm"><p>问题：{result.topic}</p><p>时间：{result.cast_at ? new Date(result.cast_at).toLocaleString() : '未记录'}</p><p>方式：{result.generation_mode==='guided_three_coins'?'逐次三币':result.generation_mode==='manual_lines'?'实体硬币手动录入':'一键模拟三币'}</p>
            <p>爻值（自下而上）：{result.input_lines.join('、')}</p>{result.coin_flips?.map((c,i)=><p key={i}>第 {i+1} 次：{c.join(' + ')} = {result.input_lines[i]}</p>)}
            <button className="btn-secondary" disabled={busy} onClick={()=>void run(async()=>{setAi(await requestAiInterpretAPI(result.topic || '',result));})}>可选 AI 研读（按设置，可能计费）</button>
            {ai && <div className="space-y-2"><p>{ai.suggestion || '研读请求已返回。'}</p><p className="whitespace-pre-wrap leading-relaxed">{ai.interpretation || '当前未连接云端模型，本地解读仍可正常使用。'}</p></div>}
            <button className="block underline text-[var(--accent-ink)]" onClick={onNavigateToRestraint}>做一次现实反思</button>
          </div>
        </details>
      </>}
    </>}
  </div>;
};
