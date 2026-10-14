# GPU 执行与 CPU 对照

缪雨轩 · 淮南师范学院

## 模型与假设

Same-input double-precision numerical comparison

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

运行小型 GPU/CPU 对照，保存工具链和数值误差。

## 运行教程

```powershell
litz-research run gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01
```

[交互研究 Notebook](notebooks/gpu_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[CUDA](../../references/README.zh-CN.md)

## 推导与结果解释

在 CPU 与 GPU 上执行相同的小型双精度运算：矩阵乘法、已知解复线性系统及真实残差、FFT 与逆变换回读。
对照验收当前输入的算术和运行时一致性；新物理场解、大规模收敛和其他负载性能须分别验证。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch gpu
