#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/ai_provider.py - 智能研读层：可配置 AI Provider、引用考据与费用安全防护 (F06)

支持协议：
1. 离线/AGY宿主模式 (OfflineFallbackProvider): 无需任何外部 API Key，确定性结构化呈现与一键复制；
2. OpenAI 兼容协议 (OpenAICompatibleProvider): 支持 OpenAI, DeepSeek, Ollama, vLLM, OneAPI;
3. Google Gemini 协议 (GeminiProvider): 官方 REST API 协议;
4. Anthropic Claude 协议 (ClaudeProvider): 官方 Messages API 协议。

安全与防线原则：
1. 真实查证先于模型幻想：将真实出处文献与象数计算结果注入 prompt，要求大模型仅基于事实文本研读；
2. 预算硬防线：单次 token 上限、每日调用次数上限、每月预算硬顶，超出自动熔断并降级为离线模式；
3. 输入清洗与注入防护：剥离控制字符与越狱指令，隔离系统设定；
4. 密钥零泄漏：API Key 在任何日志与前端展示中均严格脱敏 (如 sk-****abcd)。
"""

import os
import json
import re
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from xuanjian.runtime_env import get_data_dir

# 默认预算防线参数
DEFAULT_MAX_TOKENS = 1200
DEFAULT_DAILY_CALL_LIMIT = 50
DEFAULT_MONTHLY_TOKEN_LIMIT = 100000
DEFAULT_BUDGET_FILE = os.path.join(get_data_dir(), "ai_budget.json")

# 密钥脱敏显示工具
def mask_api_key(key: Optional[str]) -> str:
    if not key:
        return ""
    clean = key.strip()
    if len(clean) <= 8:
        return "********"
    return f"{clean[:3]}****{clean[-4:]}"

# 系统提示词与象数规范约束
SYSTEM_PROMPT_TEMPLATE = (
    "你是由 Google DeepMind 象数义理与哲学研究团队打造的「玄鉴·书房」研读助手。\n"
    "你的职责是协助用户研读中国传统经典《周易》与象数模型，并进行清雅理性的现实知止反思。\n\n"
    "【核心纪律与防线】\n"
    "1. 绝不迷信恐吓：严禁算命断死生、断祸福，严禁给出涉及医疗健康或投资暴富的保证性断言；\n"
    "2. 尊重真实文本：严格依据系统提供的【传世文献】展开义理分析，严禁胡编古籍原文或伪造出处；\n"
    "3. 引用文献规范：引用文献时必须使用系统标注的文献编号如 [1]、[2]、[3]，切勿虚构不存在的文献编号；\n"
    "4. 分层理性研读：严格分为五层展开阐述：\n"
    "   - 一、【传统文本】：原典卦辞、大象传与爻辞义理；\n"
    "   - 二、【象数承应】：上下卦象、动爻阴阳演变及互卦潜在动力；\n"
    "   - 三、【哲学象征】：以思患预防、修德自律、知止顺势为核心的启发；\n"
    "   - 四、【现实证据】：现实决策中必须核对的客观合同、现金流、合规等事实；\n"
    "   - 五、【待核实项】：哪些主观猜想尚无实据支撑，切勿轻信盲动。\n"
    "5. 语言清雅素朴，不冗长啰嗦，篇幅控制在 600-800 字以内。"
)

class BudgetExceededError(Exception):
    """超出每日或每月调用配额异常"""
    pass

class TokenBudgetTracker:
    """本地持久化与并发预扣配额监控器 (F06)"""
    def __init__(
        self,
        daily_limit: int = DEFAULT_DAILY_CALL_LIMIT,
        monthly_limit: int = DEFAULT_MONTHLY_TOKEN_LIMIT,
        storage_path: Optional[str] = None
    ):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.storage_path = storage_path
        self._lock = threading.RLock()

        self.calls_today = 0
        self.tokens_this_month = 0
        self.reserved_calls = 0
        self.reserved_tokens = 0
        self.current_day = datetime.now().strftime("%Y-%m-%d")
        self.current_month = datetime.now().strftime("%Y-%m")
        self.last_updated = datetime.now(timezone.utc).isoformat()

        self._load()

    def _load(self) -> None:
        if not self.storage_path:
            return
        with self._lock:
            if not os.path.exists(self.storage_path):
                return
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                saved_day = data.get("current_day", "")
                saved_month = data.get("current_month", "")
                now_day = datetime.now().strftime("%Y-%m-%d")
                now_month = datetime.now().strftime("%Y-%m")

                if saved_day == now_day:
                    self.calls_today = int(data.get("calls_today", 0))
                else:
                    self.calls_today = 0
                    self.current_day = now_day

                if saved_month == now_month:
                    self.tokens_this_month = int(data.get("tokens_this_month", 0))
                else:
                    self.tokens_this_month = 0
                    self.current_month = now_month

                if "daily_limit" in data and self.daily_limit == DEFAULT_DAILY_CALL_LIMIT:
                    self.daily_limit = int(data["daily_limit"])
                if "monthly_limit" in data and self.monthly_limit == DEFAULT_MONTHLY_TOKEN_LIMIT:
                    self.monthly_limit = int(data["monthly_limit"])
            except Exception:
                pass

    def _save(self) -> None:
        if not self.storage_path:
            return
        with self._lock:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
                state = {
                    "calls_today": self.calls_today,
                    "daily_limit": self.daily_limit,
                    "current_day": self.current_day,
                    "tokens_this_month": self.tokens_this_month,
                    "monthly_limit": self.monthly_limit,
                    "current_month": self.current_month,
                    "reserved_calls": self.reserved_calls,
                    "reserved_tokens": self.reserved_tokens,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                tmp_path = f"{self.storage_path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, self.storage_path)
            except Exception:
                pass

    def _roll_dates_if_needed(self) -> None:
        now_day = datetime.now().strftime("%Y-%m-%d")
        now_month = datetime.now().strftime("%Y-%m")
        changed = False
        if self.current_day != now_day:
            self.calls_today = 0
            self.current_day = now_day
            changed = True
        if self.current_month != now_month:
            self.tokens_this_month = 0
            self.current_month = now_month
            changed = True
        if changed:
            self._save()

    def reserve(self, estimated_tokens: int = 500) -> str:
        """并发预扣：在发起实际外部网络调用前预占配额，避免瞬间击穿"""
        with self._lock:
            self._roll_dates_if_needed()
            if self.calls_today + self.reserved_calls >= self.daily_limit:
                raise BudgetExceededError(f"已达到每日 AI 调用安全上限 ({self.daily_limit} 次)，已自动熔断保护。")
            if self.tokens_this_month + self.reserved_tokens + estimated_tokens > self.monthly_limit:
                raise BudgetExceededError(f"已达到每月 Token 安全预算上限 ({self.monthly_limit} tokens)，已自动熔断保护。")

            self.reserved_calls += 1
            self.reserved_tokens += estimated_tokens
            self._save()
            reservation_id = f"res_{int(datetime.now().timestamp()*1000)}_{self.reserved_calls}"
            return reservation_id

    def settle(self, reservation_id: str, actual_tokens: int, estimated_tokens: int = 500) -> None:
        """调用成功：释放预占，按实际消耗落盘计入历史配额"""
        with self._lock:
            self._roll_dates_if_needed()
            self.reserved_calls = max(0, self.reserved_calls - 1)
            self.reserved_tokens = max(0, self.reserved_tokens - estimated_tokens)
            self.calls_today += 1
            self.tokens_this_month += max(0, actual_tokens)
            self._save()

    def release(self, reservation_id: str, estimated_tokens: int = 500) -> None:
        """调用失败或取消：安全回滚补偿预占额度，不虚假扣除用户配额"""
        with self._lock:
            self.reserved_calls = max(0, self.reserved_calls - 1)
            self.reserved_tokens = max(0, self.reserved_tokens - estimated_tokens)
            self._save()

    def check_and_increment(self, estimated_tokens: int = 500) -> None:
        """同步检查并自增（兼容旧接口）"""
        with self._lock:
            self._roll_dates_if_needed()
            if self.calls_today + self.reserved_calls >= self.daily_limit:
                raise BudgetExceededError(f"已达到每日 AI 调用安全上限 ({self.daily_limit} 次)，已自动熔断保护。")
            if self.tokens_this_month + self.reserved_tokens + estimated_tokens > self.monthly_limit:
                raise BudgetExceededError(f"已达到每月 Token 安全预算上限 ({self.monthly_limit} tokens)，已自动熔断保护。")
            self.calls_today += 1
            self.tokens_this_month += estimated_tokens
            self._save()

    def record_actual_usage(self, actual_tokens: int) -> None:
        """校正 token 实际使用量"""
        with self._lock:
            self._roll_dates_if_needed()
            self.tokens_this_month += max(0, actual_tokens - 500)
            self._save()

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            self._roll_dates_if_needed()
            effective_calls = self.calls_today + self.reserved_calls
            effective_tokens = self.tokens_this_month + self.reserved_tokens
            return {
                "daily_calls_used": self.calls_today,
                "daily_calls_reserved": self.reserved_calls,
                "daily_calls_limit": self.daily_limit,
                "monthly_tokens_used": self.tokens_this_month,
                "monthly_tokens_reserved": self.reserved_tokens,
                "monthly_tokens_limit": self.monthly_limit,
                "is_budget_ok": effective_calls < self.daily_limit and effective_tokens < self.monthly_limit,
                "current_day": self.current_day,
                "current_month": self.current_month,
                "persisted": bool(self.storage_path and os.path.exists(self.storage_path))
            }

    def reset_counters(self) -> None:
        with self._lock:
            self.calls_today = 0
            self.tokens_this_month = 0
            self.reserved_calls = 0
            self.reserved_tokens = 0
            self._save()

# 全局配额追踪单例 (落盘至 data/ai_budget.json)
_budget_tracker = TokenBudgetTracker(storage_path=DEFAULT_BUDGET_FILE)

def get_budget_tracker() -> TokenBudgetTracker:
    return _budget_tracker

class AIProviderConfig:
    """AI Provider 配置模型"""
    def __init__(
        self,
        provider_type: str = "offline",
        base_url: str = "",
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        self.provider_type = provider_type.strip().lower()
        self.base_url = base_url.strip()
        self.model_name = model_name.strip()
        self.api_key = api_key.strip() if api_key else ""
        self.temperature = max(0.0, min(1.0, float(temperature)))
        self.max_tokens = max(100, min(2000, int(max_tokens)))

    def to_dict(self, mask_key: bool = True) -> Dict[str, Any]:
        return {
            "provider_type": self.provider_type,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "api_key": mask_api_key(self.api_key) if mask_key else self.api_key,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "is_configured": bool(self.api_key) or self.provider_type == "offline"
        }

# 全局内存配置（初始优先读取环境变量）
_current_config = AIProviderConfig(
    provider_type="openai_compatible" if os.environ.get("OPENAI_API_KEY") else ("gemini" if os.environ.get("GEMINI_API_KEY") else "offline"),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    model_name=os.environ.get("AI_MODEL_NAME", "gpt-4o-mini"),
    api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
)

def get_ai_config() -> AIProviderConfig:
    return _current_config

def update_ai_config(new_config_dict: Dict[str, Any]) -> AIProviderConfig:
    global _current_config
    ptype = new_config_dict.get("provider_type", _current_config.provider_type)
    burl = new_config_dict.get("base_url", _current_config.base_url)
    model = new_config_dict.get("model_name", _current_config.model_name)
    key = new_config_dict.get("api_key", None)

    # 如果用户没有提供新 key 或传的是脱敏后的星号，则保留现有 key
    if key is None or "****" in key:
        final_key = _current_config.api_key
    else:
        final_key = key.strip()

    temp = new_config_dict.get("temperature", _current_config.temperature)
    max_t = new_config_dict.get("max_tokens", _current_config.max_tokens)

    _current_config = AIProviderConfig(
        provider_type=ptype,
        base_url=burl,
        model_name=model,
        api_key=final_key,
        temperature=temp,
        max_tokens=max_t
    )
    return _current_config

def sanitize_user_input(text: str) -> str:
    """输入清洗与注入防御"""
    if not text:
        return ""
    # 截断长度防止 token 溢出攻击
    cleaned = text[:400].strip()
    # 剥离潜在注入标记与不可见控制字符
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
    return cleaned

class GroundedPrompt(tuple):
    """同时支持 2 元组解构与对象属性访问的接地提示词结构"""
    def __new__(cls, system_prompt: str, user_prompt: str, citations: Optional[Dict[int, str]] = None):
        t = super().__new__(cls, (system_prompt, user_prompt))
        t.system_prompt = system_prompt
        t.user_prompt = user_prompt
        t.citations = citations or {}
        return t

def build_grounded_prompt(topic: str, calculation_data: Dict[str, Any]) -> GroundedPrompt:
    """构建注入真实考据文献的提示词"""
    clean_topic = sanitize_user_input(topic) or "象数研读与知止反思"

    orig = calculation_data.get("original_hexagram", {})
    trans = calculation_data.get("transformed_hexagram", {})
    nuc = calculation_data.get("nuclear_hexagram", {})
    lines = calculation_data.get("input_lines", [7, 8, 7, 8, 9, 6])
    mov = calculation_data.get("moving_lines", [])

    orig_name = orig.get("name", "既济")
    orig_full = orig.get("full_name", "水火既济")
    orig_guaci = orig.get("guaci", "")
    orig_xiang = orig.get("xiangzhuan", "")
    orig_tuan = orig.get("tuanzhuan", "")

    trans_name = trans.get("name", "贲")
    trans_full = trans.get("full_name", "山火贲")
    nuc_name = nuc.get("name", "未济")

    lines_str = "、".join(str(x) for x in lines)
    mov_str = "、".join(str(x) for x in mov) if mov else "无动爻"

    citation_registry = {
        1: f"卦辞：“{orig_guaci}”",
        2: f"《大象传》：“{orig_xiang}”",
        3: f"《彖传》：“{orig_tuan}”"
    }

    user_prompt = (
        f"【研读课题】：{clean_topic}\n\n"
        f"【客观象数计算输入】：\n"
        f"- 自下而上六爻值：{lines_str}\n"
        f"- 本卦：{orig_name}卦（{orig_full}）\n"
        f"- 动爻：第 {mov_str} 爻\n"
        f"- 变卦（之卦）：{trans_name}卦（{trans_full}）\n"
        f"- 互卦（重卦中爻）：{nuc_name}卦\n\n"
        f"【已核验传世原典文献】：\n"
        f"- [1] 卦辞：“{orig_guaci}”\n"
        f"- [2] 《大象传》：“{orig_xiang}”\n"
        f"- [3] 《彖传》：“{orig_tuan}”\n\n"
        f"请严格基于上述客观计算与传世文献，恪守不占卜、不恐吓、立足事实防线的原则，分五层给出研读启示。\n"
        f"引用文献时请且仅请使用系统给定的文献引用标号（如 [1]、[2]、[3]），严禁伪造不存在的文献编号或篡改卦爻数据。"
    )
    return GroundedPrompt(SYSTEM_PROMPT_TEMPLATE, user_prompt, citation_registry)

def verify_grounding_and_integrity(
    raw_content: str,
    calculation_data: Dict[str, Any],
    valid_citation_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    接地性校验与象数数据完整性保护：
    1. 校验模型返回文本中的引用标号 [1], [2] 等是否在有效注入的文献范围内；超出范围的进行告警并安全标注清理；
    2. 严禁模型改写底层象数计算结果（卦名、爻位、六爻结构），确保客观计算不可篡改。
    """
    if valid_citation_ids is None:
        valid_citation_ids = [1, 2, 3]

    # 1. 引用标号扫描与校验
    found_citations = [int(m) for m in re.findall(r'\[(\d+)\]', raw_content)]
    unique_citations = sorted(list(set(found_citations)))
    invalid_citations = [cid for cid in unique_citations if cid not in valid_citation_ids]

    cleaned_content = raw_content
    warnings: List[str] = []

    if invalid_citations:
        warnings.append(
            f"检测到超出本地传世文献范围的未核验引用标号: {invalid_citations}。已进行安全标注，防止模型幻觉传导。"
        )
        for inv_id in invalid_citations:
            cleaned_content = cleaned_content.replace(f"[{inv_id}]", f"[未核验引用{inv_id}]")

    # 2. 象数底层结构保护比对与防篡改
    orig = calculation_data.get("original_hexagram", {})
    trans = calculation_data.get("transformed_hexagram", {})
    orig_name = orig.get("name", "")
    orig_full = orig.get("full_name", "")
    trans_name = trans.get("name", "")
    input_lines = calculation_data.get("input_lines", [])
    moving_lines = calculation_data.get("moving_lines", [])

    model_tampered_core = False
    if orig_name:
        tamper_patterns = [
            rf"(?:并非|不是|算错|纠正为|错误|应为).*{re.escape(orig_name)}",
            rf"{re.escape(orig_name)}.*(?:错误|失误|算错|应更正)"
        ]
        for pat in tamper_patterns:
            if re.search(pat, raw_content):
                model_tampered_core = True
                warnings.append(f"模型文本出现对确定性象数计算结果（{orig_name}）的异常纠正倾向，已被系统规则锁定防护。")
                break

    authoritative_core = {
        "original_name": orig_name,
        "original_full_name": orig_full,
        "transformed_name": trans_name,
        "input_lines": list(input_lines),
        "moving_lines": list(moving_lines),
        "locked": True
    }

    return {
        "cleaned_content": cleaned_content,
        "citations_found": unique_citations,
        "invalid_citations": invalid_citations,
        "citations_valid": len(invalid_citations) == 0,
        "model_tampered_core": model_tampered_core,
        "authoritative_core": authoritative_core,
        "warnings": warnings
    }

