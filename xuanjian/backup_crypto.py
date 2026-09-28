#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/backup_crypto.py - 认证加密备份与恢复引擎 (F07)

采用现代密码学标准：
1. 密钥派生：PBKDF2-HMAC-SHA256，100,000 次安全迭代，随机 16 字节 Salt；
2. 认证加密：AES-256-GCM (Galois/Counter Mode) 带关联数据 (AAD) 认证，随机 12 字节 Nonce；
3. 防篡改：任何单 bit 修改或错误密码均会触发 AEAD 认证标签校验失败，杜绝脏数据注入；
4. 数据库安全恢复：恢复前自动保留 .pre_restore.bak 快照，经 PRAGMA integrity_check 校验后原子落盘。
"""

import os
import json
import sqlite3
import hashlib
import shutil
import tempfile
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

MAGIC_ENC_HEADER = b"XUANJIAN_ENC_V1\n"
MAGIC_RAW_HEADER = b"XUANJIAN_RAW_V1\n"
SALT_LEN = 16
NONCE_LEN = 12
PBKDF2_ITERATIONS = 100000

class CryptoAuthError(Exception):
    """解密认证失败或备份文件损坏"""
    pass

def derive_key(passphrase: str, salt: bytes) -> bytes:
    """基于用户密码与 Salt 派生 256 位对称密钥"""
    if not passphrase:
        raise ValueError("备份密码不可为空")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS
    )
    return kdf.derive(passphrase.encode("utf-8"))

def encrypt_bytes(data: bytes, passphrase: str) -> bytes:
    """
    使用 AES-256-GCM 对二进制字节进行认证加密
    包结构：MAGIC_ENC_HEADER + Salt(16) + Nonce(12) + Ciphertext(with 16-byte tag)
    """
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    # 将 MAGIC HEADER 作为关联数据 (AAD) 绑定，防止头部替换攻击
    ciphertext = aesgcm.encrypt(nonce, data, MAGIC_ENC_HEADER)
    return MAGIC_ENC_HEADER + salt + nonce + ciphertext

def decrypt_bytes(encrypted_package: bytes, passphrase: str) -> bytes:
    """
    解密经 AES-256-GCM 加密的备份包
    """
    if not encrypted_package.startswith(MAGIC_ENC_HEADER):
        raise CryptoAuthError("文件格式错误：非玄鉴标准加密备份文件。")

    header_len = len(MAGIC_ENC_HEADER)
    if len(encrypted_package) < header_len + SALT_LEN + NONCE_LEN + 16:
        raise CryptoAuthError("备份文件已损坏：长度不足。")

    salt = encrypted_package[header_len : header_len + SALT_LEN]
    nonce = encrypted_package[header_len + SALT_LEN : header_len + SALT_LEN + NONCE_LEN]
    ciphertext = encrypted_package[header_len + SALT_LEN + NONCE_LEN :]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, MAGIC_ENC_HEADER)
        return plaintext
    except InvalidTag:
        raise CryptoAuthError("备份解密认证失败：密码错误或备份文件已被恶意篡改/损坏。")

def create_database_backup(db_path: str, passphrase: Optional[str] = None) -> bytes:
    """
    生成数据库导出备份包：
    若提供密码，则生成 AES-256-GCM 认证加密包；若无密码，则生成标准明文包。
    """
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    # 使用 SQLite VACUUM INTO 或复制生成一致性快照
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # 通过 SQLite 连接进行安全备份，确保 WAL 缓冲完整刷写
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(tmp_path)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()

        with open(tmp_path, "rb") as f:
            raw_db_bytes = f.read()

        checksum = hashlib.sha256(raw_db_bytes).hexdigest()

        # 构建统一信封
        envelope = {
            "version": "2.1.0",
            "format": "sqlite3_snapshot",
            "checksum_sha256": checksum,
            "raw_size": len(raw_db_bytes)
        }
        envelope_json = json.dumps(envelope).encode("utf-8")
        payload = len(envelope_json).to_bytes(4, byteorder="big") + envelope_json + raw_db_bytes

        if passphrase:
            return encrypt_bytes(payload, passphrase)
        else:
            return MAGIC_RAW_HEADER + payload
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def restore_database_backup(
    backup_bytes: bytes,
    target_db_path: str,
    passphrase: Optional[str] = None
) -> Dict[str, Any]:
    """
    安全恢复数据库备份：
    1. 解密（如有密码）并校验信封；
    2. 校验 SHA-256 数据一致性；
    3. PRAGMA integrity_check 物理完整性自检；
    4. 自动保留 .pre_restore.bak，原子替换。
    """
    if backup_bytes.startswith(MAGIC_ENC_HEADER):
        if not passphrase:
            raise CryptoAuthError("该备份文件已加密，请提供解密密码。")
        payload = decrypt_bytes(backup_bytes, passphrase)
    elif backup_bytes.startswith(MAGIC_RAW_HEADER):
        payload = backup_bytes[len(MAGIC_RAW_HEADER):]
    else:
        raise ValueError("无效的备份文件头标识。")

    if len(payload) < 4:
        raise ValueError("备份数据包结构不完整。")

    env_len = int.from_bytes(payload[:4], byteorder="big")
    envelope_raw = payload[4 : 4 + env_len]
    raw_db_bytes = payload[4 + env_len :]

    envelope = json.loads(envelope_raw.decode("utf-8"))
    actual_hash = hashlib.sha256(raw_db_bytes).hexdigest()

    if actual_hash != envelope.get("checksum_sha256"):
        raise ValueError("数据校验和不匹配，备份文件可能已受损。")

    # 写入临时文件并做完整性校验
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_restore_path = tmp.name
        tmp.write(raw_db_bytes)

    try:
        check_conn = sqlite3.connect(tmp_restore_path)
        cur = check_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_res = cur.fetchone()[0]
        if check_res != "ok":
            raise ValueError(f"SQLite 数据库完整性检查失败: {check_res}")

        # 获取记录数
        try:
            cur.execute("SELECT count(*) FROM records WHERE is_deleted = 0;")
            records_count = cur.fetchone()[0]
        except Exception:
            records_count = 0
        check_conn.close()

        # 安全防线：备份现有目标数据库
        os.makedirs(os.path.dirname(os.path.abspath(target_db_path)), exist_ok=True)
        if os.path.exists(target_db_path):
            pre_bak = f"{target_db_path}.pre_restore.bak"
            shutil.copy2(target_db_path, pre_bak)

        # 原子落盘
        shutil.move(tmp_restore_path, target_db_path)

        # 清理 wal 与 shm 临时文件避免冲突
        for extra in (f"{target_db_path}-wal", f"{target_db_path}-shm"):
            if os.path.exists(extra):
                os.remove(extra)

        return {
            "success": True,
            "restored_records_count": records_count,
            "checksum": actual_hash,
            "target_path": target_db_path
        }
    finally:
        if os.path.exists(tmp_restore_path):
            os.remove(tmp_restore_path)
