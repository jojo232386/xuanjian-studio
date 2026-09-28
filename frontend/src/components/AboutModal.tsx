// frontend/src/components/AboutModal.tsx - “关于玄鉴”极简弹窗与客户系统操作
// 遵循宋式清雅设计规范：宣纸、黛青、墨夜、知止守正，完全脱敏，提供本地文件与服务操作

import React, { useState, useEffect } from 'react';
import { X, FolderOpen, Power, Copy, Check, ShieldCheck, RefreshCw, Archive } from 'lucide-react';
import { fetchSystemInfoAPI, fetchSystemDiagnosticsAPI, openDataDirAPI, shutdownServerAPI } from '../api';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenSyncBackup?: () => void;
}

export const AboutModal: React.FC<AboutModalProps> = ({
  isOpen,
  onClose,
  onOpenSyncBackup
}) => {
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isShuttingDown, setIsShuttingDown] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadInfo();
    } else {
      setActionMsg(null);
      setError(null);
      setCopied(false);
    }
  }, [isOpen]);

  const loadInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSystemInfoAPI();
      setInfo(data);
    } catch (err: any) {
      setError(err?.message || '获取系统信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDataDir = async () => {
    try {
      setActionMsg('正在打开系统数据目录...');
      await openDataDirAPI();
      setActionMsg('已在访达 (Finder) 中打开数据目录');
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: any) {
      setError(err?.message || '无法自动打开目录，请手动在访达中查阅 ~/Library/Application Support/XuanJian');
    }
  };

  const handleCopyDiagnostics = async () => {
    try {
      const diag = await fetchSystemDiagnosticsAPI();
      const text = JSON.stringify(diag, null, 2);
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setActionMsg('已复制脱敏诊断信息至剪贴板（不含生辰、密钥与手记）');
      setTimeout(() => {
        setCopied(false);
        setActionMsg(null);
      }, 4000);
    } catch (err: any) {
      setError(err?.message || '复制诊断信息失败');
    }
  };

  const handleShutdown = async () => {
    if (!window.confirm('确定要停止「玄鉴·书房」后台服务吗？\n停止后此网页将失去连接，如需再次使用请重新启动「玄鉴·书房.app」。')) {
      return;
    }
    try {
      setIsShuttingDown(true);
      setActionMsg('正在安全停止玄鉴后台服务...');
      await shutdownServerAPI();
      setActionMsg('玄鉴后台服务已安全退出。您可以直接关闭此浏览器标签页。');
    } catch {
      // 关机时可能连接直接断开
      setIsShuttingDown(true);
      setActionMsg('玄鉴后台服务已停止。您可以直接关闭此浏览器标签页。');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-[var(--xuanzhi-card)] border border-[var(--border)] rounded-lg shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        {/* 顶部标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-light)] bg-[var(--xuanzhi-light)]">
          <div className="flex items-center gap-2">
            <span className="seal-tag">慎初</span>
            <h2 className="font-song font-bold text-lg text-[var(--ink)]">关于 玄鉴·书房</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--border-light)] transition"
            title="关闭弹窗"
          >
            <X size={18} />
          </button>
        </div>

        {/* 主体内容 */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-[var(--ink)]">
          {/* 状态提示 */}
          {actionMsg && (
            <div className="p-2.5 rounded bg-[var(--daiqing)]/10 border border-[var(--daiqing)]/20 text-[var(--daiqing)] text-xs flex items-center gap-2">
              <ShieldCheck size={15} />
              <span>{actionMsg}</span>
            </div>
          )}

          {error && (
            <div className="p-2.5 rounded bg-[var(--zhusha)]/10 border border-[var(--zhusha)]/20 text-[var(--zhusha)] text-xs">
              {error}
            </div>
          )}

          {/* 软件题辞与版本 */}
          <div className="flex items-start justify-between pb-3 border-b border-[var(--border-light)]">
            <div>
              <div className="font-song text-base font-bold text-[var(--ink)]">
                玄鉴·书房 (XuanJian Studio)
              </div>
              <div className="text-[11px] text-[var(--ink-muted)] mt-0.5">
                macOS Apple Silicon 客户试用版 · 纯本地免API
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-[var(--daiqing)] text-white">
              v3.0.1
            </span>
          </div>

          {/* 核心规格信息 */}
          <div className="space-y-2 bg-[var(--xuanzhi-light)] p-3.5 rounded border border-[var(--border-light)]">
            <div className="flex items-center justify-between">
              <span className="text-[var(--ink-muted)]">运行模式</span>
              <span className="font-medium text-[var(--ink)]">本地单机 · 离线优先 · 零API配置</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--ink-muted)]">内置研读状态</span>
              <span className="font-medium text-emerald-700 dark:text-emerald-400">已就绪 (免API全本地研读)</span>
            </div>
            <div className="flex flex-col gap-1 pt-1 border-t border-[var(--border-light)]">
              <div className="flex items-center justify-between">
                <span className="text-[var(--ink-muted)]">私有数据目录</span>
                <span className="font-mono text-[10px] text-[var(--ink-subtle)] truncate max-w-[240px]" title={info?.data_dir || '~/Library/Application Support/XuanJian'}>
                  {info?.data_dir || '~/Library/Application Support/XuanJian'}
                </span>
              </div>
            </div>
          </div>

          {/* 四术一体与典籍版本 */}
          <div>
            <div className="font-song font-semibold text-xs text-[var(--ink)] mb-2 flex items-center justify-between">
              <span>四术一体与文化研读引擎</span>
              <button
                onClick={loadInfo}
                className="text-[10px] text-[var(--daiqing)] hover:underline flex items-center gap-1"
                disabled={loading}
              >
                <RefreshCw size={10} className={loading ? 'animate-spin' : ''} />
                <span>刷新检查</span>
              </button>
            </div>
            <div className="grid grid-cols-1 gap-1.5 text-[11px]">
              <div className="flex items-center justify-between p-2 rounded bg-[var(--border-light)]/40">
                <span className="font-medium">周易象数</span>
                <span className="text-[var(--ink-muted)]">确定性互错综卦与变爻图 v3.0.1</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[var(--border-light)]/40">
                <span className="font-medium">八字推算</span>
                <span className="text-[var(--ink-muted)]">lunar-python v1.4.8 (节气分秒精准)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[var(--border-light)]/40">
                <span className="font-medium">紫微斗数</span>
                <span className="text-[var(--ink-muted)]">iztro v2.6.1 (私有独立 Node Worker)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[var(--border-light)]/40">
                <span className="font-medium">奇门遁甲</span>
                <span className="text-[var(--ink-muted)]">时家转盘拆补九宫 (bigfishmarquis)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[var(--border-light)]/40">
                <span className="font-medium">典籍研读</span>
                <span className="text-[var(--ink-muted)]">传世《道德经》八十一章与协纪辨方书考据</span>
              </div>
            </div>
          </div>

          {/* 隐私与知止原则承诺 */}
          <p className="text-[10px] text-[var(--ink-subtle)] leading-relaxed border-l-2 border-[var(--daiqing)] pl-2.5">
            以易明理，知止避险。玄鉴·书房绝不将象数推衍作为现实投资、医疗或法律决断依据；
            所有手记与排盘数据仅保存在您的本地设备，不上传云端，不收集个人生辰。
          </p>
        </div>

        {/* 底部操作按钮 */}
        <div className="p-4 border-t border-[var(--border-light)] bg-[var(--xuanzhi-light)] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenDataDir}
              disabled={isShuttingDown}
              className="px-3 py-1.5 rounded border border-[var(--border)] text-xs text-[var(--ink)] hover:bg-[var(--xuanzhi-card)] flex items-center gap-1.5 transition"
              title="在访达中打开数据存储目录"
            >
              <FolderOpen size={13} className="text-[var(--daiqing)]" />
              <span>打开数据目录</span>
            </button>

            {onOpenSyncBackup && (
              <button
                onClick={() => {
                  onClose();
                  onOpenSyncBackup();
                }}
                disabled={isShuttingDown}
                className="px-3 py-1.5 rounded border border-[var(--border)] text-xs text-[var(--ink)] hover:bg-[var(--xuanzhi-card)] flex items-center gap-1.5 transition"
                title="导出 AES-256 加密备份"
              >
                <Archive size={13} className="text-[var(--daiqing)]" />
                <span>导出备份</span>
              </button>
            )}

            <button
              onClick={handleCopyDiagnostics}
              disabled={isShuttingDown}
              className="px-3 py-1.5 rounded border border-[var(--border)] text-xs text-[var(--ink)] hover:bg-[var(--xuanzhi-card)] flex items-center gap-1.5 transition"
              title="复制脱敏环境诊断信息"
            >
              {copied ? <Check size={13} className="text-green-600" /> : <Copy size={13} />}
              <span>{copied ? '已复制' : '复制诊断信息'}</span>
            </button>
          </div>

          <button
            onClick={handleShutdown}
            disabled={isShuttingDown}
            className="px-3 py-1.5 rounded bg-[var(--zhusha)]/10 border border-[var(--zhusha)]/30 text-xs text-[var(--zhusha)] hover:bg-[var(--zhusha)]/20 flex items-center gap-1.5 transition"
            title="安全退出玄鉴后台服务"
          >
            <Power size={13} />
            <span>停止玄鉴</span>
          </button>
        </div>
      </div>
    </div>
  );
};
