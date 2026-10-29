# Windows scientific execution

[简体中文](Windows与Notebook实施路线.md)

Use the [Conda environment instructions](../automation/environments/README.md), then run `litz-research doctor`. The current execution and desktop host is Windows Server 2022, with Wolfram 15.0 and AEDT Student 2025.2. Windows 10 remains a requested validation target.

The [model guides](../README.md#choose-a-model-and-continue-the-research) provide saved parameters and CLI commands. Python and Wolfram calibration are independent. Long runs use `jobs submit/status/cancel/resume`, with input identity, eight logical processors, 24 GiB task memory, 8 GiB system reserve and owned-process cleanup.

The [six canonical LaTeX masters](../manuscript/README.md) generate Markdown readings through Pandoc 3.13. [Publication instructions](editions.md) cover compilation and page review. Run `litz-research build --run-id publication_local_01 --stage all` with a fresh run ID.

Use `data list`, `data fetch` and `data verify` to select, restore and check historical research datasets. File and archive hashes preserve original evidence identities.
