// frontend/src/views/RestraintView.tsx - 知止：传统禁忌查证与现实风险提醒 (严格分设两区)

import React, { useState } from 'react';
import type { TabooItem, ReflectionResult } from '../types';
import { verifyTabooAPI, evaluateReflectionAPI, exportDataAPI, createRecordAPI } from '../api';
import { ShieldAlert, Search, FileDown, HelpCircle, Clock, Wind, Database, Check } from 'lucide-react';
import { BreathingTimer } from '../components/BreathingTimer';

interface RestraintViewProps {
  onOpenSource: (item: TabooItem) => void;
}

export const RestraintView: React.FC<RestraintViewProps> = ({ onOpenSource }) => {
  const [activeSubTab, setActiveSubTab] = useState<'traditional' | 'real_risk' | 'breathing'>('traditional');

  // 区域 A: 传统禁忌查证状态
  const [query, setQuery] = useState('诸事不宜');
  const [searchResult, setSearchResult] = useState<{
    found: boolean;
    query: string;
    count: number;
    results?: TabooItem[];
    verification_status?: string;
    message: string;
  } | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // 区域 B: 现实事实与反思表单
  const [formTopic, setFormTopic] = useState('准备购买高配笔记本电脑并分期分批付款');
  const [budgetAvailable, setBudgetAvailable] = useState<number>(3000);
  const [costEstimate, setCostEstimate] = useState<number>(12000);
  const [usesCredit, setUsesCredit] = useState<boolean>(true);
  const [isIrreversible, setIsIrreversible] = useState<boolean>(false);
  const [deadline, setDeadline] = useState<string>('2026-10-01 优惠券截止');
  const [divinationCount, setDivinationCount] = useState<number>(3);
  const [evalResult, setEvalResult] = useState<ReflectionResult | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  // 默认启动时执行一次检索和评估
  React.useEffect(() => {
    handleSearchTaboo('诸事不宜');
    handleEvaluateRisk();
  }, []);

  const handleSearchTaboo = async (q: string) => {
    if (!q.trim()) return;
    setIsSearching(true);
    try {
      const res = await verifyTabooAPI(q);
      setSearchResult(res);
    } catch (e: any) {
      alert(`查证接口异常: ${e.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  const handleEvaluateRisk = async () => {
    setIsEvaluating(true);
    try {
      const res = await evaluateReflectionAPI({
        topic: formTopic,
        budget_available: budgetAvailable,
        cost_estimate: costEstimate,
        uses_credit_or_loan: usesCredit,
        is_irreversible: isIrreversible,
        impending_deadline: deadline,
        divination_count_today: divinationCount
      });
      setEvalResult(res);
    } catch (e: any) {
      alert(`反思评估异常: ${e.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleExportReflection = async () => {
    if (!evalResult) return;
    try {
      const md = await exportDataAPI('reflection', 'markdown', {
        topic: formTopic,
        evaluation: evalResult
      });
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `知止反思手记_${new Date().toISOString().slice(0, 10)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`导出失败: ${e.message}`);
    }
  };

  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  const handleSaveReflectionRecord = async () => {
    if (!evalResult) return;
    try {
      await createRecordAPI({
        record_type: 'reflection',
        title: `知止反思：${formTopic.slice(0, 24)}`,
        topic: formTopic,
        tags: ['知止反思', evalResult.risk_level],
        params: {
          budget_available: budgetAvailable,
          cost_estimate: costEstimate,
          uses_credit_or_loan: usesCredit,
          is_irreversible: isIrreversible,
          impending_deadline: deadline,
          divination_count_today: divinationCount
        },
        calculation_result: evalResult,
        review_data: {
          original_thought: `预估开销 ${costEstimate} 元，自有可用预算 ${budgetAvailable} 元。`,
          notes: "慎思笃行，知止不殆。"
        }
      });
      setSaveSuccessMsg('已主动保存至本地私人档案！您可在【典藏】中查阅并追加事后复盘。');
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (e: any) {
      alert(`保存失败: ${e.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto py-4">
      {/* 顶部清晰分界导航：传统禁忌查证 vs 现实风险提醒 */}
      <div className="card-xuan p-4 flex flex-col sm:flex-row items-center justify-between gap-4 bg-[#FAF7F0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="seal-tag">知止</span>
            <h2 className="font-song text-xl font-bold text-[#222622]">知止 · 避险与自省</h2>
          </div>
          <p className="text-xs text-[#5C625B]">
            传统文化考据与现实风险防范严格分离，绝不把传统凶字转化为现实灾祸警报。
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1 bg-[var(--border-light)] p-1 rounded border border-[var(--border)]">
          <button
            onClick={() => setActiveSubTab('traditional')}
            className={`px-3 py-1.5 text-xs font-song rounded transition ${
              activeSubTab === 'traditional'
                ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            区域一：传统禁忌考辨
          </button>
          <button
            onClick={() => setActiveSubTab('real_risk')}
            className={`px-3 py-1.5 text-xs font-song rounded transition ${
              activeSubTab === 'real_risk'
                ? 'bg-[var(--zhusha)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            区域二：现实风险提醒
          </button>
          <button
            onClick={() => setActiveSubTab('breathing')}
            className={`px-3 py-1.5 text-xs font-song rounded transition flex items-center gap-1 ${
              activeSubTab === 'breathing'
                ? 'bg-[var(--daiqing)] text-white font-bold shadow-sm'
                : 'text-[var(--ink)] hover:bg-[var(--border)]'
            }`}
          >
            <Wind size={13} />
            区域三：观息专注计时
          </button>
        </div>
      </div>

      {/* 区域 A：传统禁忌查证 (这是真的吗？) */}
      {activeSubTab === 'traditional' && (
        <div className="flex flex-col gap-5">
          {/* 查证检索框 */}
          <div className="card-xuan p-6 bg-[#FFFFFF]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-song text-base font-bold text-[#222622] flex items-center gap-2">
                <Search size={16} className="text-[#325350]" />
                「这是真的吗？」传统禁忌典籍考据
              </h3>
              <span className="text-xs text-[#8A9289]">宁缺毋滥 · 杜绝臆造引文</span>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchTaboo(query)}
                placeholder="输入要查证的禁忌词条，例如：诸事不宜、癸不词讼、破屋、还精补脑、杨公十三忌..."
                className="input-xuan"
              />
              <button
                onClick={() => handleSearchTaboo(query)}
                disabled={isSearching}
                className="btn-primary shrink-0"
              >
                <span>考据查证</span>
              </button>
            </div>

            {/* 常用关键词快捷点击 */}
            <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-[#5C625B]">
              <span>推荐考据词：</span>
              {['诸事不宜', '癸不词讼', '卯不穿井', '破屋', '求医', '还精补脑', '杨公十三忌'].map((tag) => (
                <button
                  key={tag}
                  onClick={() => {
                    setQuery(tag);
                    handleSearchTaboo(tag);
                  }}
                  className="px-2 py-0.5 bg-[#FAF7F0] hover:bg-[#E8ECEB] border border-[#D8D1C2] rounded text-[#325350] transition"
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* 查证结果反馈区 */}
          {searchResult && (
            <div className="flex flex-col gap-4">
              <div className="text-xs text-[#5C625B] px-1">
                {searchResult.message}
              </div>

              {searchResult.found && searchResult.results ? (
                <div className="grid grid-cols-1 gap-4">
                  {searchResult.results.map((item, idx) => (
                    <div key={idx} className="card-xuan p-5 bg-[#FAF7F0] border-l-4 border-l-[#325350]">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2 pb-2 border-b border-[#D8D1C2]/60">
                        <div className="flex items-center gap-2">
                          <span className="seal-tag">{item.content_type || '考据'}</span>
                          <h4 className="font-song text-base font-bold text-[#222622]">
                            {item.title || item.term}
                          </h4>
                          {item.domain && (
                            <span className="text-xs text-[#5C625B]">（{item.domain}）</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="seal-tag-muted">{item.source_type}</span>
                          <span className="seal-tag-muted">核验状态：{item.verification_status}</span>
                        </div>
                      </div>

                      {/* 释义与出处 */}
                      <p className="text-sm text-[#222622] leading-relaxed mb-3">
                        <strong>【传统含义】</strong>：{item.meaning}
                      </p>

                      <p className="text-xs text-[#325350] bg-[#FFFFFF] p-2.5 rounded border border-[#D8D1C2] mb-3">
                        <strong>【出处源流】</strong>：{item.source}
                      </p>

                      {item.divergent_opinions && (
                        <p className="text-xs text-[#5C625B] bg-[#FFFFFF] p-2.5 rounded border border-[#D8D1C2] mb-3 leading-relaxed">
                          <strong>【历史分歧】</strong>：{item.divergent_opinions}
                        </p>
                      )}

                      {/* 理性界限 */}
                      <div className="p-3 bg-[#FBECEB] border border-[#EAC2BF] rounded text-xs text-[#8D3129] leading-relaxed mb-3">
                        <strong className="text-[#A63B32]">【现代现实理性准则】</strong>：
                        {item.rational_handling}
                      </div>

                      <div className="flex justify-end">
                        <button
                          onClick={() => onOpenSource(item)}
                          className="text-xs text-[#325350] hover:underline"
                        >
                          在右侧抽屉细览考据 →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                /* 未收录防御展示 */
                <div className="card-xuan p-6 bg-[#FFFFFF] border-l-4 border-l-[#A63B32]">
                  <div className="flex items-center gap-2 text-[#A63B32] font-song font-bold mb-2">
                    <HelpCircle size={18} />
                    查证先于假设 · 未收录声明
                  </div>
                  <p className="text-sm text-[#5C625B] leading-relaxed">
                    词条「<strong>{searchResult.query}</strong>」尚未在《协纪辨方书》、《周易》古注或正规民俗学典籍中查实可靠版本。
                  </p>
                  <p className="text-xs text-[#8A9289] mt-2">
                    本系统严格遵守【防幻觉协议】：未知即如实标明未知，坚决不临场编造假古籍或假学者名言。建议参考经正规校勘之典籍《钦定四库全书·协纪辨方书》。
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 区域 B：现实风险提醒与决定前暂停卡 */}
      {activeSubTab === 'real_risk' && (
        <div className="flex flex-col gap-6">
          {/* 用户客观事实输入卡 */}
          <div className="card-xuan p-6 bg-[#FFFFFF]">
            <h3 className="font-song text-base font-bold text-[#222622] mb-3 flex items-center gap-2">
              <ShieldAlert size={18} className="text-[#A63B32]" />
              现实事实自检录入（纯本地安全计算，不上传外部）
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1 md:col-span-2">
                <label className="text-xs text-[#5C625B]">拟采取的具体现实行动：</label>
                <input
                  type="text"
                  value={formTopic}
                  onChange={(e) => setFormTopic(e.target.value)}
                  className="input-xuan"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-[#5C625B]">自有流动现金预算 (¥，信用额度不计入)：</label>
                <input
                  type="number"
                  value={budgetAvailable}
                  onChange={(e) => setBudgetAvailable(parseFloat(e.target.value) || 0)}
                  className="input-xuan"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-[#5C625B]">预估全部支出费用 (¥)：</label>
                <input
                  type="number"
                  value={costEstimate}
                  onChange={(e) => setCostEstimate(parseFloat(e.target.value) || 0)}
                  className="input-xuan"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-[#5C625B]">现实截止时限（考试/退款/法定维权截止）：</label>
                <input
                  type="text"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  className="input-xuan"
                  placeholder="例如：今晚24点报名截止，或无特殊期限"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-[#5C625B]">今日对同类事项起卦/占问次数：</label>
                <input
                  type="number"
                  value={divinationCount}
                  onChange={(e) => setDivinationCount(parseInt(e.target.value, 10) || 0)}
                  className="input-xuan"
                />
              </div>

              <div className="flex items-center gap-6 md:col-span-2 pt-2">
                <label className="flex items-center gap-2 text-xs text-[#222622] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={usesCredit}
                    onChange={(e) => setUsesCredit(e.target.checked)}
                    className="rounded text-[#A63B32]"
                  />
                  <span>拟使用信用卡透支、花呗或消费分期借贷</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-[#222622] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isIrreversible}
                    onChange={(e) => setIsIrreversible(e.target.checked)}
                    className="rounded text-[#A63B32]"
                  />
                  <span>此动作无法回滚或撤回（不可逆重大动作）</span>
                </label>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-[#D8D1C2]/60 flex justify-end">
              <button
                onClick={handleEvaluateRisk}
                disabled={isEvaluating}
                className="btn-zhusha"
              >
                <span>重新评估现实风险与自省卡</span>
              </button>
            </div>
          </div>

          {/* 现实风险提醒看板 */}
          {evalResult && (
            <div className="flex flex-col gap-5">
              {/* 风险等级条目卡 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded ${
                    evalResult.risk_level === 'HIGH_RISK'
                      ? 'bg-[#A63B32] text-white'
                      : evalResult.risk_level === 'ATTENTION'
                      ? 'bg-[#A17C38] text-white'
                      : 'bg-[#325350] text-white'
                  }`}>
                    现实综合风险等级：{evalResult.risk_level}
                  </span>
                  <span className="text-xs text-[#5C625B]">
                    触发 {evalResult.alerts_count} 条现实边界警示
                  </span>
                </div>

                <button
                  onClick={handleExportReflection}
                  className="btn-secondary py-1 px-3 text-xs"
                >
                  <FileDown size={14} />
                  <span>导出反思记录 (Markdown)</span>
                </button>
              </div>

              {/* 具体警示卡片 */}
              <div className="grid grid-cols-1 gap-3">
                {evalResult.alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`card-xuan p-4 border-l-4 ${
                      alert.level === 'danger'
                        ? 'border-l-[#A63B32] bg-[#FBECEB]'
                        : alert.level === 'warning'
                        ? 'border-l-[#A17C38] bg-[#FAF6EE]'
                        : 'border-l-[#325350] bg-[#FAF7F0]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="font-song font-bold text-sm text-[#222622]">
                        {alert.title}
                      </div>
                      <span className="text-[11px] font-mono uppercase px-1.5 py-0.5 rounded bg-white/70">
                        {alert.level}
                      </span>
                    </div>

                    <div className="text-xs text-[#5C625B] flex flex-col gap-1 leading-relaxed">
                      <div><strong>触发事实</strong>：{alert.trigger_fact}</div>
                      <div><strong>可能影响</strong>：{alert.possible_impact}</div>
                      <div className="text-[#325350]"><strong>稳妥替代</strong>：{alert.safer_alternative}</div>
                      <div className="text-[#8A9289]"><strong>如何调整</strong>：{alert.how_to_adjust}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 决定前暂停卡 (Pause Before Deciding) */}
              <div className="card-xuan p-6 bg-[#FFFFFF] border-2 border-[#325350]/30 shadow-md">
                <div className="flex items-center justify-between pb-3 border-b border-[#D8D1C2]">
                  <div className="flex items-center gap-2">
                    <span className="seal-tag">知止卡</span>
                    <h3 className="font-song text-lg font-bold text-[#222622]">
                      {evalResult.pause_card.title}
                    </h3>
                  </div>
                  <span className="text-xs text-[#5C625B]">破除冲动决策幻觉</span>
                </div>

                <div className="flex flex-col gap-4 my-4">
                  {evalResult.pause_card.questions.map((q) => (
                    <div key={q.id} className="p-3 bg-[#FAF7F0] rounded border border-[#D8D1C2]">
                      <div className="font-song font-bold text-sm text-[#325350] mb-0.5">
                        {q.label}
                      </div>
                      <div className="text-[11px] text-[#8A9289] mb-1.5">
                        引导要点：{q.prompt}
                      </div>
                      <div className="text-xs text-[#222622] bg-white p-2 rounded border border-[#E5DFD3]">
                        {q.user_value}
                      </div>
                    </div>
                  ))}
                </div>

                {/* 灵活冷静期选择 */}
                <div className="pt-3 border-t border-[#D8D1C2] flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 text-[#5C625B]">
                    <Clock size={14} className="text-[#325350]" />
                    <span>可选冷静节奏（不强制死板天数，不拖延退款与考试）：</span>
                  </div>
                  <div className="flex gap-2">
                    {evalResult.pause_card.pause_options.map((opt, i) => (
                      <button
                        key={i}
                        className="px-3 py-1 bg-[var(--xuanzhi-light)] hover:bg-[var(--border-light)] border border-[var(--border)] rounded text-[var(--ink)] transition"
                        onClick={() => alert(`已设定：${opt.label}`)}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 主动存为本地知止手记与导出 */}
                <div className="pt-3 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-3 text-xs mt-1">
                  <div className="flex items-center gap-1.5 text-[var(--ink-muted)]">
                    <Database size={14} className="text-[var(--daiqing)]" />
                    <span>主动留档：默认不保存隐私。若需日后复盘自省，可存入本地私人手记。</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSaveReflectionRecord}
                      className="btn-primary py-1.5 px-3 text-xs flex items-center gap-1"
                    >
                      <Database size={13} />
                      <span>存为知止手记</span>
                    </button>
                    <button
                      onClick={handleExportReflection}
                      className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1"
                    >
                      <FileDown size={13} />
                      <span>导出 Markdown</span>
                    </button>
                  </div>
                </div>

                {saveSuccessMsg && (
                  <div className="p-2.5 bg-[var(--daiqing-light)] border border-[var(--daiqing)]/30 rounded text-xs text-[var(--daiqing)] flex items-center gap-1.5 mt-2">
                    <Check size={14} />
                    <span>{saveSuccessMsg}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 区域 C：观息专注计时 (自然呼吸，无功德考核，非强迫) */}
      {activeSubTab === 'breathing' && (
        <div className="card-xuan p-6 bg-[var(--xuanzhi-light)]">
          <BreathingTimer />
        </div>
      )}
    </div>
  );
};
