# 公开发布验收

[English](README.md) · [简体中文](README.zh-CN.md)

仓库及 rc.1、rc.2、rc.3 三个预发布版本均已公开。rc.3 源码标签对应 `01aa0bc3dc12a548301a148f8fc99e12a241e075`，[四个 CI 组合](ci-source.json)各通过 59 项测试。[仓库与 Release 元数据](repository-releases.json)保存发布状态。

[匿名源码下载](verification/public-receipts/source-verification.json)的 972 个文件全部匹配提交。[已安装 CLI](verification/public-receipts/cli-restoration-verification.json)在全新环境和缓存中恢复 874 个解析文件，并复核 679 个数据对象。[独立安装清单审计](verification/public-receipts/installed-package-binding.json)确认 13 个 Python 文件均与 Git 文件清单一致。详见[再现指南](verification/INTEGRATION.zh-CN.md)及[便携收据身份](verification/public-receipts/portable-receipts-manifest.json)。

全部 127 个附件的下载正在进行，完成后补充完整字节数与哈希验收。匿名 API 元数据请求受到限流后，元数据通过具有仓库权限的账号读取；内容下载采用独立的无凭据 HTTPS 请求。本次转换没有新增物理求解或重建稿件。
