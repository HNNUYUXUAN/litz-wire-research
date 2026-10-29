"""Build current LaTeX/Markdown navigation from verified portable receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote
from PublicationContract import validate_current_edition

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = 'provenance/current-publication/reading-receipt.json'

def load(root, path):
    return json.loads((root / path).read_text(encoding='utf-8-sig'))

def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'

def generate(root):
    receipt = load(root, RECEIPT)
    if receipt.get('status') != 'passed' or receipt.get('pandoc') != '3.13':
        raise ValueError('A passed Pandoc 3.13 reading receipt is required')
    source = receipt['source_manifest']
    source_path = (root / source).resolve()
    if not source_path.is_relative_to(root.resolve()):
        raise ValueError('Source manifest must remain inside the checkout')
    manifest = load(root, source)
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != receipt['source_manifest_sha256']:
        raise ValueError('Source manifest changed without a verified build')
    records = {row['id']: row for row in receipt['documents']}
    if len(records) != len(receipt['documents']):
        raise ValueError('Duplicate reading receipt identity')
    documents = []
    for doc in manifest['documents']:
        record = records.get(doc['id'])
        if not record or record['source'] != doc['main'] or list(record['sections']) != doc['sections']:
            raise ValueError('Source identity or section order differs: ' + doc['id'])
        documents.append(dict(id=doc['id'], edition=doc['edition'], language=doc['language'],
            layout=doc['layout'], main=doc['main'], main_sha256=record['source_sha256'],
            sections=record['sections'], input_hashes=record['input_hashes'],
            markdown=record['markdown'], markdown_sha256=record['markdown_sha256']))
    index = dict(schema_version=3, run_id=receipt['run_id'], source_edition=receipt['run_id'],
        source_manifest=source, source_manifest_sha256=receipt['source_manifest_sha256'],
        reading_receipt=RECEIPT, documents=documents)
    errors = validate_current_edition(root, index)
    if errors:
        raise ValueError('; '.join(errors))
    for doc in documents:
        content = (root / doc['markdown']).read_text(encoding='utf-8-sig')
        title = next(line[2:] for line in content.splitlines() if line.startswith('# '))
        doc['title'] = re.sub(r'\s*\{#title\}\s*$', '', title)
    result = {'docs/current-edition.json': encode(index)}
    result['publications/manifest.json'] = encode(dict(schema_version=3, source_edition=receipt['run_id'],
        source_manifest=source, reading_receipt=RECEIPT,
        files=[dict(path=d['markdown'], sha256=d['markdown_sha256'], source=d['main']) for d in documents]))
    repository = load(root, 'data/catalog.json')['repository']
    if (not isinstance(repository, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository)
            or any(part in {'.', '..'} for part in repository.split('/'))):
        raise ValueError('Expected a GitHub owner/repository identity')
    base = 'https://github.com/' + repository + '/releases/'
    migration_path=root/'provenance/repository-migration.json'
    historical_base=base
    if migration_path.is_file():
        archived=load(root,'provenance/repository-migration.json')['archive_repository']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',archived) or any(x in {'.','..'} for x in archived.split('/')):
            raise ValueError('Invalid archive repository identity')
        historical_base='https://github.com/'+archived+'/releases/'
    online = load(root, 'provenance/editorial/online-assets.json')
    for lang in ('en', 'zh-CN'):
        zh = lang == 'zh-CN'
        suffix = '.zh-CN' if zh else ''
        intro = ('三份作品各有中英文 LaTeX 主稿和生成的 Markdown 阅读稿。完整报告采用单栏，两篇论文采用 IEEE journal 版式。' if zh else
                 'Three works each provide English and Chinese LaTeX masters and generated Markdown readings. The report uses one column; the two papers use the IEEE journal layout.')
        table = [('| 稿件 | LaTeX 主稿 | 阅读稿 | PDF |' if zh else '| Manuscript | LaTeX master | Reading | PDF |'), '| --- | --- | --- | --- |']
        for doc in documents:
            table.append(f"| {doc['title']} / {doc['language']} | [LaTeX](../{doc['main']}) | [Markdown]({Path(doc['markdown']).relative_to('publications').as_posix()}) | [PDF]({base}download/v1.0.0/Litz-{doc['id']}.pdf) |")
        footer = ['', f'[LaTeX source package]({base}download/v1.0.0/Litz-manuscript-sources.zip)', '', f'[JSON](../docs/current-edition.json) · [Build](../manuscript/README.md) · [Delivery](DELIVERY{suffix}.md) · [History](HISTORY{suffix}.md)', '']
        for name, title in [('README', '科研稿件' if zh else 'Research publications'), ('ONLINE', '在线阅读与源码' if zh else 'Online readings and sources')]:
            result[f'publications/{name}{suffix}.md'] = '\n'.join(['# '+title, '', '[English](README.md) · [简体中文](README.zh-CN.md)', '', intro, ''] + table + footer)
        result[f'publications/DELIVERY{suffix}.md'] = '\n'.join([
            '# '+('稿件构建与验收' if zh else 'Publication build and verification'), '',
            ('正文、摘要、关键词、公式及图注由 LaTeX 维护；Markdown 由固定版本 Pandoc 3.13 生成。PDF 用于编译与逐页检查。' if zh else
             'LaTeX maintains text, abstracts, keywords, equations and captions. Pandoc 3.13 generates Markdown. PDFs support compilation and page review.'), '',
            f"Build: `{receipt['run_id']}`", '', f'- [Reading and input identities](../{RECEIPT})',
            '- [Source manifest](../manuscript/latex-publication.json)',
            '- [Build commands and page-review procedure](../manuscript/README.md)',
            '- [Migration and retained evidence](../manuscript/migration-receipt.json)', '',
            ('转换验收与编译验收分别记录；逐页视觉检查按构建保存，不能由编译成功替代。' if zh else
             'Conversion and compilation have separate receipts. Page review belongs to a particular build and requires visual inspection.'), '',
            f'[Read](README{suffix}.md) · [Historical releases](HISTORY{suffix}.md)', ''])
        history = ['# '+('历史发布附件' if zh else 'Historical release assets'), '',
            ('以下附件保留原发布版本身份和许可；当前维护稿件见[稿件入口](README.zh-CN.md)。' if zh else
             'These assets retain their original release identities and licenses. See [publications](README.md) for current sources.'), '',
            f"[{online['release_tag']}]({historical_base}tag/{quote(online['release_tag'], safe='')})", '']
        groups = [online]
        if (root / 'provenance/maintenance/supplemental-assets.json').is_file():
            groups.append(load(root, 'provenance/maintenance/supplemental-assets.json'))
        for group in groups:
            for item in group['artifacts']:
                history.append(f"- [{item['name']}]({historical_base}download/{quote(group['release_tag'], safe='')}/{quote(item['name'], safe='')})")
        history += ['', '[SHA256 / bytes](../provenance/editorial/online-assets.json)',
                    '[License companion](../LICENSES/publication-companion/README.md)', '']
        result[f'publications/HISTORY{suffix}.md'] = '\n'.join(history)
    for doc in documents:
        result[f"publications/{doc['edition']}/{doc['language']}/README.md"] = '\n'.join([
            '# ' + doc['title'], '', f"[Markdown reading](../../reading/{doc['id']}.md)", '',
            f"[LaTeX master](../../../{doc['main']})", ''])
    return result

def build(root=ROOT, check=False):
    stale = []
    for relative, content in generate(root).items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_bytes() != content.encode('utf-8'):
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode('utf-8'))
    if stale:
        raise ValueError('Stale publication indexes: ' + ', '.join(stale))
    print('Publication indexes current: 6 LaTeX masters and 6 Markdown readings')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    build(args.root.resolve(), args.check)
