# 二维扩散有限元

缪雨轩 · 淮南师范学院

## 模型与假设

∇⊥²Ez−jωμσEz=0; Jz=σEz

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改 mesh_h；收敛判断至少运行三档网格。

## 运行教程

```powershell
litz-research run fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01
```

[交互研究 Notebook](notebooks/fem2_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[FEMDOC](../../references/README.zh-CN.md), [P04](../../references/README.zh-CN.md)

## 推导与结果解释

在圆截面求解 ∇⊥²Ez−jωμσEz=0；边界常量场通过总复电流归一化。圆周多边形、插值阶次和网格尺寸共同决定数值误差。
弱形式在区域内积分 ∇v·∇Ez+jωμσvEz，并施加给定边界值。对所得电流及焦耳密度独立积分，再将 Rac 与 Bessel 解比较。
教程只用单档网格。精度判断须至少三档递减 h/a，并检查边界及圆周离散；积分守恒本身不构成场误差上界。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch fem2
