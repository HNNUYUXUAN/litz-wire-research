"""Retrieve fixed public upstream source archives with license and hash records."""
from pathlib import Path
import json,urllib.request,hashlib,zipfile
from litz_research.common import write

def main():
    root=Path(__file__).resolve().parents[1];out=root/'outputs/automation_20261013_rc2/upstreams';out.mkdir(exist_ok=True)
    lock=json.loads((root/'automation/mcp/upstreams.lock.json').read_text());records=[]
    for name in ['wolfram','ansys']:
        item=lock[name];repo=item['repository'].removeprefix('https://github.com/');url='https://codeload.github.com/'+repo+'/zip/'+item['commit'];path=out/(name+'_'+item['commit'][:12]+'.zip')
        if not path.exists() or not zipfile.is_zipfile(path):
            partial=path.with_suffix('.zip.partial')
            with urllib.request.urlopen(url,timeout=30) as response,partial.open('wb') as stream:
                while block:=response.read(1024*1024):stream.write(block)
            with zipfile.ZipFile(partial) as archive:
                bad=archive.testzip()
                if bad:raise ValueError('Corrupt upstream member: '+bad)
            partial.replace(path)
        with zipfile.ZipFile(path) as archive:
            licenses=[n for n in archive.namelist() if n.rsplit('/',1)[-1].upper().startswith(('LICENSE','COPYING','NOTICE'))]
        if not licenses:raise ValueError('Upstream license missing from source archive')
        records.append(item|{'asset':path.name,'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'license_members':licenses})
    write(root/'automation/mcp/upstream_archives.json',records);print('Fixed upstream archives',len(records))

if __name__=='__main__':main()
