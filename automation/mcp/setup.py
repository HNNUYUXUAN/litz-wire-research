"""Prepare a separate pinned MCP environment; print the command plan by default."""
from pathlib import Path
import argparse,json,subprocess,sys

def main():
    p=argparse.ArgumentParser();p.add_argument('server',choices=['wolfram','ansys']);p.add_argument('--destination',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    root=next(x for x in Path(__file__).resolve().parents if (x/'pyproject.toml').exists());lock=json.loads((root/'automation/mcp/upstreams.lock.json').read_text())
    destination=Path(a.destination).resolve()
    if a.server=='wolfram':
        print(json.dumps({'paclet':'Wolfram/AgentTools','version':lock['wolfram']['version'],'source':lock['wolfram']['repository']+'/tree/'+lock['wolfram']['commit'],'instructions':'Install the fixed paclet into your licensed Wolfram environment, then configure the project MCP entry.'},indent=2));return
    python=destination/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    requirement='ansys-aedt-mcp @ git+https://github.com/ansys/pyaedt-mcp.git@'+lock['ansys']['commit']
    commands=[[sys.executable,'-m','venv',str(destination)],[str(python),'-m','pip','install','-c',str(root/'automation/mcp/ansys-environment.lock'),'pyaedt=='+lock['ansys']['pyaedt'],requirement],[str(python),'-m','pip','check']]
    print(json.dumps({'commands':commands,'destination':str(destination),'applied':a.apply},indent=2))
    if a.apply:
        if destination.exists():raise FileExistsError('Choose a new environment directory')
        if sys.version_info<(3,12):raise RuntimeError('Ansys MCP requires Python 3.12 or later')
        for command in commands:subprocess.run(command,check=True,cwd=root)
        frozen=subprocess.check_output([str(python),'-m','pip','freeze'],text=True)
        (destination/'environment.lock').write_text(frozen,encoding='utf-8')

if __name__=='__main__':main()
