"""Compile canonical sources into a run directory and retain page diagnostics."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/research'))
from litz_research.latex_runtime import environment
from litz_research.latex_publication import save, sha, document_inputs


def worker(run, documents):
    env = environment()
    compiler = shutil.which('xelatex', path=env['PATH'])
    if not compiler:
        raise RuntimeError('XeLaTeX is required')
    version = subprocess.check_output([compiler, '--version'], env=env, text=True, encoding='utf-8').splitlines()[:3]
    save(run / 'compiler.json', {'executable': compiler, 'version': version})
    records = []
    for doc in documents:
        main = ROOT / doc['main']
        output = run / 'pdf' / doc['id']
        output.mkdir(parents=True, exist_ok=True)
        input_hashes = document_inputs(ROOT, doc)
        steps = []
        for index in range(3):
            start = time.monotonic()
            with (output / f'compile-{index+1}.txt').open('w', encoding='utf-8') as log:
                result = subprocess.run([compiler, '--interaction=nonstopmode', '--halt-on-error', '--file-line-error',
                                         '--no-shell-escape', '--output-directory=' + str(output), main.name],
                                        cwd=main.parent, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
            steps.append({'pass': index + 1, 'exit_code': result.returncode, 'seconds': time.monotonic() - start})
            if result.returncode:
                break
        log_path = output / 'main.log'
        log = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else ''
        diagnostics = re.findall(r'^(?:Overfull \\[hv]box|Missing character:|.*(?:Citation|Reference).*undefined|.*undefined references).*$', log, re.M)
        pdf = output / 'main.pdf'
        if input_hashes != document_inputs(ROOT, doc):
            raise RuntimeError('Source changed during compilation: ' + doc['id'])
        record = {'id': doc['id'], 'source_sha256': sha(main), 'input_hashes': input_hashes, 'steps': steps,
                  'diagnostics': diagnostics, 'compiled': result.returncode == 0 and pdf.exists(),
                  'layout_checks': 'passed' if not diagnostics and result.returncode == 0 else 'failed'}
        if pdf.exists() and result.returncode == 0:
            from pypdf import PdfReader
            pages = PdfReader(pdf).pages
            record.update(pdf_sha256=sha(pdf), page_count=len(pages),
                          page_text_lengths=[len(p.extract_text() or '') for p in pages])
        records.append(record)
        save(run / 'compile-receipt.json', records)
        print(doc['id'], record['compiled'], record['layout_checks'], len(diagnostics), flush=True)
    return int(any(not r['compiled'] or r['layout_checks'] != 'passed' for r in records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--document')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run_id):
        raise ValueError('Invalid run ID')
    run = ROOT / 'outputs' / args.run_id
    run.mkdir(parents=True, exist_ok=True)
    docs = json.loads((ROOT / 'manuscript/latex-publication.json').read_text(encoding='utf-8'))['documents']
    docs = [d for d in docs if not args.document or d['id'] == args.document]
    if not docs:
        raise ValueError('Unknown document')
    if args.worker:
        return worker(run, docs)
    import psutil
    import PreManuscriptClosure as control
    process = psutil.Process()
    eligible = process.cpu_affinity()
    process.cpu_affinity(eligible[:8])
    free = psutil.virtual_memory().available
    budget = min(24 * 2**30, free - 8 * 2**30)
    if budget <= 0:
        raise RuntimeError('8 GiB system reserve unavailable')
    monitor = run / 'monitor'
    monitor.mkdir(exist_ok=False)
    save(monitor / 'policy.json', {'cpu_affinity': eligible[:8], 'memory_budget': budget,
                                 'system_reserve_bytes': 8 * 2**30})
    env = dict(environment(), PYTHONUTF8='1', LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES=str(8 * 2**30))
    command = [sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), '--run-id', args.run_id, '--worker']
    if args.document:
        command += ['--document', args.document]
    return control.run_custom_monitored(command, monitor, env, budget).returncode


if __name__ == '__main__':
    raise SystemExit(main())
