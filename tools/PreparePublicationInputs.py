"""Restore current publication panels from saved fields; never run a physical solver."""
from pathlib import Path
import argparse, json, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/publication'))
from BuildPublicationEdition import read, native_run, normalize_export_sizes, verify_panels, sha
from PublicationPanels import prepare

def verified(run):
    manifest = read(run/'panel_manifest.json')
    for panel in manifest['panels']:
        for asset in panel['assets']:
            candidates = [run/'panels'/panel['language']/(panel['id']+'.'+asset['format'])]
            if asset.get('path'): candidates.append(Path(asset['path']))
            path = next((p for p in candidates if p.is_file()), None)
            if path is None or sha(path) != asset['sha256']:
                raise ValueError('Missing or changed panel: '+panel['id']+'/'+asset['format'])
    return len(manifest['panels'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest',default='manuscript/publication.json')
    args=parser.parse_args(); manifest=read(ROOT/args.source_manifest)
    base=(ROOT/manifest['panel_run']).resolve()
    if base.parent != ROOT/'outputs': raise ValueError('Panel run must be directly under outputs/')
    if not (base/'field_reconstruction_verification.json').exists():
        if base.exists(): raise RuntimeError('Incomplete field reconstruction retained at '+str(base)+'; select a new panel_run identity in the manifest')
        subprocess.run([sys.executable,str(ROOT/'tools/publication/PublicationData.py'),'--run-id',base.name],cwd=ROOT,check=True)
    if not (base/'panel_manifest.json').exists():
        prepare(base,['zh-CN','en'])
        native_run(base,base/'render_request.json',script='BuildPublicationFigures.wls',suffix='_figures')
        normalize_export_sizes(base); verify_panels(base)
    counts={base.name:verified(base)}
    for relative in sorted(set(manifest.get('panel_overrides',{}).values())):
        run=(ROOT/relative).resolve()
        if run.parent != ROOT/'outputs': raise ValueError('Override must be directly under outputs/')
        if not run.exists():
            selected=[item for item,path in manifest['panel_overrides'].items() if path==relative]
            subprocess.run([sys.executable,str(ROOT/'tools/publication/ReframePublicationPanels.py'),'--run-id',run.name,'--source-run',manifest['panel_run']]+[arg for item in selected for arg in ['--panel',item]],cwd=ROOT,check=True)
        counts[run.name]=verified(run)
    print(json.dumps({'verified_panels':counts,'physical_solver_calls':0}))

if __name__=='__main__': main()
