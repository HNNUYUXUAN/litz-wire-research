"""Split established physics definitions without changing their package context."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
p=root/'shared/wolfram/NotebookPhysics.wl'
s=p.read_text(encoding='utf-8')
if 'Begin["`Private`"]' in s:
    head=s[:s.index('Begin["`Private`"]')]
    body=s[s.index('sigma='):s.index('End[];EndPackage[];')]
    starts=[(m.start(),m.group(1)) for m in re.finditer(r'^(WireZ|WireJ|StrandCenters|CommonPort|DiskFEM|Topology|DTM|IDTM)\[',body,re.M)]
    parts={}
    routes={'WireZ':'analytic','WireJ':'analytic','StrandCenters':'geometry','Topology':'geometry','DTM':'geometry','IDTM':'geometry','CommonPort':'common_terminal','DiskFEM':'fem2'}
    for j,(a,n) in enumerate(starts):
        parts.setdefault(routes[n],[]).append(body[a:starts[j+1][0] if j+1<len(starts) else len(body)])
    for name,items in parts.items():
        q=root/'models'/name/'src/Physics.wl';q.parent.mkdir(parents=True,exist_ok=True)
        q.write_text(head+'Begin["`Private`"];\nsigma=5.8*^7; mu=4. Pi 10.^-7;\n'+''.join(items)+'End[];EndPackage[];\n',encoding='utf-8')
    loader='(* Route definitions retain the established LitzPhysics` public context. *)\nphysicsRoot=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];\n'
    for route in ['analytic','geometry','common_terminal','fem2']:
        loader+='Get[FileNameJoin[{physicsRoot,"models","'+route+'","src","Physics.wl"}]];\n'
    p.write_text(loader,encoding='utf-8')
for folder in ['adapters/wolfram','adapters/ansys','adapters/gpu','tools/publication']:
    for q in (root/folder).glob('*.ps1'):
        text=q.read_text(encoding='utf-8')
        text=re.sub(r'Join-Path \$PSScriptRoot ([\'\"])([^\'\"]+)\1',lambda m:'Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src") '+repr(m.group(2)),text)
        text=text.replace("Join-Path (Join-Path $stageRoot 'src')",'Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src")')
        q.write_text(text,encoding='utf-8')
print('Route definitions and launcher paths prepared')
