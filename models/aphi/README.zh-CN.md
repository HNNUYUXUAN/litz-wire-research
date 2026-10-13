# 保存 A–φ 场诊断

Miao Yuxuan · Huainan Normal University

## 模型与假设

J=−σ(jωA+∇φ); ∇·J=0

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

读取实际保存场，复算 J、电势与规范残差，保留原场参数。

## 运行教程

```powershell
litz-research run aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01
```

[交互研究 Notebook](notebooks/aphi_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[FEMDOC](../../references/README.md), [GMRES1986](../../references/README.md)

## 推导与结果解释

采用 exp(+jωt)，由原保存的 A、φ 场重构 J=−σ(jωA+∇φ)，在原输入下比较电流守恒和归一化电势、规范残差。
本入口仅改变诊断采样密度，在保存场上复算导数并与原诊断量比较可复现性，不产生新的物理场解。
原电势与规范验收仍为失败。保留网格、激励、规范及边界假设；明确一致形式并通过守恒、规范和网格研究后再推进。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch aphi
