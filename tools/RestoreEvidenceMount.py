"""Restore unchanged catalogue objects into the separate evidence mount."""
from pathlib import Path
import hashlib,json,shutil,time
from litz_research.common import sha,evidence_root,write

def main():
    root=Path(__file__).resolve().parents[1];catalog=json.loads((root/'data/catalog.json').read_text(encoding='utf-8'))
    mount=evidence_root(root);cache=Path.home()/'.cache/litz-research/objects';records=[];start=time.monotonic();errors=[]
    unique={r['path']:r for d in catalog['datasets'].values() for r in d['files']}
    for index,(relative,r) in enumerate(unique.items()):
        target=mount/relative;source=root/relative
        if target.is_file() and sha(target)==r['sha256']:continue
        if not source.is_file() or sha(source)!=r['sha256']:
            candidates=[cache/r['sha256'],root.parent.parent/'archives/litz_public_preparation_20261007_01/objects'/r['sha256']]
            source=next((p for p in candidates if p.is_file() and sha(p)==r['sha256']),candidates[0])
        if not source.is_file() or sha(source)!=r['sha256']:
            errors.append(relative);continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        if sha(target)!=r['sha256']:raise RuntimeError('Restoration hash mismatch: '+relative)
        if index%2000==0:print('restored',index,'/',len(unique),flush=True)
    result={'files':len(unique),'missing':errors,'elapsed_seconds':time.monotonic()-start,'evidence_root':mount.relative_to(root).as_posix(),'source_files_unchanged':True}
    write(root/'outputs/automation_20261013_rc2/evidence_mount_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='missing'}),'missing',len(errors))
    raise SystemExit(bool(errors))

if __name__=='__main__':main()
