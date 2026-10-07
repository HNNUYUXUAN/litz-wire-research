# Windows 与 Notebook 运行

本项目使用 Python 编排、Wolfram 科学模块和可选求解适配。首次使用先执行 `litz-research doctor`，核对当前环境、字体、工具和资源。开发入口及依赖分组见 [开发说明](development.zh-CN.md)。

## 解析与数值路线

`litz-research run analytic` 运行 Python Bessel 校准；`litz-research run wolfram-analytic` 在干净 Wolfram 内核完成对应十二项回归。二维 FEM、共端场路、几何、PEEC 和 RT0 通过科学阶段运行器执行，各次运行保存独立编号、参数、源码快照、日志与验收。

Windows 基线使用 Wolfram 15.0。科学内核与 Notebook 前端分别验收。PowerShell 运行器记录本轮进程及创建身份，默认使用八线程、24 GiB 任务预算与 8 GiB 系统余量。Ansys 按对应版本、许可证、网格和四核要求执行；GPU 适配的环境与同矩阵对照见其原始运行记录。

## 文稿与 Notebook

```powershell
litz-research data fetch publication-inputs
litz-research build --run-id publication_local_01 --stage all
```

正文主源是 `manuscript/` 中的双语 Markdown 和共享清单。构建按依赖生成文档结构、独立图的组合、Notebook、LaTeX 和 PDF。Notebook 保存正文、公式、静态图件及原生 Graphics3D；打开后可以旋转和缩放三维视图。模型运行由独立计算入口调用。

Notebook 验收包含实际前端打开、保存、回读和各章节渲染；三维视角变更后再次保存回读并核对几何内容。PDF 使用 XeLaTeX、BibTeX 和 latexmk，检查引用、字体嵌入、裁切和逐页渲染。宋体及 Times New Roman 由本机字体环境提供。

## 数据恢复

数据集通过 `data list` 选择，`data fetch` 获取，`data verify` 核验。每个分片、对象和还原文件均有 SHA256。离线恢复使用 `--offline --cache <目录>`。源码路径从工程根目录推导，迁移验收覆盖含空格目录。