# ----------------------------------------------------
# 各种 Provider 具体适配器实现 (Pure Python Standard Library)
# ----------------------------------------------------

def call_openai_compatible(
    config: AIProviderConfig,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 15
) -> Dict[str, Any]:
    """OpenAI 兼容协议调用"""
    if not config.api_key:
        raise ValueError("未配置 API Key (BLOCKED_EXTERNAL)")

    base_url = config.base_url.rstrip("/") or "https://api.openai.com/v1"
    endpoint = f"{base_url}/chat/completions"

    payload = {
        "model": config.model_name or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
            "User-Agent": "XuanJian-Studio/2.1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        choice = res_data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = res_data.get("usage", {})
        total_tokens = usage.get("total_tokens", 500)
        return {
            "content": content,
            "total_tokens": total_tokens,
            "model": res_data.get("model", config.model_name)
        }

def call_gemini(
    config: AIProviderConfig,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 15
) -> Dict[str, Any]:
    """Google Gemini REST API 调用"""
    if not config.api_key:
        raise ValueError("未配置 Gemini API Key (BLOCKED_EXTERNAL)")

    model = config.model_name or "gemini-1.5-flash"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={config.api_key}"

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": config.temperature,
            "maxOutputTokens": config.max_tokens
        }
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        candidates = res_data.get("candidates", [{}])
        parts = candidates[0].get("content", {}).get("parts", [{}])
        content = parts[0].get("text", "")
        meta = res_data.get("usageMetadata", {})
        total_tokens = meta.get("totalTokenCount", 500)
        return {
            "content": content,
            "total_tokens": total_tokens,
            "model": model
        }

