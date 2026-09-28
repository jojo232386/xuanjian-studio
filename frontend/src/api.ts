// frontend/src/api.ts - 后端 API 通信模块

import type {
  CalendarDayData,
  CalculationResult,
  ReflectionResult,
  TabooItem,
  ClassicReading,
  GlossaryTerm
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function safeFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    }
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.message || `请求失败: HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<{ status: string; app: string; version: string; ai_connected: boolean }> {
  return safeFetch('/health');
}

export async function fetchCalendarDay(dateStr?: string): Promise<CalendarDayData> {
  const query = dateStr ? `?date=${encodeURIComponent(dateStr)}` : '';
  return safeFetch(`/calendar${query}`);
}

export async function calculateHexagramAPI(lines: number[], topic = ""): Promise<CalculationResult> {
  return safeFetch('/iching/calculate', {
    method: 'POST',
    body: JSON.stringify({ lines, topic })
  });
}

export async function castCoinsAPI(topic = ""): Promise<CalculationResult> {
  return safeFetch('/iching/coins', { method: 'POST', body: JSON.stringify({ topic }) });
}

export async function castSingleCoinAPI(): Promise<{coins: number[]; value: number}> {
  return safeFetch('/iching/coin', { method: 'POST', body: '{}' });
}

export async function verifyTabooAPI(q: string): Promise<{
  found: boolean;
  query: string;
  count: number;
  results?: TabooItem[];
  verification_status?: string;
  message: string;
}> {
  return safeFetch(`/taboos/verify?q=${encodeURIComponent(q)}`);
}

export async function evaluateReflectionAPI(data: {
  topic: string;
  budget_available: number;
  cost_estimate: number;
  uses_credit_or_loan: boolean;
  is_irreversible: boolean;
  impending_deadline: string;
  divination_count_today: number;
}): Promise<ReflectionResult> {
  return safeFetch('/reflection/evaluate', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function fetchClassicsAPI(query = '', category = ''): Promise<{
  readings: ClassicReading[];
  glossary: GlossaryTerm[];
}> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (category) params.append('category', category);
  return safeFetch(`/classics?${params.toString()}`);
}

export async function exportDataAPI(type: 'divination' | 'reflection' | 'bundle', format: 'markdown' | 'json', data: any): Promise<string> {
  const url = `${API_BASE}/export`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, format, data })
  });
  if (!res.ok) {
    throw new Error('导出失败');
  }
  return res.text();
}

export async function requestAiInterpretAPI(topic: string, calculation: CalculationResult): Promise<import('./types').AIInterpretResponse> {
  return safeFetch('/ai/interpret', {
    method: 'POST',
    body: JSON.stringify({ topic, calculation })
  });
}

// ----------------------------------------------------
// 本地 SQLite 记录与复盘手记 API (用户主动保存)
// ----------------------------------------------------

export async function listRecordsAPI(params: {
  type?: string;
  tag?: string;
  query?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<{ records: import('./types').RecordItem[]; total: number; limit: number; offset: number }> {
  const query = new URLSearchParams();
  if (params.type) query.append('type', params.type);
  if (params.tag) query.append('tag', params.tag);
  if (params.query) query.append('query', params.query);
  if (params.limit) query.append('limit', String(params.limit));
  if (params.offset) query.append('offset', String(params.offset));
  return safeFetch(`/records?${query.toString()}`);
}

export async function createRecordAPI(data: Partial<import('./types').RecordItem>): Promise<import('./types').RecordItem> {
  return safeFetch('/records', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function getRecordAPI(id: string): Promise<import('./types').RecordItem> {
  return safeFetch(`/records/${id}`);
}

export async function updateRecordAPI(id: string, updates: Partial<import('./types').RecordItem>): Promise<import('./types').RecordItem> {
  return safeFetch(`/records/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates)
  });
}

export async function deleteRecordAPI(id: string, permanent = false): Promise<{ deleted: boolean; id: string }> {
  return safeFetch(`/records/${id}?permanent=${permanent}`, {
    method: 'DELETE'
  });
}

