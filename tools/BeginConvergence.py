"""Preserve the exact source checkout before a convergence campaign."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


def begin(root, run_id):
    root = Path(root).resolve()
    out = root / 'outputs' / run_id
    out.mkdir(parents=True, exist_ok=False)
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.quotepath=false', *args], cwd=root)
    def save(name, data):
        (out / name).write_bytes(data)
    save('status.txt', git('status', '--porcelain=v1'))
    save('unstaged.patch', git('diff', '--binary'))
    save('staged.patch', git('diff', '--cached', '--binary'))
    save('refs.txt', git('show-ref'))
    index = root / '.git' / 'index'
    if index.is_file():
        shutil.copyfile(index, out / 'index.snapshot')
    names = set(git('ls-files', '-z', '--cached', '--others', '--exclude-standard').decode('utf-8').split('\0'))
    records = []
    with zipfile.ZipFile(out / 'source-worktree.zip', 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for name in sorted(names - {''}):
            path = root / name
            if not path.is_file():
                continue
            data = path.read_bytes()
            archive.writestr(name, data)
            records.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    with zipfile.ZipFile(out / 'source-worktree.zip') as archive:
        for record in records:
            assert hashlib.sha256(archive.read(record['path'])).hexdigest() == record['sha256']
    subprocess.run(['git', 'bundle', 'create', str(out / 'history.bundle'), '--all'], cwd=root, check=True)
    check = subprocess.run(['git', 'bundle', 'verify', str(out / 'history.bundle')], cwd=root, check=True, capture_output=True)
    save('bundle-verification.txt', check.stdout + check.stderr)
    receipt = {'schema_version': 1, 'run_id': run_id, 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'head': git('rev-parse', 'HEAD').decode().strip(), 'source_files': records,
               'scope': 'tracked and non-ignored untracked working files, staged/unstaged patches and Git refs; full evidence/LFS backup pending',
               'source_snapshot_status': 'verified', 'simulation_budget_seconds': 172800,
               'simulation_consumed_seconds': 0, 'shutdown_authorized': True, 'shutdown_ready': False,
               'stages': {k: 'pending' for k in ['research_records', 'maxwell_convergence', 'aphi_calibration', 'publications', 'repository_migration', 'quark_upload', 'full_readback', 'isolated_restore', 'final_acceptance']}}
    (out / 'campaign.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'run_id': run_id, 'source_files': len(records), 'status': 'verified', 'receipt': str(out / 'campaign.json')}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--root', default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    begin(args.root, args.run_id)
