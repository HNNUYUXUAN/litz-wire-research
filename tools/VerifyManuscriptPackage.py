"""Extract and compile all packaged manuscripts in a Chinese and space path."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from litz_research.latex_publication import save, sha
from litz_research.latex_runtime import environment
from litz_research.tasks import bounded_process

ROOT = Path(__file__).resolve().parents[1]


def worker(source_run, destination):
    import pypdfium2 as pdfium
    receipt = json.loads((source_run / 'source-package.json').read_text(encoding='utf-8'))
    package = source_run / receipt['path']
    if sha(package) != receipt['sha256']:
        raise ValueError('Package hash changed')
    extracted = destination / '中文 独立源码'
    extracted.mkdir(exist_ok=False)
    with zipfile.ZipFile(package) as archive:
        for name in archive.namelist():
            target = (extracted / name).resolve()
            if not target.is_relative_to(extracted.resolve()):
                raise ValueError('Package member escapes destination')
        archive.extractall(extracted)
    for item in receipt['files']:
        if sha(extracted / item['path']) != item['sha256']:
            raise ValueError('Extracted file hash mismatch: ' + item['path'])
    manifest = json.loads((extracted / 'manuscript/latex-publication.json').read_text(encoding='utf-8'))
    env = environment()
    compiler = shutil.which('xelatex', path=env['PATH'])
    if not compiler:
        raise RuntimeError('XeLaTeX missing')
    records = []
    for document in manifest['documents']:
        main = extracted / document['main']
        output = destination / 'pdf' / document['id']
        output.mkdir(parents=True)
        for index in range(3):
            with (output / f'pass-{index + 1}.txt').open('w', encoding='utf-8') as log:
                subprocess.run([compiler, '--interaction=nonstopmode', '--halt-on-error', '--file-line-error',
                                '--no-shell-escape', '--output-directory=' + str(output), main.name],
                               cwd=main.parent, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=300)
        log = (output / 'main.log').read_text(encoding='utf-8', errors='replace')
        if re.search(r'Overfull \\[hv]box|Missing character:|undefined references', log):
            raise ValueError('Package compilation diagnostics: ' + document['id'])
        original = pdfium.PdfDocument(source_run / 'pdf' / document['id'] / 'main.pdf')
        rebuilt = pdfium.PdfDocument(output / 'main.pdf')
        if len(original) != len(rebuilt):
            raise ValueError('Package page count differs')
        for number in range(len(original)):
            before = original[number].render(scale=1).to_pil()
            after = rebuilt[number].render(scale=1).to_pil()
            if before.size != after.size or before.tobytes() != after.tobytes():
                raise ValueError(f'Package rendered page differs: {document["id"]} / {number + 1}')
        records.append({'id': document['id'], 'status': 'passed', 'pages': len(original),
                        'pdf_sha256': sha(output / 'main.pdf'), 'rendered_pixels_match_reviewed_build': True})
        original.close()
        rebuilt.close()
        save(destination / 'receipt.json', {'status': 'in_progress', 'documents': records})
        print(document['id'], 'passed', flush=True)
    save(destination / 'receipt.json', {'status': 'passed', 'source_package_sha256': receipt['sha256'],
                                      'path_case': 'Chinese characters and spaces', 'documents': records})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    for value in (args.source_run, args.run_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
            raise ValueError('Invalid run ID')
    destination = ROOT / 'outputs' / args.run_id
    if args.worker:
        worker(ROOT / 'outputs' / args.source_run, destination)
        return 0
    destination.mkdir(exist_ok=False)
    monitor = destination / 'monitor'
    monitor.mkdir()
    command = [sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), '--source-run', args.source_run,
               '--run-id', args.run_id, '--worker']
    result = bounded_process(command, ROOT, monitor, dict(environment(), PYTHONUTF8='1'),
                             {'cpu_threads': 8, 'task_memory_bytes': 24 * 2**30,
                              'system_reserve_bytes': 8 * 2**30, 'timeout_seconds': 1800})
    save(destination / 'process.json', result)
    return int(result['actual_exit_code'] != 0)


if __name__ == '__main__':
    raise SystemExit(main())
