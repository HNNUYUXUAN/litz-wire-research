# GPU 执行与 CPU 对照

缪雨轩 · 淮南师范学院

## 模型与假设

Same-input double-precision numerical comparison

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

运行小型 GPU/CPU 对照，保存工具链和数值误差。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models gpu
litz-research run gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01 --dry-run
litz-research run gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01
litz-research jobs status gpu_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel gpu_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/gpu_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

在 CPU 与 GPU 上执行相同的小型双精度运算：矩阵乘法、已知解复线性系统及真实残差、FFT 与逆变换回读。
对照验收当前输入的算术和运行时一致性；新物理场解、大规模收敛和其他负载性能须分别验证。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch gpu

[CUDA](../../references/README.md)
