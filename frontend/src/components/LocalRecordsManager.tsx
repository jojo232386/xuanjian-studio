// frontend/src/components/LocalRecordsManager.tsx - 本地 SQLite 记录、四术排盘、中文检索、时间轴复盘与历史版本留痕
import React, { useState, useEffect } from 'react';
import type { RecordItem, ReviewStatistics } from '../types';
import {
  listRecordsAPI,
  updateRecordAPI,
  deleteRecordAPI,
  exportRecordsAPI,
  fetchReviewStatisticsAPI
} from '../api';
import {
  Database,
  Search,
  FileDown,
  Trash2,
  Edit3,
  CheckCircle2,
  Tag,
  ChevronDown,
  ChevronUp,
  Clock,
  Loader2,
  Cloud,
  List,
  GitCommit,
  History,
  AlertCircle,
  TrendingUp,
  Check,
  Sparkles
} from 'lucide-react';
import { SyncBackupModal } from './SyncBackupModal';

export const LocalRecordsManager: React.FC = () => {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [query, setQuery] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedRevisionsId, setExpandedRevisionsId] = useState<string | null>(null);

  // 视图模式：列表视图 vs 时间轴视图
  const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list');

  // 复盘统计数据
  const [stats, setStats] = useState<ReviewStatistics | null>(null);

  // 复盘编辑状态
  const [editingReviewId, setEditingReviewId] = useState<string | null>(null);
  const [reviewForm, setReviewForm] = useState<{
    original_thought: string;
    actual_outcome: string;
    missing_evidence: string;
    notes: string;
  }>({
    original_thought: '',
    actual_outcome: '',
    missing_evidence: '',
    notes: ''
  });
  const [saveStatusMsg, setSaveStatusMsg] = useState<string | null>(null);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState<boolean>(false);

  useEffect(() => {
    loadRecords();
    loadStats();
  }, [selectedType]);

  const loadStats = async () => {
    try {
      const s = await fetchReviewStatisticsAPI();
      setStats(s);
    } catch (e) {
      console.warn('载入复盘统计数据失败:', e);
    }
  };

  const loadRecords = async (searchKw?: string) => {
    setIsLoading(true);
    try {
      const res = await listRecordsAPI({
        type: selectedType || undefined,
        query: searchKw !== undefined ? searchKw : query,
        limit: 100
      });
      setRecords(res.records);
      setTotal(res.total);
    } catch (e: any) {
      console.error('加载本地记录失败:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    loadRecords(query);
  };

  const handleStartEditReview = (rec: RecordItem) => {
    setEditingReviewId(rec.id);
    setReviewForm({
      original_thought: rec.review_data?.original_thought || '',
      actual_outcome: rec.review_data?.actual_outcome || '',
      missing_evidence: rec.review_data?.missing_evidence || '',
      notes: rec.review_data?.notes || ''
    });
  };

  const handleSaveReview = async (recId: string) => {
    try {
      const updated = await updateRecordAPI(recId, {
        review_data: reviewForm
      });
      setRecords((prev) => prev.map((r) => (r.id === recId ? updated : r)));
      setEditingReviewId(null);
      setSaveStatusMsg('复盘自省已妥善更新！历史版本已写入修订留痕。');
      loadStats();
      setTimeout(() => setSaveStatusMsg(null), 3500);
    } catch (e: any) {
      alert(`保存复盘失败: ${e.message}`);
    }
  };

  const handleDeleteRecord = async (id: string) => {
    if (confirm('确认删除此条手记记录？')) {
      try {
        await deleteRecordAPI(id, false);
        setRecords((prev) => prev.filter((r) => r.id !== id));
        setTotal((t) => Math.max(0, t - 1));
        loadStats();
      } catch (e: any) {
        alert(`删除失败: ${e.message}`);
      }
    }
  };

  const handleExportAllMarkdown = async () => {
    try {
      const md = await exportRecordsAPI('markdown');
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `玄鉴本地手记全集_${new Date().toISOString().slice(0, 10)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`导出失败: ${e.message}`);
    }
  };

  const handleExportAllJSON = async () => {
    try {
      const jsonStr = await exportRecordsAPI('json');
      const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `玄鉴本地记录完整库_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`导出失败: ${e.message}`);
    }
  };

  const handleExportSingle = async (rec: RecordItem) => {
    try {
      const md = await exportRecordsAPI('markdown', [rec.id]);
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `玄鉴手记_${rec.title.replace(/\s+/g, '_')}_${rec.created_at.slice(0, 10)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`导出失败: ${e.message}`);
    }
  };

  const renderCalculationSummary = (rec: RecordItem) => {
    const calc = rec.calculation_result || {};

    if (rec.record_type === 'divination' && calc.original_hexagram) {
      return (
        <div className="px-3 py-1.5 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] text-xs text-[var(--ink)] flex flex-wrap items-center gap-3">
          <span>本卦：<strong>【{calc.original_hexagram.name}】</strong></span>
          {calc.transformed_hexagram && (
            <span>变卦：<strong>【{calc.transformed_hexagram.name}】</strong></span>
          )}
          {Array.isArray(calc.moving_lines) && (calc.moving_lines.length ?
            <span className="text-[var(--zhusha)]">动爻：第 {calc.moving_lines.join('、')} 爻</span> : <span>静卦 · 无动爻</span>
          )}
        </div>
      );
    }

    if (rec.record_type === 'bazi' && calc.four_pillars) {
      const fp = calc.four_pillars;
      return (
        <div className="px-3 py-1.5 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] text-xs text-[var(--ink)] flex flex-wrap items-center gap-3">
          <span>四柱：<strong>{fp.year?.gan_zhi || ''}年 {fp.month?.gan_zhi || ''}月 {fp.day?.gan_zhi || ''}日 {fp.hour?.gan_zhi || ''}时</strong></span>
          {calc.day_master && (
            <span>日主：<strong>{calc.day_master.gan}{calc.day_master.wuxing}</strong></span>
          )}
          {calc.gender && (
            <span className="text-[var(--ink-subtle)]">({calc.gender})</span>
          )}
        </div>
      );
    }

    if (rec.record_type === 'ziwei') {
      return (
        <div className="px-3 py-1.5 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] text-xs text-[var(--ink)] flex flex-wrap items-center gap-3">
          <span>命宫主星：<strong>{calc.soul_star || '紫微星系'}</strong></span>
          {calc.body_palace && <span>身宫：<strong>{calc.body_palace}</strong></span>}
          {calc.five_elements && <span>局数：<strong>{calc.five_elements}</strong></span>}
          {calc.chinese_date && <span className="text-[var(--ink-subtle)]">{calc.chinese_date}</span>}
        </div>
      );
    }

    if (rec.record_type === 'qimen') {
      return (
        <div className="px-3 py-1.5 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] text-xs text-[var(--ink)] flex flex-wrap items-center gap-3">
          <span>遁甲局：<strong>{calc.dun_type || ''}{calc.ju_number ? `${calc.ju_number}局` : ''}</strong></span>
          {calc.zhi_fu_star && <span>值符星：<strong className="text-[var(--daiqing)]">{calc.zhi_fu_star}</strong></span>}
          {calc.zhi_shi_door && <span>值使门：<strong className="text-[var(--zhusha)]">{calc.zhi_shi_door}</strong></span>}
          {calc.xun_shou && <span className="text-[var(--ink-subtle)]">旬首：{calc.xun_shou}</span>}
        </div>
      );
    }

    if (rec.record_type === 'reflection') {
      return (
        <div className="px-3 py-1.5 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] text-xs text-[var(--ink)] flex flex-wrap items-center gap-3">
          <span>知止评估风险等级：<strong className="text-[var(--zhusha)]">{calc.risk_level || '正常'}</strong></span>
          {calc.alerts_count !== undefined && <span>触发警示：{calc.alerts_count} 项</span>}
        </div>
      );
    }

    return null;
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'divination':
        return '周易卦象';
      case 'bazi':
        return '八字排盘';
      case 'ziwei':
        return '紫微斗数';
      case 'qimen':
        return '奇门遁甲';
      case 'reflection':
        return '知止反思';
      case 'study_note':
        return '研读手记';
      default:
        return '文化手记';
    }
  };

  return (
    <div className="flex flex-col gap-5 w-full">
      {/* 顶部统计与客观复盘宗纲 */}
      <div className="card-xuan p-5 bg-[var(--xuanzhi-light)] border-l-4 border-l-[var(--daiqing)] flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2 font-bold text-[var(--ink)] font-song text-base">
            <Database size={17} className="text-[var(--daiqing)]" />
            <span>我的手记</span>
            <span className="seal-tag-muted text-xs">共 {total} 篇</span>
          </div>
          <span className="text-[11px] text-[var(--ink-subtle)] font-song">本机离线存储 · 隐私私有</span>
        </div>

        <details><summary className="cursor-pointer text-sm text-[var(--ink-muted)]">统计与复盘提示</summary>
        {/* 统计指标 */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[var(--border-light)]">
            <div className="p-2.5 bg-[var(--xuanzhi-card)] rounded border border-[var(--border-light)] flex flex-col items-center">
              <span className="text-xs text-[var(--ink-subtle)]">已存手记</span>
              <span className="font-mono text-base font-bold text-[var(--ink)]">{stats.total_records}</span>
            </div>
            <div className="p-2.5 bg-[var(--xuanzhi-card)] rounded border border-[var(--border-light)] flex flex-col items-center">
              <span className="text-xs text-emerald-700">已事后复盘</span>
              <span className="font-mono text-base font-bold text-emerald-700">{stats.reviewed_count}</span>
            </div>
            <div className="p-2.5 bg-[var(--xuanzhi-card)] rounded border border-[var(--border-light)] flex flex-col items-center">
              <span className="text-xs text-amber-700">待补充复盘</span>
              <span className="font-mono text-base font-bold text-amber-700">{stats.pending_count}</span>
            </div>
            <div className="p-2.5 bg-[var(--xuanzhi-card)] rounded border border-[var(--border-light)] flex flex-col items-center">
              <span className="text-xs text-[var(--daiqing)]">四术分类</span>
              <span className="font-mono text-xs font-bold text-[var(--daiqing)] mt-1">
                易{stats.type_distribution['divination'] || 0} / 八{stats.type_distribution['bazi'] || 0} / 紫{stats.type_distribution['ziwei'] || 0} / 奇{stats.type_distribution['qimen'] || 0}
              </span>
            </div>
          </div>
        )}

        {/* 复盘原则提示 */}
        <div className="p-3 bg-[var(--xuanzhi-card)] rounded text-xs text-[var(--ink-muted)] leading-relaxed border border-[var(--border-light)]">
          <strong className="text-[var(--ink)]">⚖️ 客观复盘准则：</strong>
          玄鉴绝不以“准不准”进行神秘主义打分，也不篡改历史记录。复盘的核心在于对照
          <strong>【当时怎么想 vs 后来发生什么】</strong>，排查当时遗漏的现实商业或人际证据，总结自省良箴，提升未来决策审慎度。
        </div>
        </details>
      </div>

      {/* 检索、分类筛选与视图切换工具栏 */}
      <div className="card-xuan p-4 bg-[var(--xuanzhi-card)] flex flex-col gap-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* 中文搜索框 */}
          <div className="relative flex-1 w-full">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索手记标题、主题、复盘思考或标签..."
              className="input-xuan text-xs py-2 pl-8 pr-16 w-full"
            />
            <Search size={14} className="absolute left-2.5 top-3 text-[var(--ink-subtle)]" />
            <button
              onClick={handleSearch}
              disabled={isLoading}
              className="absolute right-1.5 top-1.5 px-3 py-1 bg-[var(--daiqing)] text-white text-xs rounded flex items-center gap-1"
            >
              {isLoading && <Loader2 size={11} className="animate-spin" />}
              <span>搜索</span>
            </button>
          </div>

          {/* 视图模式切换：列表 vs 时间轴 */}
          <div className="flex items-center gap-1 bg-[var(--border-light)] p-0.5 rounded border border-[var(--border)] shrink-0">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 text-xs rounded flex items-center gap-1 transition ${
                viewMode === 'list'
                  ? 'bg-[var(--daiqing)] text-white font-medium shadow-xs'
                  : 'text-[var(--ink)] hover:bg-[var(--border)]'
              }`}
            >
              <List size={13} />
              <span>列表视图</span>
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 text-xs rounded flex items-center gap-1 transition ${
                viewMode === 'timeline'
                  ? 'bg-[var(--daiqing)] text-white font-medium shadow-xs'
                  : 'text-[var(--ink)] hover:bg-[var(--border)]'
              }`}
            >
              <GitCommit size={13} />
              <span>时间轴复盘</span>
            </button>
          </div>
        </div>

        {/* 类型筛选与批量操作 */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-[var(--border-light)]">
          {/* 类型标签 */}
          <div className="flex items-center gap-1 overflow-x-auto text-xs py-0.5">
            {[
              { id: '', label: '全部' },
              { id: 'divination', label: '周易卦象' },
              { id: 'bazi', label: '八字排盘' },
              { id: 'ziwei', label: '紫微斗数' },
              { id: 'qimen', label: '奇门遁甲' },
              { id: 'reflection', label: '知止反思' },
              { id: 'study_note', label: '研读手记' }
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedType(t.id)}
                className={`px-2 py-1 rounded text-xs transition shrink-0 ${
                  selectedType === t.id
                    ? 'bg-[var(--daiqing)] text-white font-medium'
                    : 'bg-[var(--xuanzhi-light)] text-[var(--ink)] border border-[var(--border)] hover:bg-[var(--border-light)]'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 备份与同步 */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleExportAllMarkdown}
              className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1"
              title="批量导出为 Markdown"
            >
              <FileDown size={12} />
              <span>导出 MD</span>
            </button>
            <button
              onClick={handleExportAllJSON}
              className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1"
              title="备份为 JSON"
            >
              <Database size={12} />
              <span>导出 JSON</span>
            </button>
            <button
              onClick={() => setIsSyncModalOpen(true)}
              className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1 bg-[var(--daiqing)]/10 text-[var(--daiqing)] border-[var(--daiqing)]/30 hover:bg-[var(--daiqing)]/20"
              title="私有云 WebDAV 同步与强加密备份"
            >
              <Cloud size={12} />
              <span>私有云同步与加密</span>
            </button>
          </div>
        </div>
      </div>

      {saveStatusMsg && (
        <div className="p-3 bg-[var(--daiqing-light)] border border-[var(--daiqing)]/30 rounded text-xs text-[var(--daiqing)] flex items-center gap-1.5">
          <CheckCircle2 size={14} />
          <span>{saveStatusMsg}</span>
        </div>
      )}

      {/* 记录内容区 */}
      {records.length === 0 ? (
        <div className="card-xuan p-8 bg-[var(--xuanzhi-light)] text-center text-[var(--ink-muted)] text-xs flex flex-col items-center justify-center gap-2">
          <Database size={28} className="text-[var(--ink-subtle)]" />
          <p className="font-song text-sm font-semibold text-[var(--ink)]">暂无已保存的手记记录</p>
          <p className="text-[11px] text-[var(--ink-subtle)] max-w-sm leading-relaxed">
            系统严格遵循隐私安全，默认不留存排盘起卦与私人问题。
            在【问事】推算或【知止】评估后，可点击“存为手记”将心得保存在本机私有档案中。
          </p>
        </div>
      ) : viewMode === 'timeline' ? (
        /* ──────── 时间轴复盘视图 ──────── */
        <div className="relative pl-6 sm:pl-8 border-l-2 border-[var(--border)] space-y-6 my-2">
          {records.map((rec) => {
            const review = rec.review_data || {};
            const isReviewed = Boolean(review.actual_outcome && review.actual_outcome.trim());
            const hasRevisions = review.revisions && review.revisions.length > 0;
            const isExpandedRev = expandedRevisionsId === rec.id;

            return (
              <div key={rec.id} className="relative group">
                {/* 时间轴节点标记 */}
                <div
                  className={`absolute -left-[31px] sm:-left-[39px] top-4 w-4 h-4 rounded-full border-2 bg-white flex items-center justify-center ${
                    isReviewed ? 'border-emerald-600 ring-2 ring-emerald-100' : 'border-amber-600 ring-2 ring-amber-100'
                  }`}
                >
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${isReviewed ? 'bg-emerald-600' : 'bg-amber-600'}`}
                  />
                </div>

                {/* 卡片主体 */}
                <div className="card-xuan p-5 bg-[var(--xuanzhi-card)] flex flex-col gap-3 shadow-xs">
                  {/* 时间与状态标头 */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 border-b border-[var(--border-light)] pb-2.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="seal-tag">{getTypeLabel(rec.record_type)}</span>
                      <h4 className="font-song font-bold text-base text-[var(--ink)]">
                        {rec.title}
                      </h4>
                      {isReviewed ? (
                        <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded font-medium flex items-center gap-0.5">
                          <Check size={10} />
                          已完成事后复盘
                        </span>
                      ) : (
                        <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium flex items-center gap-0.5">
                          <AlertCircle size={10} />
                          待补充现实结果
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-[var(--ink-subtle)] font-mono flex items-center gap-1">
                      <Clock size={12} />
                      {new Date(rec.created_at).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false})}
                    </span>
                  </div>

                  {/* 象数推算摘要 */}
                  {renderCalculationSummary(rec)}

                  {/* 对照卡：当时预期 vs 后来结果 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs mt-1">
                    <div className="p-3 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] flex flex-col gap-1">
                      <div className="font-song font-bold text-[var(--daiqing)] flex items-center gap-1">
                        <Sparkles size={13} />
                        <span>当时预判与假设 (怎么想)</span>
                      </div>
                      <p className="text-[var(--ink-muted)] leading-relaxed min-h-[40px]">
                        {review.original_thought || '未记录当时的直觉预判。可点击右下方编辑补充。'}
                      </p>
                    </div>

                    <div className="p-3 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] flex flex-col gap-1">
                      <div className="font-song font-bold text-emerald-800 flex items-center gap-1">
                        <TrendingUp size={13} />
                        <span>现实实际演进 (后来发生什么)</span>
                      </div>
                      <p className="text-[var(--ink-muted)] leading-relaxed min-h-[40px]">
                        {review.actual_outcome || '尚无后来现实演进记录。发生后续后请及时复盘留痕。'}
                      </p>
                    </div>
                  </div>

                  {/* 忽略的证据与自省良箴 */}
                  {(review.missing_evidence || review.notes) && (
                    <div className="p-3 bg-[var(--xuanzhi-light)]/70 rounded border border-[var(--border-light)] text-xs flex flex-col gap-1.5">
                      {review.missing_evidence && (
                        <div className="text-[var(--ink-muted)]">
                          <strong className="text-[var(--zhusha)]">当时遗漏的现实证据：</strong>
                          {review.missing_evidence}
                        </div>
                      )}
                      {review.notes && (
                        <div className="text-[var(--ink)] font-song italic">
                          <strong className="text-[var(--daiqing)]">复盘良箴：</strong>
                          “{review.notes}”
                        </div>
                      )}
                    </div>
                  )}

                  {/* 历史版本留痕折叠 */}
                  {hasRevisions && (
                    <div className="border-t border-[var(--border-light)] pt-2 text-xs">
                      <button
                        onClick={() =>
                          setExpandedRevisionsId(isExpandedRev ? null : rec.id)
                        }
                        className="text-[var(--ink-subtle)] hover:text-[var(--daiqing)] flex items-center gap-1 text-[11px]"
                      >
                        <History size={12} />
                        <span>
                          {isExpandedRev ? '收起修订历史' : `查看历次复盘修订轨迹 (共 ${review.revisions!.length} 次)`}
                        </span>
                      </button>
                      {isExpandedRev && (
                        <div className="mt-2 space-y-2 p-2 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)]">
                          {review.revisions!.map((rev, idx) => (
                            <div key={idx} className="p-2 border-b border-[var(--border-light)] last:border-b-0 text-[11px] text-[var(--ink-muted)]">
                              <div className="font-mono text-xs text-[var(--ink-subtle)] mb-1">
                                第 {idx + 1} 次修订时间：{rev.revised_at.slice(0, 19).replace('T', ' ')}
                              </div>
                              {rev.previous_outcome && (
                                <p><strong>当时结果：</strong>{rev.previous_outcome}</p>
                              )}
                              {rev.previous_thought && (
                                <p><strong>当时预判：</strong>{rev.previous_thought}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 底部操作条 */}
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-[var(--border-light)]">
                    <button
                      onClick={() => handleStartEditReview(rec)}
                      className="text-[var(--daiqing)] hover:underline flex items-center gap-1 font-medium"
                    >
                      <Edit3 size={13} />
                      <span>{isReviewed ? '修改复盘 / 记录新修订' : '补充事后复盘'}</span>
                    </button>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleExportSingle(rec)}
                        className="btn-secondary py-1 px-2 text-xs flex items-center gap-1"
                      >
                        <FileDown size={11} />
                        <span>导出 MD</span>
                      </button>
                      <button
                        onClick={() => handleDeleteRecord(rec.id)}
                        className="btn-secondary py-1 px-2 text-xs text-[var(--zhusha)] border-[var(--zhusha)]/30 hover:bg-[var(--zhusha-light)]"
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* ──────── 标准列表视图 ──────── */
        <div className="flex flex-col gap-3">
          {records.map((rec) => {
            const isExpanded = expandedId === rec.id;
            const isEditing = editingReviewId === rec.id;
            const review = rec.review_data || {};
            const hasRevisions = review.revisions && review.revisions.length > 0;
            const isExpandedRev = expandedRevisionsId === rec.id;

            return (
              <div
                key={rec.id}
                className="card-xuan p-5 bg-[var(--xuanzhi-card)] flex flex-col gap-3 transition"
              >
                {/* 头部信息 */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-light)] pb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="seal-tag-muted">{getTypeLabel(rec.record_type)}</span>
                    <h4 className="font-song font-bold text-base text-[var(--ink)]">
                      {rec.title}
                    </h4>
                    {review.actual_outcome ? (
                      <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded font-medium">
                        已复盘
                      </span>
                    ) : (
                      <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium">
                        待复盘
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[var(--ink-subtle)]">
                    <Clock size={12} />
                    <span>{new Date(rec.created_at).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false})}</span>
                  </div>
                </div>

                {/* 主题 */}
                {rec.topic && (
                  <p className="text-xs text-[var(--ink-muted)]">
                    <strong className="text-[var(--ink)]">主题：</strong>{rec.topic}
                  </p>
                )}

                {/* 象数概要 */}
                {renderCalculationSummary(rec)}

                {/* 标签 */}
                {rec.tags && (
                  <div className="flex flex-wrap items-center gap-1.5 text-xs text-[var(--ink-subtle)]">
                    <Tag size={12} />
                    {(Array.isArray(rec.tags) ? rec.tags : String(rec.tags).split(',')).map((t, i) => (
                      <span
                        key={i}
                        className="px-1.5 py-0.5 rounded bg-[var(--border-light)] text-[var(--ink-muted)] text-[11px]"
                      >
                        {String(t).trim()}
                      </span>
                    ))}
                  </div>
                )}

                {/* 展开复盘区 */}
                {isExpanded && (
                  <div className="mt-2 pt-3 border-t border-[var(--border-light)] flex flex-col gap-3">
                    {rec.calculation_result?.reading && (
                      <section className="p-4 rounded bg-[var(--xuanzhi-light)] border border-[var(--border)] space-y-2 text-sm">
                        <h4 className="font-song font-bold">当时的解读 · {rec.calculation_result.reading.headline}</h4>
                        <p>{rec.calculation_result.reading.summary}</p>
                        <p>{rec.calculation_result.reading.context}</p>
                        <p>{rec.calculation_result.reading.action}</p>
                        <details className="text-xs text-[var(--ink-muted)]">
                          <summary className="cursor-pointer">查看原始起卦记录</summary>
                          <p className="mt-2">问题：{rec.calculation_result.topic}</p>
                          <p>起卦时间：{new Date(rec.calculation_result.cast_at).toLocaleString()}</p>
                          <p>爻值（自下而上）：{rec.calculation_result.input_lines?.join('、')}</p>
                          {rec.calculation_result.coin_flips?.map((coins: number[], i: number) => <p key={i}>第 {i+1} 次：{coins.join(' + ')} = {coins.reduce((a,b)=>a+b,0)}</p>)}
                        </details>
                      </section>
                    )}
                    <div className="font-song font-bold text-xs text-[var(--daiqing)] flex items-center justify-between">
                      <span>【事后复盘思考与留痕】（不改动原始卦象）</span>
                      {!isEditing && (
                        <button
                          onClick={() => handleStartEditReview(rec)}
                          className="text-xs text-[var(--daiqing)] hover:underline flex items-center gap-1"
                        >
                          <Edit3 size={12} />
                          <span>编辑复盘</span>
                        </button>
                      )}
                    </div>

                    {isEditing ? (
                      <div className="flex flex-col gap-2.5 p-3 bg-[var(--xuanzhi-light)] rounded border border-[var(--border)] text-xs">
                        <div>
                          <label className="block text-[var(--ink-muted)] mb-1">
                            1. 原先怎么想 (当时的预测与主观假设)：
                          </label>
                          <textarea
                            value={reviewForm.original_thought}
                            onChange={(e) =>
                              setReviewForm({ ...reviewForm, original_thought: e.target.value })
                            }
                            className="input-xuan w-full text-xs h-16"
                            placeholder="例如：当时以为万事俱备，对方会严格履约..."
                          />
                        </div>
                        <div>
                          <label className="block text-[var(--ink-muted)] mb-1">
                            2. 后来发生什么 (现实实际演进)：
                          </label>
                          <textarea
                            value={reviewForm.actual_outcome}
                            onChange={(e) =>
                              setReviewForm({ ...reviewForm, actual_outcome: e.target.value })
                            }
                            className="input-xuan w-full text-xs h-16"
                            placeholder="例如：次月发生突发政策调整，项目进度延期..."
                          />
                        </div>
                        <div>
                          <label className="block text-[var(--ink-muted)] mb-1">
                            3. 当时缺什么客观证据 (未被注意的盲点)：
                          </label>
                          <input
                            type="text"
                            value={reviewForm.missing_evidence}
                            onChange={(e) =>
                              setReviewForm({ ...reviewForm, missing_evidence: e.target.value })
                            }
                            className="input-xuan w-full text-xs"
                            placeholder="例如：未核实对方母公司的债务评级与现金流报表..."
                          />
                        </div>
                        <div>
                          <label className="block text-[var(--ink-muted)] mb-1">
                            4. 复盘自省良箴：
                          </label>
                          <textarea
                            value={reviewForm.notes}
                            onChange={(e) =>
                              setReviewForm({ ...reviewForm, notes: e.target.value })
                            }
                            className="input-xuan w-full text-xs h-16"
                            placeholder="知止而后有定，事预则立..."
                          />
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <button
                            onClick={() => handleSaveReview(rec.id)}
                            className="btn-primary py-1 px-4 text-xs font-song"
                          >
                            保存复盘手记 (写入修订历史)
                          </button>
                          <button
                            onClick={() => setEditingReviewId(null)}
                            className="btn-secondary py-1 px-3 text-xs"
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-2 p-3 bg-[var(--xuanzhi-light)] rounded border border-[var(--border-light)] text-xs text-[var(--ink-muted)]">
                        {review.original_thought || review.actual_outcome || review.missing_evidence || review.notes ? (
                          <>
                            {review.original_thought && (
                              <p><strong>原先怎么想：</strong>{review.original_thought}</p>
                            )}
                            {review.actual_outcome && (
                              <p><strong>后来发生什么：</strong>{review.actual_outcome}</p>
                            )}
                            {review.missing_evidence && (
                              <p><strong>缺什么证据：</strong>{review.missing_evidence}</p>
                            )}
                            {review.notes && (
                              <p className="text-[var(--ink)] font-song italic">
                                <strong>自省感悟：</strong>“{review.notes}”
                              </p>
                            )}
                          </>
                        ) : (
                          <div className="text-[var(--ink-subtle)] text-center py-2">
                            暂无事后复盘思考。随时点击“编辑复盘”追加现实结果。
                          </div>
                        )}

                        {/* 修订历史 */}
                        {hasRevisions && (
                          <div className="border-t border-[var(--border-light)] pt-2 mt-2">
                            <button
                              onClick={() => setExpandedRevisionsId(isExpandedRev ? null : rec.id)}
                              className="text-[11px] text-[var(--ink-subtle)] hover:text-[var(--daiqing)] flex items-center gap-1"
                            >
                              <History size={12} />
                              <span>{isExpandedRev ? '收起修订历史' : `查看历次复盘修订记录 (${review.revisions!.length} 次)`}</span>
                            </button>
                            {isExpandedRev && (
                              <div className="mt-2 space-y-1.5 p-2 bg-[var(--xuanzhi-card)] rounded border border-[var(--border-light)] text-[11px]">
                                {review.revisions!.map((rev, i) => (
                                  <div key={i} className="border-b border-[var(--border-light)] pb-1 last:border-0">
                                    <span className="font-mono text-xs text-[var(--ink-subtle)]">
                                      [{rev.revised_at.slice(0, 16).replace('T', ' ')}]
                                    </span>
                                    <span className="ml-1 text-[var(--ink-muted)]">
                                      {rev.previous_outcome || rev.previous_thought || '更新了复盘记录'}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* 底部功能条 */}
                <div className="pt-2 flex items-center justify-between text-xs border-t border-[var(--border-light)] mt-1">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : rec.id)}
                    className="text-[var(--daiqing)] hover:underline flex items-center gap-1 font-medium"
                  >
                    <span>{isExpanded ? '收起复盘详情' : '展开复盘与推算明细'}</span>
                    {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleExportSingle(rec)}
                      className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1"
                    >
                      <FileDown size={12} />
                      <span>导出 MD</span>
                    </button>
                    <button
                      onClick={() => handleDeleteRecord(rec.id)}
                      className="btn-secondary py-1 px-2 text-xs text-[var(--zhusha)] border-[var(--zhusha)]/30 hover:bg-[var(--zhusha-light)]"
                      title="删除记录"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 私有云同步与加密备份弹窗 */}
      <SyncBackupModal
        isOpen={isSyncModalOpen}
        onClose={() => setIsSyncModalOpen(false)}
        onDataRestored={() => {
          loadRecords();
          loadStats();
        }}
      />
    </div>
  );
};
