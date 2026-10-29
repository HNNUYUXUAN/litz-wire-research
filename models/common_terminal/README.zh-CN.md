# 共端复电流分配

缪雨轩 · 淮南师范学院

## 模型与假设

Zi+e=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改股数或回流几何；检查复电流及输入功率与损耗。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models coax
litz-research run coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01 --dry-run
litz-research run coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01
litz-research jobs status common_terminal_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel common_terminal_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/common_terminal_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

股线沿途绝缘，仅端部并联。二维 Az 弱形式把各导体区域与未知轴向电势梯度耦合，并用受控同轴铜回流闭合输运问题。
线性模型形成 Az 与源束/回流电势梯度的块系统。施加 ΣIi=20 A RMS、Ireturn=−20 A；各股共享源束电势梯度，复电流 Ii 由求得的电流密度积分得到。
分别积分束线及回流焦耳损耗，与输入有功功率比较。纯输运工况可定义 Rac,bundle=Pbundle/|It|²。七股为方法演示，铜面积不满足 Q2。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch common-terminal

[P01](../../references/README.md), [P02](../../references/README.md)
