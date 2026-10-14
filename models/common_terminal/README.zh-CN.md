# 共端复电流分配

缪雨轩 · 淮南师范学院

## 模型与假设

Zi+e=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改股数或回流几何；检查复电流及输入功率与损耗。

## 运行教程

```powershell
litz-research run coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01
```

[交互研究 Notebook](notebooks/common_terminal_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[P01](../../references/README.zh-CN.md), [P02](../../references/README.zh-CN.md)

## 推导与结果解释

股线沿途绝缘，仅端部并联。二维 Az 弱形式把各导体区域与未知轴向电势梯度耦合，并用受控同轴铜回流闭合输运问题。
线性模型形成 Az 与源束/回流电势梯度的块系统。施加 ΣIi=20 A RMS、Ireturn=−20 A；各股共享源束电势梯度，复电流 Ii 由求得的电流密度积分得到。
分别积分束线及回流焦耳损耗，与输入有功功率比较。纯输运工况可定义 Rac,bundle=Pbundle/|It|²。七股为方法演示，铜面积不满足 Q2。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch common-terminal
