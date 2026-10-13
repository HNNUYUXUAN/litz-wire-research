# Litz 线分层建模与数值验证：完整研究报告 · D 数据来源与环境交接

缪雨轩 · 淮南师范学院

[合并稿](../README.md#chapter-D)

<a id="chapter-D"></a>
## D 数据来源与环境交接

复现分为研究计算与成稿构建两个入口。研究入口读取原始输入和求解配置，执行相应验证；成稿入口读取冻结数据、已验收单图与 Markdown 正文，生成章节、合并稿和多种格式。每一阶段保存输入哈希和输出哈希，只有依赖与产物一致时才复用已完成阶段。独立单图保留矢量曲线及其字体，组图清单保存面板身份与布局参数。

来源清单 / Source manifest: source_provenance.json; quantities.json; asset_sources.json.

冻结来源与完整性 / Frozen sources and integrity

| Source | SHA256 |
| --- | --- |
| docs/总控/当前运行索引.json | 3324976d4af8f58e60820a88ae978246443f78fbdd0cfa1050e86809110ae60d |
| outputs/prewrite_closure_state.json | 80a66afa79c321a89f730b102af0e70125f6e1655372717d6b59f470c6520e71 |
<a id="references"></a>
## 参考文献