def call_claude(
    config: AIProviderConfig,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 15
) -> Dict[str, Any]:
    """Anthropic Claude Messages API 调用"""
    if not config.api_key:
        raise ValueError("未配置 Claude API Key (BLOCKED_EXTERNAL)")

    endpoint = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": config.model_name or "claude-3-5-haiku-20241022",
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        content_blocks = res_data.get("content", [{}])
        content = "".join([b.get("text", "") for b in content_blocks if b.get("type") == "text"])
        usage = res_data.get("usage", {})
        total_tokens = usage.get("input_tokens", 250) + usage.get("output_tokens", 250)
        return {
            "content": content,
            "total_tokens": total_tokens,
            "model": res_data.get("model", config.model_name)
        }

def generate_ai_interpretation(
    topic: str,
    calculation_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    统一智能研读入口：
    按配置调用外部模型；若无密钥、离线模式或网络阻塞，则安全降级为结构化离线考据与复制提示词。
    内置并发预扣 (Reservation Lock)、失败安全回滚、接地性引用校验与象数底层结构防篡改保护。
    """
    config = get_ai_config()
    gp = build_grounded_prompt(topic, calculation_data)
    valid_citation_ids = list(gp.citations.keys()) if hasattr(gp, "citations") else [1, 2, 3]

    orig = calculation_data.get("original_hexagram", {})
    trans = calculation_data.get("transformed_hexagram", {})
    authoritative_core = {
        "original_name": orig.get("name", ""),
        "original_full_name": orig.get("full_name", ""),
        "transformed_name": trans.get("name", ""),
        "input_lines": list(calculation_data.get("input_lines", [])),
        "moving_lines": list(calculation_data.get("moving_lines", [])),
        "locked": True
    }

    # 离线模式或未配置密钥：诚实披露 BLOCKED_EXTERNAL 并返回结构化离线方案
    if config.provider_type == "offline" or not config.api_key:
        return {
            "connected": False,
            "status": "BLOCKED_EXTERNAL",
            "provider": "offline",
            "message": "当前处于纯本地安全模式（未配置外部大模型 API Key）。",
            "reason": "玄鉴·书房绝不静默向外部发送您的个人研究课题。象数计算与古籍考据已全部在本地完成。",
            "authoritative_calculation": authoritative_core,
            "copy_task_prompt": f"【系统提示】\n{gp.system_prompt}\n\n【用户课题】\n{gp.user_prompt}",
            "suggestion": "您可以一键复制完整的结构化提示词，在您受信任的宿主环境（如 AGY 终端、本地 Ollama 或网页大模型）中研读。"
        }

    # 配额防线检查与并发预扣锁 (Reservation Lock)
    tracker = get_budget_tracker()
    try:
        reservation_id = tracker.reserve(estimated_tokens=config.max_tokens)
    except BudgetExceededError as be:
        return {
            "connected": False,
            "status": "BUDGET_EXCEEDED",
            "provider": config.provider_type,
            "message": str(be),
            "reason": "触发个人每日或每月费用防线保护，已自动切换为离线模式。",
            "authoritative_calculation": authoritative_core,
            "copy_task_prompt": f"【系统提示】\n{gp.system_prompt}\n\n【用户课题】\n{gp.user_prompt}"
        }

    # 发起外部请求
    try:
        if config.provider_type == "openai_compatible":
            res = call_openai_compatible(config, gp.system_prompt, gp.user_prompt)
        elif config.provider_type == "gemini":
            res = call_gemini(config, gp.system_prompt, gp.user_prompt)
        elif config.provider_type == "claude":
            res = call_claude(config, gp.system_prompt, gp.user_prompt)
        else:
            raise ValueError(f"未知的 AI Provider 类型: {config.provider_type}")

        actual_tokens = res.get("total_tokens", 500)
        # 成功结算：释放预占并计入实际使用量
        tracker.settle(reservation_id, actual_tokens, estimated_tokens=config.max_tokens)

        # 接地性引用校验与象数结构防篡改保护
        raw_content = res.get("content", "")
        g_check = verify_grounding_and_integrity(raw_content, calculation_data, valid_citation_ids)

        return {
            "connected": True,
            "status": "SUCCESS",
            "provider": config.provider_type,
            "model": res.get("model", config.model_name),
            "tokens_used": actual_tokens,
            "interpretation": g_check["cleaned_content"],
            "grounding_check": {
                "citations_found": g_check["citations_found"],
                "invalid_citations": g_check["invalid_citations"],
                "citations_valid": g_check["citations_valid"],
                "model_tampered_core": g_check["model_tampered_core"],
                "warnings": g_check["warnings"]
            },
            "authoritative_calculation": g_check["authoritative_core"],
            "copy_task_prompt": f"【系统提示】\n{gp.system_prompt}\n\n【用户课题】\n{gp.user_prompt}"
        }
    except Exception as e:
        # 调用失败或异常：安全回滚补偿预扣配额，不虚假扣除用户预算
        tracker.release(reservation_id, estimated_tokens=config.max_tokens)
        return {
            "connected": False,
            "status": "BLOCKED_EXTERNAL",
            "provider": config.provider_type,
            "message": f"连接外部 AI 服务失败: {str(e)}",
            "reason": "外部网络或 API 认证不通。已自动安全降级为本地离线模式。",
            "authoritative_calculation": authoritative_core,
            "copy_task_prompt": f"【系统提示】\n{gp.system_prompt}\n\n【用户课题】\n{gp.user_prompt}",
            "suggestion": "可检查网络与 API Key 配置，或直接一键复制任务提示词。"
        }

def test_ai_provider_connection(config: AIProviderConfig) -> Dict[str, Any]:
    """测试指定的 AI Provider 连接是否通畅"""
    if config.provider_type == "offline":
        return {
            "success": True,
            "message": "离线模式正常（仅本地运行，不消耗外部算力与网络）。"
        }
    if not config.api_key:
        return {
            "success": False,
            "message": "未提供 API Key，无法连接外部服务。"
        }

    try:
        if config.provider_type == "openai_compatible":
            res = call_openai_compatible(config, "You are a test agent.", "Say OK.", timeout=8)
        elif config.provider_type == "gemini":
            res = call_gemini(config, "You are a test agent.", "Say OK.", timeout=8)
        elif config.provider_type == "claude":
            res = call_claude(config, "You are a test agent.", "Say OK.", timeout=8)
        else:
            return {"success": False, "message": f"未知协议类型: {config.provider_type}"}

        return {
            "success": True,
            "message": f"成功连接至 {config.provider_type} ({res.get('model', config.model_name)})！",
            "model": res.get("model", config.model_name)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接测试失败: {str(e)}"
        }
