"""Generate the paired dataset inventory from its catalog and translated descriptions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
ZH={
'academic-editions':'历史双语报告、论文、Notebook、PDF、图件及文档验收记录',
'analytic':'圆线 Bessel 校准、径向电流和解析验收',
'ansys':'Maxwell 输入、工程、接口探针、网格限制和验证记录',
'aphi':'三维 A–φ 保存场、校准诊断及求解边界',
'common-terminal':'共同端电压场路模型、逐股复电流及受控回流',
'fem2':'二维有限元校准、网格、场和敏感性检查',
'geometry':'股线身份、中心线、弧长、铜体积及几何检查',
'gpu':'CPU/GPU 矩阵和复电流比较、资源与退出状态',
'peec':'有限长度纵向 PEEC 输入、解及长度和积分敏感性',
'publication-inputs':'成稿使用的独立面板、绘图数据和观测量',
'research-records':'跨路线运行记录、验证摘要和保存源码',
'research-shared':'由路线依赖恢复的去重共享内容对象',
'rt0':'外场 RT0 解、面通量重构、空间收敛和算子检查',
'automation-rc2':'自动化源码快照、可见工具事件、原生求解、任务恢复及 Notebook 记录'}

def main():
    c=json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
    for lang in ('en','zh-CN'):
        zh=lang=='zh-CN'
        lines=['# '+('研究数据集' if zh else 'Research datasets'),'','[English](datasets.md)' if zh else '[简体中文](datasets.zh-CN.md)','',
          '在 Python 3.11 或后续版本的虚拟环境中，从仓库根目录安装 CLI：' if zh else 'Install the CLI from the repository root in a virtual environment with Python 3.11 or later:',
          '', '```powershell','python -m pip install -e .','```','',
          '通过 CLI 选择所需路线，依赖会一并恢复。还原后核对文件身份：' if zh else 'Select the required route through the CLI. Dependencies are restored with it; verify file identities after restoration:',
          '', '```powershell','litz-research data list','litz-research data fetch publication-inputs','litz-research data verify publication-inputs','```','',
          '## '+('下载与身份验证' if zh else 'Downloads and authentication'),'']
        if c.get('private',True):
            lines += ['本目录当前设置为 `private: true`。具有仓库访问权的用户先执行 `gh auth login`；恢复器从 GitHub API 获取附件，并通过 `gh auth token` 取得当前凭据。' if zh else
                      'This catalog currently sets `private: true`. Users with repository access first run `gh auth login`; the restorer retrieves attachments through the GitHub API using the current credential from `gh auth token`.','']
        else:
            lines += ['本目录设置为 `private: false`，已发布的公开附件可直接下载，无需 GitHub CLI 或登录。' if zh else
                      'This catalog sets `private: false`; published public attachments download directly without GitHub CLI or sign-in.','']
        lines += [
          '公开模式优先使用分片的 `public_url`。恢复器核对其与 `repository`、数据集的 `source_version`（缺省时使用目录的 `tag`）及附件文件名完全对应，URL 使用 `https://github.com/<repository>/releases/download/<version>/<name>`，文件名按 URL 编码。未提供 `public_url` 的旧目录继续使用 `url`，不附带身份凭据。' if zh else
          'Public mode prefers each part’s `public_url`. The restorer checks it against `repository`, the dataset’s `source_version` (or catalog `tag`) and the attachment filename. Its form is `https://github.com/<repository>/releases/download/<version>/<name>`, with the filename URL-encoded. Older catalogs without `public_url` continue to use `url` without authentication.',
          '',
          '私有历史目录保留 `private: true`，始终使用分片的 API `url` 并忽略 `public_url`。凭据仅用于 HTTPS 的 `api.github.com` 请求，跨主机跳转时移除。公开发布要求附件所属的 Release 已发布；仅将仓库设为公开不会使 Draft 附件可下载。' if zh else
          'Historical private catalogs retain `private: true`, always use the part’s API `url` and ignore `public_url`. Credentials are attached only to HTTPS requests to `api.github.com` and removed on cross-host redirects. Public downloads require the attachment’s release to be published; public repository visibility alone does not expose draft attachments.',
          '',
          '| 数据集 | 文件映射 | 压缩 MiB | 内容 |' if zh else '| Dataset | File mappings | Compressed MiB | Contents |','| --- | ---: | ---: | --- |']
        for name,d in c['datasets'].items():
            size=sum(x['bytes'] for x in d['parts'])/2**20
            lines.append(f'| `{name}` | {len(d["files"]):,} | {size:.2f} | {ZH[name] if zh else d["description"]} |')
        lines+=['','## '+('数据身份与离线恢复' if zh else 'Identity and offline restoration'),'']
        lines += [
          '`data/catalog.json` 定义分片顺序、依赖、对象与文件 SHA256。表中压缩体积为各数据集自身分片大小，共享依赖会增加首次下载量。每个分片至多 128 MiB。历史科学记录恢复到 `data/evidence/v1.0.0-rc.1/`，自动化记录恢复到 `data/evidence/v1.0.0-rc.2/`，并保留原相对路径。新运行写入 `outputs/`。' if zh else
          '`data/catalog.json` defines part order, dependencies, object and file SHA256 identities. Compressed sizes count each dataset’s own parts; shared dependencies add to the first download. Parts are at most 128 MiB. Historical scientific records restore beneath `data/evidence/v1.0.0-rc.1/`, and automation records beneath `data/evidence/v1.0.0-rc.2/`, preserving original relative paths. New runs write to `outputs/`.',
          '', '```powershell','litz-research data fetch publication-inputs --offline --cache "C:/Research Cache"','```','',
          '恢复器检查分片、归档成员、对象与最终文件；现有文件通过哈希核验后复用。损坏对象保留明确诊断。外场损耗、输运电阻、几何量及三维诊断使用各自模型定义。当前本地稿件见[学术文件](../publications/README.zh-CN.md)，历史成稿由 `academic-editions` 定位。' if zh else
          'The restorer checks parts, archive membership, objects and final files; existing files are reused after hash verification. Corrupt objects produce explicit diagnostics. Imposed-field loss, transport resistance, geometric quantities and three-dimensional diagnostics retain their model definitions. Current local editions are indexed in [Publications](../publications/README.md); `academic-editions` locates historical editions.','']
        (ROOT/'docs'/('datasets.zh-CN.md' if zh else 'datasets.md')).write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':main()
