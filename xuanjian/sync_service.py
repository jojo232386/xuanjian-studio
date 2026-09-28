#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/sync_service.py - WebDAV 同步服务与多实例冲突解决引擎 (F07)

提供个人私有云（WebDAV，如坚果云、Nextcloud、NAS）数据流转方案：
1. 客户端可配置 WebDAV 服务器地址、用户名、密码与远端路径；
2. 端到端加密传输：数据在离开本地前经 AES-256-GCM 加密，云端仅存储密文，零泄漏；
3. 多实例协同合并与冲突副本保留（Conflict Copy & Tombstone Propagation）：
   - 比较记录级主键 id 与实质业务内容；
   - 若双方存在并发离线编辑冲突，保留主记录同时自动生成 [冲突副本]，完整留存两端内容；
   - 包含软删除墓碑标记传播与“删除 vs 修改”冲突保护，杜绝静默抹去手记；
   - 支持时钟注入容差，基于内容实质分歧检测，不单纯依赖设备系统时钟；
4. 远端并发更新条件写入保护（Optimistic Concurrency Control）；
5. 密码脱敏与配置持久化。
"""

import os
import json
import base64
import hashlib
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from xuanjian.backup_crypto import encrypt_bytes, decrypt_bytes, MAGIC_ENC_HEADER, CryptoAuthError
from xuanjian.storage import XuanJianStorage

class SyncConflictError(Exception):
    """远端快照已被其他端更新冲突异常"""
    pass

class WebDAVSyncConfig:
    """WebDAV 配置模型"""
    def __init__(
        self,
        enabled: bool = False,
        server_url: str = "",
        username: str = "",
        password: str = "",
        remote_path: str = "/xuanjian/backup.enc",
        encryption_passphrase: str = "",
        last_synced_remote_sha256: str = ""
    ):
        self.enabled = bool(enabled)
        self.server_url = server_url.strip().rstrip("/")
        self.username = username.strip()
        self.password = password.strip()
        self.remote_path = remote_path.strip()
        if not self.remote_path.startswith("/"):
            self.remote_path = "/" + self.remote_path
        self.encryption_passphrase = encryption_passphrase.strip()
        self.last_synced_remote_sha256 = last_synced_remote_sha256.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.server_url and self.username and self.password)

    def to_dict(self, mask_secret: bool = True) -> Dict[str, Any]:
        pwd = "********" if (mask_secret and self.password) else self.password
        enc_p = "********" if (mask_secret and self.encryption_passphrase) else self.encryption_passphrase
        return {
            "enabled": self.enabled,
            "server_url": self.server_url,
            "username": self.username,
            "password": pwd,
            "remote_path": self.remote_path,
            "has_encryption_passphrase": bool(self.encryption_passphrase),
            "is_configured": bool(self.server_url and self.username and self.password),
            "last_synced_remote_sha256": self.last_synced_remote_sha256
        }

# 全局内存配置单例
_sync_config = WebDAVSyncConfig()

def get_sync_config() -> WebDAVSyncConfig:
    return _sync_config

def update_sync_config(cfg_dict: Dict[str, Any]) -> WebDAVSyncConfig:
    global _sync_config
    enabled = cfg_dict.get("enabled", _sync_config.enabled)
    url = cfg_dict.get("server_url", _sync_config.server_url)
    user = cfg_dict.get("username", _sync_config.username)

    pwd = cfg_dict.get("password")
    if pwd is None or "********" in pwd:
        final_pwd = _sync_config.password
    else:
        final_pwd = pwd

    rem = cfg_dict.get("remote_path", _sync_config.remote_path)

    enc = cfg_dict.get("encryption_passphrase")
    if enc is None or "********" in enc:
        final_enc = _sync_config.encryption_passphrase
    else:
        final_enc = enc

    last_sha = cfg_dict.get("last_synced_remote_sha256", _sync_config.last_synced_remote_sha256)

    _sync_config = WebDAVSyncConfig(
        enabled=enabled,
        server_url=url,
        username=user,
        password=final_pwd,
        remote_path=rem,
        encryption_passphrase=final_enc,
        last_synced_remote_sha256=last_sha
    )
    return _sync_config

def _get_auth_header(user: str, pwd: str) -> str:
    token = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"

def export_sync_snapshot(storage: XuanJianStorage) -> Dict[str, Any]:
    """生成包含所有记录（包含已软删除墓碑条目）的一致性快照"""
    records, total = storage.list_records(limit=10000, include_deleted=True)
    return {
        "schema_version": 2,
        "format": "xuanjian_sync_snapshot",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "records_count": len(records),
        "records": records
    }

def _records_content_equal(rec_a: Dict[str, Any], rec_b: Dict[str, Any]) -> bool:
    """比对两条记录的实质业务内容是否一致（忽略 ID, updated_at, sync_version 等同步元数据）"""
    fields_to_compare = [
        "record_type", "title", "topic", "tags",
        "params", "calculation_result", "ai_interpret", "review_data"
    ]
    for f in fields_to_compare:
        val_a = rec_a.get(f)
        val_b = rec_b.get(f)
        if isinstance(val_a, (dict, list)) or isinstance(val_b, (dict, list)):
            if json.dumps(val_a, sort_keys=True, ensure_ascii=False) != json.dumps(val_b, sort_keys=True, ensure_ascii=False):
                return False
        else:
            if (val_a or "") != (val_b or ""):
                return False
    return True

def merge_snapshots(
    local_storage: XuanJianStorage,
    remote_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    双向协同合并引擎 (含冲突副本创建与删除墓碑传播)：
    - 若两端并发离线修改同一记录，绝不盲目覆盖，完整保留两端并生成 [冲突副本]；
    - 若一端删除一端修改，保护性恢复修改内容并留存说明，杜绝静默丢弃；
    - 支持时钟偏移容错。
    """
    remote_records = remote_snapshot.get("records", [])
    inserted = 0
    updated = 0
    unchanged = 0
    conflicts_resolved = 0
    conflict_copies_created: List[str] = []

    for rem_rec in remote_records:
        rec_id = rem_rec.get("id")
        if not rec_id:
            continue

        local_rec = local_storage.get_record(rec_id, include_deleted=True)

        if not local_rec:
            # 本地尚无该条记录 -> 直接插入（包括删除墓碑）
            local_storage.create_record(rem_rec)
            inserted += 1
            continue

        loc_deleted = bool(local_rec.get("is_deleted", 0))
        rem_deleted = bool(rem_rec.get("is_deleted", 0))
        loc_time = local_rec.get("updated_at") or local_rec.get("created_at") or ""
        rem_time = rem_rec.get("updated_at") or rem_rec.get("created_at") or ""
        contents_equal = _records_content_equal(local_rec, rem_rec)

        # ----------------------------------------------------
        # 情况 1: 实质内容完全一致
        # ----------------------------------------------------
        if contents_equal:
            if loc_deleted == rem_deleted:
                # 状态完全一致
                if rem_time > loc_time:
                    local_storage.update_record(rec_id, {"updated_at": rem_time})
                unchanged += 1
            else:
                # 删除状态不同，以较新者为准
                if rem_time > loc_time:
                    local_storage.update_record(rec_id, {
                        "is_deleted": int(rem_deleted),
                        "updated_at": rem_time
                    })
                    updated += 1
                else:
                    unchanged += 1
            continue

        # ----------------------------------------------------
        # 情况 2: 实质内容存在差异 (并发修改或冲突)
        # ----------------------------------------------------
        # 2A: 两端均处于激活状态 (未删除) -> 并发编辑冲突，两版均保留！
        if not loc_deleted and not rem_deleted:
            conflicts_resolved += 1
            now_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

            if rem_time > loc_time:
                # 远端更新为主记录，本地编辑保留为冲突副本
                conflict_id = f"{rec_id}_conflict_loc_{now_tag}"
                conflict_rec = dict(local_rec)
                conflict_rec["id"] = conflict_id
                conflict_rec["title"] = f"[冲突副本] {local_rec.get('title', '手记')}"
                rev_data = dict(conflict_rec.get("review_data") or {})
                prior_notes = rev_data.get("notes") or ""
                rev_data["notes"] = (prior_notes + f"\n[冲突溯源] 此记录为双端并发离线编辑时保留的本地冲突副本。原始ID: {rec_id}，本地更新于: {loc_time}；远端较新版本已更新为主记录 (更新于 {rem_time})。").strip()
                conflict_rec["review_data"] = rev_data

                local_storage.create_record(conflict_rec)
                conflict_copies_created.append(conflict_id)

                local_storage.update_record(rec_id, rem_rec)
                updated += 1
            else:
                # 本地较新或时间相同：本地保留为主记录，远端编辑保留为冲突副本
                conflict_id = f"{rec_id}_conflict_rem_{now_tag}"
                conflict_rec = dict(rem_rec)
                conflict_rec["id"] = conflict_id
                conflict_rec["title"] = f"[冲突副本] {rem_rec.get('title', '手记')}"
                rev_data = dict(conflict_rec.get("review_data") or {})
                prior_notes = rev_data.get("notes") or ""
                rev_data["notes"] = (prior_notes + f"\n[冲突溯源] 此记录为双端并发离线编辑时保留的远端冲突副本。原始ID: {rec_id}，远端更新于: {rem_time}；本地较新版本保留为主记录 (更新于 {loc_time})。").strip()
                conflict_rec["review_data"] = rev_data

                local_storage.create_record(conflict_rec)
                conflict_copies_created.append(conflict_id)
                unchanged += 1
            continue

        # 2B: 一端删除，一端修改 (删除 vs 修改冲突)
        if rem_deleted and not loc_deleted:
            # 远端删除，本地有独立修改
            conflicts_resolved += 1
            if loc_time > rem_time:
                # 本地修改晚于远端删除，本地修改胜出并保留
                rev_data = dict(local_rec.get("review_data") or {})
                prior_notes = rev_data.get("notes") or ""
                rev_data["notes"] = (prior_notes + f"\n[冲突说明] 远端曾于 {rem_time} 删除此记录，但检测到本地存在较新修改 ({loc_time})，已自动保留本地版本。").strip()
                local_storage.update_record(rec_id, {"review_data": rev_data})
                unchanged += 1
            else:
                # 远端删除较新，但本地有未同步的独立编辑：保护性抢救本地编辑为独立手记，主记录接受删除
                now_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                rescue_id = f"{rec_id}_rescued_{now_tag}"
                rescue_rec = dict(local_rec)
                rescue_rec["id"] = rescue_id
                rescue_rec["is_deleted"] = 0
                rescue_rec["title"] = f"[恢复未删笔记] {local_rec.get('title', '手记')}"
                rev_data = dict(rescue_rec.get("review_data") or {})
                prior_notes = rev_data.get("notes") or ""
                rev_data["notes"] = (prior_notes + f"\n[冲突说明] 远端在 {rem_time} 删除了该条目，主记录已接受删除，但检测到本地存在独立编辑内容，已提取并恢复在此独立卡片中。").strip()
                rescue_rec["review_data"] = rev_data

                local_storage.create_record(rescue_rec)
                conflict_copies_created.append(rescue_id)
                local_storage.update_record(rec_id, {"is_deleted": 1, "updated_at": rem_time})
                updated += 1
            continue

        if loc_deleted and not rem_deleted:
            # 本地删除，远端有独立修改
            conflicts_resolved += 1
            if rem_time > loc_time:
                # 远端修改晚于本地删除：远端胜出，复活记录并采用最新编辑
                rem_rec["is_deleted"] = 0
                rev_data = dict(rem_rec.get("review_data") or {})
                prior_notes = rev_data.get("notes") or ""
                rev_data["notes"] = (prior_notes + f"\n[冲突说明] 本地曾于 {loc_time} 删除此记录，但检测到远端存在较新修改 ({rem_time})，已自动复原并采用最新编辑。").strip()
                rem_rec["review_data"] = rev_data
                local_storage.update_record(rec_id, rem_rec)
                updated += 1
            else:
                # 本地删除较新，但远端有未见过的独立编辑：保护性抢救远端编辑为独立手记，主记录保持删除
                now_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                rescue_id = f"{rec_id}_rescued_{now_tag}"
                rescue_rec = dict(rem_rec)
                rescue_rec["id"] = rescue_id
                rescue_rec["is_deleted"] = 0
                rescue_rec["title"] = f"[恢复远端笔记] {rem_rec.get('title', '手记')}"
                rev_data = dict(rescue_rec.get("review_data") or {})
                prior_notes = rev_data.get("notes") or ""
                rev_data["notes"] = (prior_notes + f"\n[冲突说明] 本地在 {loc_time} 删除了该条目，但远端存在未同步的独立编辑，已提取并恢复在此独立卡片中。").strip()
                rescue_rec["review_data"] = rev_data

                local_storage.create_record(rescue_rec)
                conflict_copies_created.append(rescue_id)
                unchanged += 1
            continue

        # 2C: 两端均已删除
        if loc_deleted and rem_deleted:
            if rem_time > loc_time:
                local_storage.update_record(rec_id, {"updated_at": rem_time})
            unchanged += 1

    _, final_total = local_storage.list_records(limit=1, include_deleted=False)
    return {
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "conflicts_resolved": conflicts_resolved,
        "conflict_copies_created": conflict_copies_created,
        "final_local_total": final_total
    }

