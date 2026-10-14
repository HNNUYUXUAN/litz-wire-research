# 单圆线解析校准

缪雨轩 · 淮南师范学院

## 模型与假设

∇²Ez−jωμσEz=0; Zint=κ I0(κa)/(2πaσ I1(κa))

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改频率与总电流，核对独立电流积分与焦耳积分。

## 运行教程

```powershell
litz-research run wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01
```

[交互研究 Notebook](notebooks/analytic_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[BESSEL](../../references/README.zh-CN.md)

## 推导与结果解释

均匀长圆柱导体的轴对称内场仅保留 Ez(r)，并有 Jz=σEz。由安培与法拉第定律及 exp(+jωt) 得 (1/r)d(r dEz/dr)/dr=jωμσEz；轴心正则解为 C I0(κr)，κ²=jωμσ。
用 2π∫Jz r dr=It 确定 C，得到内阻抗 Zint=κ I0(κa)/(2πaσ I1(κa))。独立积分 ∫|J|²/σ dA，与 |It|² Re Zint 比较；采用 RMS 相量，无额外 1/2 系数。
κa→0 时 I0→1、I1→κa/2，因此 Rdc=1/(σπa²)。模型不含端效应与回流外电感。Q1 的 a=1 mm 保留为解析校准。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic
