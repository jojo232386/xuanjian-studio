#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/build_macos_client_app.py - 玄鉴·书房 v3.0.1 macOS Apple Silicon 客户应用组装与打包脚本

功能：
1. 编译并打包 Python 后端 arm64 独立运行体 (xuanjian_server)；
2. 搬运版本锁定、经许可证核查的 Node.js arm64 独立可执行二进制至应用私有资源库；
3. 同步前端生产包 (frontend/dist) 与计算 Worker (calc_worker.bundle.js)；
4. 生成符合 Apple 标准规范的「玄鉴·书房.app」目录结构、Info.plist、PkgInfo 与高清 AppIcon.icns；
5. 生成免终端原生启动引导脚本 (Contents/MacOS/玄鉴·书房) 与安全退出助手；
6. 收集并记录第三方组件许可证 (Python, Node, lunar-python, iztro, bigfishmarquis-qimen, cryptography)；
7. 执行适合本地试用的 ad-hoc 签名 (codesign --force --deep --sign -)。
"""

import os
import sys
import shutil
import subprocess
import json
import stat
import platform
import importlib.metadata as metadata
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
APP_NAME = "玄鉴·书房.app"
APP_DIR = os.path.join(DIST_DIR, APP_NAME)
CONTENTS_DIR = os.path.join(APP_DIR, "Contents")
MACOS_DIR = os.path.join(CONTENTS_DIR, "MacOS")
RESOURCES_DIR = os.path.join(CONTENTS_DIR, "Resources")

# Node 原生 arm64 二进制源路径
CANDIDATE_NODE_PATHS = [os.environ.get("XUANJIAN_NODE_BIN", ""), shutil.which("node") or ""]


def run_cmd(cmd, cwd=PROJECT_ROOT):
    print(f"执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"错误输出:\n{res.stderr}")
        raise RuntimeError(f"命令执行失败 ({res.returncode}): {cmd}")
    return res.stdout.strip()


def find_valid_node_bin():
    for p in CANDIDATE_NODE_PATHS:
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            p = os.path.realpath(p)
            # 校验是否为 arm64
            out = subprocess.check_output(["file", p], text=True)
            if "arm64" in out:
                return p
    raise FileNotFoundError("未找到可用的 Node.js arm64 独立二进制")


def copy_license_notices(node_bin_src: str, licenses_dir: str) -> None:
    """Ship the notices for the runtimes and packages bundled in the app."""
    destination = Path(licenses_dir)
    shutil.copy2(Path(PROJECT_ROOT) / "LICENSE", destination / "XuanJian-LICENSE")

    node_license = Path(node_bin_src).parent.parent / "LICENSE"
    if not node_license.is_file():
        raise FileNotFoundError(
            f"Node LICENSE not found beside {node_bin_src}; set XUANJIAN_NODE_BIN "
            "to bin/node from an official Node.js distribution"
        )
    shutil.copy2(node_license, destination / "Node-LICENSE")

    python_license = next(
        (parent / name for parent in (Path(sys.base_prefix), *Path(sys.base_prefix).parents)
         for name in ("LICENSE", "LICENSE.txt") if (parent / name).is_file()),
        None,
    )
    if python_license is None:
        if sys.version_info[:2] != (3, 14):
            raise FileNotFoundError("Python runtime LICENSE not found for this version")
        python_license = Path(PROJECT_ROOT) / "third_party" / "Python-3.14-LICENSE"
        if not python_license.is_file():
            raise FileNotFoundError("Python 3.14 LICENSE fallback is missing")
    shutil.copy2(python_license, destination / "Python-LICENSE")

    for distribution in metadata.distributions():
        name = distribution.metadata.get("Name", "unknown").replace("/", "_")
        for relative in distribution.files or []:
            rel = Path(str(relative))
            if not any(part.lower() == "licenses" for part in rel.parts) and not rel.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")):
                continue
            source = Path(distribution.locate_file(relative))
            if source.is_file() and source.stat().st_size < 2_000_000:
                target = destination / "python-packages" / name / rel.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    npm_root = Path(PROJECT_ROOT) / "frontend" / "node_modules"
    for package in (*npm_root.glob("*/package.json"), *npm_root.glob("@*/*/package.json")):
        for source in package.parent.iterdir():
            if source.is_file() and source.name.upper().startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE")):
                name = str(package.parent.relative_to(npm_root)).replace("/", "__")
                target = destination / "npm-packages" / name / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def assemble_app():
    print("=" * 60)
    print("开始组装「玄鉴·书房.app」macOS Apple Silicon 客户试用版")
    print("=" * 60)

    # 1. 确保前端产物与图标存在
    frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")
    if not os.path.isdir(frontend_dist) or not os.path.isfile(os.path.join(frontend_dist, "index.html")):
        print("构建前端生产产物...")
        run_cmd("npm run build", cwd=os.path.join(PROJECT_ROOT, "frontend"))

    icon_path = os.path.join(PROJECT_ROOT, "build_assets", "AppIcon.icns")
    if not os.path.isfile(icon_path):
        print("生成应用图标 AppIcon.icns...")
        run_cmd([sys.executable, os.path.join(PROJECT_ROOT, "scripts", "generate_app_icon.py")])

    # 2. 编译后端 PyInstaller standalone bundle
    server_dist = os.path.join(DIST_DIR, "xuanjian_server")
    print("编译打包 Python 后端 arm64 独立运行体...")
    env_pyinstaller = os.environ.copy()
    env_pyinstaller["PYTHONPATH"] = PROJECT_ROOT
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--noconfirm",
        "--name", "xuanjian_server",
        "--paths", PROJECT_ROOT,
        "--collect-all", "xuanjian",
        "--hidden-import", "scripts.iching",
        os.path.join(PROJECT_ROOT, "backend", "server.py")
    ]
    subprocess.check_call(pyinstaller_cmd, cwd=PROJECT_ROOT, env=env_pyinstaller)

    # 3. 清理并创建 .app 目录结构
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
    os.makedirs(MACOS_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)

    # 4. 写入 Contents/Info.plist
    info_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>玄鉴·书房</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.xuanjian.studio</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>玄鉴·书房</string>
    <key>CFBundleDisplayName</key>
    <string>玄鉴·书房</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>3.0.1</string>
    <key>CFBundleVersion</key>
    <string>3.0.1</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 玄鉴·书房 XuanJian Studio. 象数求真 · 知止自省.</string>
</dict>
</plist>
"""
    with open(os.path.join(CONTENTS_DIR, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(info_plist)

    # 写入 PkgInfo
    with open(os.path.join(CONTENTS_DIR, "PkgInfo"), "w", encoding="utf-8") as f:
        f.write("APPL????")

    # 5. 复制 AppIcon.icns
    shutil.copy2(icon_path, os.path.join(RESOURCES_DIR, "AppIcon.icns"))

    # 6. 复制 Python 后端二进制及其依赖库到 Resources/server
    target_server_dir = os.path.join(RESOURCES_DIR, "server")
    print(f"复制后端运行体至: {target_server_dir}")
    shutil.copytree(server_dist, target_server_dir)

    # 7. 复制 Node.js arm64 独立二进制到 Resources/node/bin/node
    node_bin_src = find_valid_node_bin()
    print(f"搬运私有 Node arm64 运行时: {node_bin_src}")
    target_node_bin_dir = os.path.join(RESOURCES_DIR, "node", "bin")
    os.makedirs(target_node_bin_dir, exist_ok=True)
    target_node_bin = os.path.join(target_node_bin_dir, "node")
    shutil.copy2(node_bin_src, target_node_bin)
    os.chmod(target_node_bin, os.stat(target_node_bin).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 8. 复制 calc_worker.bundle.js 到 Resources/scripts
    target_scripts_dir = os.path.join(RESOURCES_DIR, "scripts")
    os.makedirs(target_scripts_dir, exist_ok=True)
    shutil.copy2(
        os.path.join(PROJECT_ROOT, "scripts", "calc_worker.bundle.js"),
        os.path.join(target_scripts_dir, "calc_worker.bundle.js")
    )

    # 9. 复制前端构建产物到 Resources/frontend/dist
    target_frontend_dir = os.path.join(RESOURCES_DIR, "frontend", "dist")
    print(f"复制前端静态产物至: {target_frontend_dir}")
    shutil.copytree(frontend_dist, target_frontend_dir)

    # 10. 收集第三方许可证说明
    licenses_dir = os.path.join(RESOURCES_DIR, "LICENSES")
    os.makedirs(licenses_dir, exist_ok=True)
    copy_license_notices(node_bin_src, licenses_dir)

    summary_license = f"""# 玄鉴·书房 v3.0.1 第三方开源许可声明 (Open Source Licenses)

本软件随包私有携带与调用的组件及许可证如下：

1. **Python Runtime**
   - 版本: {platform.python_version()} (macOS arm64)
   - 许可: Python Software Foundation License (PSFL)
   - 协议: 开源自由分发

2. **Node.js Standalone Runtime**
   - 版本: {subprocess.check_output([node_bin_src, '--version'], text=True).strip()} (macOS arm64)
   - 许可: Node.js distribution LICENSE, including bundled third-party notices
   - 说明: 随包私有携带，后台按需调用计算 Worker，不修改客户 PATH，不写入系统 /usr/local。

3. **lunar-python (历法与八字计算)**
   - 版本: {metadata.version('lunar_python')}
   - 许可: MIT License
   - 用途: 阴阳历高精度转换、二十四节气与立春时辰秒级交接。

4. **iztro (紫微斗数排盘算法)**
   - 版本: v2.6.1
   - 许可: MIT License
   - 用途: 十二宫位、十四主星、吉凶曜与四化确定性推算。

5. **bigfishmarquis-qimen (奇门遁甲时家转盘)**
   - 版本: v1.0.0
   - 许可: MIT License
   - 用途: 拆补定局与洛书九宫门星神排布。

6. **cryptography (AES-256-GCM 本地加密)**
   - 版本: {metadata.version('cryptography')}
   - 许可: Apache License 2.0 OR BSD 3-Clause License
   - 用途: 本地数据导出备份与 WebDAV 快照端到端加密保护。
"""
    with open(os.path.join(licenses_dir, "LICENSE_SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write(summary_license)
    for package in ("iztro", "bigfishmarquis-qimen"):
        shutil.copy2(
            os.path.join(PROJECT_ROOT, "third_party", f"{package}-LICENSE"),
            os.path.join(licenses_dir, f"{package}-LICENSE"),
        )

    # 11. 编写原生双击启动脚本: Contents/MacOS/玄鉴·书房
    launcher_script = """#!/bin/bash
# 玄鉴·书房 macOS 双击无终端极速启动引导器
# 自动探测可用端口、检查单实例、启动私有后台并唤起默认浏览器

set -e

# 定位当前 App 内部路径
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
CONTENTS_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

SERVER_BIN="$RESOURCES_DIR/server/xuanjian_server"
NODE_BIN="$RESOURCES_DIR/node/bin/node"
WORKER_BUNDLE="$RESOURCES_DIR/scripts/calc_worker.bundle.js"
FRONTEND_DIST="$RESOURCES_DIR/frontend/dist"

# 用户级私有数据目录 (符合 Apple 规范，升级/删除 App 不丢失用户手记)
DATA_DIR="$HOME/Library/Application Support/XuanJian"
LOGS_DIR="$DATA_DIR/logs"
BACKUPS_DIR="$DATA_DIR/backups"
PID_FILE="$DATA_DIR/server.pid"
PORT_FILE="$DATA_DIR/server.port"

mkdir -p "$DATA_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$BACKUPS_DIR"

# Reuse only the same build and private data directory. Never attach to a dev server.
BUILD_ID=$(shasum -a 256 "$SERVER_BIN" | awk '{print $1}')
check_running_instance() {
  if [ -f "$PORT_FILE" ]; then
    SAVED_PORT=$(cat "$PORT_FILE" 2>/dev/null || echo "")
    if [ -n "$SAVED_PORT" ] && [ -x "$NODE_BIN" ]; then
      INFO=$(curl -s --noproxy 127.0.0.1 -m 1 "http://127.0.0.1:$SAVED_PORT/api/system/info" 2>/dev/null || true)
      MATCH=$(printf '%s' "$INFO" | "$NODE_BIN" -e '
        let s="";process.stdin.on("data",c=>s+=c);process.stdin.on("end",()=>{
          try{let x=JSON.parse(s);console.log(x.app?.includes("玄鉴") && x.data_dir===process.argv[1] ? (x.build_id===process.argv[2] ? "same" : "older") : "other");}catch{console.log("other")}
        });' "$DATA_DIR" "$BUILD_ID")
      if [ "$MATCH" = "same" ]; then
        open "http://127.0.0.1:$SAVED_PORT/?source=app"
        exit 0
      elif [ "$MATCH" = "older" ]; then
        open "http://127.0.0.1:$SAVED_PORT/?source=app"
        osascript -e 'display alert "请先退出正在运行的旧版玄鉴" message "已为您打开旧版页面。请点左下角「关于玄鉴」→「停止玄鉴」，然后重新打开新版。您的手记会保留。"'
        exit 0
      fi
    fi
  fi
}
check_running_instance

# 2. 检查内部组件完整性
if [ ! -f "$SERVER_BIN" ] || [ ! -x "$SERVER_BIN" ]; then
  osascript -e 'display alert "玄鉴·书房 启动失败" message "核心服务组件丢失或未获得执行权限。请尝试重新解压或将应用移至 /Applications。" as critical'
  exit 1
fi

if [ ! -f "$NODE_BIN" ] || [ ! -x "$NODE_BIN" ]; then
  osascript -e 'display alert "玄鉴·书房 启动失败" message "内置 Node.js 计算组件丢失或未获得执行权限。请尝试重新解压应用。" as critical'
  exit 1
fi

# 3. 动态寻找可用端口 (优先 8788，已被占用则探测 8789-8800)
find_free_port() {
  for test_p in 8788 8789 8790 8791 8792 8793 8794 8795 8796 8797 8798 8799; do
    if ! lsof -nP -iTCP:"$test_p" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "$test_p"
      return 0
    fi
  done
  echo ""
  return 1
}

TARGET_PORT=$(find_free_port || true)
if [ -z "$TARGET_PORT" ]; then
  osascript -e 'display alert "玄鉴·书房 启动失败" message "网络端口冲突：本地端口 8788-8799 均被其他程序占用。请关闭占用端口的程序后重试。" as critical'
  exit 1
fi

# 4. 配置运行环境变量并启动服务 (定向日志至用户数据目录，避免黑框弹出)
export XUANJIAN_DATA_DIR="$DATA_DIR"
export XUANJIAN_HOST="127.0.0.1"
export XUANJIAN_PORT="$TARGET_PORT"
export XUANJIAN_NODE_PATH="$NODE_BIN"
export XUANJIAN_WORKER_PATH="$WORKER_BUNDLE"
export XUANJIAN_FRONTEND_DIST="$FRONTEND_DIST"
export XUANJIAN_APP_MODE="1"
export XUANJIAN_BUILD_ID="$BUILD_ID"

# 剥离可能导致外部代理拦截的代理变量
unset http_proxy HTTP_PROXY https_proxy HTTPS_PROXY all_proxy ALL_PROXY

# 后台启动
"$SERVER_BIN" >> "$LOGS_DIR/server.log" 2>&1 &
SERVER_PID=$!

echo "$SERVER_PID" > "$PID_FILE"
echo "$TARGET_PORT" > "$PORT_FILE"

# 5. 等待服务就绪并打开默认浏览器
READY=0
for i in {1..30}; do
  sleep 0.4
  HEALTH_CHECK=$(curl -s --noproxy 127.0.0.1 -m 1 "http://127.0.0.1:$TARGET_PORT/api/health" 2>/dev/null || echo "")
  if echo "$HEALTH_CHECK" | grep -q '"status":[[:space:]]*"healthy"'; then
    READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
done

if [ "$READY" -eq 1 ]; then
  open "http://127.0.0.1:$TARGET_PORT/?source=app"
else
  osascript -e 'display alert "玄鉴·书房 服务未能就绪" message "后台服务未能在预期时间内启动。\n\n请在访达中查阅详细运行日志：\n~/Library/Application Support/XuanJian/logs/server.log" as critical'
  exit 1
fi
"""
    launcher_dest = os.path.join(MACOS_DIR, "玄鉴·书房")
    with open(launcher_dest, "w", encoding="utf-8") as f:
        f.write(launcher_script)
    os.chmod(launcher_dest, os.stat(launcher_dest).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 12. 编写独立安全停止脚本: Contents/MacOS/stop
    stop_script = """#!/bin/bash
# 玄鉴·书房 安全退出脚本

DATA_DIR="$HOME/Library/Application Support/XuanJian"
PID_FILE="$DATA_DIR/server.pid"
PORT_FILE="$DATA_DIR/server.port"

STOPPED=0

# 优先通过 HTTP 优雅关机
if [ -f "$PORT_FILE" ]; then
  SAVED_PORT=$(cat "$PORT_FILE" 2>/dev/null || echo "")
  if [ -n "$SAVED_PORT" ]; then
    curl -s --noproxy 127.0.0.1 -X POST "http://127.0.0.1:$SAVED_PORT/api/system/shutdown" -H "Host: 127.0.0.1:$SAVED_PORT" >/dev/null 2>&1 || true
    sleep 0.5
    STOPPED=1
  fi
fi

# 次级通过 PID 关闭
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    STOPPED=1
  fi
  rm -f "$PID_FILE"
fi

rm -f "$PORT_FILE"

if [ "$STOPPED" -eq 1 ]; then
  echo "「玄鉴·书房」后台服务已安全停止。"
else
  echo "未检测到正在运行的「玄鉴·书房」服务。"
fi
"""
    # 12. 编写独立安全停止脚本: Contents/Resources/scripts/stop
    stop_dest = os.path.join(RESOURCES_DIR, "scripts", "stop")
    with open(stop_dest, "w", encoding="utf-8") as f:
        f.write(stop_script)
    os.chmod(stop_dest, os.stat(stop_dest).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 13. 清理扩展属性并执行本地适用 ad-hoc 代码签名
    print("清理扩展属性并对「玄鉴·书房.app」执行本地适用 ad-hoc 代码签名...")
    subprocess.run(["xattr", "-cr", APP_DIR], check=True)
    sign_cmd = ["codesign", "--force", "--deep", "--sign", "-", APP_DIR]
    subprocess.check_call(sign_cmd)

    # 验证签名 (容忍桌面环境 fileprovider 产生的 FinderInfo，在发布打包阶段由独立沙盒严格验证)
    verify_cmd = ["codesign", "--verify", "--deep", APP_DIR]
    subprocess.check_call(verify_cmd)
    print("签名验证通过 (ad-hoc signed, ready for local trial)！")

    print("=" * 60)
    print(f"「玄鉴·书房.app」已成功生成: {APP_DIR}")
    print("=" * 60)
    return APP_DIR


if __name__ == "__main__":
    assemble_app()