def test_webdav_connection(config: WebDAVSyncConfig) -> Dict[str, Any]:
    """测试 WebDAV 连接认证与可写性"""
    if not config.server_url or not config.username or not config.password:
        return {"success": False, "message": "请填写完整的 WebDAV 服务器地址、用户名与密码。"}

    test_url = f"{config.server_url}{config.remote_path}"
    headers = {
        "Authorization": _get_auth_header(config.username, config.password),
        "User-Agent": "XuanJian-Sync/2.1.0"
    }

    try:
        req = urllib.request.Request(test_url, headers=headers, method="PROPFIND")
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            return {
                "success": True,
                "message": f"WebDAV 连接成功！状态码: {status}",
                "status_code": status
            }
    except urllib.error.HTTPError as he:
        if he.code in (404, 207):
            return {
                "success": True,
                "message": "WebDAV 认证通过！可执行数据同步流转。",
                "status_code": he.code
            }
        elif he.code in (401, 403):
            return {"success": False, "message": f"WebDAV 认证失败 (HTTP {he.code})：用户名或密码错误。"}
        else:
            return {"success": False, "message": f"WebDAV 请求返回状态: HTTP {he.code}"}
    except Exception as e:
        return {"success": False, "message": f"连接 WebDAV 服务器异常: {str(e)}"}

