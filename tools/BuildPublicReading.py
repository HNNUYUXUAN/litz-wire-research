"""Build complete bilingual reading entries from an explicit publication run."""
from pathlib import Path
import argparse, re
from PIL import Image
from litz_research.common import sha, write, read
ROOT = Path(__file__).resolve().parents[1]

def build(run_id):
    base = ROOT/'outputs'/run_id
    documents = read(base/'document_manifest.json')['documents']
    if len(documents) != 6 or any(d['form'] != 'merged' for d in documents):
        raise ValueError('Six complete bilingual manuscripts are required')
    records = []
    for d in documents:
        source = base/d['markdown']
        target = ROOT/'publications'/d['edition']/d['language']/'README.md'
        target.parent.mkdir(parents=True, exist_ok=True)
        def image(match):
            label, relative = match.groups()
            original = (source.parent/relative).resolve()
            dest = ROOT/'publications/assets'/d['language']/original.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(original) as picture:
                picture.thumbnail((1600,1600))
                picture.convert('RGB').save(dest,optimize=True)
            records.append(dict(path=dest.relative_to(ROOT).as_posix(),source=original.relative_to(ROOT).as_posix(),source_sha256=sha(original),sha256=sha(dest),processing='RGB preview bounded to 1600 pixels'))
            return '!['+label+'](../../assets/'+d['language']+'/'+dest.name+')'
        body = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',image,source.read_text(encoding='utf-8'))
        body = body.replace(d['id']+'.md#','README.md#')
        target.write_text(body,encoding='utf-8')
        records.append(dict(path=target.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),sha256=sha(target)))
    for lang in ['en','zh-CN']:
        zh = lang == 'zh-CN'
        lines = ['# '+('完整学术稿件' if zh else 'Complete research publications'),'',
                 '[English](README.md) · [简体中文](README.zh-CN.md)','',
                 ('三部作品各含中英文完整 Markdown、原生 Wolfram Notebook，以及通用单栏、IEEE 期刊和 IEEE 会议三种 LaTeX/PDF。下列文件为本地构建产物，随交付包提供。' if zh else 'Each work has complete Chinese and English Markdown, a native Wolfram Notebook, and LaTeX/PDF in general single-column, IEEE journal and IEEE conference layouts. Local build artifacts below are supplied in the delivery package.'),'',
                 '| '+('作品 / 语言 | Markdown | Notebook | PDF：单栏 / 期刊 / 会议 |' if zh else 'Work / language | Markdown | Notebook | PDF: single / journal / conference |'),
                 '| --- | --- | --- | --- |']
        for d in documents:
            pdfs = ' · '.join('['+layout+'](../outputs/'+run_id+'/documents/'+d['edition']+'/'+d['language']+'/'+d['id']+'_'+layout+'.pdf)' for layout in ['single','ieee-journal','ieee-conference'])
            lines.append('| '+d['title']+' / '+d['language']+' | [Markdown]('+d['edition']+'/'+d['language']+'/README.md) | [Wolfram](../'+d['notebook']+') | '+pdfs+' |')
        lines += ['',('图件、数字和物理验收保留冻结来源。二维 Maxwell MCP 比较、三维 Ansys 诊断与 A–φ 验收分别叙述。' if zh else 'Figures, quantities and physical acceptance retain their frozen sources. The two-dimensional Maxwell MCP comparison, three-dimensional Ansys diagnostics and A–φ acceptance are treated separately.'),'',
                  '[LaTeX / templates](../latex/README'+('.zh-CN' if zh else '')+'.md) · [Editorial style](../docs/editorial-style'+('.zh-CN' if zh else '')+'.md)','']
        (ROOT/'publications'/('README.zh-CN.md' if zh else 'README.md')).write_text('\n'.join(lines),encoding='utf-8')
    write(ROOT/'publications/manifest.json',dict(source_edition=run_id,approved_specimen='publication_20261013_paper_sample_09',files=records))
    print('Complete manuscripts',len(documents),'preview/source records',len(records))
if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    build(p.parse_args().run_id)
