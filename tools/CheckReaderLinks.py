"""Validate relative Markdown reader links against Git-tracked files.

Historical outputs, provenance snapshots and original problem material keep their
original identities. URL availability and heading anchors are separate checks.
"""
import argparse
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit

READER_ROOTS = {'docs', 'publications', 'automation', 'models', 'adapters',
                'references', 'latex', 'LICENSES', '.github', 'manuscript'}
LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+"[^"\n]*")?\s*\)')


def check(root, tracked):
    issues = []
    files = [p for p in sorted(tracked) if p.endswith('.md') and
             ('/' not in p or p.split('/')[0] in READER_ROOTS)]
    checked = 0
    for path in files:
        text = (root / path).read_text(encoding='utf-8-sig')
        text = re.sub(r'```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~', '', text, flags=re.S)
        text = re.sub(r'`[^`\n]*`', '', text)
        for match in LINK.finditer(text):
            target = match.group(1).strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            checked += 1
            target_path = unquote(parsed.path)
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(path), target_path))
            good = relative in tracked or any(p.startswith(relative.rstrip('/') + '/') for p in tracked)
            if relative.startswith('../') or target_path.startswith('/') or not good:
                issues.append(dict(source=path, target=target, resolved=relative))
    return dict(schema_version=1, status='failed' if issues else 'passed',
                scope='tracked_reader_markdown_relative_paths', markdown_files=len(files),
                relative_links=checked, failed_links=issues,
                excluded_archives=['outputs/', 'provenance/', 'originals/', 'problem/'],
                external_urls_and_heading_anchors='not_checked')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    rows = subprocess.check_output(['git', '-c', 'safe.directory=' + str(root), '-C', str(root), 'ls-files', '-z'])
    tracked = {path for path in rows.decode('utf-8').split('\0') if path and (root / path).is_file()}
    result = check(root, tracked)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return bool(result['failed_links'])


if __name__ == '__main__':
    raise SystemExit(main())
