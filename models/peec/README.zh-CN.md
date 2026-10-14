# 有限长度纵向 PEEC

缪雨轩 · 淮南师范学院

## 模型与假设

Z=R+jωL; Zi=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改长度或横向离散，核对复端口约束与功率。基函数沿纵向。

## 运行教程

```powershell
litz-research run peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01
```

[交互研究 Notebook](notebooks/peec_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[P03](../../references/README.zh-CN.md), [RUEHLI1974](../../references/README.zh-CN.md)

## 推导与结果解释

将截面离散为纵向电流基函数。磁准静态积分方程经 Galerkin 投影得到 Z=R+jωL；R 由电导率与基函数重叠构造，L 含有限长度互项与自项。
联立 Zi=V1、1ᵀi=It 求未知端电压与复电流。有功输入须与电阻二次型损耗 iᴴRi 一致。
横向离散、轴向长度和积分阶数分别研究。纵向基函数未保留一般横向电流及完整端区电荷，适用范围应据此解释。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch peec
