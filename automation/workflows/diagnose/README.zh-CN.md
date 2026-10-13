# 诊断失败并恢复

保留原失败和工具响应，定位协议、API、求解、资源或物理问题；验证最小相关修正，记录依据与差异，使用新身份重跑并核对原验收条件。

必要输入：研究问题、模型与案例、物理条件、源码和证据身份、资源预算。

可复核产物：任务与参数、源码清单、日志、结果及测试证据；涉及修改时保存实际代码差异，并解释科学结论的适用范围。

Use `litz-research models`, `litz-research run <model> --case tutorial --dry-run`, and `litz-research jobs submit/status/cancel/resume`. Read the route guide before a full campaign.

完成标准：输入与源码可复现、执行证据真实、适用范围明确、验收状态准确。科学门槛见 tests/ACCEPTANCE.md，来源见 references/README.md。