export async function exportRecordsAPI(format: 'markdown' | 'json', ids?: string[]): Promise<string> {
  const res = await fetch(`${API_BASE}/records/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ format, ids })
  });
  if (!res.ok) throw new Error('导出记录失败');
  return res.text();
}

export async function clearAllRecordsAPI(): Promise<{ cleared: boolean; message: string }> {
  return safeFetch('/records/clear', {
    method: 'POST',
    body: JSON.stringify({})
  });
}

export async function calculateBaziAPI(params: {
  year: number;
  month: number;
  day: number;
  hour?: number | null;
  minute?: number;
  gender?: string;
  is_lunar?: boolean;
  is_leap_month?: boolean;
  zi_hour_sect?: number;
}): Promise<import('./types').BaziResult> {
  return safeFetch('/bazi/calculate', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

export async function fetchHexagramsAPI(q = ''): Promise<{
  count: number;
  hexagrams: import('./types').HexagramSummary[];
}> {
  const query = q ? `?q=${encodeURIComponent(q)}` : '';
  return safeFetch(`/hexagrams${query}`);
}

export async function fetchHexagramDetailAPI(idOrName: string | number): Promise<import('./types').HexagramNode> {
  return safeFetch(`/hexagrams/${encodeURIComponent(String(idOrName))}`);
}

export async function fetchAIConfigAPI(): Promise<{
  config: import('./types').AIConfig;
  budget: import('./types').AIBudgetStatus;
}> {
  return safeFetch('/ai/config');
}

export async function updateAIConfigAPI(config: Partial<import('./types').AIConfig>): Promise<{
  config: import('./types').AIConfig;
  budget: import('./types').AIBudgetStatus;
  message: string;
}> {
  return safeFetch('/ai/config', {
    method: 'POST',
    body: JSON.stringify(config)
  });
}

export async function testAIConnectionAPI(testConfig?: any): Promise<{
  success: boolean;
  message: string;
  model?: string;
}> {
  return safeFetch('/ai/test', {
    method: 'POST',
    body: JSON.stringify(testConfig || {})
  });
}

export async function exportBackupAPI(passphrase?: string): Promise<import('./types').BackupExportResult> {
  return safeFetch('/backup/export', {
    method: 'POST',
    body: JSON.stringify({ passphrase: passphrase || undefined })
  });
}

export async function restoreBackupAPI(dataBase64: string, passphrase?: string): Promise<import('./types').BackupRestoreResult> {
  return safeFetch('/backup/restore', {
    method: 'POST',
    body: JSON.stringify({ data: dataBase64, passphrase: passphrase || undefined })
  });
}

export async function fetchSyncConfigAPI(): Promise<{ config: import('./types').WebDAVSyncConfig }> {
  return safeFetch('/sync/config');
}

export async function updateSyncConfigAPI(config: Partial<import('./types').WebDAVSyncConfig & { encryption_passphrase?: string }>): Promise<{
  success: boolean;
  config: import('./types').WebDAVSyncConfig;
}> {
  return safeFetch('/sync/config', {
    method: 'POST',
    body: JSON.stringify(config)
  });
}

export async function testSyncConnectionAPI(testConfig?: any): Promise<{
  success: boolean;
  message: string;
  status_code?: number;
}> {
  return safeFetch('/sync/test', {
    method: 'POST',
    body: JSON.stringify(testConfig || {})
  });
}

export async function syncPushAPI(): Promise<import('./types').SyncOperationResult> {
  return safeFetch('/sync/push', {
    method: 'POST',
    body: JSON.stringify({})
  });
}

export async function syncPullAPI(): Promise<import('./types').SyncOperationResult> {
  return safeFetch('/sync/pull', {
    method: 'POST',
    body: JSON.stringify({})
  });
}

// ─── 紫微斗数与奇门遁甲计算接口 ──────────────────
export async function calculateZiweiAPI(params: {
  year: number;
  month: number;
  day: number;
  hour: number | null;
  gender?: string;
  calendar?: string;
  is_leap_month?: boolean;
  target_date?: string;
}): Promise<import('./types').ZiweiResult> {
  return safeFetch('/ziwei/calculate', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

export async function calculateQimenAPI(params: {
  year?: number;
  month?: number;
  day?: number;
  hour?: number;
  minute?: number;
  topic?: string;
  solar_term?: string;
}): Promise<import('./types').QimenResult> {
  return safeFetch('/qimen/calculate', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

// ─── 内置研读与道德经查询接口 ──────────────────────
export async function fetchBuiltinReadingAPI(params: {
  record_type: string;
  calculation: any;
  topic?: string;
}): Promise<import('./types').BuiltinReadingResponse> {
  return safeFetch('/builtin/read', {
    method: 'POST',
    body: JSON.stringify(params)
  });
}

export async function fetchDaodejingChapterAPI(chapterNum?: number): Promise<any> {
  const query = chapterNum ? `?chapter=${chapterNum}` : '';
  return safeFetch(`/classics/daodejing${query}`);
}

export async function fetchReviewStatisticsAPI(): Promise<import('./types').ReviewStatistics> {
  return safeFetch('/records/statistics');
}

// ─── 系统管理与关于接口 ──────────────────────────
export async function fetchSystemInfoAPI(): Promise<{
  status: string;
  app: string;
  version: string;
  mode: string;
  data_dir: string;
  db_path: string;
  logs_dir: string;
  backups_dir: string;
  engines: Record<string, string>;
  node_runtime: { is_bundled: boolean; path: string };
  ai_connected: boolean;
}> {
  return safeFetch('/system/info');
}

export async function fetchSystemDiagnosticsAPI(): Promise<any> {
  return safeFetch('/system/diagnostics');
}

export async function openDataDirAPI(): Promise<{ status: string; opened: string }> {
  return safeFetch('/system/open_data_dir', {
    method: 'POST',
    body: JSON.stringify({})
  });
}

export async function shutdownServerAPI(): Promise<{ status: string; message: string }> {
  return safeFetch('/system/shutdown', {
    method: 'POST',
    body: JSON.stringify({})
  });
}
