# 参与贡献

[English](CONTRIBUTING.md)

欢迎改进物理模型、执行适配、研究工作流、数据读取和双语稿件。开始前阅读[开发说明](docs/development.zh-CN.md)、所选路线的 README 及[验收标准](tests/ACCEPTANCE.zh-CN.md)。使用智能体协作时，[AGENTS.md](AGENTS.md)提供相同的研究约定。

## 确定具体改动

通过 [Issues](https://github.com/HNNUYUXUAN/litz-wire-research/issues) 描述可复现的问题或研究扩展建议，提供源码版本、命令、输入参数、软件版本及相关运行号，说明实际行为和预期行为。分享日志前移除凭据、许可证信息和个人机器路径，同时保留数值及错误信息。

在分支中实施改动。物理模型逻辑放入 `models/`，软件连接放入 `adapters/`，研究任务说明放入 `automation/`；保留 `src/` 中仍有用途的兼容入口。调整生成的文档或索引时，同时修改对应生成器。

## 检查源码工作区

使用 Python 3.11 或 3.12 的独立环境，在仓库根目录安装项目并执行基础检查：

```text
python -m pip install -e ".[automation]"
python -B tools/CheckSourceCheckout.py --output outputs/ci/source-checkout.json
```

检查器覆盖数据身份与恢复样例、参数与进程约定、CLI 入口、参考文献和六份完整稿件索引。它使用临时测试数据，无需下载保存场，也不依赖 Wolfram、Ansys、排版字体或 GPU。源码中的显式测试清单及 JSON 记录说明实际执行的项目。[开发说明](docs/development.zh-CN.md)分别介绍这些检查、原生求解器验证和成稿验证。

## 保持物理约定

采用 SI 单位、`exp(+jωt)` 和 RMS 相量。参考铜导体条件为 σ = 58 MS/m、μr = 1、20 ℃、200 kHz、20 A RMS。直径 2 mm 的 Q1 圆线用于校准；Q2 线束的名义铜截面积至少为 5 mm²。

绝缘股线通过共同端电压及总复电流约束求解。保留实际股线长度、铜体积、各股复电流、绝对交流电阻、交流与直流电阻比及损耗。明确回流、端接、外场和边界条件；含独立外加场时，区分总损耗除以电流平方与内禀输运电阻。候选结构应与传统多级 Litz 在匹配条件下比较，并考虑数值不确定性。

物理模型改动需要相应的解析极限、独立积分、功率守恒，以及适用的网格、分段、边界或长度敏感性检查。保留通过项与失败项。使用唯一运行号，保存源码和输入哈希，保持既有证据不变。[模型工作流](docs/tool-workflows.zh-CN.md)列出执行入口及验收范围。

## 维护双语内容与来源

同步更新中文和英文读者文档，使代码标识、命令、单位、公式身份及引用 key 保持一致。在 `references/library.bib` 维护题录，在 `references/sources.json` 记录实际贡献、版本及许可。修改这些来源后，重新生成并验证导出结果：

```text
litz-research references build
litz-research references verify
```

改编上游代码时保留版权和许可声明。原创软件及 Notebook 代码采用 MIT；原创正文、图件和数据采用 CC BY 4.0；第三方内容遵循其原有条款，详见[许可说明](LICENSES/README.zh-CN.md)。

## 提交便于评审的 Pull Request

说明问题、改动后的行为及已执行的验证。科学改动应列出物理假设、比较条件、证据位置和适用的不确定性；工作流改动应说明实际检查的工具或运行器行为。如实记录不可用的原生环境及尚未完成的科学检查。通过带文件哈希的清单连接新产物，提交内容不包含凭据、缓存和本地软件安装文件。

稿件及仓库发布步骤见[发布准备](docs/release-preparation.zh-CN.md)。
