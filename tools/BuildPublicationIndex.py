"""Generate the current reading index from frozen delivery and online identities.

No generated PDF, Notebook, solver, or restored evidence is needed. --check is
suitable for a clean source checkout and never changes files.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = ('single', 'ieee-journal', 'ieee-conference')


def load(root, path):
    return json.loads((root / path).read_text(encoding='utf-8-sig'))


def generate(root):
    delivery = load(root, 'provenance/editorial/delivery-manifest.json')
    online = load(root, 'provenance/editorial/online-assets.json')
    reading = load(root, 'publications/manifest.json')
    if delivery['run_id'] != reading['source_edition']:
        raise ValueError('Reading and delivery run identities differ')
    artifacts = delivery['artifacts']
    remote = online['artifacts']
    def artifact(filename):
        matches = [a for a in artifacts if Path(a['path']).name == filename]
        if len(matches) != 1:
            raise ValueError('Expected one delivery artifact: ' + filename)
        source = matches[0]
        assets = [a for a in remote if a['name'].endswith('_' + filename)]
        if len(assets) != 1 or any(assets[0][k] != source[k] for k in ('sha256', 'bytes')):
            raise ValueError('Online identity differs from delivery: ' + filename)
        return dict(local_path=source['path'], asset_name=assets[0]['name'],
                    sha256=source['sha256'], bytes=source['bytes'])
    documents = []
    for edition in ('report', 'automation', 'paper'):
        for language in ('en', 'zh-CN'):
            identity = edition + '_' + language
            markdown = f'publications/{edition}/{language}/README.md'
            content = (root / markdown).read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            records = [r for r in reading['files'] if r['path'] == markdown]
            if len(records) != 1 or records[0]['sha256'] != digest:
                raise ValueError('Reading manuscript changed without a build: ' + markdown)
            title = next(s[2:] for s in content.decode('utf-8-sig').splitlines() if s.startswith('# '))
            documents.append(dict(id=identity, edition=edition, language=language,
                                  title=title, markdown=markdown, markdown_sha256=digest,
                                  notebook=artifact(identity + '.nb'),
                                  pdfs={layout: artifact(identity + '_' + layout + '.pdf') for layout in LAYOUTS}))
    index = dict(schema_version=2, run_id=delivery['run_id'], source_edition=delivery['run_id'],
                 release=dict(tag=online['release_tag'], url=online['release_url']), documents=documents)
    result = {'docs/current-edition.json': json.dumps(index, ensure_ascii=False, indent=2) + '\n'}
    for language in ('en', 'zh-CN'):
        zh = language == 'zh-CN'
        suffix = '.zh-CN' if zh else ''
        lines = ['# ' + ('完整学术稿件' if zh else 'Complete research publications'), '',
                 '[English](README.md) · [简体中文](README.zh-CN.md)', '',
                 ('三部作品各有中英文完整正文和原生 Wolfram Notebook。每份稿件另有通用单栏、IEEE 期刊及 IEEE 会议三种 LaTeX/PDF。' if zh else 'Each of the three works has complete English and Chinese text and a native Wolfram Notebook, plus general single-column, IEEE journal and IEEE conference LaTeX/PDF editions.'), '',
                 ('| 作品 / 语言 | 在线正文 | PDF、Notebook 与源码 |' if zh else '| Work / language | Online text | PDFs, Notebook and sources |'),
                 '| --- | --- | --- |']
        for doc in documents:
            lines.append(f"| {doc['title']} / {doc['language']} | [Markdown]({doc['edition']}/{doc['language']}/README.md) | [" + ('附件索引' if zh else 'Asset index') + f"](ONLINE{suffix}.md) |")
        lines += ['', ('在附件索引中按稿件 ID 和版式选择下载；各文件的大小与 SHA256 记录于机器索引。' if zh else 'Choose an asset by manuscript ID and layout in the attachment index; file sizes and SHA256 identities are recorded in the machine index.'), '',
                  f'[JSON](../docs/current-edition.json) · [LaTeX / templates](../latex/README{suffix}.md) · [Delivery](DELIVERY{suffix}.md)', '',
                  ('图件、数字和物理验收采用冻结来源。二维 Maxwell MCP 比较、三维 Ansys 诊断和 A–φ 验收分别说明其条件与结论。' if zh else 'Figures, quantities and physical acceptance use frozen sources. The 2D Maxwell MCP comparison, 3D Ansys diagnostics and A–φ acceptance each retain their conditions and conclusions.'), '']
        result[f'publications/README{suffix}.md'] = '\n'.join(lines)
        lines = ['# ' + ('稿件交付与校验' if zh else 'Publication delivery and verification'), '',
                 '[English](DELIVERY.md) · [简体中文](DELIVERY.zh-CN.md)', '',
                 ('三部作品含六份完整 Markdown、六份原生 Wolfram Notebook、十八份 LaTeX/PDF 和六份可编辑模板。' if zh else 'Three works provide six complete Markdown manuscripts, six native Wolfram Notebooks, eighteen LaTeX/PDF editions and six editable templates.'), '',
                 f'- [Markdown](README{suffix}.md)',
                 f'- [' + ('附件下载及文件名' if zh else 'Downloads and asset names') + f'](ONLINE{suffix}.md)',
                 '- [SHA256 / bytes](../provenance/editorial/online-assets.json)',
                 '- [Build manifest](../provenance/editorial/delivery-manifest.json)', '',
                 ('完整交付、独立 LaTeX 源码和视觉候选分别打包；所有下载入口见附件索引。本地复现后的路径由 `docs/current-edition.json` 的 `local_path` 给出。' if zh else 'The complete delivery, standalone LaTeX sources and visual candidates are separate packages listed in the attachment index. After local restoration, `local_path` in `docs/current-edition.json` identifies each file.'), '',
                 ('构建验收记录涵盖 240 页 PDF、84 个 Notebook 渲染片段及独立目录中的 24 份稿件与模板编译。21 类科学图从保存证据重新制图。' if zh else 'Build acceptance records cover 240 PDF pages, 84 Notebook render chunks, and independent compilation of 24 manuscripts and templates. The 21 scientific figure families were redrawn from saved evidence.'), '',
                 '- [Visual review](../provenance/editorial/visual-review.json)',
                 '- [Standalone compilation](../provenance/editorial/standalone-compile-receipt.json)', '']
        result[f'publications/DELIVERY{suffix}.md'] = '\n'.join(lines)
        lines = ['# ' + ('在线稿件与附件' if zh else 'Online manuscripts and attachments'), '',
                 '[English](ONLINE.md) · [简体中文](ONLINE.zh-CN.md)', '',
                 ('完整 Markdown 可在线阅读。PDF、Notebook 和源码包见下方 Release 的 Assets；访问私有仓库或草稿附件需使用有权限的账号登录。' if zh else 'Read complete Markdown manuscripts online. PDFs, Notebooks and source packages are in the release Assets below. Access to a private repository or draft assets requires signing in with repository access.'), '',
                 f"[{online['release_tag']} · Assets]({online['release_url']})", '',
                 ('| 作品 / 语言 | 在线正文 | 附件文件名前缀 |' if zh else '| Work / language | Online text | Asset filename prefix |'),
                 '| --- | --- | --- |']
        for doc in documents:
            stem = doc['notebook']['asset_name'][:-3]
            if any(doc['pdfs'][layout]['asset_name'] != stem + '_' + layout + '.pdf' for layout in LAYOUTS):
                raise ValueError('Asset naming does not share a manuscript prefix: ' + doc['id'])
            lines.append(f"| {doc['title']} / {doc['language']} | [Markdown]({doc['edition']}/{doc['language']}/README.md) | `{stem}` |")
        lines += ['', ('每个前缀分别加 `.nb`、`_single.pdf`、`_ieee-journal.pdf` 或 `_ieee-conference.pdf`，对应六份 Notebook 和十八份 PDF。' if zh else 'Append `.nb`, `_single.pdf`, `_ieee-journal.pdf` or `_ieee-conference.pdf` to each prefix to identify six Notebooks and eighteen PDFs.'), '']
        for item in remote:
            if item['name'].endswith('.zip'):
                lines.append(f"- `{item['name']}`")
        lines += ['', '[SHA256 / bytes](../provenance/editorial/online-assets.json) · [JSON index](../docs/current-edition.json)', '']
        result[f'publications/ONLINE{suffix}.md'] = '\n'.join(lines)
    return result


def build(root=ROOT, check=False):
    stale = []
    for path, text in generate(root).items():
        target = root / path
        if check:
            if not target.is_file() or target.read_bytes() != text.encode('utf-8'):
                stale.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode('utf-8'))
    if stale:
        raise ValueError('Stale publication indexes: ' + ', '.join(stale))
    print('Publication indexes current: 6 manuscripts, 6 Notebooks, 18 PDFs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    build(args.root.resolve(), args.check)
