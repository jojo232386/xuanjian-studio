# xuanjian/storage.py - 本地 SQLite 数据引擎、检索、复盘与安全迁移机制

import os
import json
import sqlite3
import uuid
import datetime
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple
from xuanjian.runtime_env import get_data_dir, get_default_db_path

logger = logging.getLogger("xuanjian.storage")

CURRENT_SCHEMA_VERSION = 1

DEFAULT_DB_DIR = get_data_dir()
DEFAULT_DB_PATH = get_default_db_path()


class StorageError(Exception):
    """存储模块专用异常"""
    pass


class StorageManager:
    """
    玄鉴·书房 SQLite 存储管理器
    支持记录保存、事后复盘、中文检索、软删除、幂等导入与版本迁移。
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """获取线程安全的 SQLite 连接并设置超时与 WAL 模式"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            return conn
        except sqlite3.DatabaseError as e:
            logger.error(f"数据库连接异常: {e}")
            raise StorageError(f"数据库连接失败: {e}")

    def _init_db(self):
        """初始化表结构并应用迁移"""
        try:
            with self.get_connection() as conn:
                # 检查数据库完整性
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                check_result = cursor.fetchone()[0]
                if check_result != "ok":
                    raise sqlite3.DatabaseError(f"数据库完整性受损: {check_result}")

                # 创建版本迁移表
                conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT NOT NULL
                );
                """)

                # 运行迁移
                self._run_migrations(conn)
        except (sqlite3.DatabaseError, StorageError) as e:
            logger.warning(f"检测到数据库异常或损坏，执行安全恢复保护: {e}")
            self._recover_corrupted_db()

    def _recover_corrupted_db(self):
        backup_path = None
        if os.path.exists(self.db_path):
            backup_path = f"{self.db_path}.corrupted.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
            try:
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"已将损坏数据库隔离至: {backup_path}")
            except Exception as copy_err:
                logger.error(f"隔离损坏数据库失败: {copy_err}")
            try:
                os.remove(self.db_path)
                # 同时也清理 wal 和 shm
                for ext in ["-wal", "-shm", "-journal"]:
                    if os.path.exists(self.db_path + ext):
                        os.remove(self.db_path + ext)
            except Exception as rm_err:
                logger.error(f"移除损坏数据库失败: {rm_err}")

        # 重新创建全新干净库
        with self.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT NOT NULL
            );
            """)
            self._run_migrations(conn)

            # 若先前存在受损库隔离备份，写入显式安全防线提示手记，明确说明空库重建不等于找回旧数据
            if backup_path:
                bak_filename = os.path.basename(backup_path)
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                notice_id = f"SYS_CORRUPT_NOTICE_{uuid.uuid4().hex[:8]}"
                conn.execute("""
                INSERT INTO records (
                    id, schema_version, record_type, title, topic, tags,
                    review_data_json, engine_version, created_at, updated_at,
                    is_deleted, sync_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    notice_id, 1, "study_note",
                    "【安全提示】检测到本地数据库损坏并已隔离，已重建全新空库",
                    "数据库损坏隔离与数据自主防护说明",
                    "系统提示,安全防护,数据容灾",
                    json.dumps({
                        "notes": (
                            f"【数据安全与容灾说明】系统检测到原 SQLite 数据库存在底层格式损坏或物理异常。\n\n"
                            f"1. 受损数据库已安全复制隔离至磁盘备份：{bak_filename}，绝无静默丢弃；\n"
                            f"2. 当前服务已自动重建全新空库以保障可用性，这仅代表服务恢复启动，绝不等于已找回原受损数据；\n"
                            f"3. 若您此前曾导出过 AES-256-GCM 备份文件（.xjb），请前往「设置 -> 恢复备份」导入恢复历史手记。"
                        )
                    }, ensure_ascii=False),
                    "3.0.0", now_iso, now_iso, 0, 1
                ))
                conn.commit()

    def _run_migrations(self, conn: sqlite3.Connection):
        """应用未应用的增量迁移"""
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_migrations;")
        row = cursor.fetchone()
        current_db_version = row[0] if (row and row[0] is not None) else 0

        if current_db_version > CURRENT_SCHEMA_VERSION:
            raise StorageError(
                f"数据库版本 ({current_db_version}) 高于当前程序支持版本 ({CURRENT_SCHEMA_VERSION})，请升级程序。"
            )

        # 迁移 1: 核心记录表
        if current_db_version < 1:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                schema_version INTEGER DEFAULT 1,
                record_type TEXT NOT NULL,
                title TEXT NOT NULL,
                topic TEXT,
                tags TEXT,
                params_json TEXT,
                calculation_result_json TEXT,
                ai_interpret_json TEXT,
                review_data_json TEXT,
                engine_version TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                sync_version INTEGER DEFAULT 1,
                client_id TEXT
            );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_records_type ON records(record_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_records_created ON records(created_at);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_records_deleted ON records(is_deleted);")

            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # 全新库自动初始化写入一条入门指引手记
            cursor.execute("SELECT COUNT(*) FROM records;")
            if cursor.fetchone()[0] == 0:
                welcome_id = "REC_WELCOME_001"
                conn.execute("""
                INSERT INTO records (
                    id, schema_version, record_type, title, topic, tags,
                    review_data_json, engine_version, created_at, updated_at,
                    is_deleted, sync_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    welcome_id, 1, "study_note",
                    "《玄鉴·书房》使用指南与知止守则",
                    "象数研读与现实知止",
                    "入门指引,知止守则,传世文献",
                    json.dumps({
                        "notes": "欢迎研习玄鉴·书房。本案定位于易学象数研究与理性决策反思，不占卜吉凶，不恐吓宿命。所有数据存储于本地 SQLite 数据库中，支持端到端 AES-256-GCM 加密备份与 WebDAV 私有同步。"
                    }, ensure_ascii=False),
                    "2.1.0", now_iso, now_iso, 0, 1
                ))

            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at, description) VALUES (?, ?, ?);",
                (1, now_iso, "初始化记录核心表、基础索引与初始入门指引条目")
            )
            conn.commit()

    # ----------------------------------------------------
    # CRUD 核心能力
    # ----------------------------------------------------

    def create_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新建本地记录。必须由用户主动开启保存时调用。
        """
        rec_id = str(data.get("id") or uuid.uuid4())
        record_type = data.get("record_type", "divination")
        title = data.get("title") or "未命名记录"
        topic = data.get("topic", "")
        tags = data.get("tags", "")
        if isinstance(tags, list):
            tags = ",".join(tags)

        params_json = json.dumps(data.get("params", {}), ensure_ascii=False)
        calc_json = json.dumps(data.get("calculation_result", {}), ensure_ascii=False)
        ai_json = json.dumps(data.get("ai_interpret", {}), ensure_ascii=False)
        review_data = dict(data.get("review_data", {}))
        if review_data:
            if review_data.get("original_thought") and not review_data.get("initial_thought"):
                review_data["initial_thought"] = review_data["original_thought"]
            if review_data.get("observation_window") and not review_data.get("initial_observation_window"):
                review_data["initial_observation_window"] = review_data["observation_window"]
        review_json = json.dumps(review_data, ensure_ascii=False)

        engine_version = data.get("engine_version", "xuanjian-v3.0.0/lunar-1.4.8")
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        created_at = data.get("created_at") or now_str
        updated_at = data.get("updated_at") or now_str
        is_deleted = int(data.get("is_deleted", 0))
        sync_version = int(data.get("sync_version", 1))
        client_id = data.get("client_id", "local")

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO records (
                    id, schema_version, record_type, title, topic, tags,
                    params_json, calculation_result_json, ai_interpret_json,
                    review_data_json, engine_version, created_at, updated_at,
                    is_deleted, sync_version, client_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    rec_id, CURRENT_SCHEMA_VERSION, record_type, title, topic, tags,
                    params_json, calc_json, ai_json, review_json, engine_version,
                    created_at, updated_at, is_deleted, sync_version, client_id
                )
            )
            conn.commit()

        return self.get_record(rec_id, include_deleted=True)  # type: ignore

    def get_record(self, rec_id: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """根据 ID 获取单条记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if include_deleted:
                cursor.execute("SELECT * FROM records WHERE id = ?;", (rec_id,))
            else:
                cursor.execute("SELECT * FROM records WHERE id = ? AND is_deleted = 0;", (rec_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def update_record(self, rec_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新记录部分字段（如标题、标签、手记复盘等）"""
        existing = self.get_record(rec_id, include_deleted=True)
        if not existing:
            return None

        allowed_fields = [
            "title", "topic", "tags", "review_data", "ai_interpret",
            "params", "calculation_result", "is_deleted"
        ]
        sql_parts = []
        values = []

        for k in allowed_fields:
            if k in updates:
                val = updates[k]
                if k in ("review_data", "ai_interpret", "params", "calculation_result"):
                    sql_parts.append(f"{k}_json = ?")
                    values.append(json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val)
                elif k == "tags":
                    sql_parts.append("tags = ?")
                    values.append(",".join(val) if isinstance(val, list) else str(val))
                elif k == "is_deleted":
                    sql_parts.append("is_deleted = ?")
                    values.append(int(val))
                else:
                    sql_parts.append(f"{k} = ?")
                    values.append(val)

        if not sql_parts and "updated_at" not in updates:
            return existing

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        updated_at_val = updates.get("updated_at") or now_str
        sql_parts.append("updated_at = ?")
        values.append(updated_at_val)

        if "sync_version" in updates:
            sql_parts.append("sync_version = ?")
            values.append(int(updates["sync_version"]))
        else:
            sql_parts.append("sync_version = sync_version + 1")

        values.append(rec_id)
        sql = f"UPDATE records SET {', '.join(sql_parts)} WHERE id = ?;"

        with self.get_connection() as conn:
            conn.execute(sql, values)
            conn.commit()

        return self.get_record(rec_id, include_deleted=True)

    def update_review(self, rec_id: str, review_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新事后复盘数据：
        当时预期 (original_thought/initial_thought)、现实依据 (realistic_basis)、
        观察窗口 (observation_window)、实际结果 (actual_outcome)、缺失证据 (missing_evidence)、
        自评标签 (review_tags)。
        自动保留修订历史 (revisions)，杜绝事后悄悄修改原始判断伪造应验。
        """
        existing = self.get_record(rec_id)
        if not existing:
            return None

        prev_review = existing.get("review_data") or {}
        revisions = list(prev_review.get("revisions", []))

        # 锁定最初预期与最初观察窗口（一旦设定，永久不可被后续修改或切片截断冲掉）
        first_thought = (
            prev_review.get("initial_thought")
            or prev_review.get("original_thought")
            or review_data.get("initial_thought")
            or review_data.get("original_thought")
            or ""
        )
        first_window = (
            prev_review.get("initial_observation_window")
            or prev_review.get("observation_window")
            or review_data.get("initial_observation_window")
            or review_data.get("observation_window")
            or ""
        )

        # 若原先已有复盘内容，且本次更新发生实质修改，保留历史修订版本
        prev_thought = prev_review.get("original_thought") or prev_review.get("initial_thought", "")
        prev_outcome = prev_review.get("actual_outcome", "")
        new_thought = review_data.get("original_thought") or review_data.get("initial_thought", "")
        new_outcome = review_data.get("actual_outcome", "")

        total_rev_count = prev_review.get("total_revisions", len(revisions))
        if (prev_thought or prev_outcome) and (prev_thought != new_thought or prev_outcome != new_outcome):
            snapshot = {
                "revised_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "previous_thought": prev_thought,
                "previous_outcome": prev_outcome,
                "previous_basis": prev_review.get("realistic_basis", ""),
                "previous_tags": prev_review.get("review_tags", [])
            }
            revisions.append(snapshot)
            total_rev_count += 1

        # 保护修订历史与最初不可磨灭预期
        updated_review = dict(review_data)
        updated_review["initial_thought"] = first_thought
        updated_review["original_thought"] = new_thought or first_thought
        if first_window:
            updated_review["initial_observation_window"] = first_window
        updated_review["total_revisions"] = total_rev_count
        updated_review["revisions"] = revisions[-30:] # 保留最多30次修订轨迹

        return self.update_record(rec_id, {"review_data": updated_review})

    def get_review_statistics(self) -> Dict[str, Any]:
        """
        获取记录与复盘统计：
        仅统计客观条目数、待复盘条目数与用户自评标签分布，绝不进行玄学准确率评估。
        """
        records, total = self.list_records(limit=5000)
        pending_count = 0
        reviewed_count = 0
        type_dist: Dict[str, int] = {}
        tag_dist: Dict[str, int] = {}

        for r in records:
            rtype = r.get("record_type", "unknown")
            type_dist[rtype] = type_dist.get(rtype, 0) + 1

            rev = r.get("review_data") or {}
            outcome = (rev.get("actual_outcome") or "").strip()
            if outcome:
                reviewed_count += 1
            else:
                pending_count += 1

            tags = rev.get("review_tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            for t in tags:
                tag_dist[t] = tag_dist.get(t, 0) + 1

        return {
            "total_records": total,
            "reviewed_count": reviewed_count,
            "pending_count": pending_count,
            "type_distribution": type_dist,
            "tag_distribution": tag_dist
        }

    def delete_record(self, rec_id: str, permanent: bool = False) -> bool:
        """删除记录。默认软删除 (is_deleted=1) 便于同步墓碑传播；permanent=True 为物理硬删除"""
        with self.get_connection() as conn:
            if permanent:
                cursor = conn.execute("DELETE FROM records WHERE id = ?;", (rec_id,))
            else:
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                cursor = conn.execute(
                    "UPDATE records SET is_deleted = 1, updated_at = ?, sync_version = sync_version + 1 WHERE id = ?;",
                    (now_str, rec_id)
                )
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_records(self, permanent: bool = True):
        """用户在设置页主动选择“一键清除所有本地手记与历史”"""
        with self.get_connection() as conn:
            if permanent:
                conn.execute("DELETE FROM records;")
            else:
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                conn.execute("UPDATE records SET is_deleted = 1, updated_at = ?;", (now_str,))
            conn.commit()

    def list_records(
        self,
        record_type: Optional[str] = None,
        tag: Optional[str] = None,
        query: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        条件筛选与中文全文关键词检索。
        支持在标题、主题、标签、复盘手记中跨字段模糊匹配。
        """
        conditions = []
        params = []

        if not include_deleted:
            conditions.append("is_deleted = 0")

        if record_type:
            conditions.append("record_type = ?")
            params.append(record_type)

        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")

        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

        if query and query.strip():
            # 中文关键词跨字段检索
            keywords = [kw.strip() for kw in query.replace("，", " ").replace("、", " ").split() if kw.strip()]
            sub_conds = []
            for kw in keywords:
                sub_conds.append(
                    "(title LIKE ? OR topic LIKE ? OR tags LIKE ? OR review_data_json LIKE ? OR calculation_result_json LIKE ?)"
                )
                kw_pattern = f"%{kw}%"
                params.extend([kw_pattern, kw_pattern, kw_pattern, kw_pattern, kw_pattern])
            if sub_conds:
                conditions.append(f"({' AND '.join(sub_conds)})")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self.get_connection() as conn:
            # 统计总数
            count_cursor = conn.cursor()
            count_cursor.execute(f"SELECT COUNT(*) FROM records {where_clause};", params)
            total = count_cursor.fetchone()[0]

            # 获取分页结果
            list_params = list(params) + [limit, offset]
            list_cursor = conn.cursor()
            list_cursor.execute(
                f"SELECT * FROM records {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                list_params
            )
            rows = list_cursor.fetchall()
            records = [self._row_to_dict(r) for r in rows]

        return records, total

    # ----------------------------------------------------
    # 单条与批量导出
    # ----------------------------------------------------

    def export_records_as_markdown(self, ids: Optional[List[str]] = None) -> str:
        """导出记录为 Markdown 格式，便于外部笔记软件（Obsidian、Notion）阅读"""
        records, _ = self.list_records(limit=1000)
        if ids:
            records = [r for r in records if r["id"] in ids]

        lines = [
            "# 玄鉴·书房 ｜ 本地记录与复盘手记导出",
            f"> 导出时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ｜ 记录数量：{len(records)} 篇",
            "",
            "---",
            ""
        ]

        for i, rec in enumerate(records, 1):
            lines.append(f"## {i}. {rec['title']}")
            lines.append(f"- **类型**：`{rec['record_type']}` ｜ **记录 ID**：`{rec['id']}`")
            lines.append(f"- **创建时间**：{rec['created_at']} ｜ **标签**：{rec['tags'] or '无'}")
            if rec.get("topic"):
                lines.append(f"- **问事主题**：{rec['topic']}")
            lines.append("")

            # 象数计算结果
            calc = rec.get("calculation_result") or {}
            if calc:
                lines.append("### 【当时象数推算】")
                lines.append(f"- **卦象**：【{(calc.get('original_hexagram') or calc.get('primary_hexagram', {})).get('name', '')}】之【{calc.get('transformed_hexagram', {}).get('name', '')}】")
                if calc.get("moving_lines"):
                    lines.append(f"- **动爻**：第 {calc.get('moving_lines')} 爻")
                lines.append("")

            # Frozen local reading and throw trace belong to the original calculation.
            reading = calc.get("reading") or {}
            if reading:
                lines.append("### 【当时的解读】")
                lines.extend(str(reading.get(k, "")) for k in ("headline", "summary", "context", "action"))
                lines.append(f"- 起卦时间：{calc.get('cast_at', '')}")
                lines.append(f"- 爻值（自下而上）：{calc.get('input_lines', [])}")
                for n, coins in enumerate(calc.get("coin_flips", []), 1):
                    lines.append(f"- 第{n}次：{' + '.join(map(str, coins))} = {sum(coins)}")
                lines.append("")

            # 事后复盘
            review = rec.get("review_data") or {}
            if review:
                lines.append("### 【事后复盘思考】")
                if review.get("original_thought"):
                    lines.append(f"- **原先怎么想**：{review['original_thought']}")
                if review.get("actual_outcome"):
                    lines.append(f"- **后来发生什么**：{review['actual_outcome']}")
                if review.get("missing_evidence"):
                    lines.append(f"- **缺什么证据**：{review['missing_evidence']}")
                if review.get("notes"):
                    lines.append(f"- **复盘总结**：{review['notes']}")
                lines.append("")

            # AI 研读记录（如有，明确分层）
            ai = rec.get("ai_interpret") or {}
            if ai and ai.get("suggestion"):
                lines.append("### 【AI 研读记录 (不可覆盖程序卦象)】")
                lines.append(f"{ai.get('suggestion')}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将 sqlite3.Row 转换为 Python 字典，安全解析 JSON 字段"""
        d = dict(row)
        for json_field in ["params_json", "calculation_result_json", "ai_interpret_json", "review_data_json"]:
            field_name = json_field.replace("_json", "")
            raw = d.pop(json_field, None)
            try:
                d[field_name] = json.loads(raw) if raw else {}
            except Exception:
                d[field_name] = {}
        return d


# 模块全局单例
_storage_instance: Optional[StorageManager] = None


def get_storage(db_path: Optional[str] = None) -> StorageManager:
    global _storage_instance
    if _storage_instance is None or (db_path and _storage_instance.db_path != db_path):
        _storage_instance = StorageManager(db_path)
    return _storage_instance

# 兼容别名
XuanJianStorage = StorageManager
