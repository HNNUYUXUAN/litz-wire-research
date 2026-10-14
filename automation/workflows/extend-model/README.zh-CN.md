# 扩展模型并验证

说明新增能力与物理条件，阅读方程和实现；保存代码差异，增加独立物理及回归检查，运行原案例与新案例，解释适用范围与不确定性。

必要输入：研究问题、模型与案例、物理条件、源码和证据身份、资源预算。

可复核产物：任务与参数、源码清单、日志、结果及测试证据；涉及修改时保存实际代码差异，并解释科学结论的适用范围。

使用 `litz-research models` 查询模型，通过 `litz-research run <model> --case tutorial --dry-run` 预检，长任务使用 `litz-research jobs submit/status/cancel/resume`。完整研究前阅读对应路线说明。

完成标准：输入与源码可复现、执行证据真实、适用范围明确、验收状态准确。科学门槛见 tests/ACCEPTANCE.md，来源见 references/README.md。
