#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backend/server.py - 玄鉴·书房 本地服务

纯标准库 HTTP 架构，无繁复框架开销，极速启动与响应。
提供日历计算、六爻象数、禁忌考据、知止反思、典藏检索、本地 SQLite 记录与数据导出接口。
具备跨站 DNS Rebinding 与非授权 Host 访问校验，保障本地威胁边界安全。
"""

import sys
import os
import json
import datetime
import base64
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

# 将上级目录加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.iching import (
    calculate_hexagram,
    cast_coins,
    cast_random_uniform,
    COINS_DISTRIBUTION,
    UNIFORM_RANDOM_DISTRIBUTION
)
from xuanjian.calendar_engine import get_calendar_day, ENGINE_METADATA
from xuanjian.taboos_data import YI_JI_GLOSSARY, TRADITIONAL_TABOOS, search_taboos, get_taboo_by_term
from xuanjian.reflection_engine import evaluate_reflection
from xuanjian.classics_data import CLASSICAL_READINGS, GLOSSARY_TERMS, search_classics
from xuanjian.export_service import export_divination_markdown, export_reflection_markdown, export_bundle_json
from xuanjian.storage import get_storage
from xuanjian.bazi_engine import calculate_bazi
from xuanjian.hexagram_graph import get_hexagram_node, get_all_hexagrams_summary, search_hexagrams
from xuanjian.ai_provider import (
    get_ai_config,
    update_ai_config,
    get_budget_tracker,
    generate_ai_interpretation,
    test_ai_provider_connection,
    AIProviderConfig
)
from xuanjian.backup_crypto import (
    create_database_backup,
    restore_database_backup,
    CryptoAuthError
)
from xuanjian.sync_service import (
    get_sync_config,
    update_sync_config,
    test_webdav_connection,
    sync_push,
    sync_pull_and_merge,
    WebDAVSyncConfig
)
from xuanjian.ziwei_engine import calculate_ziwei
from xuanjian.qimen_engine import calculate_qimen
from xuanjian.builtin_reader import generate_builtin_reading
from xuanjian.divination_reading import enrich_calculation, FLOW_VERSION
import secrets
from xuanjian.daodejing_data import get_all_daodejing_chapters, get_daodejing_chapter
from xuanjian.runtime_env import (
    get_data_dir,
    get_default_db_path,
    get_node_bin_path,
    is_bundled_node,
    get_frontend_dist_dir,
    get_desensitized_diagnostics
)

HOST = os.environ.get("XUANJIAN_HOST", "127.0.0.1")
PORT = int(os.environ.get("XUANJIAN_PORT", 8788))

_CURRENT_SERVER: Optional[HTTPServer] = None

class XuanJianAPIHandler(BaseHTTPRequestHandler):

    def log_message(self, format: str, *args: Any) -> None:
        # 安全脱敏日志：剥离 query 参数，绝不在日志中保留私人输入
        try:
            msg = format % args
            import re
            msg = re.sub(r'\?[^ ]*', '?[REDACTED]', msg)
            sys.stderr.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _verify_request_origin(self) -> bool:
        """防御跨站 DNS Rebinding 与非授权 Host/Origin 访问"""
        host = self.headers.get("Host", "")
        host_name = host.split(":")[0].strip()
        if host_name not in ("127.0.0.1", "localhost", "::1"):
            self._respond_error("禁止未授权的主机名访问 (Host invalid)", 403)
            return False

        origin = self.headers.get("Origin")
        if origin:
            parsed_origin = urllib.parse.urlparse(origin)
            origin_host = parsed_origin.hostname
            if origin_host not in ("127.0.0.1", "localhost", "::1", None):
                self._respond_error("禁止跨站来源请求 (Origin invalid)", 403)
                return False
        return True

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json; charset=utf-8"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _respond_json(self, data: Any, status_code: int = 200):
        self._set_headers(status_code, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _respond_error(self, message: str, status_code: int = 400):
        self._respond_json({"error": True, "message": message}, status_code)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. 健康状态与基础自检
        if path == "/api/health":
            has_api_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("XUANJIAN_OPERATOR_API_KEY"))
            self._respond_json({
                "status": "healthy",
                "app": "玄鉴·书房 (XuanJian Studio)",
                "version": "3.0.1",
                "flow_version": FLOW_VERSION,
                "build_id": os.environ.get("XUANJIAN_BUILD_ID", FLOW_VERSION),
                "app_mode": os.environ.get("XUANJIAN_APP_MODE") == "1",
                "ai_connected": has_api_key,
                "engines": ["zhouyi", "bazi", "ziwei", "qimen"],
                "engine": ENGINE_METADATA["engine"],
                "engine_version": ENGINE_METADATA["version"],
                "timezone": ENGINE_METADATA["timezone"],
                "running_mode": "纯本地·免API·离线优先"
            })
            return

        # 1.1 系统信息查询 (关于弹窗)
        if path == "/api/system/info":
            storage = get_storage()
            data_dir = get_data_dir()
            db_path = storage.db_path
            node_path = get_node_bin_path()
            has_api_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("XUANJIAN_OPERATOR_API_KEY"))
            self._respond_json({
                "status": "healthy",
                "pid": os.getpid(),
                "app": "玄鉴·书房 (XuanJian Studio)",
                "version": "3.0.1",
                "flow_version": FLOW_VERSION,
                "build_id": os.environ.get("XUANJIAN_BUILD_ID", FLOW_VERSION),
                "app_mode": os.environ.get("XUANJIAN_APP_MODE") == "1",
                "mode": "本地单机 · 离线优先 · 免API",
                "data_dir": data_dir,
                "db_path": db_path,
                "logs_dir": os.path.join(data_dir, "logs"),
                "backups_dir": os.path.join(data_dir, "backups"),
                "engines": {
                    "zhouyi": "六爻象数确定性引擎 v3.0.1 (互错综/变爻图)",
                    "bazi": "lunar-python v1.4.8 (高精度节气立春交接)",
                    "ziwei": "iztro v2.6.1 (私有Node Worker确定性排盘)",
                    "qimen": "bigfishmarquis-qimen v1.0.0 (时家转盘拆补九宫)",
                    "builtin_reader": "免API确定性传统研读引擎",
                    "daodejing": "《道德经》八十一章传世本全息研读"
                },
                "node_runtime": {
                    "is_bundled": is_bundled_node(),
                    "path": node_path
                },
                "ai_connected": has_api_key
            })
            return

        # 1.2 严格脱敏系统诊断导出
        if path == "/api/system/diagnostics":
            storage = get_storage()
            extra = {}
            try:
                with storage.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT count(*) FROM records WHERE is_deleted = 0;")
                    extra["records_count"] = cur.fetchone()[0]
                    cur.execute("PRAGMA integrity_check;")
                    extra["db_integrity"] = cur.fetchone()[0]
            except Exception:
                pass
            extra["port"] = PORT
            diag = get_desensitized_diagnostics(extra)
            self._respond_json(diag)
            return

        # 2. 历法查询
        if path == "/api/calendar":
            date_str = query.get("date", [None])[0]
            try:
                if date_str:
                    target_date = datetime.date.fromisoformat(date_str)
                else:
                    target_date = datetime.date.today()
                cal_data = get_calendar_day(target_date)
                self._respond_json(cal_data)
            except ValueError as ve:
                self._respond_error(f"日期格式或范围错误: {str(ve)}", 400)
            except Exception as e:
                self._respond_error(f"历法计算异常: {str(e)}", 500)
            return

        # 3. 禁忌出处考据查证接口
        if path == "/api/taboos/verify":
            q = query.get("q", [""])[0].strip() or query.get("term", [""])[0].strip()
            result = search_taboos(q)
            self._respond_json(result)
            return

        # 4. 典籍通识与六十四卦义理检索
        if path in ("/api/classics", "/api/classics/search"):
            q = query.get("q", [""])[0].strip()
            category = query.get("category", [None])[0] or ""
            result = search_classics(q, category)
            self._respond_json(result)
            return

        # 5. 传统通书完整宜忌词汇表查询
        if path == "/api/taboos/glossary":
            self._respond_json({
                "count": len(YI_JI_GLOSSARY),
                "glossary": YI_JI_GLOSSARY
            })
            return

        # 5.1 六十四卦关系网概览与检索
        if path == "/api/hexagrams":
            q = urllib.parse.unquote(query.get("q", [""])[0].strip())
            if q:
                res = search_hexagrams(q)
            else:
                res = get_all_hexagrams_summary()
            self._respond_json({"count": len(res), "hexagrams": res})
            return

        # 5.2 六十四卦单卦关系节点查询: /api/hexagrams/<id_or_name>
        if path.startswith("/api/hexagrams/"):
            ident = urllib.parse.unquote(path[len("/api/hexagrams/"):].strip())
            if ident:
                try:
                    node = get_hexagram_node(ident)
                    self._respond_json(node)
                except Exception as e:
                    self._respond_error(f"查询卦象失败: {str(e)}", 404)
                return

        # 5.3 八字排盘查询 (GET 快捷推算)
        if path == "/api/bazi/calculate":
            try:
                y = int(query.get("year", [2000])[0])
                m = int(query.get("month", [1])[0])
                d = int(query.get("day", [1])[0])
                h_param = query.get("hour", [None])[0]
                h = int(h_param) if h_param is not None and h_param != "" else None
                min_param = query.get("minute", [0])[0]
                minute = int(min_param) if min_param is not None and min_param != "" else 0
                gender = query.get("gender", ["乾造"])[0]
                is_lunar = query.get("is_lunar", ["false"])[0].lower() in ("true", "1")
                is_leap = query.get("is_leap", ["false"])[0].lower() in ("true", "1")
                zi_sect_param = query.get("zi_hour_sect", [query.get("zi_hour_mode", ["2"])[0]])[0]
                zi_hour_sect = 1 if str(zi_sect_param) in ("1", "23", "23:00") else 2
                bazi_res = calculate_bazi(y, m, d, h, minute, gender, is_lunar, is_leap, zi_hour_sect=zi_hour_sect)
                self._respond_json(bazi_res)
            except Exception as e:
                self._respond_error(f"八字推算异常: {str(e)}", 400)
            return

        # 5.4 紫微斗数排盘查询 (GET)
        if path == "/api/ziwei/calculate":
            try:
                y = int(query.get("year", [1990])[0])
                m = int(query.get("month", [5])[0])
                d = int(query.get("day", [15])[0])
                h_param = query.get("hour", [None])[0]
                h = int(h_param) if h_param is not None and h_param != "" else None
                gender = query.get("gender", ["男"])[0]
                cal = query.get("calendar", ["solar"])[0]
                is_leap = query.get("is_leap", ["false"])[0].lower() in ("true", "1")
                target_date = query.get("target_date", [None])[0]
                zw_res = calculate_ziwei(y, m, d, h, calendar_type=cal, gender=gender, is_leap_month=is_leap, target_date=target_date)
                self._respond_json(zw_res)
            except Exception as e:
                self._respond_error(f"紫微排盘异常: {str(e)}", 400)
            return

        # 5.5 时家转盘奇门排盘查询 (GET)
        if path == "/api/qimen/calculate":
            try:
                now = datetime.datetime.now()
                y = int(query.get("year", [now.year])[0])
                m = int(query.get("month", [now.month])[0])
                d = int(query.get("day", [now.day])[0])
                h = int(query.get("hour", [now.hour])[0])
                minute = int(query.get("minute", [now.minute])[0])
                topic = urllib.parse.unquote(query.get("topic", [""])[0].strip())
                term = query.get("term", [None])[0]
                qm_res = calculate_qimen(y, m, d, h, minute, topic=topic, solar_term=term)
                self._respond_json(qm_res)
            except Exception as e:
                self._respond_error(f"奇门排盘异常: {str(e)}", 400)
            return

        # 5.6 道德经章节查询 (GET): /api/classics/daodejing?chapter=1
        if path == "/api/classics/daodejing":
            ch_param = query.get("chapter", [None])[0]
            if ch_param is not None and ch_param != "":
                try:
                    ch_num = int(ch_param)
                except (ValueError, TypeError):
                    self._respond_error(f"道德经章次参数必须为整数: {ch_param}", 400)
                    return

                ch = get_daodejing_chapter(ch_num)
                if ch is None:
                    self._respond_error(f"道德经章次无效 (仅支持 1-81 章): {ch_num}", 404)
                    return
                self._respond_json(ch)
            else:
                chapters = get_all_daodejing_chapters()
                self._respond_json({"total": len(chapters), "chapters": chapters})
            return

        # 6.0 本地 SQLite 记录与复盘统计查询
        if path == "/api/records/statistics":
            try:
                storage = get_storage()
                stats = storage.get_review_statistics()
                self._respond_json(stats)
            except Exception as e:
                self._respond_error(f"获取复盘统计失败: {str(e)}", 500)
            return

        # 6. 本地 SQLite 记录列表查询
        if path == "/api/records":
            record_type = query.get("type", [None])[0]
            tag = query.get("tag", [None])[0]
            kw = query.get("query", [None])[0]
            limit = int(query.get("limit", [50])[0])
            offset = int(query.get("offset", [0])[0])
            try:
                storage = get_storage()
                records, total = storage.list_records(
                    record_type=record_type,
                    tag=tag,
                    query=kw,
                    limit=limit,
                    offset=offset
                )
                self._respond_json({
                    "records": records,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                })
            except Exception as e:
                self._respond_error(f"查询记录失败: {str(e)}", 500)
            return

        # 6.1 单条记录获取: /api/records/<id>
        if path.startswith("/api/records/"):
            rec_id = path[len("/api/records/"):].strip()
            if rec_id:
                try:
                    storage = get_storage()
                    rec = storage.get_record(rec_id)
                    if rec:
                        self._respond_json(rec)
                    else:
                        self._respond_error("记录不存在", 404)
                except Exception as e:
                    self._respond_error(f"获取记录失败: {str(e)}", 500)
                return

        # 6.2 AI 配置与预算状态查询
        if path == "/api/ai/config":
            cfg = get_ai_config()
            tracker = get_budget_tracker()
            self._respond_json({
                "config": cfg.to_dict(mask_key=True),
                "budget": tracker.get_status()
            })
            return

        # 6.3 WebDAV 同步配置查询
        if path == "/api/sync/config":
            cfg = get_sync_config()
            self._respond_json({
                "config": cfg.to_dict(mask_secret=True)
            })
            return

        # 静态资源服务 (前端生产构建产物 frontend/dist)
        dist_dir = get_frontend_dist_dir()
        if os.path.exists(dist_dir):
            req_file = path.lstrip("/")
            if not req_file:
                req_file = "index.html"

            # 严格解析真实路径与包含关系，防目录穿越
            real_dist = os.path.realpath(dist_dir)
            try:
                decoded_file = urllib.parse.unquote(req_file)
                candidate_path = os.path.abspath(os.path.join(real_dist, decoded_file))
                if os.path.commonpath([real_dist, candidate_path]) != real_dist:
                    self._respond_error("禁止越界访问 (目录穿越防护)", 403)
                    return
            except ValueError:
                self._respond_error("禁止越界访问 (路径异常)", 403)
                return

            if os.path.exists(candidate_path):
                real_candidate = os.path.realpath(candidate_path)
                try:
                    if os.path.commonpath([real_dist, real_candidate]) != real_dist:
                        self._respond_error("禁止越界访问 (符号链接越界)", 403)
                        return
                except ValueError:
                    self._respond_error("禁止越界访问 (符号链接异常)", 403)
                    return
                file_path = real_candidate
            else:
                file_path = os.path.join(real_dist, "index.html")

            if os.path.isfile(file_path):
                content_type = "text/plain"
                if file_path.endswith(".html"):
                    content_type = "text/html; charset=utf-8"
                elif file_path.endswith(".js"):
                    content_type = "application/javascript; charset=utf-8"
                elif file_path.endswith(".css"):
                    content_type = "text/css; charset=utf-8"
                elif file_path.endswith(".svg"):
                    content_type = "image/svg+xml"
                elif file_path.endswith(".json"):
                    content_type = "application/json; charset=utf-8"

                with open(file_path, "rb") as f:
                    content = f.read()
                self._set_headers(200, content_type)
                self.wfile.write(content)
                return

        self._respond_error("接口不存在", 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # 1. 六爻起卦与象数计算
        if path == "/api/iching/calculate":
            lines = body.get("lines")
            if not lines or not isinstance(lines, list) or len(lines) != 6:
                self._respond_error("请提供自下而上的6个爻值列表 (初爻至上爻)，取值必须为 6, 7, 8, 9", 400)
                return
            try:
                calc_result = calculate_hexagram([int(x) for x in lines])
                enrich_calculation(calc_result, body.get("topic", ""), "manual_lines")
                self._respond_json(calc_result)
            except Exception as e:
                self._respond_error(f"计算失败: {str(e)}", 400)
            return

        # 1.1 八字排盘与干支四柱计算 (POST)
        if path == "/api/bazi/calculate":
            try:
                y = int(body.get("year", 2000))
                m = int(body.get("month", 1))
                d = int(body.get("day", 1))
                h = body.get("hour", None)
                if h is not None and h != "":
                    h = int(h)
                else:
                    h = None
                minute = int(body.get("minute", 0)) if body.get("minute") is not None and body.get("minute") != "" else 0
                gender = str(body.get("gender", "乾造"))
                is_lunar = bool(body.get("is_lunar", False))
                is_leap = bool(body.get("is_leap_month", False))
                zi_sect_param = body.get("zi_hour_sect", body.get("zi_hour_mode", 2))
                zi_hour_sect = 1 if str(zi_sect_param) in ("1", "23", "23:00") else 2
                bazi_res = calculate_bazi(y, m, d, h, minute, gender, is_lunar, is_leap, zi_hour_sect=zi_hour_sect)
                self._respond_json(bazi_res)
            except Exception as e:
                self._respond_error(f"八字排盘计算失败: {str(e)}", 400)
            return

        # 1.2 紫微斗数排盘 (POST)
        if path == "/api/ziwei/calculate":
            try:
                y = int(body.get("year", 1990))
                m = int(body.get("month", 5))
                d = int(body.get("day", 15))
                h = body.get("hour", None)
                if h is not None and h != "":
                    h = int(h)
                else:
                    h = None
                gender = str(body.get("gender", "男"))
                cal = str(body.get("calendar", body.get("calendar_type", "solar")))
                is_leap = bool(body.get("is_leap_month", False))
                target_date = body.get("target_date", None)
                zw_res = calculate_ziwei(y, m, d, h, calendar_type=cal, gender=gender, is_leap_month=is_leap, target_date=target_date)
                self._respond_json(zw_res)
            except Exception as e:
                self._respond_error(f"紫微排盘计算失败: {str(e)}", 400)
            return

        # 1.3 时家转盘奇门排盘 (POST)
        if path == "/api/qimen/calculate":
            try:
                now = datetime.datetime.now()
                y = int(body.get("year", now.year))
                m = int(body.get("month", now.month))
                d = int(body.get("day", now.day))
                h = int(body.get("hour", now.hour))
                minute = int(body.get("minute", now.minute))
                topic = str(body.get("topic", "")).strip()
                term = body.get("solar_term", body.get("term", None))
                qm_res = calculate_qimen(y, m, d, h, minute, topic=topic, solar_term=term)
                self._respond_json(qm_res)
            except Exception as e:
                self._respond_error(f"奇门排盘计算失败: {str(e)}", 400)
            return

        # 1.4 内置传统典籍研读 (POST, 100% 离线·免外部 API)
        if path == "/api/builtin/read":
            try:
                rec_type = body.get("record_type", "divination")
                calc_data = body.get("calculation", {})
                topic = body.get("topic", "")
                read_res = generate_builtin_reading(rec_type, calc_data, topic)
                self._respond_json(read_res)
            except Exception as e:
                self._respond_error(f"生成内置研读失败: {str(e)}", 400)
            return

        # One real draw per click; the UI accumulates six throws bottom-to-top.
        if path == "/api/iching/coin":
            coins = [2 + secrets.randbelow(2) for _ in range(3)]
            self._respond_json({"coins": coins, "value": sum(coins)})
            return

        # 2. 模拟三铜钱起卦 (二项分布)
        if path == "/api/iching/coins":
            lines, flips = cast_coins()
            calc_result = calculate_hexagram(lines)
            calc_result["coin_flips"] = flips
            calc_result["generation_mode"] = "three_coins"
            calc_result["distribution_info"] = COINS_DISTRIBUTION
            enrich_calculation(calc_result, body.get("topic", ""), "three_coins")
            self._respond_json(calc_result)
            return

        # 2.1 离散等概率随机起卦 (离散均匀分布)
        if path == "/api/iching/random":
            lines = cast_random_uniform()
            calc_result = calculate_hexagram(lines)
            calc_result["generation_mode"] = "random_uniform"
            calc_result["distribution_info"] = UNIFORM_RANDOM_DISTRIBUTION
            enrich_calculation(calc_result, body.get("topic", ""), "random_uniform")
            self._respond_json(calc_result)
            return

        # 3. 现实风险提醒与决定前暂停卡评估
        if path == "/api/reflection/evaluate":
            try:
                res = evaluate_reflection(body)
                self._respond_json(res)
            except Exception as e:
                self._respond_error(f"反思评估失败: {str(e)}", 400)
            return

        # 4. 数据导出服务 (Markdown / JSON)
        if path == "/api/export":
            export_type = body.get("type", "divination")
            format_type = body.get("format", "markdown")
            payload = body.get("data", {})

            if format_type == "json":
                out = export_bundle_json(payload)
                self._set_headers(200, "application/json; charset=utf-8")
                self.wfile.write(out.encode("utf-8"))
                return
            else:
                if export_type == "reflection":
                    out = export_reflection_markdown(payload)
                else:
                    out = export_divination_markdown(payload)
                self._set_headers(200, "text/markdown; charset=utf-8")
                self.wfile.write(out.encode("utf-8"))
                return

        # 5. AI 解读接口 (严格区分有 API 与无 API 模式，支持各协议及配额防线)
        if path == "/api/ai/interpret":
            topic = body.get("topic", "")
            calc_data = body.get("calculation", {})
            res = generate_ai_interpretation(topic, calc_data)
            self._respond_json(res)
            return

        # 5.1 AI Provider 配置更新
        if path == "/api/ai/config":
            if not self._verify_request_origin():
                return
            new_cfg = update_ai_config(body)
            tracker = get_budget_tracker()
            self._respond_json({
                "config": new_cfg.to_dict(mask_key=True),
                "budget": tracker.get_status(),
                "message": "AI Provider 配置已更新"
            })
            return

        # 5.2 AI 连接测试接口
        if path == "/api/ai/test":
            if not self._verify_request_origin():
                return
            cfg = get_ai_config()
            if body and isinstance(body, dict) and body.get("provider_type"):
                test_cfg = AIProviderConfig(
                    provider_type=body.get("provider_type", cfg.provider_type),
                    base_url=body.get("base_url", cfg.base_url),
                    model_name=body.get("model_name", cfg.model_name),
                    api_key=cfg.api_key if (not body.get("api_key") or "****" in body.get("api_key")) else body.get("api_key"),
                    temperature=body.get("temperature", cfg.temperature),
                    max_tokens=body.get("max_tokens", cfg.max_tokens)
                )
            else:
                test_cfg = cfg
            res = test_ai_provider_connection(test_cfg)
            self._respond_json(res)
            return

        # 6. 新建本地 SQLite 记录 (用户主动保存)
        if path == "/api/records":
            if not self._verify_request_origin():
                return
            storage = get_storage()
            try:
                rec = storage.create_record(body)
                self._respond_json(rec, 201)
            except Exception as e:
                self._respond_error(f"保存记录失败: {str(e)}", 400)
            return

        # 6.1 批量导出记录
        if path == "/api/records/export":
            format_type = body.get("format", "markdown")
            ids = body.get("ids", None)
            storage = get_storage()
            if format_type == "json":
                records, _ = storage.list_records(limit=1000)
                if ids:
                    records = [r for r in records if r["id"] in ids]
                self._respond_json({
                    "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "count": len(records),
                    "records": records
                })
            else:
                md_text = storage.export_records_as_markdown(ids)
                self._set_headers(200, "text/markdown; charset=utf-8")
                self.wfile.write(md_text.encode("utf-8"))
            return

        # 6.2 清除全部记录 (严格隔离防护，仅在显式设置 XUANJIAN_ALLOW_CLEAR_RECORDS=1 的测试隔离环境中允许执行)
        if path == "/api/records/clear":
            if not self._verify_request_origin():
                return
            if os.environ.get("XUANJIAN_ALLOW_CLEAR_RECORDS") != "1":
                self._respond_error("禁止在非测试隔离环境下清除全部记录 (XUANJIAN_ALLOW_CLEAR_RECORDS != 1)", 403)
                return
            storage = get_storage()
            storage.clear_all_records()
            self._respond_json({"cleared": True, "message": "所有本地记录已清除"})
            return

        # 7.1 加密备份导出 (AES-256-GCM AEAD)
        if path == "/api/backup/export":
            if not self._verify_request_origin():
                return
            storage = get_storage()
            passphrase = body.get("passphrase") if isinstance(body, dict) else None
            try:
                enc_bytes = create_database_backup(storage.db_path, passphrase=passphrase)
                b64_data = base64.b64encode(enc_bytes).decode("ascii")
                ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"xuanjian_backup_{ts_str}.{'xjb' if passphrase else 'db'}"
                self._respond_json({
                    "success": True,
                    "filename": filename,
                    "size": len(enc_bytes),
                    "encrypted": bool(passphrase),
                    "data": b64_data
                })
            except Exception as e:
                self._respond_error(f"导出备份失败: {str(e)}", 500)
            return

        # 7.2 备份恢复
        if path == "/api/backup/restore":
            if not self._verify_request_origin():
                return
            storage = get_storage()
            if not body or not isinstance(body, dict) or "data" not in body:
                self._respond_error("缺少备份数据包 (data 字段)", 400)
                return
            passphrase = body.get("passphrase")
            try:
                raw_bytes = base64.b64decode(body["data"])
                res = restore_database_backup(raw_bytes, storage.db_path, passphrase=passphrase)
                if "message" not in res:
                    res["message"] = f"备份数据校验无误，已恢复 {res.get('restored_records_count', 0)} 条记录。"
                self._respond_json(res)
            except CryptoAuthError as ce:
                self._respond_error(str(ce), 401)
            except Exception as e:
                self._respond_error(f"恢复备份失败: {str(e)}", 500)
            return

        # 7.3 保存 WebDAV 配置
        if path == "/api/sync/config":
            if not self._verify_request_origin():
                return
            if not body or not isinstance(body, dict):
                self._respond_error("请求体必须为 JSON 对象", 400)
                return
            updated = update_sync_config(body)
            self._respond_json({
                "success": True,
                "config": updated.to_dict(mask_secret=True)
            })
            return

        # 7.4 测试 WebDAV 连接
        if path == "/api/sync/test":
            if not self._verify_request_origin():
                return
            cfg = get_sync_config()
            if body and isinstance(body, dict) and body.get("server_url"):
                test_cfg = WebDAVSyncConfig(
                    enabled=body.get("enabled", cfg.enabled),
                    server_url=body.get("server_url", cfg.server_url),
                    username=body.get("username", cfg.username),
                    password=cfg.password if (not body.get("password") or "********" in body.get("password")) else body.get("password"),
                    remote_path=body.get("remote_path", cfg.remote_path),
                    encryption_passphrase=cfg.encryption_passphrase if (not body.get("encryption_passphrase") or "********" in body.get("encryption_passphrase")) else body.get("encryption_passphrase")
                )
            else:
                test_cfg = cfg
            res = test_webdav_connection(test_cfg)
            self._respond_json(res)
            return

        # 7.5 WebDAV 快照推送
        if path == "/api/sync/push":
            if not self._verify_request_origin():
                return
            cfg = get_sync_config()
            if not cfg.is_configured:
                self._respond_error("WebDAV 尚未配置完整的服务器地址与账号", 400)
                return
            storage = get_storage()
            try:
                res = sync_push(storage, cfg)
                self._respond_json(res)
            except Exception as e:
                self._respond_error(f"推送同步失败: {str(e)}", 500)
            return

        # 7.6 WebDAV 快照拉取与合并
        if path == "/api/sync/pull":
            if not self._verify_request_origin():
                return
            cfg = get_sync_config()
            if not cfg.is_configured:
                self._respond_error("WebDAV 尚未配置完整的服务器地址与账号", 400)
                return
            storage = get_storage()
            try:
                res = sync_pull_and_merge(storage, cfg)
                self._respond_json(res)
            except CryptoAuthError as ce:
                self._respond_error(str(ce), 401)
            except Exception as e:
                self._respond_error(f"拉取合并失败: {str(e)}", 500)
            return

        # 8. 系统级交互操作
        if path == "/api/system/open_data_dir":
            if not self._verify_request_origin():
                return
            data_dir = get_data_dir()
            os.makedirs(data_dir, exist_ok=True)
            import subprocess
            try:
                if sys.platform == "darwin":
                    subprocess.Popen(["open", data_dir])
                elif sys.platform.startswith("win"):
                    os.startfile(data_dir)
                else:
                    subprocess.Popen(["xdg-open", data_dir])
                self._respond_json({"status": "ok", "opened": data_dir})
            except Exception as e:
                self._respond_error(f"打开数据目录失败: {str(e)}", 500)
            return

        if path == "/api/system/shutdown":
            if not self._verify_request_origin():
                return
            self._respond_json({"status": "ok", "message": "玄鉴后台服务正在安全停止..."})
            import threading
            def _shutdown_bg():
                import time
                time.sleep(0.5)
                global _CURRENT_SERVER
                if _CURRENT_SERVER:
                    _CURRENT_SERVER.shutdown()
                else:
                    os._exit(0)
            threading.Thread(target=_shutdown_bg, daemon=True).start()
            return

        self._respond_error("接口不存在", 404)

    def do_PUT(self):
        if not self._verify_request_origin():
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # 更新记录或复盘
        if path.startswith("/api/records/"):
            rec_id = path[len("/api/records/"):].strip()
            if rec_id:
                try:
                    storage = get_storage()
                    if "review_data" in body:
                        rev_data = body.pop("review_data")
                        storage.update_review(rec_id, rev_data)
                    updated = storage.update_record(rec_id, body) if body else storage.get_record(rec_id)
                    if updated:
                        self._respond_json(updated)
                    else:
                        self._respond_error("记录不存在或更新失败", 404)
                except Exception as e:
                    self._respond_error(f"更新记录异常: {str(e)}", 500)
                return

        self._respond_error("接口不存在", 404)

    def do_DELETE(self):
        if not self._verify_request_origin():
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 删除单条记录
        if path.startswith("/api/records/"):
            rec_id = path[len("/api/records/"):].strip()
            if rec_id:
                permanent = query.get("permanent", ["false"])[0].lower() == "true"
                try:
                    storage = get_storage()
                    success = storage.delete_record(rec_id, permanent=permanent)
                    if success:
                        self._respond_json({"deleted": True, "id": rec_id, "permanent": permanent})
                    else:
                        self._respond_error("记录不存在或已被删除", 404)
                except Exception as e:
                    self._respond_error(f"删除记录异常: {str(e)}", 500)
                return

        self._respond_error("接口不存在", 404)

def run_server(port: Optional[int] = None):
    global _CURRENT_SERVER
    actual_port = port or PORT
    server_address = (HOST, actual_port)
    httpd = HTTPServer(server_address, XuanJianAPIHandler)
    _CURRENT_SERVER = httpd
    print(f"「玄鉴·书房」后端服务已启动: http://{HOST}:{actual_port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
