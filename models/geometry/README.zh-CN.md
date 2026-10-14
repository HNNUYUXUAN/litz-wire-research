# 几何与换位

缪雨轩 · 淮南师范学院

## 模型与假设

ℓi=∫√(1+x′²+y′²) dz; Rdc=(ΣσAi/ℓi)⁻¹

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改结构、节距或长度；检查间隙、弧长与铜体积。几何是场模型的输入。

## 运行教程

```powershell
litz-research run geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01
```

[交互研究 Notebook](notebooks/geometry_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[P01](../../references/README.zh-CN.md), [N01](../../references/README.zh-CN.md)

## 推导与结果解释

结构把持续不变的股线身份映射到中心线 (xi(z),yi(z),z)。教程采样路径，检查表面间隙，并积分弧长 ℓi=∫√(1+x′i²+y′i²)dz。
轴向长度 L 对应铜体积 ΣAiℓi，共端直流电阻为 Rdc=(ΣσAi/ℓi)⁻¹。名义铜面积相等仍须计入弧长增长，并保持一致的端接约束。
几何为后续场模型提供输入。性能排名须独立电磁场解、受控回流与端区及数值不确定性；传统多级 Litz 是强基线。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch geometry
