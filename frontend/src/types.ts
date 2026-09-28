// frontend/src/types.ts - 核心数据结构定义

export type NavTab = 'studio' | 'calendar' | 'divination' | 'restraint' | 'archive';

export interface TrigramInfo {
  name: string;
  nature: string;
  symbol: string;
  attr: string;
}

export interface HexagramData {
  number: number;
  name: string;
  full_name: string;
  upper_trigram: string;
  lower_trigram: string;
  guaci: string;
  xiangzhuan: string;
  tuanzhuan: string;
}

export interface LineDetail {
  position: number; // 1..6 自下而上
  position_name: string; // 初, 二, 三, 四, 五, 上
  value: number; // 6, 7, 8, 9
  bit: number; // 0 or 1
  nature: '阳' | '阴';
  is_moving: boolean;
  yao_name: string; // 初九, 六二等
  description: string;
  yaoci: string;
  yaoci_source?: string;
  yaoci_status?: string;
}

export interface CalculationResult {
  topic?: string;
  cast_at?: string;
  generation_mode?: string;
  flow_version?: string;
  reading?: {
    headline: string; summary: string; context: string; action: string;
    basis: string[]; label: string; rule_version: string; boundary: string;
  };
  input_lines: number[];
  direction: string;
  method: string;
  original_hexagram: HexagramData;
  moving_lines: number[];
  transformed_hexagram: HexagramData;
  nuclear_hexagram: HexagramData;
  lines: LineDetail[];
  special_statement?: string | null;
  is_pure_yang: boolean;
  is_pure_yin: boolean;
  coin_flips?: number[][];
  layered_interpretation?: {
    traditional_text: string;
    math_calculation: string;
    symbolic_insight: string;
    real_world_evidence: string;
    to_verify: string;
  };
}

export interface CalendarDayData {
  solar: {
    date: string;
    year: number;
    month: number;
    day: number;
    weekday: string;
  };
  lunar: {
    full_string: string;
    year_chinese: string;
    month_chinese: string;
    day_chinese: string;
    ganzhi_year: string;
    ganzhi_month: string;
    ganzhi_day: string;
    animal: string;
    nayin: string;
    is_leap_month: boolean;
  };
  solar_term: {
    current: string | null;
    prev_term?: { name: string; date: string } | null;
    next_term?: { name: string; date: string } | null;
  };
  pengzu_baiji: {
    gan: string;
    zhi: string;
    full: string;
    source: string;
    verification_status: string;
  };
  yi: TabooItem[];
  ji: TabooItem[];
  metadata: {
    engine: string;
    version: string;
    license: string;
    timezone: string;
    date_range: string;
    verification_reference: string;
    disclaimer: string;
  };
}

export interface TabooItem {
  id?: string;
  term?: string;
  title?: string;
  content_type?: string;
  domain?: string;
  source: string;
  source_type: string;
  verification_status: string;
  scope?: string;
  meaning: string;
  divergent_opinions?: string;
  rational_handling: string;
}

export interface ReflectionAlert {
  id: string;
  level: 'info' | 'warning' | 'danger';
  title: string;
  trigger_fact: string;
  possible_impact: string;
  safer_alternative: string;
  how_to_adjust: string;
}

export interface PauseQuestion {
  id: string;
  label: string;
  prompt: string;
  user_value: string;
}

export interface ReflectionResult {
  status: string;
  risk_level: 'NORMAL' | 'ATTENTION' | 'HIGH_RISK';
  alerts_count: number;
  alerts: ReflectionAlert[];
  pause_card: {
    title: string;
    questions: PauseQuestion[];
    pause_options: Array<{ label: string; duration_minutes: number }>;
  };
  boundaries_enforced: string[];
}

export interface ClassicReading {
  id: string;
  title: string;
  author: string;
  source: string;
  source_type: string;
  verification_status: string;
  category: string;
  original_text: string;
  translation: string;
  commentary: string;
}

export interface GlossaryTerm {
  term: string;
  category: string;
  source: string;
  definition: string;
}

export interface RecordRevision {
  revised_at: string;
  previous_thought?: string;
  previous_outcome?: string;
  previous_basis?: string;
  previous_tags?: string[];
}

export interface RecordItem {
  id: string;
  schema_version: number;
  record_type: 'divination' | 'bazi' | 'ziwei' | 'qimen' | 'reflection' | 'study_note' | 'bookmark';
  title: string;
  topic?: string;
  tags?: string | string[];
  params?: Record<string, any>;
  calculation_result?: Record<string, any>;
  ai_interpret?: Record<string, any>;
  review_data?: {
    original_thought?: string;
    initial_thought?: string;
    realistic_basis?: string;
    observation_window?: string;
    actual_outcome?: string;
    missing_evidence?: string;
    review_tags?: string[];
    notes?: string;
    revisions?: RecordRevision[];
  };
  engine_version?: string;
  created_at: string;
  updated_at: string;
  is_deleted?: number;
}

