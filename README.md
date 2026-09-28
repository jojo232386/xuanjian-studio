# 玄鉴·书房 · XuanJian Studio

**写下问题，研读传统，留下事后可回看的手记。** 一个本地优先的《周易》与中国传统历法研读工具。默认离线运行，不需要账号或付费 AI 密钥。当前公开仓库提供源码；独立 Mac 安装包仍在另一台干净设备上等待验收。

[![Source checks](https://github.com/jojo232386/xuanjian-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/jojo232386/xuanjian-studio/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> An offline-first study app for the *I Ching*, Chinese calendar, and reflective journaling. The interface and classical texts are currently in Chinese.

## 两分钟体验

1. 打开「书房」，点 **从这里开始**。
2. 在「问事」里选一个问题例子，改成自己的话；点 **快速起卦**，或逐次模拟投币六次。
3. 先读简短解读。想日后回看，再点 **保存这次问事**；在「典藏 → 我的手记」补充事后复盘。

“起卦”在这里是用六次模拟投币生成卦象，供传统文化研读和自我反思。它不能预测现实事件的发生概率，也不能替代医疗、法律或财务判断。

## 能做什么

| 功能 | 当前能力 |
| --- | --- |
| 周易问事 | 逐次三币、快速起卦、实体硬币录入；本卦、变卦、互卦与爻辞 |
| 传统排盘 | 八字、紫微斗数、奇门遁甲的确定性排盘 |
| 历法与典籍 | 公农历、节气、传统宜忌查询；《道德经》八十一章 |
| 本地手记 | 主动保存、查看原始解读、追加复盘；加密备份与可选 WebDAV 同步 |
| 本地解读 | 按卦象和问题类别生成简短规则解读；云端 AI 为可选项，默认关闭 |

## 从源码运行

需要 **Python 3.14** 和 **Node.js 22**。在项目根目录执行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python backend/server.py
```

然后打开 `http://127.0.0.1:8788/`。数据默认保存在项目的 `data/` 目录；客户 App 模式使用 macOS 的 `~/Library/Application Support/XuanJian/`。请不要把真实手记或密钥提交到 Git。

只想验证周易排盘，也可以运行：

```bash
PYTHONPATH=. .venv/bin/python scripts/iching.py lines 7 8 7 8 9 6
```

这组固定爻值会得到 **本卦既济、动爻 5 和 6、变卦贲、互卦未济**。固定输入便于核对计算，不代表对现实问题作预测。

紫微与奇门使用随源码提供的 `scripts/calc_worker.bundle.js`；它包含 MIT 许可的第三方代码，原始适配逻辑在 `scripts/calc_worker_src.ts`。依赖与文本来源见 [来源与许可](SOURCES_AND_LICENSES.md)，随源码分发的第三方许可原文在 [third_party](third_party/)。

## 验证与现状

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider --ignore=tests/test_macos_client_app_e2e.py
npm --prefix frontend run build
```

macOS 独立 App 的端到端测试另在 `tests/test_macos_client_app_e2e.py`，需要先准备打包依赖。2026-09-28 的本地完整测试为 **130 passed**；这不是跨平台或另一台干净 Mac 的安装验收。

运行测试前请安装 `requirements-dev.txt`。在 macOS Apple Silicon 上试做独立 App，可安装 `requirements-build-macos.txt` 后运行 `scripts/build_macos_client_app.py`；生成的 `dist/` 不属于源码仓库。

当前源码可用于本地研究和试用。384 个爻位来自传世古籍电子录入，尚未逐条独立校订；传统日时标签也没有经验证的“最佳时段”排序或现实预测能力。欢迎先从这些可核验的缺口贡献。

## 参与

欢迎提交可复现的问题、典籍底本与异文线索，或改进首次使用体验。请先看 [贡献指南](CONTRIBUTING.md)。项目自身代码按 [MIT License](LICENSE) 开源；第三方代码和文本来源单独说明。

---

**English:** XuanJian Studio is a local-first cultural study tool, not a fortune-telling guarantee. Build the React frontend with `npm --prefix frontend ci && npm --prefix frontend run build`, install Python dependencies from `requirements.txt`, then run `backend/server.py`. The UI is Chinese-only today; translations are welcome.
