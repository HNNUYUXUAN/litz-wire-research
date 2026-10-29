"""Build reading editions from canonical LaTeX with Pandoc 3.13 and strict checks."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from .common import resolve_read_path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def write_reading(path, payload):
    """Publish complete reading bytes through a same-directory atomic replacement."""
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload)
        for attempt in range(3):
            try:
                os.replace(temporary, path)
                return
            except OSError as error:
                if os.name != 'nt' or error.errno not in (13, 22) or attempt == 2:
                    raise
                time.sleep(0.2 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)


def command(args, *, text=None, cwd=None):
    return subprocess.run([str(a) for a in args], input=text, capture_output=True, text=True,
                          encoding='utf-8', errors='strict', cwd=cwd, check=True, timeout=120).stdout


def pandoc_path():
    path = Path(sys.executable).parent / 'Library/bin/pandoc.exe'
    selected = str(path) if path.exists() else shutil.which('pandoc')
    if not selected or command([selected, '--version']).splitlines()[0] != 'pandoc 3.13':
        raise ValueError('This publication requires Pandoc 3.13')
    return selected


def tex_escape(text):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
               '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
               '^': r'\textasciicircum{}'}
    return ''.join(mapping.get(c, c) for c in text)


def generate_shared(root, manifest, metrics):
    """Regenerate numeric substitutions and bibliography from their canonical data."""
    directory = root / 'manuscript/generated'
    directory.mkdir(exist_ok=True)
    lines = [r'% Generated from metrics.json; source identities are verified by the builder.',
             r'\newcommand{\metric}[1]{\csname litzmetric#1\endcsname}']
    lines += [r'\expandafter\def\csname litzmetric' + key + r'\endcsname{' + record['formatted'] + '}'
              for key, record in metrics.items()]
    (directory / 'metrics.tex').write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    from .references import publication_references
    for edition in dict.fromkeys(d['edition'] for d in manifest['documents']):
        docs = [d for d in manifest['documents'] if d['edition'] == edition]
        citation_lists = []
        for doc in docs:
            text = '\n'.join((root / path).read_text(encoding='utf-8') for path in [doc['main']] + doc['sections'])
            keys = list(dict.fromkeys(key.strip() for group in re.findall(r'\\cite\{([^{}]+)\}', text) for key in group.split(',')))
            citation_lists.append(keys)
        if len(citation_lists) != 2 or citation_lists[0] != citation_lists[1]:
            raise ValueError('Bilingual citation order differs: ' + edition)
        refs = publication_references(root, citation_lists[0])
        lines = [r'% Generated from references/library.bib.', r'\begin{thebibliography}{99}']
        for ref in refs:
            clean = lambda s: re.sub(r'[{}]', '', str(s))
            source = ', '.join(clean(v) for v in [ref['venue'], ref.get('version'), ref['year']] if v)
            text = ', '.join(clean(a) for a in ref['authors']) + '. ' + clean(ref['title']) + '. ' + source + '.'
            url = 'https://doi.org/' + ref['doi'] if ref.get('doi') else ref.get('url', '')
            lines.append(r'\bibitem{' + ref['id'] + '} ' + tex_escape(text) + (r' \url{' + url + '}' if url else ''))
        (directory / (edition + '-references.tex')).write_bytes('\n'.join(lines + [r'\end{thebibliography}', '']).encode('utf-8'))


def verify_metrics(root, metrics):
    """Recompute mapped observables from the retained numerical inputs."""
    cache = {}
    for key, record in metrics.items():
        path = resolve_read_path(root, record['source'])
        if sha(path) != record['source_sha256']:
            raise ValueError('Changed metric evidence: ' + key)
        if path not in cache:
            with path.open(encoding='utf-8-sig', newline='') as stream:
                cache[path] = list(csv.DictReader(stream)) if path.suffix == '.csv' else json.load(stream)
        data = cache[path]
        locator = record['locator']
        if key == 'coax_spread':
            currents = [complex(float(row['Re_I_RMS_A']), float(row['Im_I_RMS_A'])) for row in data]
            mean = 20 / 640
            value = math.sqrt(sum(abs(i - mean)**2 for i in currents) / 640) / mean
        elif key == 'peec_rac':
            value = float(next(row for row in data if row['case_id'] == 'peec_m80_l064_q4_s12p10')['Rac_ohm_per_axial_m'])
        elif key in ('coax_rdc', 'coax_rac_rdc'):
            parameter = record['parameter_source']
            path = resolve_read_path(root, parameter['path'])
            if sha(path) != parameter['sha256']:
                raise ValueError('Changed conductivity source')
            sigma = json.loads(path.read_text(encoding='utf-8'))['conductivity_S_per_m']
            case = data['cases'][2]
            rdc = 1 / (sigma * case['polygonal_bundle_area_m2'])
            value = rdc if key == 'coax_rdc' else case['bundle_Rac_ohm_per_m'] / rdc
        elif locator.startswith('cases[2].'):
            value = data['cases'][2]
            for field in locator.removeprefix('cases[2].').split('.'):
                value = value[field]
        elif locator in data.get('values', {}):
            value = float(data['values'][locator]) * (0.001 if key != 'q1_loss' else 1)
        else:
            raise ValueError('Unsupported metric locator: ' + locator)
        if not math.isclose(value, record['value'], rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError('Mapped value differs from evidence: ' + key)
        if format(value * record['display_scale'], record['display_format']) != record['formatted']:
            raise ValueError('Formatted value differs from evidence: ' + key)


def expand_inputs(path, root, stack=(), inputs=None):
    path = path.resolve()
    if not path.is_relative_to((root / 'manuscript').resolve()):
        raise ValueError('TeX input escapes the manuscript directory: ' + str(path))
    if path in stack:
        raise ValueError('Cyclic TeX input: ' + str(path))
    if inputs is not None:
        inputs.add(path)
    text = path.read_text(encoding='utf-8')
    # TeX resolves nested inputs against the main document's working directory.
    base = stack[0].parent if stack else path.parent
    return re.sub(r'\\input\{([^{}]+)\}', lambda m: expand_inputs(
        base / (m[1] if Path(m[1]).suffix else m[1] + '.tex'), root, stack + (path,), inputs), text)


def document_inputs(root, doc):
    main = root / doc['main']
    paths = set()
    text = expand_inputs(main, root, inputs=paths)
    for name in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}', text):
        asset = (main.parent / name).resolve()
        if not asset.is_relative_to((root / 'manuscript/assets').resolve()):
            raise ValueError('Figure escapes source assets')
        paths.add(asset)
        paths.add(asset.with_suffix('.png'))
    paths.update([root / 'manuscript/metrics.json', root / 'references/library.bib'])
    if (main.parent / 'IEEEtran.cls').exists():
        paths.add(main.parent / 'IEEEtran.cls')
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths)}


def brace_argument(text, start):
    """Read a balanced TeX argument, preserving nested braces and escaped characters."""
    if text[start] != '{':
        raise ValueError('Expected TeX argument')
    depth, i = 1, start + 1
    while i < len(text):
        if text[i] == '\\':
            i += 2
            continue
        depth += (text[i] == '{') - (text[i] == '}')
        if depth == 0:
            return text[start + 1:i], i + 1
        i += 1
    raise ValueError('Unbalanced TeX argument')


def replace_command(text, name, callback):
    pattern = re.compile(r'\\' + re.escape(name) + r'\s*(?=\{)')
    output, offset = [], 0
    while match := pattern.search(text, offset):
        argument, end = brace_argument(text, match.end())
        output.extend([text[offset:match.start()], callback(argument)])
        offset = end
    return ''.join(output) + text[offset:]


def labels(text):
    mapping = {}
    for kind, prefix in [('equation', 'eq'), ('figure', 'fig'), ('table', 'tab')]:
        count = 0
        for match in re.finditer(r'\\begin\{' + kind + r'\*?\}(.*?)\\end\{' + kind + r'\*?\}', text, re.S):
            count += 1
            tag = re.search(r'\\tag\{([^{}]+)\}', match[1])
            value = tag[1] if tag else str(count)
            for label in re.findall(r'\\label\{([^{}]+)\}', match[1]):
                if label in mapping:
                    raise ValueError('Duplicate label: ' + label)
                mapping[label] = value
    return mapping


def adapt_tex(text, metrics):
    """Translate only documented presentation commands; retain all substantive text."""
    original = text
    refs = labels(text)
    text = re.sub(r'(?<!\\)%[^\n]*', '', text)
    text = replace_command(text, 'metric', lambda key: metrics[key]['formatted'])
    def reference(key, equation=False):
        if key not in refs:
            raise ValueError('Unresolved cross-reference: ' + key)
        value = '(' + refs[key] + ')' if equation else refs[key]
        return r'\hyperlink{' + key + '}{' + value + '}'
    text = replace_command(text, 'eqref', lambda key: reference(key, True))
    text = replace_command(text, 'ref', reference)
    text = text.replace(r'\maketitle', '').replace(r'\appendices', '').replace(r'\appendix', '')
    text = text.replace(r'\begin{IEEEkeywords}', r'\paragraph{Keywords}')
    text = text.replace(r'\end{IEEEkeywords}', '')
    text = text.replace(r'\noindent', '').replace(r'\centering', '')
    text = text.replace('{table*}', '{table}').replace('{figure*}', '{figure}')
    text = replace_command(text, 'thanks', lambda value: ' (' + value + ')')
    text = replace_command(text, 'seqsplit', lambda value: value)
    text = text.replace(r'\allowbreak', '')
    text = text.replace(r'\begingroup', '').replace(r'\endgroup', '').replace(r'\footnotesize', '')
    # tabularx uses X for flexible columns. Pandoc receives the same cells in tabular.
    tabular = r'\begin{tabularx}{\textwidth}{'
    while tabular in text:
        start = text.index(tabular)
        arg_start = start + len(tabular) - 1
        specification, end = brace_argument(text, arg_start)
        count = specification.count('X')
        if not count or specification != r'>{\raggedright\arraybackslash}X' * count:
            raise ValueError('Unsupported tabularx column specification')
        text = text[:start] + r'\begin{tabular}{' + 'l' * count + '}' + text[end:]
    text = text.replace(r'\end{tabularx}', r'\end{tabular}')
    text = re.sub(r'\\begin\{thebibliography\}\{[^{}]*\}', r'\\section*{References}', text)
    text = text.replace(r'\end{thebibliography}', '')
    text = re.sub(r'\\bibitem\{([^{}]+)\}', lambda m: '\n\n' + r'\hypertarget{ref:' + m[1] + '}{} [' + m[1] + '] ', text)
    # Labels on equations become explicit anchors as well as math identities.
    text = re.sub(r'(\\begin\{equation\})(.*?)(\\end\{equation\})', lambda m:
                  ''.join(r'\hypertarget{' + key + '}{}' for key in re.findall(r'\\label\{([^{}]+)\}', m[2])) + m[0], text, flags=re.S)
    return text, {'block_ids': re.findall(r'% block-id: ([\w.]+)', original), 'labels': refs}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def check_raw(value, inside_cite=False):
    if isinstance(value, dict):
        if value.get('t') in ('RawBlock', 'RawInline') and not inside_cite:
            raise ValueError('Unsupported LaTeX content: ' + str(value['c']))
        for child in value.values():
            check_raw(child, inside_cite or value.get('t') == 'Cite')
    elif isinstance(value, list):
        for child in value:
            check_raw(child, inside_cite)


def prepare_ast(ast, main_dir, root):
    check_raw(ast)
    metadata = ast['meta']
    front = []
    if 'title' not in metadata or 'abstract' not in metadata:
        raise ValueError('Title and abstract must be present in the LaTeX master')
    front.append({'t': 'Header', 'c': [1, ['title', [], []], metadata['title']['c']]})
    authors = metadata.get('author', {}).get('c', [])
    for author in authors:
        front.append({'t': 'Para', 'c': author['c']})
    front += [{'t': 'Header', 'c': [2, ['abstract', [], []], [{'t': 'Str', 'c': 'Abstract'}]]}]
    front += metadata['abstract']['c']
    ast['meta'] = {}
    ast['blocks'] = front + ast['blocks']
    for node in walk(ast):
        if node.get('t') == 'Math' and node['c'][0]['t'] == 'DisplayMath':
            math_source = node['c'][1]
            if math_source.startswith(r'\begin{equation}') and math_source.endswith(r'\end{equation}'):
                math_source = math_source.removeprefix(r'\begin{equation}').removesuffix(r'\end{equation}').strip()
                math_source = re.sub(r'\\label\{[^{}]+\}', '', math_source)
                node['c'][1] = math_source
        if node.get('t') == 'Image':
            original = main_dir / node['c'][2][0]
            if not original.resolve().is_relative_to((root / 'manuscript/assets').resolve()) or not original.is_file():
                raise ValueError('Missing or uncontained figure: ' + str(original))
            image = original.with_suffix('.png')
            if not image.exists():
                raise ValueError('Reading figure missing: ' + str(image))
            node['c'][0][2] = []
            node['c'][2][0] = os.path.relpath(image, root / 'publications/reading').replace('\\', '/')
        if node.get('t') == 'Header' and node['c'][1][0] not in ('title', 'abstract'):
            node['c'][0] = 2 if node['c'][1][0] == 'keywords' else node['c'][0] + 1
        if node.get('t') == 'Div' and not node['c'][1]:
            identity = node['c'][0][0]
            node.clear()
            node.update(t='RawBlock', c=['html', '<a id="' + identity + '"></a>'])
    return ast


def signature(ast):
    """Visible prose and mathematics, excluding alternate labels and link destinations."""
    result = {'words': [], 'math': []}
    def visit(value):
        if isinstance(value, dict):
            kind = value.get('t')
            if kind == 'Str':
                result['words'].append(value['c'])
            elif kind == 'Math':
                result['math'].append(re.sub(r'\s+', '', value['c'][1]))
            elif kind == 'Cite':
                result['words'].extend('@' + c['citationId'] for c in value['c'][0])
            elif kind == 'Image':
                visit(value['c'][1])
            elif kind in ('RawBlock', 'RawInline'):
                return
            else:
                for child in value.values():
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(ast['blocks'])
    result['text'] = re.sub(r'\s+', '', ''.join(result.pop('words')))
    return result


def render_markdown(root, doc, pandoc, metrics):
    main = root / doc['main']
    flattened = expand_inputs(main, root)
    adapted, identities = adapt_tex(flattened, metrics)
    ast = json.loads(command([pandoc, '-f', 'latex+raw_tex', '-t', 'json', '-s'], text=adapted, cwd=main.parent))
    ast = prepare_ast(ast, main.parent, root)
    markdown = command([pandoc, '-f', 'json', '-t', 'markdown+pipe_tables+citations+raw_html-raw_tex',
                        '--wrap=none'], text=json.dumps(ast, ensure_ascii=False))
    roundtrip = json.loads(command([pandoc, '-f', 'markdown+citations+raw_html-raw_tex', '-t', 'json'], text=markdown))
    if signature(ast) != signature(roundtrip):
        save(root / 'build/latex-debug' / (doc['id'] + '-source.json'), ast)
        save(root / 'build/latex-debug' / (doc['id'] + '-roundtrip.json'), roundtrip)
        raise ValueError('Markdown roundtrip changes text or mathematics: ' + doc['id'])
    if len(identities['block_ids']) != len(set(identities['block_ids'])):
        raise ValueError('Duplicate paragraph identity in ' + doc['id'])
    for identity in identities['block_ids']:
        if f'id="{identity}"' not in markdown:
            raise ValueError('Lost paragraph identity: ' + identity)
    return '<!-- Generated from ' + doc['main'] + '; edit the LaTeX source. -->\n\n' + markdown, identities


def build(root, run, manifest_path, edition='all', language='all'):
    manifest = json.loads((root / manifest_path).read_text(encoding='utf-8'))
    metrics = json.loads((root / manifest['metrics']).read_text(encoding='utf-8'))
    verify_metrics(root, metrics)
    generate_shared(root, manifest, metrics)
    pandoc = pandoc_path()
    receipt = {'pandoc': '3.13', 'documents': [], 'status': 'in_progress'}
    for doc in manifest['documents']:
        if edition not in ('all', doc['edition']) or language not in ('all', doc['language']):
            continue
        markdown, identities = render_markdown(root, doc, pandoc, metrics)
        target = root / 'publications/reading' / (doc['id'] + '.md')
        target.parent.mkdir(parents=True, exist_ok=True)
        write_reading(target, markdown.encode('utf-8'))
        receipt['documents'].append({'id': doc['id'], 'source': doc['main'], 'source_sha256': sha(root / doc['main']),
                                     'input_hashes': document_inputs(root, doc),
                                     'sections': {s: sha(root / s) for s in doc['sections']},
                                     'markdown': target.relative_to(root).as_posix(), 'markdown_sha256': sha(target),
                                     **identities, 'roundtrip_text_and_math': 'passed'})
        save(run / 'reading-receipt.json', receipt)
        print(doc['id'], 'Markdown passed', flush=True)
    if not receipt['documents']:
        raise ValueError('No matching documents')
    for edition_name in {d['edition'] for d in manifest['documents']}:
        pair = [d for d in receipt['documents'] if d['id'].startswith(edition_name + '_')]
        if len(pair) == 2 and pair[0]['block_ids'] != pair[1]['block_ids']:
            raise ValueError('Bilingual paragraph identities differ: ' + edition_name)
    receipt['status'] = 'passed'
    save(run / 'reading-receipt.json', receipt)
    return receipt


def package(root, run, manifest):
    """Package source, reading text, required assets and original license notices."""
    paths = {root / 'manuscript/preamble.tex', root / manifest['metrics'], root / manifest['bibliography'],
             root / 'manuscript/latex-publication.json', root / 'manuscript/migration-receipt.json'}
    for doc in manifest['documents']:
        paths.update(root / path for path in [doc['main']] + doc['sections'])
        cls = (root / doc['main']).parent / 'IEEEtran.cls'
        if cls.exists():
            paths.add(cls)
        paths.add(root / 'publications/reading' / (doc['id'] + '.md'))
    for folder in ['manuscript/assets', 'manuscript/generated', 'manuscript/data', 'LICENSES']:
        paths.update(p for p in (root / folder).rglob('*') if p.is_file())
    paths.add(root / 'configs/reference_parameters.json')
    paths.add(root / 'configs/reference_values.json')
    target = run / 'Litz-manuscript-sources.zip'
    records = []
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            relative = path.relative_to(root).as_posix()
            archive.write(path, relative)
            records.append({'path': relative, 'sha256': sha(path)})
        archive.writestr('README.md', '# Litz manuscript sources\n\nSix canonical LaTeX masters are listed in manuscript/latex-publication.json. '
                         'Compile each main.tex from its own directory with XeLaTeX three times. '
                         'MiKTeX, Times New Roman and SimSun are external dependencies. '
                         'The report is single-column; the methods and physics papers use IEEE journal. '
                         'Markdown in publications/reading is generated from these sources. '
                         'PDFs are temporary compile/preview products; figure PDFs are required source assets. '
                         'Original license texts are retained under LICENSES and in IEEEtran.cls.\n')
    save(run / 'source-package.json', {'path': target.name, 'sha256': sha(target), 'files': records})
    return target


def verify_page_review(run, compiled):
    path = run / 'page-review.json'
    if not path.exists():
        return 'requires_page_review'
    reviews = json.loads(path.read_text(encoding='utf-8'))
    if any(row.get('visual_review') != 'passed' for row in reviews):
        return 'requires_page_review'
    by_id = {row['document']: row for row in reviews}
    if len(by_id) != len(reviews) or set(by_id) != {row['id'] for row in compiled}:
        raise ValueError('Page review document identities differ from compilation')
    for doc in compiled:
        row = by_id[doc['id']]
        if (row.get('pdf_sha256') != doc['pdf_sha256']
                or row.get('reviewed_pages') != list(range(1, doc['page_count'] + 1))
                or len(row.get('pages', [])) != doc['page_count']):
            raise ValueError('Page review must cover every page of the compiled PDF')
        hashes = row.get('page_hashes', {})
        if set(hashes) != set(row['pages']):
            raise ValueError('Reviewed page image identities are incomplete')
        for relative, digest in hashes.items():
            page = resolve_read_path(run, relative)
            if sha(page) != digest:
                raise ValueError('Reviewed page image changed: ' + relative)
    return 'passed'


def verify_run(root, run):
    receipt = json.loads((run / 'reading-receipt.json').read_text(encoding='utf-8'))
    if receipt['status'] != 'passed':
        raise ValueError('Reading build did not pass')
    for doc in receipt['documents']:
        identities = {doc['source']: doc['source_sha256'], doc['markdown']: doc['markdown_sha256'],
                      **doc['sections'], **doc.get('input_hashes', {})}
        for path, digest in identities.items():
            if sha(root / path) != digest:
                raise ValueError('Run input or output changed; use a new run ID: ' + path)
    compile_path = run / 'compile-receipt.json'
    if compile_path.exists():
        compiled = json.loads(compile_path.read_text(encoding='utf-8'))
        for doc in compiled:
            if not doc['compiled'] or doc['layout_checks'] != 'passed':
                raise ValueError('Compilation or layout check failed: ' + doc['id'])
            if sha(run / 'pdf' / doc['id'] / 'main.pdf') != doc['pdf_sha256']:
                raise ValueError('Compiled PDF identity changed')
            for path, digest in doc['input_hashes'].items():
                if sha(root / path) != digest:
                    raise ValueError('Compiled source dependency changed: ' + path)
    result = {'reading': 'passed', 'compilation': 'passed' if compile_path.exists() else 'not_run',
              'visual_review': verify_page_review(run, compiled) if compile_path.exists() else 'requires_page_review',
              'documents': len(receipt['documents'])}
    save(run / 'verification.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--source-manifest', default='manuscript/latex-publication.json')
    parser.add_argument('--edition', choices=['all', 'report', 'automation', 'paper'], default='all')
    parser.add_argument('--language', choices=['all', 'en', 'zh-CN'], default='all')
    parser.add_argument('--stage', choices=['preflight', 'documents', 'pdf', 'verify', 'package', 'all'], default='documents')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.run_id) or args.run_id in ('.', '..'):
        raise ValueError('Invalid run ID')
    run = root / 'outputs' / args.run_id
    manifest = json.loads((root / args.source_manifest).read_text(encoding='utf-8'))
    if args.stage == 'preflight':
        verify_metrics(root, json.loads((root / manifest['metrics']).read_text(encoding='utf-8')))
        print('Pandoc 3.13:', pandoc_path())
        return 0
    if args.stage in ('documents', 'all'):
        if (run / 'reading-receipt.json').exists():
            raise ValueError('Reading build already exists; use a new run ID')
        build(root, run, args.source_manifest, args.edition, args.language)
    if args.stage in ('pdf', 'all'):
        if args.edition != 'all' or args.language != 'all':
            raise ValueError('The compile stage validates all six masters together')
        result = subprocess.run([sys.executable, '-X', 'utf8', str(root / 'tools/CompileLatexMasters.py'), '--run-id', args.run_id], cwd=root)
        if result.returncode:
            return result.returncode
    if args.stage in ('verify', 'all', 'package'):
        verify_run(root, run)
    if args.stage in ('package', 'all'):
        if len(json.loads((run / 'reading-receipt.json').read_text(encoding='utf-8'))['documents']) != 6:
            raise ValueError('Source packaging requires all six reading manuscripts')
        package(root, run, manifest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
