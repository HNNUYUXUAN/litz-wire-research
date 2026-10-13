"""Preserve the candidate baseline and migrate maintained sources by responsibility."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'outputs/automation_20261013_rc2'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    if (ROOT/'provenance/source_migration.json').exists():
        print('Canonical source migration already installed');return
    RUN.mkdir(parents=True, exist_ok=True)
    baseline = RUN / 'baseline'
    if not baseline.exists():
        baseline.mkdir()
        names = subprocess.check_output(['git','-c','core.longpaths=true','ls-files','-m','-o','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
        records=[]
        for name in filter(None,names):
            p=ROOT/name
            if p.is_file():
                q=baseline/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
                records.append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        write(baseline/'manifest.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':records})
        (baseline/'tracked.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=ROOT))
    if (RUN/'source_migration.json').exists():
        print('Source migration already recorded');return
    mapping={}
    for p in (ROOT/'src').iterdir():
        if not p.is_file() or p.suffix not in {'.py','.wl','.wls','.ps1'}:continue
        name=p.name;low=name.lower()
        if name=='NotebookPhysics.wl':target='shared/wolfram/NotebookPhysics.wl'
        elif name=='NotebookView.wl':target='shared/wolfram/NotebookView.wl'
        elif name in {'Q1Analytical.wl','ExploreRoundWireCPU.wls','RunCalibration.wls'}:target='models/analytic/src/'+name
        elif name=='CoaxFEM.wl':target='models/common_terminal/src/'+name
        elif name in {'PEEC.wl'}:target='models/peec/src/'+name
        elif low.startswith('voxel'):target='models/rt0/src/'+name
        elif low.startswith('gpu') or 'gpu' in low:target='adapters/gpu/'+name
        elif 'ansys' in low:target='adapters/ansys/'+name
        elif 'topology' in low:target='models/geometry/src/'+name
        elif any(s in low for s in ('publication','manuscript','panel','latex','renderdelivery')):target='tools/publication/'+name
        elif p.suffix in {'.wls','.ps1'}:target='adapters/wolfram/'+name
        else:target='tools/research/'+name
        mapping[p.relative_to(ROOT).as_posix()]=target
    for p in (ROOT/'src/stages').glob('*.wl'):
        n=p.stem
        route=('common_terminal' if n.startswith(('coax','scale','circuits')) else 'analytic' if n=='analytic' else 'fem2' if n=='fem2' else 'geometry' if 'geometry' in n or n=='copper' or n=='handoff' else 'peec' if 'peec' in n else 'rt0' if 'voxel' in n or 'rt0' in n else 'aphi' if 'fem3' in n else None)
        target=f'models/{route}/src/stages/{p.name}' if route else f'adapters/{"gpu" if "gpu" in n else "wolfram"}/stages/{p.name}'
        mapping[p.relative_to(ROOT).as_posix()]=target
    root_expr='next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())'
    wl_root='NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&]'
    for old,new in mapping.items():
        p=ROOT/old;q=ROOT/new;q.parent.mkdir(parents=True,exist_ok=True)
        text=p.read_text(encoding='utf-8-sig')
        if p.suffix=='.py':
            text=text.replace('Path(__file__).resolve().parents[1]',root_expr).replace('Path(__file__).resolve().parent.parent',root_expr)
            q.write_text(text,encoding='utf-8')
            p.write_text('"""Compatibility entry; maintained implementation: '+new+'."""\nfrom pathlib import Path as _Path\n_target = _Path(__file__).resolve().parents[1] / '+repr(new)+'\nexec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), globals())\n',encoding='utf-8')
        elif p.suffix in {'.wl','.wls'}:
            text=text.replace('DirectoryName[DirectoryName[$InputFileName]]',wl_root)
            if p.name=='RunNotebookStage.wls':
                text=text.replace('stageSources=Join[','stageSources=Join[Flatten[FileNames[{"*.wl","*.wls","*.py","*.ps1","*.json","*.md"},FileNameJoin[{stageRoot,#}],Infinity]&/@{"models","adapters","shared","automation","python","tools"}],')
            q.write_text(text,encoding='utf-8')
            parts=new.split('/')
            p.write_text('(* Compatibility entry; maintained implementation: '+new+' *)\nGet[FileNameJoin[{'+wl_root+','+','.join(json.dumps(x) for x in parts)+'}]];\n',encoding='utf-8')
        else:
            # Original argument declarations remain at the compatibility entry.
            q.write_text(text.replace('Split-Path -Parent $PSScriptRoot',"(Get-Item (Join-Path $PSScriptRoot '../../')).FullName").replace('Split-Path $PSScriptRoot -Parent',"(Get-Item (Join-Path $PSScriptRoot '../../')).FullName"),encoding='utf-8')
            param=text[:text.index("\n",text.index('param('))] if 'param(' in text else ''
            # Parameter blocks can span lines. Keep the existing launcher as a
            # thin call after extracting its balanced declaration.
            if 'param(' in text:
                start=text.index('param(');depth=0;quote=None;end=None
                for i,c in enumerate(text[start+5:],start+5):
                    if quote:
                        if c==quote:quote=None
                    elif c in "\"'":quote=c
                    elif c=='(':depth+=1
                    elif c==')':
                        depth-=1
                        if depth==0:end=i+1;break
                param=text[start:end] if end else param
            p.write_text(param+'\n$ErrorActionPreference="Stop"\n& (Join-Path (Split-Path -Parent $PSScriptRoot) '+repr(new)+') @PSBoundParameters\nexit $LASTEXITCODE\n',encoding='utf-8')
            # Sibling references continue through compatibility entry points.
            active=q.read_text(encoding='utf-8')
            active=re.sub(r'Join-Path \$PSScriptRoot ([\'\"])([^\'\"]+)\1',lambda m:"Join-Path (Join-Path $stageRoot 'src') "+repr(m.group(2)) if p.name=='RunNotebookStage.ps1' else m.group(0),active)
            q.write_text(active,encoding='utf-8')
    write(RUN/'source_migration.json',{'baseline':'29bfaef','mapping':mapping,'compatibility':'single implementation; former entry forwards to maintained source'})
    print('Migrated',len(mapping),'source entries; baseline preserved')

if __name__=='__main__':main()