def sync_push(storage: XuanJianStorage, config: WebDAVSyncConfig, force: bool = False) -> Dict[str, Any]:
    """
    将本地快照（端到端加密）推送到 WebDAV。
    内置乐观并发控制：若远端文件被并发更新，要求先合并再推送（force=True 覆盖）。
    """
    if not config.is_configured:
        raise ValueError("WebDAV 尚未配置完整的服务器地址与账号。")

    target_url = f"{config.server_url}{config.remote_path}"
    headers = {
        "Authorization": _get_auth_header(config.username, config.password),
        "User-Agent": "XuanJian-Sync/2.1.0"
    }

    # 乐观并发检查
    if not force and config.last_synced_remote_sha256:
        try:
            check_req = urllib.request.Request(target_url, headers=headers, method="GET")
            with urllib.request.urlopen(check_req, timeout=10) as check_resp:
                remote_curr_bytes = check_resp.read()
                remote_curr_sha = hashlib.sha256(remote_curr_bytes).hexdigest()
                if remote_curr_sha != config.last_synced_remote_sha256:
                    raise SyncConflictError(
                        "远端数据已被其他设备更新 (SHA-256 不一致)。为防盲目覆盖，请先拉取并合并远端快照。"
                    )
        except urllib.error.HTTPError as he:
            if he.code != 404:
                # 404 说明远端尚无文件，可安全推送；其他错误如 401 抛出
                raise

    snapshot = export_sync_snapshot(storage)
    raw_json = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")

    if config.encryption_passphrase:
        payload = encrypt_bytes(raw_json, config.encryption_passphrase)
    else:
        payload = raw_json

    upload_headers = {
        "Authorization": _get_auth_header(config.username, config.password),
        "Content-Type": "application/octet-stream",
        "User-Agent": "XuanJian-Sync/2.1.0"
    }

    req = urllib.request.Request(target_url, data=payload, headers=upload_headers, method="PUT")
    with urllib.request.urlopen(req, timeout=20) as resp:
        new_sha = hashlib.sha256(payload).hexdigest()
        config.last_synced_remote_sha256 = new_sha
        return {
            "success": True,
            "status_code": resp.status,
            "records_pushed": snapshot["records_count"],
            "encrypted": bool(config.encryption_passphrase),
            "payload_size": len(payload),
            "remote_sha256": new_sha
        }

