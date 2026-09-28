#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuanjian/runtime_env.py - 客户运行时环境、私有依赖定位与数据目录管理

为 macOS 客户独立打包（.app Bundle）、本地源码开发与隔离测试提供统一路径决议：
1. 区分用户数据目录 (~/Library/Application Support/XuanJian) 与应用资源目录；
2. 优先检索随应用私有携带的 Node arm64 runtime 与 calc_worker.bundle.js；
3. 支持严格脱敏的系统诊断信息导出；
4. 保证源码开发环境、CI 测试与独立分发包的向后兼容性。
"""

import os
import sys
import shutil
import platform
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir() -> str:
    """
    获取用户数据持久化目录。
    1. 显式环境变量 XUANJIAN_DATA_DIR (测试或自定义指定最高优先级)；
    2. macOS 客户打包模式 (XUANJIAN_APP_MODE=1 或 PyInstaller 运行态或处于 .app 内部):
       统一使用 ~/Library/Application Support/XuanJian；
    3. 源码开发默认: 项目根目录下的 data/ 目录。
    """
    env_dir = os.environ.get("XUANJIAN_DATA_DIR")
    if env_dir:
        return os.path.abspath(env_dir)

    is_app_mode = (
        os.environ.get("XUANJIAN_APP_MODE") == "1"
        or getattr(sys, "frozen", False)
        or ".app/Contents/" in os.path.abspath(__file__)
    )

    if is_app_mode:
        app_support = os.path.expanduser("~/Library/Application Support/XuanJian")
        return os.path.abspath(app_support)

    return os.path.join(PROJECT_ROOT, "data")


def get_default_db_path() -> str:
    """获取默认 SQLite 数据库绝对路径"""
    env_db = os.environ.get("XUANJIAN_DB_PATH")
    if env_db:
        return os.path.abspath(env_db)
    return os.path.join(get_data_dir(), "xuanjian.db")


def get_node_bin_path() -> str:
    """
    获取 Node 可执行文件路径。
    优先应用私有打包的 Node runtime，杜绝依赖客户全局环境。
    """
    # 1. 显式环境变量 (强制生效，便于测试与定制)
    env_node = os.environ.get("XUANJIAN_NODE_PATH")
    if env_node:
        return os.path.abspath(env_node)

    # 2. PyInstaller 解压目录
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = os.path.join(meipass, "node", "bin", "node")
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return os.path.abspath(p)

    # 3. macOS .app Bundle Resources 目录探测
    candidates = [
        # Resources/node/bin/node (从 executable 探测：位于 Contents/Resources/server 或 Contents/MacOS)
        os.path.join(os.path.dirname(sys.executable), "..", "node", "bin", "node"),
        os.path.join(os.path.dirname(sys.executable), "..", "Resources", "node", "bin", "node"),
        os.path.join(os.path.dirname(sys.executable), "node", "bin", "node"),
        # Resources/node/bin/node (从 __file__ 探测)
        os.path.join(PROJECT_ROOT, "runtime", "node", "bin", "node"),
        os.path.join(PROJECT_ROOT, "node", "bin", "node"),
        os.path.join(os.path.dirname(PROJECT_ROOT), "Resources", "node", "bin", "node"),
    ]

    for cand in candidates:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return os.path.realpath(cand)

    # 4. 系统环境 fallback
    sys_node = shutil.which("node")
    if sys_node:
        return sys_node

    return "node"


def is_bundled_node() -> bool:
    """判断当前使用的是否为私有打包的 Node"""
    node_path = get_node_bin_path()
    if node_path == "node":
        return False
    # 判断是否在 .app 或 runtime 目录内
    return (".app" in node_path or "runtime" in node_path or getattr(sys, "frozen", False))


def get_worker_bundle_path() -> str:
    """获取紫微/奇门计算核心 bundle 脚本路径"""
    env_worker = os.environ.get("XUANJIAN_WORKER_PATH")
    if env_worker and os.path.isfile(env_worker):
        return os.path.abspath(env_worker)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = os.path.join(meipass, "scripts", "calc_worker.bundle.js")
        if os.path.isfile(p):
            return os.path.abspath(p)

    candidates = [
        os.path.join(os.path.dirname(sys.executable), "..", "scripts", "calc_worker.bundle.js"),
        os.path.join(os.path.dirname(sys.executable), "..", "Resources", "scripts", "calc_worker.bundle.js"),
        os.path.join(PROJECT_ROOT, "scripts", "calc_worker.bundle.js"),
        os.path.join(os.path.dirname(PROJECT_ROOT), "Resources", "scripts", "calc_worker.bundle.js"),
    ]

    for cand in candidates:
        if os.path.isfile(cand):
            return os.path.realpath(cand)

    return os.path.join(PROJECT_ROOT, "scripts", "calc_worker.bundle.js")


def get_frontend_dist_dir() -> str:
    """获取前端静态产物目录路径"""
    env_dist = os.environ.get("XUANJIAN_FRONTEND_DIST")
    if env_dist and os.path.isdir(env_dist):
        return os.path.abspath(env_dist)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = os.path.join(meipass, "frontend", "dist")
        if os.path.isdir(p):
            return os.path.abspath(p)

    candidates = [
        os.path.join(os.path.dirname(sys.executable), "..", "frontend", "dist"),
        os.path.join(os.path.dirname(sys.executable), "..", "Resources", "frontend", "dist"),
        os.path.join(PROJECT_ROOT, "frontend", "dist"),
        os.path.join(os.path.dirname(PROJECT_ROOT), "Resources", "frontend", "dist"),
    ]

    for cand in candidates:
        if os.path.isdir(cand):
            return os.path.realpath(cand)

    return os.path.join(PROJECT_ROOT, "frontend", "dist")


def get_desensitized_diagnostics(extra_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    生成严格脱敏的诊断信息。
    绝对排除：真实生辰、手记文本、数据库明细、任何 API 密钥或密码。
    保留：操作系统架构、Python/Node 版本、引擎加载状态、数据目录形态。
    """
    data_dir = get_data_dir()
    home_dir = os.path.expanduser("~")
    safe_data_dir = data_dir.replace(home_dir, "~") if home_dir in data_dir else data_dir

    node_bin = get_node_bin_path()
    safe_node_bin = node_bin.replace(home_dir, "~") if home_dir in node_bin else node_bin

    node_available = False
    node_version = "unavailable"
    if node_bin != "node" and os.path.isfile(node_bin) and os.access(node_bin, os.X_OK):
        try:
            import subprocess
            out = subprocess.check_output([node_bin, "-v"], text=True, timeout=2.0).strip()
            node_version = out
            node_available = True
        except Exception:
            node_available = False
    elif shutil.which("node"):
        try:
            import subprocess
            out = subprocess.check_output(["node", "-v"], text=True, timeout=2.0).strip()
            node_version = out
            node_available = True
        except Exception:
            node_available = False

    diag: Dict[str, Any] = {
        "app_name": "玄鉴·书房 (XuanJian Studio)",
        "app_version": "3.0.1",
        "release_edition": "macOS Apple Silicon 客户试用版",
        "running_mode": "纯本地·离线优先·免API",
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "mac_ver": platform.mac_ver()[0] if hasattr(platform, "mac_ver") else "unknown",
            "python_version": platform.python_version()
        },
        "runtimes": {
            "bundled_python": bool(getattr(sys, "frozen", False) or "xuanjian_server" in sys.executable),
            "node_runtime_available": node_available,
            "node_version": node_version,
            "is_bundled_node": is_bundled_node(),
            "node_path_masked": safe_node_bin
        },
        "engines": {
            "zhouyi": "内置确定性六爻象数引擎 (互错综卦/变爻图)",
            "bazi": "lunar-python v1.4.8 (高精度节气立春分秒)",
            "ziwei": "iztro v2.6.1 (私有Node Worker确定性排盘)",
            "qimen": "bigfishmarquis-qimen v1.0.0 (时家转盘拆补九宫)",
            "builtin_reader": "免API确定性传统研读与知止反思引擎",
            "daodejing": "传世八十一章全息研读与知止防线"
        },
        "storage": {
            "data_directory": safe_data_dir,
            "db_exists": os.path.isfile(get_default_db_path()),
            "storage_engine": "SQLite 3 (WAL mode)"
        }
    }

    if extra_info:
        # 仅合并安全允许的字段
        for k in ("records_count", "db_integrity", "port", "uptime_seconds"):
            if k in extra_info:
                diag[k] = extra_info[k]

    return diag
