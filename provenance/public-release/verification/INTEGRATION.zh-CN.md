# 公开源码与已安装 CLI 验收

这些工具记录发布后的独立验收。工具与收据在 rc.3 源码标签之后维护，
它们的来源身份与被验收的 rc.3 提交分别保存。工具不会发布仓库或安装依赖。
执行下载验收前，仓库、所需 Releases 和源码标签应已公开。

以下命令从当前仓库根目录执行。源码 ZIP 没有 `.git` 目录，因此应从包含指定
提交的本地 Git 检出建立预期文件清单。所有输出目录均须为新目录。

## 1. 匿名下载并核验源码标签

```powershell
$repo = (Resolve-Path '.').Path
$tools = Join-Path $repo 'provenance/public-release/verification'
$python = (Get-Command python).Source
$commit = '01aa0bc3dc12a548301a148f8fc99e12a241e075'
$acceptance = Join-Path $repo 'outputs/public source acceptance'
& $python "$tools/VerifyPublicSource.py" --root $repo --commit $commit --tag 'v1.0.0-rc.3' --directory $acceptance
```

工具只通过本地 Git 对象读取预期清单，然后匿名下载 GitHub 标签 ZIP。
所有文件的清单、长度和原始字节 SHA-256 全部匹配后才提取到新建的
`source checkout/`。路径穿越、符号链接、意外成员、文件名冲突和已存在的
提取目录均会导致验收失败。收据保存为 `source-verification.json`。

## 2. 在全新虚拟环境安装已验证源码

安装是独立的准备步骤，其结果与匿名下载证据分开记录。虚拟环境位于源码
提取目录之外，不启用系统包，也不复用现有环境。

```powershell
$source = "$acceptance/source checkout"
$venv = "$acceptance/clean environment"
& $python -m venv $venv
& "$venv/Scripts/python.exe" -m pip --isolated install --disable-pip-version-check --no-cache-dir --index-url 'https://pypi.org/simple' --report "$acceptance/pip-install-report.json" $source
```

## 3. 通过实际 CLI 匿名恢复数据

```powershell
& "$venv/Scripts/python.exe" "$tools/VerifyAnonymousCLI.py" --source $source --directory "$acceptance/cli restoration acceptance"
```

工具重新核对源码收据中的全部文件，并直接从收据的 Git 文件清单投影包内
Python 文件的预期清单和哈希。当前源码包和已安装包都必须与该清单完全
一致，包括拒绝额外 Python 文件。随后实际调用 `litz_research.cli.main`：

```text
--project <source checkout> data fetch analytic --cache <new empty object cache>
```

CLI 的参数解析、目录选择、分片下载、对象解包、依赖递归和目标文件恢复均
执行真实实现。HTTP 传输显式禁用环境代理，拒绝认证与 Cookie 请求头，仅
接受可信 GitHub HTTPS 重定向，并记录请求头名称和响应状态。记录会移除
签名重定向 URL 的查询参数。命令执行期间拦截全部子进程，包括任何
`gh auth` 调用。缓存必须全新，已登记的目标文件必须全部不存在。

`cli-restoration-verification.json` 保存源码提交、目录和已安装代码身份、
CLI 返回结果、每个下载分片的哈希、匿名请求记录及所有恢复文件的核验结果。
每个依赖缓存对象也会再次核对长度和哈希。`research-shared` 提供共享缓存
对象，没有直接目标文件记录。文件数量从提交中的目录计算；当前解析数据
为 874 个文件。此过程不启动物理求解。

## 4. 离线测试

```powershell
Push-Location $tools
& "$venv/Scripts/python.exe" -m unittest -v test_public_source test_anonymous_cli test_portable_receipts
Pop-Location
```

14 项测试覆盖原始 ZIP 字节、缺失与额外成员、路径穿越、符号链接、大小写
冲突、覆盖拦截、代理与认证头、模拟 HTTP 下的真实 CLI 恢复、损坏响应、
认证子进程拦截、依赖循环、已安装代码变更、源码与安装目录额外 Python
文件，以及收据路径转换。测试不联网。

## 5. 可公开的便携收据

原始收据保留原位。使用新的输出目录创建独立副本和转换清单：

```powershell
& "$venv/Scripts/python.exe" "$tools/SanitizePublicReceipts.py" --acceptance-root $acceptance --output "$acceptance/portable public receipts"
```

`${ACCEPTANCE_ROOT}` 替代验收目录的绝对路径，`${PYTHON_BASE}` 替代基础
Python 安装目录，JSON 中的文件 URI 按同样规则转换。源码、下载、文件的
哈希，数量，状态和公开 HTTPS 请求 URL 保持不变。清单记录原始文件与副本
的原始字节 SHA-256；收据内已有的哈希引用继续指向原始收据。

经过检查的便携副本位于脚本旁的 `public-receipts/`。重新验收时应写入新的
输出目录，保留既有公开收据的身份。
