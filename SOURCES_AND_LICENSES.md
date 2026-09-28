# 来源与许可

本仓库自己的代码按根目录 [MIT License](LICENSE) 发布。第三方库仍适用各自的许可证；这个许可不替它们重新授权。

## 软件依赖

| 依赖 | 用途 | 本地核对的版本 / 许可 | 来源 |
| --- | --- | --- | --- |
| lunar-python | 公农历与节气计算 | 1.4.8 / MIT | [6tail/lunar-python](https://github.com/6tail/lunar-python) |
| iztro | 紫微斗数计算 | 2.6.1 / MIT | [SylarLong/iztro](https://github.com/SylarLong/iztro) |
| bigfishmarquis-qimen | 奇门排盘计算 | 1.0.0 / MIT | [perfhelf/bigfishmarquis-qimen](https://github.com/perfhelf/bigfishmarquis-qimen) |
| lucide-react | 界面图标 | 1.48.0 / ISC | [lucide-icons/lucide](https://github.com/lucide-icons/lucide) |
| React | 界面框架 | 19.3.0 / MIT | [facebook/react](https://github.com/facebook/react) |
| cryptography | 加密备份 | 按 `requirements.txt` 安装 / Apache-2.0 OR BSD-3-Clause | [pyca/cryptography](https://github.com/pyca/cryptography) |

`scripts/calc_worker.bundle.js` 实际包含 `iztro` 与 `bigfishmarquis-qimen` 的代码，所以仓库保留了两者的完整 [许可原文](third_party/)。其他依赖由包管理器安装。版本以锁定文件或本地安装记录为准；许可证如上按本次所用版本核对。

## 典籍与历法资料

- 《周易》卦爻辞、十翼、《道德经》及《协纪辨方书》等古籍原文属于传世文献。项目中的现代说明、选择和程序代码与古籍原文分开处理。
- 384 个爻位的电子录入依据 [open-iching 的 `iching.json`](https://github.com/john-walks-slow/open-iching/blob/main/iching/iching.json)，原始文件 SHA-256 为 `7fe029a32c51f2da39d702f8064825262cfd3a7d004353738cd893b0a017ab10`。项目只取古籍经文，不复制现代评注或对方程序；录入文本尚未逐条独立校订。
- 历法对照可参考 [香港天文台公农历对照表](https://www.hko.gov.hk/en/gts/time/conversion.htm)。项目测试覆盖了部分边界样例，不能据此声称完整历表已经逐日核验。

如发现出处、版本或许可证标注有误，请提交带原始来源的 Issue 或 Pull Request。
