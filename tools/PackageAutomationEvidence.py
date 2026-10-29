"""Package explicit rc.2 run artifacts as verified content-addressed objects."""
from pathlib import Path
import argparse,gzip,hashlib,io,json,tarfile
from litz_research.common import read,write,sha
from litz_research.provenance import derive_text,portable_text,numeric_tree,derive_wxf

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    verification=read(root/'automation/examples/verification.json')
    runs={r['run_id'] for case in verification['cases'] for r in case['runs']}
    notebooks=read(root/'provenance/rc2/notebook_verification.json')
    runs.update(rid for n in notebooks for rid in n['run_ids'])
    runs.update(['rc2_route_circuits_01','rc2_route_copper_01','rc2_route_peec_01','rc2_route_rt0_01','rc2_gpu_full_small_01','rc2_wolfram_environment_02','rc2_maxwell_mcp_final_01','rc2_maxwell_mcp_final_02','rc2_legacy_aphi_mount_02'])
    selected={p.relative_to(root):p for rid in runs for p in (root/'outputs'/rid).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.lock','.semaphore'}}
    controls=root/'outputs/automation_20261013_rc2'
    for folder in ['aedt_owner_verified','notebook_frontend']:
        for file in (controls/folder).iterdir():
            if file.is_file() and file.suffix in {'.json','.png'}:selected[file.relative_to(root)]=file
    selected[(controls/'evidence_mount_verification.json').relative_to(root)]=controls/'evidence_mount_verification.json'
    for file in (controls/'native_lifecycle_validation_01').glob('*.json'):selected[file.relative_to(root)]=file
    recovery=controls/'recovery_verification_20261014_023334'
    for name in ['recovery_receipt.json','historical_fixtures.json','verification.json']:
        file=recovery/name
        if file.exists():selected[file.relative_to(root)]=file
    staging=out/'files';objects={};files=[];lineage=[]
    text_suffixes={'.json','.jsonl','.txt','.log','.py','.wl','.wls','.wlt','.md','.toml','.bib','.ps1','.nb','.csv','.xml','.asol','.aedt'}
    for relative,source in sorted(selected.items()):
        raw=source.read_bytes();target=staging/relative;target.parent.mkdir(parents=True,exist_ok=True)
        proof='byte_identical'
        if source.suffix=='.wxf':
            # Only WXF string metadata may change; all non-string tokens are verified.
            proof=derive_wxf(source,target);data=target.read_bytes()
        elif source.suffix=='.jsonl':
            lines=[]
            for line in raw.decode('utf-8-sig').splitlines():
                before=json.loads(line);after=json.loads(portable_text(line))
                if list(numeric_tree(before))!=list(numeric_tree(after)):raise ValueError('Event quantitative identity changed')
                lines.append(json.dumps(after,ensure_ascii=False))
            data=('\n'.join(lines)+'\n').encode();proof='all_event_numeric_paths_equal'
        elif source.suffix in text_suffixes:
            try:data,proof=derive_text(raw,source.suffix)
            except UnicodeDecodeError:data=raw
        else:data=raw
        target.write_bytes(data);identity=hashlib.sha256(data).hexdigest()
        objects.setdefault(identity,target)
        files.append({'path':relative.as_posix(),'sha256':identity,'bytes':len(data)})
        lineage.append({'path':relative.as_posix(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'public_sha256':identity,'verification':proof})
    lineage_path=staging/'provenance/rc2/evidence_derivation.json'
    write(lineage_path,{'scope':'Visible events and numerical artifacts; machine-path derivatives retain original raw identities. Source/request hashes in original run manifests refer to raw_sha256; public_sha256 identifies the restored derivative. Original historical rc.1 evidence is unchanged.','files':lineage})
    identity=sha(lineage_path);objects[identity]=lineage_path;files.append({'path':'provenance/rc2/evidence_derivation.json','sha256':identity,'bytes':lineage_path.stat().st_size})
    archive=out/'litz_automation_rc2.tar.gz'
    with archive.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|') as bundle:
        for identity,path in sorted(objects.items()):
            info=tarfile.TarInfo('objects/'+identity);info.size=path.stat().st_size;info.mtime=0;info.mode=0o644
            with path.open('rb') as stream:bundle.addfile(info,stream)
    parts=[]
    with archive.open('rb') as stream:
        while block:=stream.read(128*2**20):
            part=out/('litz_automation_rc2.part'+str(len(parts)+1).zfill(2));part.write_bytes(block)
            parts.append({'name':part.name,'sha256':sha(part),'bytes':len(block)})
    dataset={'description':'Actual Codex/MCP automation cases, bounded task snapshots, Maxwell projects, route regressions and twenty native Notebook execution records','source_version':'v1.0.0-rc.2','dependencies':[],'objects':[{'sha256':h,'bytes':path.stat().st_size} for h,path in sorted(objects.items())],'files':files,'parts':parts}
    catalog=read(root/'data/catalog.json');catalog['datasets']['automation-rc2']=dataset;write(root/'data/catalog.json',catalog)
    provenance=[r for r in read(root/'provenance/candidate_files.json') if r['dataset']!='automation-rc2']
    by_path={r['path']:r for r in lineage}
    for record in files:
        derivation=by_path.get(record['path'],{})
        code=Path(record['path']).suffix in {'.py','.wl','.wls','.wlt','.ps1'}
        provenance.append(record|{'dataset':'automation-rc2','source_path':record['path'],'source_sha256':derivation.get('raw_sha256',record['sha256']),'source_commit':None,'source_identity':'actual saved run source/input snapshot','author':'Miao Yuxuan','affiliation':'Huainan Normal University','license':'MIT' if code else 'MIT code cells; CC-BY-4.0 text and figures' if Path(record['path']).suffix=='.nb' else 'CC-BY-4.0','processing':'portable metadata derivative with retained raw identity','quantitative_check':derivation.get('verification','generated lineage index'),'inspection':'explicit workflow artifact and quantitative identity verification'})
    write(root/'provenance/candidate_files.json',provenance)
    write(out/'packaging_report.json',{'runs':sorted(runs),'files':len(files),'objects':len(objects),'parts':parts,'lineage_sha256':sha(lineage_path)})
    print(json.dumps({'files':len(files),'objects':len(objects),'archive_bytes':archive.stat().st_size,'parts':len(parts)}))

if __name__=='__main__':main()
