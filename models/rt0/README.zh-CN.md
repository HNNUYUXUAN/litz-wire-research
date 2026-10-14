# 向量 RT0 体积 PEEC

缪雨轩 · 淮南师范学院

## 模型与假设

(R+jωL)i+e=Cᵀv; Ci=b

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

选择外场或输运激励。外场算例为 1 mT RMS Bz、零净输运。

## 运行教程

```powershell
litz-research run rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01
```

[交互研究 Notebook](notebooks/rt0_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[P03](../../references/README.zh-CN.md), [RUEHLI1974](../../references/README.zh-CN.md), [RT1977](../../references/README.zh-CN.md), [GMRES1986](../../references/README.zh-CN.md)

## 推导与结果解释

最低阶 Raviart–Thomas 面通量自由度表示具有单元散度的向量电流；相邻单元共享带方向的面通量，关联矩阵 C 实现离散电流连续性。
混合 PEEC 系统为 (R+jωL)i+e=Cᵀv、Ci=b。外场教程采用 Bz=1 mT RMS、零净输运，分别由重构电流与电阻二次型计算损耗。
检查真实线性残差、连续性、积分及空间敏感性。外场损耗是诊断量；用另设输运电流的平方去除它，不能据此定义内禀电阻。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch rt0
