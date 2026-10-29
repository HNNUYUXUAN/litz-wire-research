# 中文论文样稿与使用体验检查

当前样稿运行身份为 `publication_20261013_paper_sample_09`。完整样稿已获用户确认，包括第 6、8 页的图 4、5、9、10；其来源身份保持独立。

## 阅读位置

- PDF、Markdown、LaTeX：`outputs/publication_20261013_paper_sample_09/documents/paper/zh-CN/`。
- Wolfram Notebook：`notebooks/publication/publication_20261013_paper_sample_09/paper/zh-CN/paper_zh-CN.nb`。
- 配套包：`outputs/publication_20261013_paper_sample_09/Litz_publication_package.zip`。
- 正文源：`manuscript/specimens/paper-zh-CN/`；统一清单：`manuscript/specimens/publication.paper-zh-CN.json`。

PDF 共 19 页，前 10 页为五章正文，后 9 页为补充材料和参考文献。第 6、8 页两组独立图采用统一画布、坐标框高度和横轴基线；图题居中，说明另段左对齐。曲线图例置于框内留白处，截面色标采用原色值函数生成连续色带。

## 实际检查范围

| 检查 | 结果 |
| --- | --- |
| 独立图尺寸 | 四张图的中英文 PDF 五种页面边界均为 252×198 pt，即 88.9×69.85 mm；PNG 为 2100×1650 像素，600 dpi |
| 字体与图形 | 宋体、Times New Roman 及数学字符实际渲染；PDF 字体嵌入通过；曲线矢量保留；图 5 高分辨率检查确认曲线连续 |
| PDF 阅读 | 19 页实际编译和渲染；第 6、8 页以及顺延的第 9、10 页目视检查通过；其他 15 页与已确认样稿逐像素一致 |
| Notebook | 180 个单元分 15 批前端渲染；实际打开、保存、回读通过；修改图件的屏幕渲染通过；9 个原生三维图形视角保存回读通过 |
| 数值与来源 | 原图基元、坐标范围、色标函数、范围和端点颜色一致；量值清单、Markdown 与 LaTeX 正文逐字节一致 |
| 配套材料 | 240 个其他面板文件、16 份数据表和 12 个标注文件与已确认样稿 SHA256 一致 |
| 构建检查 | 本轮 12 项正文及科学量值回归通过；最终成稿 40 项检查通过 |

`visual_review.json`、`four_figure_verification.json`、`edition_verification.json`、`pdf_verification_details.json` 和 `notebook_verification.json` 保存实际验收范围及文件身份。正文和科学数据沿用已确认版本。

## 独立图重排入口

`src/ReframePublicationPanels.py` 从保存的 Wolfram 图形表达式生成独立 PDF、SVG 和 PNG，记录数值基元、布局及来源身份。示例：

```powershell
python src/ReframePublicationPanels.py --run-id publication_panels_YYYYMMDD_01
```

可使用重复的 `--panel` 参数选取单图。统一清单通过 `panel_overrides` 绑定验收后的图件运行；文档构建按清单确定每个面板文件的唯一来源。

## 阶段衔接

已批准的版式与制图范式见 manuscript/style.json；全部双语论文、报告和章节稿的推广在后续成稿阶段安排。当前正式成稿索引保持已有候选版本，样稿及其验收记录独立保存。
