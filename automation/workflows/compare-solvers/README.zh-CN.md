# 比较一致的场模型

对齐几何、铜面积、材料、频率、RMS/峰值、轴向长度、端口、回流和边界；独立求解后比较复电流、功率与 Rac，同时报告离散和几何差异。

必要输入：研究问题、模型与案例、物理条件、源码和证据身份、资源预算。

可复核产物：任务与参数、源码清单、日志、结果及测试证据；涉及修改时保存实际代码差异，并解释科学结论的适用范围。

Use `litz-research models`, `litz-research run <model> --case tutorial --dry-run`, and `litz-research jobs submit/status/cancel/resume`. Read the route guide before a full campaign.

完成标准：输入与源码可复现、执行证据真实、适用范围明确、验收状态准确。科学门槛见 tests/ACCEPTANCE.md，来源见 references/README.md。
