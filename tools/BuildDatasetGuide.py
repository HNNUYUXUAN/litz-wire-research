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
          '通过 CLI 选择所需路线，依赖会一并恢复。还原后核对文件身份：' if zh else 'Select the required route through the CLI. Dependencies are restored with it; verify file identities after restoration:',
          '', '```powershell','litz-research data list','litz-research data fetch publication-inputs','litz-research data verify publication-inputs','```','',
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
