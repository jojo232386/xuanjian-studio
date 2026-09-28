// frontend/src/components/AISettingsModal.tsx - AI 模型配置与费用预算控制弹窗 (F06)

import React, { useState, useEffect } from 'react';
import type { AIConfig, AIBudgetStatus } from '../types';
import { fetchAIConfigAPI, updateAIConfigAPI, testAIConnectionAPI } from '../api';
import { Shield, Check, AlertCircle, X, Key, Gauge, Sliders, Eye, EyeOff } from 'lucide-react';

interface AISettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfigSaved?: () => void;
}

export const AISettingsModal: React.FC<AISettingsModalProps> = ({ isOpen, onClose, onConfigSaved }) => {
  const [config, setConfig] = useState<AIConfig>({
    provider_type: 'offline',
    base_url: 'https://api.openai.com/v1',
    model_name: 'gpt-4o-mini',
    api_key: '',
    temperature: 0.3,
    max_tokens: 1200,
    is_configured: true
  });
  const [budget, setBudget] = useState<AIBudgetStatus>({
    daily_calls_used: 0,
    daily_calls_limit: 50,
    monthly_tokens_used: 0,
    monthly_tokens_limit: 100000,
    is_budget_ok: true
  });

  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  const loadConfig = async () => {
    setIsLoading(true);
    setTestResult(null);
    try {
      const res = await fetchAIConfigAPI();
      setConfig(res.config);
      setBudget(res.budget);
      setApiKeyInput(res.config.api_key || '');
    } catch (e: any) {
      console.error('加载 AI 配置失败:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testAIConnectionAPI({
        provider_type: config.provider_type,
        base_url: config.base_url,
        model_name: config.model_name,
        api_key: apiKeyInput,
        temperature: config.temperature,
        max_tokens: config.max_tokens
      });
      setTestResult(res);
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || '测试失败' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const res = await updateAIConfigAPI({
        ...config,
        api_key: apiKeyInput
      });
      setConfig(res.config);
      setBudget(res.budget);
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        if (onConfigSaved) onConfigSaved();
        onClose();
      }, 1200);
    } catch (e: any) {
      alert(`保存失败: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card-xuan bg-[var(--xuanzhi-light)] w-full max-w-xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl border border-[var(--border)] rounded-xl flex flex-col gap-5">
        {/* 标题栏 */}
        <div className="flex items-center justify-between pb-3 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className="seal-tag">智能研读</span>
            <h3 className="font-song text-lg font-bold text-[var(--ink)]">AI 模型与费用预算配置</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--border-light)]"
          >
            <X size={18} />
          </button>
        </div>

        {/* 协议类型选择 */}
        <div>
          <label className="block text-xs font-bold text-[var(--ink)] mb-2">选择模型协议 Provider</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { id: 'offline', label: '纯本地离线', desc: '不消耗外部 Key' },
              { id: 'openai_compatible', label: 'OpenAI 兼容', desc: 'DeepSeek/Ollama' },
              { id: 'gemini', label: 'Google Gemini', desc: '官方 REST API' },
              { id: 'claude', label: 'Anthropic', desc: 'Claude Messages' }
            ].map((p) => {
              const isSelected = config.provider_type === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => {
                    setConfig({
                      ...config,
                      provider_type: p.id as any,
                      model_name:
                        p.id === 'openai_compatible'
                          ? 'deepseek-chat'
                          : p.id === 'gemini'
                          ? 'gemini-1.5-flash'
                          : p.id === 'claude'
                          ? 'claude-3-5-haiku-20241022'
                          : 'gpt-4o-mini'
                    });
                    setTestResult(null);
                  }}
                  className={`p-2.5 rounded border text-left transition ${
                    isSelected
                      ? 'border-[var(--daiqing)] bg-[var(--daiqing)] text-white shadow-sm font-bold'
                      : 'border-[var(--border)] bg-[var(--xuanzhi)] text-[var(--ink)] hover:border-[var(--daiqing)]'
                  }`}
                >
                  <div className="text-xs">{p.label}</div>
                  <div className={`text-[10px] mt-0.5 ${isSelected ? 'text-white/80' : 'text-[var(--ink-muted)]'}`}>
                    {p.desc}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 参数表单 */}
        {config.provider_type !== 'offline' && (
          <div className="space-y-3 p-3.5 rounded bg-[var(--xuanzhi)] border border-[var(--border)]">
            {config.provider_type === 'openai_compatible' && (
              <div>
                <label className="block text-xs text-[var(--ink-muted)] mb-1">API Base URL</label>
                <input
                  type="text"
                  placeholder="https://api.openai.com/v1 或 http://localhost:11434/v1"
                  value={config.base_url}
                  onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-[var(--ink)]"
                />
              </div>
            )}

            <div>
              <label className="block text-xs text-[var(--ink-muted)] mb-1">模型名称 (Model Name)</label>
              <input
                type="text"
                value={config.model_name}
                onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                className="w-full px-3 py-1.5 text-xs bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-[var(--ink)] font-mono"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs text-[var(--ink-muted)] flex items-center gap-1">
                  <Key size={12} />
                  <span>API Key</span>
                </label>
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="text-[10px] text-[var(--daiqing)] flex items-center gap-1 hover:underline"
                >
                  {showKey ? <EyeOff size={11} /> : <Eye size={11} />}
                  <span>{showKey ? '隐藏' : '显示'}</span>
                </button>
              </div>
              <input
                type={showKey ? 'text' : 'password'}
                placeholder="输入对应平台 API Key (本地保存，绝不上报第三方)"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                className="w-full px-3 py-1.5 text-xs bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-[var(--ink)] font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-xs text-[var(--ink-muted)] mb-1">
                  采样温度 (Temperature): {config.temperature}
                </label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full accent-[var(--daiqing)] cursor-pointer"
                />
              </div>
              <div>
                <label className="block text-xs text-[var(--ink-muted)] mb-1">
                  最大输出 Token: {config.max_tokens}
                </label>
                <input
                  type="number"
                  min="200"
                  max="2000"
                  step="100"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) || 1200 })}
                  className="w-full px-2.5 py-1 text-xs bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded text-[var(--ink)]"
                />
              </div>
            </div>
          </div>
        )}

        {/* 预算与配额安全状态 */}
        <div className="p-3.5 rounded bg-[var(--border-light)] border border-[var(--border)]">
          <div className="flex items-center gap-2 mb-2">
            <Gauge size={14} className="text-[var(--daiqing)]" />
            <span className="text-xs font-bold text-[var(--ink)]">费用与配额安全监控</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <div className="flex justify-between text-[11px] text-[var(--ink-muted)] mb-1">
                <span>今日调用次数</span>
                <span>{budget.daily_calls_used} / {budget.daily_calls_limit} 次</span>
              </div>
              <div className="h-2 bg-[var(--border)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--daiqing)] transition-all"
                  style={{ width: `${Math.min(100, (budget.daily_calls_used / budget.daily_calls_limit) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-[var(--ink-muted)] mb-1">
                <span>本月估计 Token</span>
                <span>{budget.monthly_tokens_used} / {budget.monthly_tokens_limit}</span>
              </div>
              <div className="h-2 bg-[var(--border)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--zhusha)] transition-all"
                  style={{ width: `${Math.min(100, (budget.monthly_tokens_used / budget.monthly_tokens_limit) * 100)}%` }}
                />
              </div>
            </div>
          </div>

          <p className="text-[10px] text-[var(--ink-muted)] mt-2">
            硬预算保护：若调用达到单日或单月上限，系统自动熔断并切换为离线模式，杜绝意外扣费。
          </p>
        </div>

        {/* 测试结果反馈 */}
        {testResult && (
          <div
            className={`p-2.5 rounded text-xs flex items-center gap-2 ${
              testResult.success
                ? 'bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30'
                : 'bg-red-500/10 text-red-800 dark:text-red-300 border border-red-500/30'
            }`}
          >
            {testResult.success ? <Check size={14} /> : <AlertCircle size={14} />}
            <span>{testResult.message}</span>
          </div>
        )}

        {/* 底部按钮栏 */}
        <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]">
          <button
            onClick={handleTestConnection}
            disabled={isTesting || isLoading}
            className="btn-secondary px-3.5 py-1.5 text-xs flex items-center gap-1.5"
          >
            <Sliders size={13} />
            <span>{isTesting ? '正在测试...' : '测试连接'}</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs text-[var(--ink-muted)] hover:bg-[var(--border-light)] rounded"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading || saveSuccess}
              className={`px-4 py-1.5 text-xs font-song rounded flex items-center gap-1.5 transition ${
                saveSuccess
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'btn-antique'
              }`}
            >
              {saveSuccess ? <Check size={14} /> : <Shield size={14} />}
              <span>{saveSuccess ? '已保存！' : '保存配置'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