export interface BaziPillar {
  pillar_name: string;
  gan: string;
  zhi: string;
  gan_zhi: string;
  wuxing: string;
  nayin: string;
  ten_god: string;
  hidden_stems: Array<{
    gan: string;
    wuxing: string;
    ten_god: string;
  }>;
  xun_kong: string;
}

export interface BaziDayunItem {
  index: number;
  gan_zhi: string;
  gan: string;
  zhi: string;
  ten_god: string;
  nayin: string;
  hidden_stems: Array<{
    gan: string;
    wuxing: string;
    ten_god: string;
  }>;
  start_age: number;
  end_age: number;
  start_year: number;
  end_year: number;
}

export interface BaziResult {
  solar_date: string;
  lunar_date: string;
  gender: string;
  is_lunar_input: boolean;
  is_leap_month: boolean;
  degraded_to_three_pillars: boolean;
  day_master: {
    gan: string;
    wuxing: string;
    yinyang: string;
    description: string;
  };
  four_pillars: {
    year: BaziPillar;
    month: BaziPillar;
    day: BaziPillar;
    hour: BaziPillar;
  };
  wuxing_analysis: {
    total_chars_analyzed: number;
    counts: Record<string, number>;
    percentages: Record<string, number>;
    strongest: string[];
    missing: string[];
    note?: string;
  };
  wuxing_distribution?: {
    total_chars_analyzed: number;
    counts: Record<string, number>;
    percentages: Record<string, number>;
    strongest: string[];
    missing: string[];
    note?: string;
  };
  time_boundary_notes?: {
    zi_hour_sect: number;
    zi_hour_mode: string;
    solar_time_system: string;
    timezone_and_dst_notice: string;
  };
  dayun: {
    metadata: {
      is_forward: boolean;
      direction_text: string;
      start_year_offset: number;
      start_month_offset: number;
      start_day_offset: number;
      start_solar_date: string;
      approx_note: string;
    };
    sequence: BaziDayunItem[];
  };
  disclaimer: string;
}

export interface HexagramRelationBrief {
  number: number;
  name: string;
  full_name: string;
  upper_trigram: string;
  lower_trigram: string;
  relation_type?: string;
  meaning?: string;
  is_self_reversed?: boolean;
}

export interface HexagramNode {
  number: number;
  name: string;
  full_name: string;
  upper_trigram: {
    name: string;
    nature: string;
    symbol: string;
    attr: string;
  };
  lower_trigram: {
    name: string;
    nature: string;
    symbol: string;
    attr: string;
  };
  lines: number[];
  line_structures: Array<{
    index: number;
    bit: number;
    nature: '阳' | '阴';
    name: string;
    symbol: string;
  }>;
  texts: {
    guaci: string;
    xiangzhuan: string;
    tuanzhuan: string;
  };
  relationships: {
    opposite: HexagramRelationBrief;
    reverse: HexagramRelationBrief;
    nuclear: HexagramRelationBrief;
    changes: Array<{
      line_index: number;
      line_name: string;
      line_bit: number;
      target_hexagram: HexagramRelationBrief;
    }>;
    prev_hexagram: HexagramRelationBrief;
    next_hexagram: HexagramRelationBrief;
  };
}

export interface HexagramSummary {
  number: number;
  name: string;
  full_name: string;
  upper_trigram: string;
  lower_trigram: string;
  lines: number[];
  guaci_summary: string;
  xiangzhuan: string;
}

export interface AIConfig {
  provider_type: 'offline' | 'openai_compatible' | 'gemini' | 'claude';
  base_url: string;
  model_name: string;
  api_key: string;
  temperature: number;
  max_tokens: number;
  is_configured: boolean;
}

export interface AIBudgetStatus {
  daily_calls_used: number;
  daily_calls_limit: number;
  monthly_tokens_used: number;
  monthly_tokens_limit: number;
  is_budget_ok: boolean;
}

export interface AIInterpretResponse {
  connected: boolean;
  status?: 'SUCCESS' | 'BLOCKED_EXTERNAL' | 'BUDGET_EXCEEDED';
  provider?: string;
  model?: string;
  tokens_used?: number;
  interpretation?: string;
  message?: string;
  reason?: string;
  copy_task_prompt: string;
  suggestion?: string;
}

export interface WebDAVSyncConfig {
  enabled: boolean;
  server_url: string;
  username: string;
  password?: string;
  remote_path: string;
  has_encryption_passphrase?: boolean;
  is_configured: boolean;
}

export interface BackupExportResult {
  success: boolean;
  filename: string;
  size: number;
  encrypted: boolean;
  data: string; // base64
}

export interface BackupRestoreResult {
  success: boolean;
  message: string;
  restored_records_count: number;
  checksum_sha256?: string;
  backup_version?: string;
}

export interface SyncOperationResult {
  success: boolean;
  message?: string;
  status_code?: number;
  records_pushed?: number;
  inserted?: number;
  updated?: number;
  unchanged?: number;
  final_local_total?: number;
  encrypted?: boolean;
}

// ─── 紫微斗数结构 ──────────────────────────────────
export interface ZiweiStar {
  name: string;
  type: string;
  scope?: string;
  brightness?: string;
  mutagen?: string;
}

