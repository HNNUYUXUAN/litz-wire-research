"""Build an independent source checkout without changing the original Git index."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

def stage(root,destination):
    root=Path(root).resolve();destination=Path(destination).absolute()
    destination.mkdir(parents=True,exist_ok=False)
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root).decode().split('\0')
    manifest=[]
    for relative in sorted(set(names)-{''}):
        source=root/relative
        if not source.is_file():continue
        target=destination/relative
        if not target.is_relative_to(destination):raise ValueError('Path escape')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        manifest.append({'path':relative,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size})
    subprocess.run(['git','init','--initial-branch=main'],cwd=destination,check=True)
    subprocess.run(['git','add','--all'],cwd=destination,check=True)
    (destination.parent/'staging-source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'path':str(destination),'files':len(manifest),'status':'staged_without_commit'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--destination',required=True)
    a=p.parse_args();stage(a.root,a.destination)
