"""Build a deterministic license companion for the frozen publication archives."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'LICENSES/publication-companion/'


def build(root, output):
    paths = subprocess.check_output(['git', '-c', 'safe.directory=' + str(root), '-C', str(root),
                                     'ls-files', '-z', '--', PREFIX]).decode('utf-8').split('\0')
    paths = sorted(p for p in paths if p)
    if not paths or PREFIX + 'package-licenses.json' not in paths:
        raise ValueError('Tracked companion content is required')
    output.parent.mkdir(parents=True, exist_ok=True)
    members = []
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in paths:
            data = (root/path).read_bytes()
            name = path[len(PREFIX):]
            info = zipfile.ZipInfo(name, date_time=(2026,10,20,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    with zipfile.ZipFile(output) as bundle:
        if bundle.namelist() != [m['path'] for m in members]:
            raise ValueError('Companion membership differs after writing')
        for item in members:
            if hashlib.sha256(bundle.read(item['path'])).hexdigest() != item['sha256']:
                raise ValueError('Companion member verification failed')
    return dict(schema_version=1, release_tag='v1.0.0-rc.2',
                release_url='https://github.com/HNNUYUXUAN/litz-wire-research/releases',
                artifacts=[dict(name=output.name, bytes=output.stat().st_size,
                                sha256=hashlib.sha256(output.read_bytes()).hexdigest())],
                source_root=PREFIX, members=members)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    manifest = build(args.root.resolve(), args.output.resolve())
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(manifest['artifacts'], ensure_ascii=False))
