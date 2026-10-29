"""Back up and merge accepted project MCP settings while preserving other settings."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[1]


def merge_client(original, candidate):
    parsed=tomllib.loads(original)
    names={name.lower():name for name in parsed.get('mcp_servers',{})}
    sections=re.split(r'(?m)(?=^\[)',original)
    selected={'wolfram','ansys'}
    kept=[]
    for block in sections:
        match=re.match(r'\[mcp_servers\.([A-Za-z0-9_-]+)(?:\.[^\]]+)?\]',block)
        if match and match[1].lower() in selected:continue
        kept.append(block)
    def encode(value):
        if isinstance(value,dict):return '{'+', '.join(json.dumps(k)+' = '+encode(v) for k,v in value.items())+'}'
        return json.dumps(value,ensure_ascii=False)
    text=''.join(kept).rstrip()+'\n\n'
    for name in ('wolfram','ansys'):
        actual=names.get(name,name)
        server=dict(parsed.get('mcp_servers',{}).get(actual,{}))
        server.update(candidate[name])
        text+='[mcp_servers.'+actual+']\n'
        text+=''.join(k+' = '+encode(v)+'\n' for k,v in server.items())+'\n'
    updated=tomllib.loads(text)
    def unrelated(data):
        data=json.loads(json.dumps(data))
        data['mcp_servers']={k:v for k,v in data.get('mcp_servers',{}).items() if k.lower() not in selected}
        return data
    if unrelated(parsed)!=unrelated(updated):raise ValueError('Unrelated configuration changed')
    return text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--client-config',type=Path,required=True)
    p.add_argument('--backup-dir',type=Path,required=True)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    candidate=tomllib.loads(a.candidate.read_text(encoding='utf-8-sig'))['mcp_servers']
    old_client=a.client_config.read_text(encoding='utf-8-sig')
    client=merge_client(old_client,candidate)
    project_path=ROOT/'litz.config.json'
    local=json.loads(project_path.read_text(encoding='utf-8-sig'))
    local.setdefault('tools',{}).update(python=sys.executable,ansys_python=candidate['ansys']['command'])
    for name in ('wolfram','ansys'):
        local.setdefault('mcp_servers',{})[name]={k:v for k,v in candidate[name].items()
            if k in ('command','args','env','cwd','url')}
    if not a.apply:
        print('Candidate merge validated; pass --apply to back up and switch.');return
    a.backup_dir.mkdir(parents=True,exist_ok=False)
    shutil.copy2(a.client_config,a.backup_dir/'codex-config.toml')
    shutil.copy2(project_path,a.backup_dir/'litz.config.json')
    a.client_config.write_text(client,encoding='utf-8')
    project_path.write_text(json.dumps(local,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    receipt={'status':'configuration_switched','native_client_status':'pending_refresh',
             'files':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (a.client_config,project_path)}}
    (a.backup_dir/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
