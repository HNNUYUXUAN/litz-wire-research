"""Select a compiled six-manuscript build for portable reading navigation.

Compilation and conversion must pass. Page-review status remains explicit and
is not promoted by selecting a build. Historical run receipts stay unchanged.
"""
import argparse
import json
from pathlib import Path
import re

from litz_research.latex_publication import save, sha, verify_run
from BuildPublicationIndex import build


def select(root, run_id):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', run_id) or run_id in ('.', '..'):
        raise ValueError('Invalid run ID')
    run = root / 'outputs' / run_id
    verification = verify_run(root, run)
    reading = json.loads((run / 'reading-receipt.json').read_text(encoding='utf-8-sig'))
    compiled = json.loads((run / 'compile-receipt.json').read_text(encoding='utf-8-sig'))
    ids = {f'{work}_{lang}' for work in ('report', 'automation', 'paper') for lang in ('en', 'zh-CN')}
    if (len(reading['documents']) != 6 or {d['id'] for d in reading['documents']} != ids
            or len(compiled) != 6 or {d['id'] for d in compiled} != ids):
        raise ValueError('A complete six-manuscript build is required')
    if any(not row['compiled'] or row['layout_checks'] != 'passed' for row in compiled):
        raise ValueError('Compilation and layout diagnostics must pass')
    manifest = 'manuscript/latex-publication.json'
    reading.update(run_id=run_id, source_manifest=manifest, source_manifest_sha256=sha(root / manifest))
    public = root / 'provenance/current-publication'
    save(public / 'reading-receipt.json', reading)
    save(public / 'compilation.json', {
        'run_id': run_id, 'status': 'passed', 'scope': 'compilation_and_automated_layout_checks',
        'visual_review': verification['visual_review'],
        'documents': [{k: row[k] for k in ('id', 'source_sha256', 'input_hashes', 'compiled',
                                          'layout_checks', 'pdf_sha256', 'page_count', 'diagnostics')}
                      for row in compiled]})
    review = json.loads((run / 'page-review.json').read_text(encoding='utf-8')) if (run / 'page-review.json').exists() else []
    save(public / 'visual-review.json', {
        'run_id': run_id, 'status': verification['visual_review'],
        'page_count': sum(row['page_count'] for row in compiled),
        'documents': [{key: row[key] for key in ('document', 'pdf_sha256', 'reviewed_pages',
                                                'page_hashes', 'method', 'findings') if key in row}
                      for row in review]})
    build(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    select(Path(__file__).resolve().parents[1], args.run_id)
