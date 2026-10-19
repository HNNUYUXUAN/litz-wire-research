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
    write(ROOT/'publications/manifest.json',dict(source_edition=run_id,approved_specimen='publication_20261013_paper_sample_09',files=records))
    from BuildPublicationIndex import build as build_index
    delivery_path = ROOT/'provenance/editorial/delivery-manifest.json'
    if delivery_path.exists() and read(delivery_path)['run_id'] == run_id:
        build_index(ROOT)
    else:
        print('Refresh delivery and online asset manifests, then run BuildPublicationIndex.py')
    print('Complete manuscripts',len(documents),'preview/source records',len(records))
if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    build(p.parse_args().run_id)