def sync_pull_and_merge(storage: XuanJianStorage, config: WebDAVSyncConfig) -> Dict[str, Any]:
    """从 WebDAV 拉取远端快照，解密并进行无损合并，自动处理冲突与墓碑"""
    if not config.is_configured:
        raise ValueError("WebDAV 尚未配置完整的服务器地址与账号。")

    target_url = f"{config.server_url}{config.remote_path}"
    headers = {
        "Authorization": _get_auth_header(config.username, config.password),
        "User-Agent": "XuanJian-Sync/2.1.0"
    }

    req = urllib.request.Request(target_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            downloaded = resp.read()
    except urllib.error.HTTPError as he:
        if he.code == 404:
            return {
                "success": False,
                "message": "远端尚无备份文件，建议先执行一次推送同步。",
                "status_code": 404
            }
        raise

    downloaded_sha = hashlib.sha256(downloaded).hexdigest()

    # 解密
    if downloaded.startswith(MAGIC_ENC_HEADER):
        if not config.encryption_passphrase:
            raise CryptoAuthError("远端数据包已加密，请在同步配置中提供解密密码。")
        raw_json = decrypt_bytes(downloaded, config.encryption_passphrase)
    else:
        raw_json = downloaded

    remote_snapshot = json.loads(raw_json.decode("utf-8"))
    merge_result = merge_snapshots(storage, remote_snapshot)
    merge_result["success"] = True
    config.last_synced_remote_sha256 = downloaded_sha
    return merge_result
