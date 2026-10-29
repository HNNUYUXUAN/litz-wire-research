# 几何与换位

缪雨轩 · 淮南师范学院

## 模型与假设

ℓi=∫√(1+x′²+y′²) dz; Rdc=(ΣσAi/ℓi)⁻¹

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改结构、节距或长度；检查间隙、弧长与铜体积。几何是场模型的输入。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models geometry
litz-research run geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01 --dry-run
litz-research run geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01
litz-research jobs status geometry_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel geometry_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/geometry_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

结构把持续不变的股线身份映射到中心线 (xi(z),yi(z),z)。教程采样路径，检查表面间隙，并积分弧长 ℓi=∫√(1+x′i²+y′i²)dz。
轴向长度 L 对应铜体积 ΣAiℓi，共端直流电阻为 Rdc=(ΣσAi/ℓi)⁻¹。名义铜面积相等仍须计入弧长增长，并保持一致的端接约束。
几何为后续场模型提供输入。性能排名须独立电磁场解、受控回流与端区及数值不确定性；传统多级 Litz 是强基线。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch geometry

[P01](../../references/README.md), [N01](../../references/README.md)