export interface ZiweiPalace {
  index: number;
  name: string;
  isSoulPalace?: boolean;    // 命宫 (Soul Palace)
  isOriginalPalace: boolean; // 来因宫 (Original Palace / Origin of Karma, 钦天门四化本宫)
  isBodyPalace: boolean;     // 身宫 (Body Palace)
  earthlyBranch: string;
  heavenlyStem: string;
  majorStars: ZiweiStar[];
  minorStars: ZiweiStar[];
  adjectiveStars: Array<{ name: string; type: string; scope: string }>;
  changsheng12?: string;
  boshi12?: string;
  decadal?: {
    range: [number, number];
    heavenlyStem: string;
    earthlyBranch: string;
  } | null;
  ages?: number[];
  sanFangSiZheng?: {
    opposite: string;
    trine1: string;
    trine2: string;
  };
}

export interface ZiweiResult {
  success: boolean;
  degraded?: boolean;
  message?: string;
  input: {
    calendar_type?: string;
    year: number;
    month: number;
    day: number;
    hour: number | null;
    gender: string;
    is_leap_month?: boolean;
  };
  basic?: {
    solarDate: string;
    lunarDate: string;
    chineseDate: string;
    time: string;
    timeRange: string;
    sign: string;
    zodiac: string;
    gender: string;
    soul: string;
    body: string;
    fiveElementsClass: string;
    earthlyBranchOfSoulPalace: string;
    earthlyBranchOfBodyPalace: string;
    soulPalaceName?: string;
    bodyPalaceName?: string;
    originalPalaceName?: string;
    earthlyBranchOfOriginalPalace?: string;
  };
  palaces?: ZiweiPalace[];
  decadalList?: any[];
  horoscope?: {
    targetDate: string;
    decadal: any;
    yearly: any;
    age: any;
  } | null;
  engine_version?: string;
  rules?: Record<string, string>;
  disclaimer?: string;
  star_cultural_info?: Record<string, any>;
}

// ─── 奇门遁甲结构 ──────────────────────────────────
export interface QimenPalace {
  palaceNumber: number;
  palaceName: string;
  fullName: string;
  gua: string;
  direction: string;
  element: string;
  tianPanGan?: string;  // 规范语义: 天盘天干
  diPanGan?: string;    // 规范语义: 地盘天干
  skyStem: string;      // 兼容历史字段: 地盘天干 (upstream historical mapping)
  earthStem: string;    // 兼容历史字段: 天盘天干 (upstream historical mapping)
  hiddenStems?: string[];
  jiGanStem?: string;   // 寄干 (如中五宫天禽所寄之干)
  star: string;
  starElement?: string;
  door: string;
  doorElement?: string;
  god: string;
  godShort?: string;
  diGod?: string;
  keYing?: Array<{
    key: string;
    name: string;
    type: string;
    desc: string;
    source?: string;
  }>;
  isZhiFu: boolean;
  isZhiShi: boolean;
  isKongWang: boolean;
}

export interface QimenResult {
  success: boolean;
  input: {
    solarTerm: string;
    solar_date?: string;
    fourPillars: {
      year: { gan: string; zhi: string };
      month: { gan: string; zhi: string };
      day: { gan: string; zhi: string };
      hour: { gan: string; zhi: string };
    };
    hourNumber: number;
    topic: string;
  };
  meta: {
    type: string;
    system: string;
    juMethod: string;
    dun: string;
    dunRaw: string;
    juNumber: number;
    yuan: string;
    solarTerm: string;
    zhiFuStar: string;
    zhiFuPalace: number;
    zhiShiDoor: string;
    zhiShiPalace: number;
    kongWang: string[];
    tianYiStar?: string;
    tianYiPalace?: number;
  };
  palaces: QimenPalace[];
  engine_version?: string;
  rules?: Record<string, string>;
  disclaimer?: string;
  door_cultural_info?: Record<string, any>;
  star_cultural_info?: Record<string, any>;
}

// ─── 内置研读结构 ──────────────────────────────────
export interface BuiltinReadingSection {
  heading: string;
  content: string;
  citation_ids?: string[];
}

export interface CitationItem {
  id: string;
  book: string;
  chapter: string;
  quote: string;
  applicability: string;
}

export interface BuiltinReadingResponse {
  reading_type: 'builtin';
  reading_label: string;
  title: string;
  rule_version: string;
  is_ai: boolean;
  sections: BuiltinReadingSection[];
  citations: CitationItem[];
  summary: string;
}

// ─── 道德经与复盘统计 ──────────────────────────────
export interface DaodejingChapter {
  chapter_num: number;
  part: string;
  title: string;
  short_title: string;
  source: string;
  original_text: string;
  translation: string;
  reflection: string;
  verification_status: string;
}

export interface ReviewStatistics {
  total_records: number;
  reviewed_count: number;
  pending_count: number;
  type_distribution: Record<string, number>;
  tag_distribution: Record<string, number>;
}
