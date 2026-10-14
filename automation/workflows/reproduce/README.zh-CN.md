# 复现已有模型

选择模型、案例和证据数据集，核对来源与假设；完成环境检查和预检后使用新运行号执行，解释验收并比较一致的观测量。

必要输入：研究问题、模型与案例、物理条件、源码和证据身份、资源预算。

可复核产物：任务与参数、源码清单、日志、结果及测试证据；涉及修改时保存实际代码差异，并解释科学结论的适用范围。

使用 `litz-research models` 查询模型，通过 `litz-research run <model> --case tutorial --dry-run` 预检，长任务使用 `litz-research jobs submit/status/cancel/resume`。完整研究前阅读对应路线说明。

完成标准：输入与源码可复现、执行证据真实、适用范围明确、验收状态准确。科学门槛见 tests/ACCEPTANCE.md，来源见 references/README.md。
