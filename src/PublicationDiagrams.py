"""Explicit physical relationships and point-based layouts for publication diagrams."""
import argparse,hashlib,json,shutil
from pathlib import Path
from BuildPublicationEdition import ROOT,read,write,native_run,normalize_export_sizes,verify_panels,sha

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def diagram(identity,lang):
 zh=lang=='zh-CN'
 def tr(a,b):return a if zh else b
 nodes=[];edges=[];groups=[];labels=[];wires=[];dots=[]
 def node(key,xy,size,lines,icon='none'):nodes.append(dict(id=key,center=xy,size=size,lines=lines,icon=icon))
 def group(key,box,label):groups.append(dict(id=key,box=box,label=label))
 def label(text,xy,size=9):labels.append(dict(text=text,position=xy,size=size))
 def edge(a,b,path,label_text,at,style='solid'):edges.append(dict(source=a,target=b,path=path,label=label_text,label_position=at,style=style))
 if identity=='model_hierarchy':
  height=362
  group('internal',[[3,243],[249,358]],tr('圆线内部场 · J、Rac','Round-wire internal field · J, Rac'))
  node('bessel',[62,296],[102,65],[tr('圆线解析','Round-wire analysis'),'Bessel'], 'round')
  node('disk_fem',[190,296],[102,65],[tr('二维圆盘','2D disk diffusion'),'FEM'], 'mesh')
  edge('bessel','disk_fem',[[113,303],[139,303]],tr('校准','Calibration'),[126,253])
  group('transport',[[3,76],[249,209]],tr('轴向输运 · Z、I、Rac','Axial transport · Z, I, Rac'))
  node('common',[66,145],[110,74],[tr('多股二维共端','2D common terminals'),tr('复电流分配','Phasor current sharing')],'bundle')
  node('peec',[190,145],[102,74],[tr('纵向 PEEC','Longitudinal PEEC'),tr('有限长度','Finite length')],'filaments')
  edge('bessel','peec',[[62,263],[62,239],[246,239],[246,145],[241,145]],tr('等面积 Rac 参照','Equal-area Rac reference'),[127,224], 'dashed')
  group('independent',[[3,3],[249,68]],tr('独立激励与三维诊断','Separate excitation and 3D diagnostics'))
  node('rt0',[66,27],[110,34],['RT0 · '+tr('外场损耗','Imposed-field loss'),tr('零净输运','Zero net transport')],'none')
  node('aphi',[190,27],[102,34],['3D A–φ',tr('场误差与规范','Field / gauge errors')],'none')
  label(tr('共同电压与总电流约束','Common voltage and total-current constraint'),[126,88],9)
 elif identity=='common_terminal':
  height=304
  group('inputs',[[4,265],[248,300]],tr('输入 / 已知量','Inputs / known quantities'))
  label('Z, e, Iₜ = 20 A RMS',[126,275],10)
  label(tr('公共端点 A','Common terminal A'),[52,245],9)
  label(tr('公共端点 B','Common terminal B'),[195,245],9)
  wires=[[[30,228],[30,89]],[[222,228],[222,89]]]
  for key,y,current in [('s1',215,'I₁'),('s2',171,'I₂'),('sn',112,'Iₙ')]:
   node(key,[126,y],[66,21],[tr('股线 ','Strand ')+{'s1':'1','s2':'2','sn':'N'}[key]])
   wires.extend([[[30,y],[93,y]],[[159,y],[222,y]]]);dots.extend([[30,y],[222,y]])
   edge('A',key,[[45,y],[79,y]],current,[63,y+12])
  label('⋮',[126,142],13)
  edge('s1','s2',[[168,209],[179,199],[179,187],[168,177]],tr('耦合','Coupling'),[204,192], 'dashed')
  node('return',[126,64],[90,23],[tr('受控回流','Controlled return')])
  wires.extend([[[30,64],[81,64]],[[171,64],[222,64]]])
  edge('B','return',[[179,64],[214,64]],'−Iₜ',[198,48])
  dots.extend([[30,64],[222,64]])
  label('V = V(A) − V(B)',[126,231],10)
  label('Zi + e = V1     Σ Iₖ = Iₜ',[126,26],11)
  label(tr('未知量：i、V；回流端场独立','Unknowns: i, V; separate return field'),[126,9],9)
 elif identity=='ansys_limits':
  height=254
  group('license',[[3,76],[249,249]],'Ansys Student · v252')
  node('two_d',[67,189],[110,68],[tr('二维网格','2D mesh'),'2000',tr('三角形','triangles')],'none')
  node('three_d',[190,189],[102,68],[tr('三维网格','3D mesh'),'64000 / 8000',tr('体 / 面单元','volume / surface')],'none')
  node('cores',[126,110],[224,40],['CPU · 4 '+tr('核','cores')],'none')
  group('interface',[[3,3],[249,66]],tr('接口诊断','Interface diagnostics'))
  label(tr('电流密度表达式 J','Current-density expression J'),[126,37],10)
  label(tr('表达式探针 → 场积分核验','Expression probe → field-integral check'),[126,17],9)
 else:raise ValueError(identity)
 semantics=dict(id=identity,nodes=[{k:v for k,v in n.items() if k in ['id','lines','icon']} for n in nodes],edges=[{k:v for k,v in e.items() if k in ['source','target','label','style']} for e in edges],groups=[{k:v for k,v in g.items() if k in ['id','label']} for g in groups])
 layout=dict(width=252,height=height,nodes=nodes,edges=edges,groups=groups,labels=labels,wires=wires,dots=dots)
 return dict(semantics=semantics,layout=layout,semantic_sha256=digest(semantics),layout_sha256=digest(layout))

def build(run_id):
 run=ROOT/'outputs'/run_id
 if run.exists():raise ValueError('A new diagram run identity is required')
 run.mkdir();m=read(ROOT/'manuscript/publication.json');base=ROOT/m['panel_run'];request=read(base/'render_request.json')
 panels=[]
 for identity in ['model_hierarchy','common_terminal','ansys_limits']:
  for lang in ['zh-CN','en']:
   spec=dict(id=identity,kind='schematic',language=lang,**diagram(identity,lang),caption=m['figures'][identity]['title'][lang],source_model='explicit_physical_model_relationships',source_run_id='6b5574b',source_physical_acceptance_status=m['figures'][identity]['source_acceptance'])
   spec['data_sha256']=digest(spec['semantics']);panels.append(spec)
 request.update(run_id=run.name,output_directory=str(run),panels=panels)
 write(run/'render_request.json',request);shutil.copy2(base/'source_manifest.json',run/'source_manifest.json')
 shutil.copy2(Path(__file__),run/Path(__file__).name)
 native_run(run,run/'render_request.json');normalize_export_sizes(run);verify_panels(run)
 records=read(run/'panel_manifest.json')
 for panel in records['panels']:
  spec=next(p for p in panels if (p['id'],p['language'])==(panel['id'],panel['language']))
  panel.update(semantic_sha256=spec['semantic_sha256'],layout_sha256=spec['layout_sha256'],expression_sha256=sha(run/'panels'/panel['language']/(panel['id']+'.wl')))
 write(run/'panel_manifest.json',records)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args();build(a.run_id)
