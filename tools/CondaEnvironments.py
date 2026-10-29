"""Export or recreate project runtimes without depending on a download checkout."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ROOT / 'automation/environments/locks'


def run(args, capture=False):
    return subprocess.run([str(x) for x in args], check=True, cwd=ROOT,
                          capture_output=capture, text=True, encoding='utf-8',
                          env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8')).stdout


def manage(action, name, conda, prefix):
    python = prefix / 'python.exe'
    if action == 'export':
        explicit = run([conda, 'list', '--prefix', prefix, '--explicit'], True)
        (LOCKS / f'{name}-win-64.explicit.txt').write_text(
            '\n'.join(line for line in explicit.splitlines() if not line.startswith('#'))+'\n', encoding='utf-8')
        packages = json.loads(run([python, '-m', 'pip', 'list', '--format=json'], True))
        (LOCKS / f'{name}-pip.json').write_text(json.dumps(packages, indent=2)+'\n', encoding='utf-8')
        pins = [p['name']+'=='+p['version'] for p in packages
                if p['name'].lower().replace('_','-') not in ('litz-research', 'ansys-aedt-mcp')]
        (LOCKS / f'{name}-pip.txt').write_text('\n'.join(pins)+'\n', encoding='utf-8')
    elif action == 'verify':
        actual = json.loads(run([python, '-m', 'pip', 'list', '--format=json'], True))
        expected = json.loads((LOCKS/f'{name}-pip.json').read_text(encoding='utf-8-sig'))
        normalize = lambda values: {p['name'].lower().replace('_','-'):p['version'] for p in values}
        if normalize(actual) != normalize(expected):
            raise ValueError('Installed package versions differ from the exported inventory.')
        run([python, '-m', 'pip', 'check'])
        if name == 'project':
            run([python, '-c', 'import litz_research,mcp,mpmath,psutil,bibtexparser'])
            run([prefix/'Library/bin/pandoc.exe', '--version'])
        elif name == 'research':
            run([prefix/'node.exe', '--version'])
            run([python, '-c', 'import yaml'])
        elif name == 'ansys':
            commit = json.loads((ROOT/'automation/mcp/upstreams.lock.json').read_text())['ansys']['commit']
            run([python, '-c', 'import ansys.aedt.core,ansys.aedt.mcp,json,importlib.metadata as m,sys; '
                 'origin=json.loads(m.distribution("ansys-aedt-mcp").read_text("direct_url.json")); '
                 'assert origin.get("vcs_info",{}).get("commit_id")==sys.argv[1]', commit])
        print(f'{name}: inventory, dependencies and executable identity passed')
    else:
        if prefix.exists():
            raise ValueError('Rebuild requires a new prefix; existing environments are preserved.')
        run([conda, 'create', '--prefix', prefix, '--override-channels', '-c', 'conda-forge',
             '--file', LOCKS / f'{name}-win-64.explicit.txt', '-y'])
        run([python, '-m', 'pip', 'install', '-r', LOCKS / f'{name}-pip.txt'])
        if name == 'project':
            run([python, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation', '-e', ROOT])
        elif name == 'ansys':
            upstream = json.loads((ROOT/'automation/mcp/upstreams.lock.json').read_text())['ansys']
            run([python, '-m', 'pip', 'install', '--no-deps',
                 'git+'+upstream['repository']+'@'+upstream['commit']])
        run([python, '-m', 'pip', 'check'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['export', 'rebuild', 'verify'])
    parser.add_argument('name', choices=['project', 'ansys', 'research'])
    parser.add_argument('--conda', default='conda')
    parser.add_argument('--prefix', type=Path)
    args = parser.parse_args()
    manage(args.action, args.name, args.conda, (args.prefix or ROOT/'.conda'/args.name).resolve())
