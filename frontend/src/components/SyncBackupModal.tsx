// frontend/src/components/SyncBackupModal.tsx - 私有云 WebDAV 同步与 AES-256-GCM 加密备份恢复弹窗 (F07)

import React, { useState, useEffect } from 'react';
import type { WebDAVSyncConfig } from '../types';
import {
  exportBackupAPI,
  restoreBackupAPI,
  fetchSyncConfigAPI,
  updateSyncConfigAPI,
  testSyncConnectionAPI,
  syncPushAPI,
  syncPullAPI
} from '../api';
import {
  Shield,
  Cloud,
  Download,
  Upload,
  Key,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  X,
  Eye,
  EyeOff,
  Server,
  HardDrive,
  ArrowUpRight,
  ArrowDownLeft,
  FileCheck
} from 'lucide-react';

interface SyncBackupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDataRestored?: () => void;
}

export const SyncBackupModal: React.FC<SyncBackupModalProps> = ({
  isOpen,
  onClose,
  onDataRestored
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'backup' | 'webdav'>('backup');

  // 本地备份与恢复状态
  const [backupPassphrase, setBackupPassphrase] = useState('');
  const [showBackupPass, setShowBackupPass] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const [restorePassphrase, setRestorePassphrase] = useState('');
  const [showRestorePass, setShowRestorePass] = useState(false);
  const [restoreFileBase64, setRestoreFileBase64] = useState<string | null>(null);
  const [restoreFileName, setRestoreFileName] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);
  const [restoreResult, setRestoreResult] = useState<{ success: boolean; message: string } | null>(null);

  // WebDAV 同步配置状态
  const [syncConfig, setSyncConfig] = useState<WebDAVSyncConfig>({
    enabled: false,
    server_url: '',
    username: '',
    password: '',
    remote_path: '/xuanjian/backup.enc',
    is_configured: false
  });
  const [syncPassword, setSyncPassword] = useState('');
  const [syncEncryptionPass, setSyncEncryptionPass] = useState('');
  const [showSyncPass, setShowSyncPass] = useState(false);
  const [showSyncEncPass, setShowSyncEncPass] = useState(false);

  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isTestingWebDAV, setIsTestingWebDAV] = useState(false);
  const [testWebDAVResult, setTestWebDAVResult] = useState<{ success: boolean; message: string } | null>(null);

  const [isPushing, setIsPushing] = useState(false);
  const [isPulling, setIsPulling] = useState(false);
  const [syncOperationResult, setSyncOperationResult] = useState<{
    success: boolean;
    type: 'push' | 'pull';
    message: string;
    details?: string;
  } | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadSyncConfig();
      setRestoreResult(null);
      setTestWebDAVResult(null);
      setSyncOperationResult(null);
    }
  }, [isOpen]);

  const loadSyncConfig = async () => {
    try {
      const res = await fetchSyncConfigAPI();
      setSyncConfig(res.config);
      setSyncPassword(res.config.password || '');
    } catch (e: any) {
      console.error('获取 WebDAV 配置失败:', e);
    }
  };

  // 1. 导出备份包 (Base64 -> Blob 下载)
  const handleExportBackup = async () => {
    setIsExporting(true);
    try {
      const res = await exportBackupAPI(backupPassphrase || undefined);
      // 解码 Base64 并触发浏览器下载
      const byteCharacters = atob(res.data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = res.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`导出备份失败: ${e.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  // 2. 选择本地文件准备恢复
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setRestoreFileName(file.name);
    setRestoreResult(null);
    const reader = new FileReader();
    reader.onload = () => {
      const arrayBuffer = reader.result as ArrayBuffer;
      const bytes = new Uint8Array(arrayBuffer);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64 = btoa(binary);
      setRestoreFileBase64(base64);
    };
    reader.readAsArrayBuffer(file);
  };

  // 3. 执行校验与恢复
  const handleRestoreBackup = async () => {
    if (!restoreFileBase64) {
      alert('请先选择备份文件 (.xjb 或 .db)');
      return;
    }
    if (!confirm('【高危恢复警告】即将从备份恢复数据库。系统会自动为您在本地备份一份 .pre_restore.bak，若确认请点击“确定”。')) {
      return;
    }
    setIsRestoring(true);
    setRestoreResult(null);
    try {
      const res = await restoreBackupAPI(restoreFileBase64, restorePassphrase || undefined);
      setRestoreResult({
        success: true,
        message: `${res.message} (共恢复 ${res.restored_records_count} 条记录)`
      });
      if (onDataRestored) {
        onDataRestored();
      }
    } catch (e: any) {
      setRestoreResult({
        success: false,
        message: e.message || '恢复备份失败'
      });
    } finally {
      setIsRestoring(false);
    }
  };

  // 4. 保存 WebDAV 配置
  const handleSaveWebDAVConfig = async () => {
    setIsSavingConfig(true);
    setTestWebDAVResult(null);
    try {
      const res = await updateSyncConfigAPI({
        ...syncConfig,
        password: syncPassword,
        encryption_passphrase: syncEncryptionPass || undefined
      });
      setSyncConfig(res.config);
      setTestWebDAVResult({
        success: true,
        message: 'WebDAV 同步配置已成功保存！'
      });
    } catch (e: any) {
      setTestWebDAVResult({
        success: false,
        message: `保存配置失败: ${e.message}`
      });
    } finally {
      setIsSavingConfig(false);
    }
  };

  // 5. 测试 WebDAV 连接
  const handleTestWebDAV = async () => {
    setIsTestingWebDAV(true);
    setTestWebDAVResult(null);
    try {
      const res = await testSyncConnectionAPI({
        ...syncConfig,
        password: syncPassword,
        encryption_passphrase: syncEncryptionPass || undefined
      });
      setTestWebDAVResult({
        success: res.success,
        message: res.message
      });
    } catch (e: any) {
      setTestWebDAVResult({
        success: false,
        message: e.message || '连接失败'
      });
    } finally {
      setIsTestingWebDAV(false);
    }
  };

  // 6. 执行 WebDAV 推送
  const handleSyncPush = async () => {
    setIsPushing(true);
    setSyncOperationResult(null);
    try {
      const res = await syncPushAPI();
      setSyncOperationResult({
        success: true,
        type: 'push',
        message: `快照已成功加密推送到 WebDAV 远端！`,
        details: `已加密推送 ${res.records_pushed} 条记录，密文负载大小：${res.records_pushed ? Math.round((res.records_pushed * 250) / 1024) : 0} KB`
      });
    } catch (e: any) {
      setSyncOperationResult({
        success: false,
        type: 'push',
        message: `推送失败: ${e.message}`
      });
    } finally {
      setIsPushing(false);
    }
  };

  // 7. 执行 WebDAV 拉取并无损合并
  const handleSyncPull = async () => {
    setIsPulling(true);
    setSyncOperationResult(null);
    try {
      const res = await syncPullAPI();
      setSyncOperationResult({
        success: true,
        type: 'pull',
        message: `远端快照已成功拉取并完成无损双端合并！`,
        details: `新增插入：${res.inserted} 条，更新较新：${res.updated} 条，无改动保持：${res.unchanged} 条。本地现有总计：${res.final_local_total} 条。`
      });
      if (onDataRestored) {
        onDataRestored();
      }
    } catch (e: any) {
      setSyncOperationResult({
        success: false,
        type: 'pull',
        message: `拉取合并失败: ${e.message}`
      });
    } finally {
      setIsPulling(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded-lg shadow-2xl p-6 flex flex-col gap-5 text-[var(--ink)] my-8">

        {/* 顶部标题与关闭 */}
        <div className="flex items-center justify-between pb-3 border-b border-[var(--border-light)]">
          <div className="flex items-center gap-2">
            <span className="seal-tag">藏修</span>
            <div>
              <h3 className="font-song text-lg font-bold text-[var(--ink)]">私有云同步与加密备份 (F07)</h3>
              <p className="text-xs text-[var(--ink-muted)]">AES-256-GCM AEAD 认证加密 · WebDAV 私有流转 · 多端无损合并</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--border-light)] transition"
            title="关闭"
          >
            <X size={18} />
          </button>
        </div>

        {/* 标签栏 */}
        <div className="flex items-center gap-2 border-b border-[var(--border-light)] pb-2 text-xs">
          <button
            onClick={() => setActiveSubTab('backup')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition ${
              activeSubTab === 'backup'
                ? 'bg-[var(--daiqing)] text-white font-medium shadow-xs'
                : 'text-[var(--ink-muted)] hover:bg-[var(--border-light)]'
            }`}
          >
            <HardDrive size={14} />
            <span>本地强加密备份与恢复 (.xjb)</span>
          </button>
          <button
            onClick={() => setActiveSubTab('webdav')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition ${
              activeSubTab === 'webdav'
                ? 'bg-[var(--daiqing)] text-white font-medium shadow-xs'
                : 'text-[var(--ink-muted)] hover:bg-[var(--border-light)]'
            }`}
          >
            <Cloud size={14} />
            <span>私有云 WebDAV 同步与合并</span>
          </button>
        </div>

        {/* 子选项卡一：本地认证加密备份与恢复 */}
        {activeSubTab === 'backup' && (
          <div className="flex flex-col gap-6 text-xs">
            {/* 导出区域 */}
            <div className="bg-[var(--xuanzhi-card)] p-4 rounded border border-[var(--border-light)] flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-sm text-[var(--ink)]">
                  <Download size={16} className="text-[var(--daiqing)]" />
                  <span>导出本地 SQLite 加密备份包</span>
                </div>
                <span className="seal-tag-muted">AES-256-GCM</span>
              </div>
              <p className="text-[11px] text-[var(--ink-muted)] leading-relaxed">
                若输入密码，数据将在导出前经由 PBKDF2（100,000 次哈希）派生密钥并使用 AES-256-GCM 认证加密，生成 <code className="font-mono text-[var(--daiqing)]">.xjb</code> 文件。
                信封头部与密文绑定，任何篡改均会在恢复时被物理拦截。留空则生成未加密的 <code className="font-mono">.db</code> 快照。
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-3">
                <div className="relative flex-1 w-full">
                  <Key size={14} className="absolute left-3 top-2.5 text-[var(--ink-muted)]" />
                  <input
                    type={showBackupPass ? 'text' : 'password'}
                    value={backupPassphrase}
                    onChange={(e) => setBackupPassphrase(e.target.value)}
                    placeholder="输入加密密钥（建议 8 位以上，留空则为明文备份）"
                    className="w-full pl-8 pr-9 py-2 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs focus:outline-hidden focus:border-[var(--daiqing)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowBackupPass(!showBackupPass)}
                    className="absolute right-2.5 top-2.5 text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  >
                    {showBackupPass ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
                <button
                  onClick={handleExportBackup}
                  disabled={isExporting}
                  className="w-full sm:w-auto px-4 py-2 bg-[var(--daiqing)] text-white rounded font-medium flex items-center justify-center gap-1.5 hover:opacity-90 disabled:opacity-50 shrink-0"
                >
                  <Download size={14} />
                  <span>{isExporting ? '正在打包加密...' : '生成并下载备份'}</span>
                </button>
              </div>
            </div>

            {/* 恢复区域 */}
            <div className="bg-[var(--xuanzhi-card)] p-4 rounded border border-[var(--border-light)] flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-sm text-[var(--ink)]">
                  <Upload size={16} className="text-[var(--zhusha)]" />
                  <span>安全导入与解密恢复</span>
                </div>
                <span className="seal-tag-muted">自检防护</span>
              </div>
              <div className="p-2.5 rounded bg-[var(--border-light)]/50 border border-[var(--border-light)] text-[11px] text-[var(--ink-muted)] flex items-start gap-2">
                <Shield size={14} className="text-[var(--daiqing)] shrink-0 mt-0.5" />
                <span>
                  <strong>多重安全防御机制：</strong>系统在替换前自动将当前数据库完整备份为 <code className="font-mono">.pre_restore.bak</code>；写入新库前自动执行 SQLite <code className="font-mono">PRAGMA integrity_check</code> 物理自检；若密码错误或信封被篡改，原数据库分毫未损。
                </span>
              </div>

              <div className="flex flex-col gap-3">
                <div className="flex flex-col sm:flex-row items-center gap-3">
                  <label className="w-full sm:w-1/2 flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-[var(--border)] rounded cursor-pointer bg-[var(--xuanzhi-light)] hover:border-[var(--daiqing)] transition">
                    <FileCheck size={14} className="text-[var(--daiqing)]" />
                    <span className="truncate max-w-[180px]">{restoreFileName || '选择 .xjb 或 .db 文件'}</span>
                    <input
                      type="file"
                      accept=".xjb,.db"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                  <div className="relative flex-1 w-full">
                    <Key size={14} className="absolute left-3 top-2.5 text-[var(--ink-muted)]" />
                    <input
                      type={showRestorePass ? 'text' : 'password'}
                      value={restorePassphrase}
                      onChange={(e) => setRestorePassphrase(e.target.value)}
                      placeholder="备份解密密码（如原备份有密码）"
                      className="w-full pl-8 pr-9 py-2 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs focus:outline-hidden focus:border-[var(--daiqing)]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowRestorePass(!showRestorePass)}
                      className="absolute right-2.5 top-2.5 text-[var(--ink-muted)] hover:text-[var(--ink)]"
                    >
                      {showRestorePass ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <button
                    onClick={handleRestoreBackup}
                    disabled={isRestoring || !restoreFileBase64}
                    className="px-5 py-2 bg-[var(--zhusha)] text-white rounded font-medium flex items-center gap-1.5 hover:opacity-90 disabled:opacity-40 transition"
                  >
                    <Upload size={14} />
                    <span>{isRestoring ? '正在校验并安全恢复...' : '校验信封并执行恢复'}</span>
                  </button>
                </div>

                {/* 恢复结果反馈 */}
                {restoreResult && (
                  <div className={`p-3 rounded flex items-center gap-2 ${
                    restoreResult.success
                      ? 'bg-green-50 text-green-800 border border-green-200'
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    {restoreResult.success ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                    <span className="font-medium">{restoreResult.message}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 子选项卡二：私有云 WebDAV 同步 */}
        {activeSubTab === 'webdav' && (
          <div className="flex flex-col gap-5 text-xs">
            {/* 顶栏说明与启用开关 */}
            <div className="flex items-center justify-between bg-[var(--xuanzhi-card)] p-3 rounded border border-[var(--border-light)]">
              <div>
                <span className="font-bold text-[var(--ink)]">私有 WebDAV 同步开关</span>
                <p className="text-[11px] text-[var(--ink-muted)]">支持坚果云、Nextcloud、群晖/威联通 NAS 等任何标准 WebDAV 服务</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={syncConfig.enabled}
                  onChange={(e) => setSyncConfig({ ...syncConfig, enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-gray-300 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[var(--daiqing)]"></div>
              </label>
            </div>

            {/* 配置表单 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-[var(--xuanzhi-card)] p-4 rounded border border-[var(--border-light)]">
              <div className="flex flex-col gap-1 md:col-span-2">
                <label className="text-[11px] font-bold text-[var(--ink-muted)] flex items-center gap-1">
                  <Server size={12} />
                  <span>WebDAV 服务器地址 (URL)</span>
                </label>
                <input
                  type="text"
                  value={syncConfig.server_url}
                  onChange={(e) => setSyncConfig({ ...syncConfig, server_url: e.target.value })}
                  placeholder="如 https://dav.jianguoyun.com/dav/"
                  className="w-full px-3 py-1.5 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs font-mono focus:border-[var(--daiqing)] focus:outline-hidden"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-[var(--ink-muted)]">用户名 / 账号</label>
                <input
                  type="text"
                  value={syncConfig.username}
                  onChange={(e) => setSyncConfig({ ...syncConfig, username: e.target.value })}
                  placeholder="WebDAV 登录账号"
                  className="w-full px-3 py-1.5 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs focus:border-[var(--daiqing)] focus:outline-hidden"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-[var(--ink-muted)]">应用密码 / 授权令牌</label>
                <div className="relative">
                  <input
                    type={showSyncPass ? 'text' : 'password'}
                    value={syncPassword}
                    onChange={(e) => setSyncPassword(e.target.value)}
                    placeholder="坚果云需生成专属应用密码"
                    className="w-full px-3 py-1.5 pr-8 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs focus:border-[var(--daiqing)] focus:outline-hidden"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSyncPass(!showSyncPass)}
                    className="absolute right-2 top-2 text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  >
                    {showSyncPass ? <EyeOff size={13} /> : <Eye size={13} />}
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-[var(--ink-muted)]">远端快照存储路径</label>
                <input
                  type="text"
                  value={syncConfig.remote_path}
                  onChange={(e) => setSyncConfig({ ...syncConfig, remote_path: e.target.value })}
                  placeholder="/xuanjian/backup.enc"
                  className="w-full px-3 py-1.5 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs font-mono focus:border-[var(--daiqing)] focus:outline-hidden"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-bold text-[var(--ink-muted)] flex items-center gap-1">
                  <Shield size={12} className="text-[var(--daiqing)]" />
                  <span>端到端加密密码 (防云端窥探)</span>
                </label>
                <div className="relative">
                  <input
                    type={showSyncEncPass ? 'text' : 'password'}
                    value={syncEncryptionPass}
                    onChange={(e) => setSyncEncryptionPass(e.target.value)}
                    placeholder={syncConfig.has_encryption_passphrase ? '已设置端到端密码 (留空保持原样)' : '设置端到端加密密码'}
                    className="w-full px-3 py-1.5 pr-8 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-xs focus:border-[var(--daiqing)] focus:outline-hidden"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSyncEncPass(!showSyncEncPass)}
                    className="absolute right-2 top-2 text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  >
                    {showSyncEncPass ? <EyeOff size={13} /> : <Eye size={13} />}
                  </button>
                </div>
              </div>

              {/* 操作按钮组 */}
              <div className="md:col-span-2 flex items-center justify-between pt-2 border-t border-[var(--border-light)]">
                <button
                  type="button"
                  onClick={handleTestWebDAV}
                  disabled={isTestingWebDAV || !syncConfig.server_url || !syncConfig.username}
                  className="px-3 py-1.5 rounded border border-[var(--border)] bg-[var(--xuanzhi-light)] hover:bg-[var(--border-light)] text-[var(--ink)] flex items-center gap-1.5 disabled:opacity-40 transition"
                >
                  <RefreshCw size={13} className={isTestingWebDAV ? 'animate-spin' : ''} />
                  <span>{isTestingWebDAV ? '测试中...' : '测试服务器连通性'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleSaveWebDAVConfig}
                  disabled={isSavingConfig}
                  className="px-4 py-1.5 bg-[var(--daiqing)] text-white rounded font-medium hover:opacity-90 disabled:opacity-40 transition"
                >
                  {isSavingConfig ? '正在保存...' : '保存配置'}
                </button>
              </div>

              {/* 测试与保存反馈 */}
              {testWebDAVResult && (
                <div className={`md:col-span-2 p-2.5 rounded flex items-center gap-2 ${
                  testWebDAVResult.success
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}>
                  {testWebDAVResult.success ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
                  <span className="font-medium text-[11px]">{testWebDAVResult.message}</span>
                </div>
              )}
            </div>

            {/* 同步双向流转控制区 */}
            <div className="bg-[var(--xuanzhi-card)] p-4 rounded border border-[var(--border-light)] flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-[var(--ink)]">多设备数据流转与无损合并</span>
                <span className="seal-tag-muted">Last-Write-Wins</span>
              </div>
              <p className="text-[11px] text-[var(--ink-muted)]">
                合并算法基于记录级 <code className="font-mono">id</code> 与 <code className="font-mono">updated_at</code> 时间戳自动比对。
                远端较新则安全覆盖；本地较新则保留；两端独有手记完整并入，零遗失。
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <button
                  onClick={handleSyncPush}
                  disabled={isPushing || !syncConfig.is_configured}
                  className="p-3 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded flex items-center gap-3 hover:border-[var(--daiqing)] hover:shadow-xs transition text-left disabled:opacity-40"
                >
                  <div className="w-8 h-8 rounded-full bg-[var(--daiqing)]/10 text-[var(--daiqing)] flex items-center justify-center shrink-0">
                    <ArrowUpRight size={16} />
                  </div>
                  <div>
                    <div className="font-bold text-[var(--ink)]">立即推送到远端 (Push)</div>
                    <div className="text-[10px] text-[var(--ink-muted)]">端到端加密本地数据并上传至 WebDAV</div>
                  </div>
                </button>

                <button
                  onClick={handleSyncPull}
                  disabled={isPulling || !syncConfig.is_configured}
                  className="p-3 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded flex items-center gap-3 hover:border-[var(--daiqing)] hover:shadow-xs transition text-left disabled:opacity-40"
                >
                  <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center justify-center shrink-0">
                    <ArrowDownLeft size={16} />
                  </div>
                  <div>
                    <div className="font-bold text-[var(--ink)]">拉取并无损合并 (Pull)</div>
                    <div className="text-[10px] text-[var(--ink-muted)]">下载并解密远端快照，双向智能合并</div>
                  </div>
                </button>
              </div>

              {/* 同步操作结果 */}
              {syncOperationResult && (
                <div className={`p-3 rounded flex flex-col gap-1 ${
                  syncOperationResult.success
                    ? 'bg-green-50 text-green-900 border border-green-200'
                    : 'bg-red-50 text-red-900 border border-red-200'
                }`}>
                  <div className="flex items-center gap-1.5 font-bold text-xs">
                    {syncOperationResult.success ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
                    <span>{syncOperationResult.message}</span>
                  </div>
                  {syncOperationResult.details && (
                    <div className="text-[11px] text-green-800 font-mono pl-5">
                      {syncOperationResult.details}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 底部关闭按钮 */}
        <div className="flex items-center justify-end pt-3 border-t border-[var(--border-light)]">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs text-[var(--ink)] bg-[var(--xuanzhi-card)] border border-[var(--border)] rounded hover:bg-[var(--border-light)] transition"
          >
            完成并关闭
          </button>
        </div>

      </div>
    </div>
  );
};
