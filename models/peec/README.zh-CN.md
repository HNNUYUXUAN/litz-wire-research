# 有限长度纵向 PEEC

缪雨轩 · 淮南师范学院

## 模型与假设

Z=R+jωL; Zi=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改长度或横向离散，核对复端口约束与功率。基函数沿纵向。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models peec
litz-research run peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01 --dry-run
litz-research run peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01
litz-research jobs status peec_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel peec_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/peec_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

将截面离散为纵向电流基函数。磁准静态积分方程经 Galerkin 投影得到 Z=R+jωL；R 由电导率与基函数重叠构造，L 含有限长度互项与自项。
联立 Zi=V1、1ᵀi=It 求未知端电压与复电流。有功输入须与电阻二次型损耗 iᴴRi 一致。
横向离散、轴向长度和积分阶数分别研究。纵向基函数未保留一般横向电流及完整端区电荷，适用范围应据此解释。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch peec

[P03](../../references/README.md), [RUEHLI1974](../../references/README.md)
