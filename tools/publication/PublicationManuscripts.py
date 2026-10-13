"""Build scholarly editions from paired Markdown blocks and frozen observables."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,re,shutil,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from BuildPublicationEdition import sha,read,write,native_run

def input_path(relative):
 from litz_research.common import resolve_read_path
 return resolve_read_path(ROOT,relative)

def rows(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def metrics(m):
 """Units come from the model quantity, with explicit SI-to-display conversions."""
 b=input_path(m['frozen_bundle']);p=input_path(m['panel_run']);raw=b/'routes/coax640/data.json';c=read(raw)['cases'][2]
 peec=next(r for r in rows(p/'tables/peec_cases.csv') if r['case_id']=='peec_m80_l064_q4_s12p10')
 currents=[complex(float(r['Re_I_RMS_A']),float(r['Im_I_RMS_A'])) for r in rows(p/'tables/coax640_currents.csv')]
 v=c['source_voltage_V_per_m'];print('terminal field',v,flush=True)
 def complex_value(o):
  if isinstance(o,dict):return complex(o.get('re',o.get('real',o.get('Re',0))),o.get('im',o.get('imag',o.get('Im',0))))
  if isinstance(o,list):return complex(*o)
  raise TypeError('Archived complex record required')
 voltage=complex_value(v)
 return_voltage=complex_value(c['return_voltage_V_per_m']);physical_inputs=read(ROOT/'configs/reference_parameters.json')
 rdc=1/(physical_inputs['conductivity_S_per_m']*c['polygonal_bundle_area_m2'])
 ref=read(ROOT/'configs/reference_values.json')
 specifications={
  'coax_rac':(c['bundle_Rac_ohm_per_m'],'ohm/m','mΩ/axial m',1000,9,raw,'cases[2].bundle_Rac_ohm_per_m'),
  'coax_bundle_loss':(c['bundle_loss_W_per_m'],'W/m','W/axial m',1,9,raw,'cases[2].bundle_loss_W_per_m'),
  'coax_return_loss':(c['return_loss_W_per_m'],'W/m','W/axial m',1,9,raw,'cases[2].return_loss_W_per_m'),
  'coax_area':(c['polygonal_bundle_area_m2'],'m2','mm²',1e6,6,raw,'cases[2].polygonal_bundle_area_m2'),
  'coax_voltage_re':(voltage.real,'V/m','V/m',1,9,raw,'cases[2].source_voltage_V_per_m.real'),
  'coax_voltage_im':(voltage.imag,'V/m','V/m',1,9,raw,'cases[2].source_voltage_V_per_m.imag'),
  'coax_return_voltage_re':(return_voltage.real,'V/m','V/m',1,9,raw,'cases[2].return_voltage_V_per_m.real'),
  'coax_return_voltage_im':(return_voltage.imag,'V/m','V/m',1,9,raw,'cases[2].return_voltage_V_per_m.imag'),
  'coax_rdc':(rdc,'ohm/m','mΩ/axial m',1000,9,raw,'1/(reference conductivity*cases[2].polygonal_bundle_area_m2)'),
  'coax_rac_rdc':(c['bundle_Rac_ohm_per_m']/rdc,'1','1',1,9,raw,'cases[2].bundle_Rac_ohm_per_m/derived straight-bundle Rdc'),
  'coax_spread':(math.sqrt(sum(abs(i-20/640)**2 for i in currents)/640)/(20/640),'1','1',1,6,p/'tables/coax640_currents.csv','sqrt(mean(abs(I-It/N)^2))/(It/N)'),
  'peec_rac':(float(peec['Rac_ohm_per_axial_m']),'ohm/m','mΩ/axial m',1000,9,p/'tables/peec_cases.csv','case_id=peec_m80_l064_q4_s12p10.Rac_ohm_per_axial_m'),
 }
 # Reference JSON includes display values with explicit units in names.
 for name,key,unit,display,si_scale,display_scale,digits in [('skin_depth','delta_mm','m','mm',.001,1000,9),('q1_rac','Q1_Rac_mohm_per_m','ohm/m','mΩ/m',.001,1000,9),('q1_rdc','Q1_Rdc_mohm_per_m','ohm/m','mΩ/m',.001,1000,9),('q1_loss','Q1_P_W_per_m','W/m','W/m',1,1,9)]:
  value=ref['values'][key]
  specifications[name]=(float(value)*si_scale,unit,display,display_scale,digits,ROOT/'configs/reference_values.json',key)
 result={}
 for name,(value,unit,display,scale,digits,source,locator) in specifications.items():
  display_format=m.get('quantity_display',{}).get(name,f'.{digits}f')
  result[name]=dict(value=value,unit=unit,display_unit=display,display_scale=scale,formatted=format(value*scale,display_format),source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),locator=locator,source_model='2D_common_terminal_coax640' if name.startswith('coax') else 'finite_length_longitudinal_PEEC' if name.startswith('peec') else 'round_wire_Bessel',execution_status='archived_completed')
  if name in ['coax_rdc','coax_rac_rdc']:result[name]['parameter_source']=dict(path='configs/reference_parameters.json',sha256=sha(ROOT/'configs/reference_parameters.json'))
 result['coax_voltage_re']['complex_quantity']={'real':voltage.real,'imag':voltage.imag,'magnitude':abs(voltage),'phase_deg':math.degrees(math.atan2(voltage.imag,voltage.real)),'unit':'V/m','unit_basis':'common axial terminal electric field of the two-dimensional formulation'}
 return result

def blocks(path):
 text=Path(path).read_text(encoding='utf-8');parts=re.split(r'<!-- id: ([\w.]+) -->\s*',text)
 if parts[0].strip():raise ValueError('Every authoring block requires a stable identity: '+str(path))
 result=[{'id':parts[i],'markdown':parts[i+1].strip()} for i in range(1,len(parts),2)]
 if len({x['id'] for x in result})!=len(result):raise ValueError('Duplicate paragraph identity')
 return result

def numbering(m,edition):
 doc=m['edition'][edition];found={'equation':[],'figure':[]}
 for ch in doc['chapters']:
  text=(ROOT/ch['sources'][m.get('numbering_language','en')]).read_text(encoding='utf-8')
  for kind,key in re.findall(r'\{\{(equation|figure):([\w]+)\}\}',text):
   if key in found[kind]:raise ValueError('One display location required: '+key)
   found[kind].append(key)
 return {kind:{key:i+1 for i,key in enumerate(ids)} for kind,ids in found.items()}

def reference_text(r,num):return f"[{num}] {', '.join(r['authors'])}. {r['title']}. {r['venue']}, {r['year']}. "+('https://doi.org/'+r['doi'] if r.get('doi') else r.get('url',''))

def tex_escape(s):
 result=[]
 for c in s:result.append({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','∇':r'\(\nabla\)','∈':r'\(\in\)','∫':r'\(\int\)','Σ':r'\(\sum\)','ᴴ':r'\(^{\mathrm H}\)','ᵀ':r'\(^{\mathrm T}\)','₀':r'\(_0\)','₁':r'\(_1\)','ₐ':r'\(_a\)','ᵃ':r'\(^a\)','∂':r'\(\partial\)','₂':r'\(_2\)','↦':r'\(\mapsto\)','ℓ':r'\(\ell\)','→':r'\(\to\)'}.get(c,c))
 return ''.join(result)

def display_text(text,nums,quantities,refnums,lang):
 def token(match):
  kind,key=match.groups()
  if kind=='metric':return quantities[key]['formatted']
  if kind=='eqref':return '('+str(nums['equation'][key])+')'
  if kind=='figref':return ('图 ' if lang=='zh-CN' else 'Fig. ')+str(nums['figure'][key])
  raise ValueError('Unresolved inline token '+match[0])
 text=re.sub(r'\{\{(metric|eqref|figref):([\w]+)\}\}',token,text)
 text=re.sub(r'\[@([^\]]+)\]',lambda x:'['+', '.join(str(refnums[y.strip().lstrip('@')]) for y in x[1].split(';'))+']',text)
 return text

def references_in(text):return list(dict.fromkeys(y.strip().lstrip('@') for x in re.findall(r'\[@([^\]]+)\]',text) for y in x.split(';')))

def copy_assets(run,m):
 base=input_path(m['panel_run']);records=[]
 # Each final attachment has one owner selected before files are copied.
 for folder in ['panels','tables','annotations']:
  expected={p.relative_to(base):p for p in (base/folder).rglob('*') if p.is_file()}
  if folder=='panels':
   for fid,source_run in m.get('panel_overrides',{}).items():
    expected={rel:p for rel,p in expected.items() if not rel.name.startswith(fid+'.')}
    for lang in ['zh-CN','en']:
     owner=ROOT/source_run
     files=list((owner/'panels'/lang).glob(fid+'.*'))
     if not files:raise ValueError('Required panel family '+fid+' '+lang)
     expected.update({p.relative_to(owner):p for p in files})
  for relative,original in sorted(expected.items()):
   p=run/relative;p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():shutil.copy2(original,p)
   if sha(original)!=sha(p):raise ValueError('Verified asset bytes '+str(p))
   records.append(dict(path=relative.as_posix(),source=original.relative_to(ROOT).as_posix(),sha256=sha(p)))
  actual={p.relative_to(run) for p in (run/folder).rglob('*') if p.is_file()}
  if actual!=set(expected):raise ValueError('Attachment set requires a fresh run ID: '+folder)
 write(run/'asset_sources.json',records)
 # Composition is derived from the independently exported, byte-verified panels.
 from BuildPublicationEdition import compose
 panel_manifest=read(base/'panel_manifest.json')
 for panel in panel_manifest['panels']:
  override=m.get('panel_overrides',{}).get(panel['id'])
  if override:
   replacement=next(x for x in read(ROOT/override/'panel_manifest.json')['panels'] if x['id']==panel['id'] and x['language']==panel['language'])
   panel.update(replacement)
  for asset in panel['assets']:
   relative='panels/'+panel['language']+'/'+Path(asset['path']).name
   asset.update(path=str(run/relative),path_relative_to_run=relative,sha256=sha(run/relative))
  owner=next((f for f in m['figures'].values() if panel['id'] in f['panels']),None)
  if owner:panel['caption']=owner['title'][panel['language']]+' '+owner['descriptions']['report'][panel['language']]
 write(run/'panel_manifest.json',panel_manifest)
 write(run/'render_request.json',{'composition_groups':[(k,f['panels']) for k,f in m['figures'].items() if len(f['panels'])>1]})
 compose(run)
 import pypdfium2 as pdfium
 for pdf in (run/'composites').rglob('*.pdf'):
  doc=pdfium.PdfDocument(str(pdf));page=doc[0];bitmap=page.render(scale=300/72);bitmap.to_pil().save(pdf.with_suffix('.png'));bitmap.close();page.close();doc.close()

def table_cells(run,lang='en'):
 tables=[]
 specs=[
  ('q1_fem2_convergence.csv',('单圆线二维校准','Round-wire two-dimensional calibration'),[('nodes','节点数','Nodes',1),('h_over_a','h/a','h/a',1),('Rac_ohm_per_m','Rac (mΩ/m)','Rac (mΩ/m)',1000),('Rac_relative_error','电阻相对误差','Relative resistance error',1)]),
  ('peec_length.csv',('纵向 PEEC 长度敏感性','Longitudinal PEEC length sensitivity'),[('filaments','自由度','Degrees of freedom',1),('length_m','长度 (m)','Length (m)',1),('Rac_ohm_per_axial_m','Rac (mΩ/轴向m)','Rac (mΩ/axial m)',1000),('Rac_over_Rdc','Rac/Rdc','Rac/Rdc',1)]),
  ('rt0_cases.csv',('RT0 外场损耗与积分阶数','RT0 imposed-field loss and quadrature order'),[('cells','单元数','Cells',1),('q','积分阶数','Quadrature order',1),('recomputed_loss_W','损耗 (mW)','Loss (mW)',1000)]),
  ('gpu_equivalence.csv',('CPU/GPU 同模型对照','CPU/GPU comparison for the same model'),[('filaments','自由度','Degrees of freedom',1),('L_matrix_relative_error','电感矩阵相对差','Relative inductance difference',1),('current_relative_error','复电流相对差','Relative current difference',1)])]
 for name,titles,cols in specs:
  rs=rows(run/'tables'/name)
  if not rs:continue
  index=1 if lang=='zh-CN' else 2
  table_rows=[[c[index] for c in cols]]+[[format(float(r[c[0]])*c[3],'.6g') for c in cols] for r in rs]
  tables.append(dict(type='table',title=titles[index-1],rows=table_rows,source='tables/'+name,display_columns=[dict(field=c[0],scale=c[3]) for c in cols]))
 sensitivity=[r for r in rows(run/'tables/peec_sensitivity.csv') if r['acceptance_metric']]
 headers=['图中编号','单因素比较','图示相对变化 (%)'] if lang=='zh-CN' else ['Plot index','Single-factor comparison','Plotted relative change (%)']
 labels=[r['display_label'].replace('m40','1264 自由度').replace('m80','5024 自由度') if lang=='zh-CN' else r['id'] for r in sensitivity]
 tables.append(dict(type='table',title='PEEC 敏感性图的编号与量值' if lang=='zh-CN' else 'PEEC sensitivity plot indices and values',rows=[headers]+[[str(i+1),labels[i],format(100*float(r['acceptance_metric']),'.6g')] for i,r in enumerate(sensitivity)],source='tables/peec_sensitivity.csv',display_scale=100))
 return tables

def figure(run,m,edition,lang,fid,num):
 spec=m['figures'][fid];ps=spec['panels'];folder='composites' if len(ps)>1 else 'panels';asset=f'{folder}/{lang}/{fid}'
 for suffix in ['.pdf','.png']:
  if not (run/(asset+suffix)).exists():raise FileNotFoundError(asset+suffix)
 return dict(type='figure',id=fid,number=num,panels=[f'panels/{lang}/{p}.wl' for p in ps],panel_ids=ps,pdf=asset+'.pdf',png=asset+'.png',width_mm=182 if len(ps)>1 else 88.9,title=('图 ' if lang=='zh-CN' else 'Fig. ')+str(num)+'. '+spec['title'][lang],description=spec['descriptions'][edition][lang],source_models=spec['source_models'])

def source_cells(run,m):
 return [dict(type='text',text='来源清单 / Source manifest: source_provenance.json; quantities.json; asset_sources.json.'),dict(type='table',title='冻结来源与完整性 / Frozen sources and integrity',rows=[['Source','SHA256']]+[[p,h] for p,h in m['scientific_hashes'].items()])]

def chapter(run,m,ed,lang,ch,nums,quantities):
 label=str(int(ch['id'])) if ch['id'].isdigit() else ch['id']
 refnums={r['id']:i+1 for i,r in enumerate(m['references'])};cells=[dict(type='heading',level=1,text=label+' '+ch['title'][lang],tag='chapter-'+ch['id'])];refs=[];ast=blocks(ROOT/ch['sources'][lang]);parser=MarkdownIt('commonmark').enable('table').use(dollarmath_plugin);subsection=0
 for block in ast:
  text=block['markdown'];refs.extend(references_in(text));marker=re.fullmatch(r'\{\{(equation|figure):([\w]+)\}\}',text)
  if marker:
   kind,key=marker.groups()
   c=dict(type='equation',id=key,number=nums['equation'][key],**m['equations'][key]) if kind=='equation' else figure(run,m,ed,lang,key,nums['figure'][key]);cells.append(c)
  elif text=='{{sources}}':cells+=source_cells(run,m)
  elif text=='{{tables}}':cells+=table_cells(run,lang)
  else:
   parsed=parser.parse(text)
   if parsed and parsed[0].type=='heading_open':
    subsection+=1
    cells.append(dict(type='heading',level=2,text=label+'.'+str(subsection)+' '+display_text(parsed[1].content,nums,quantities,refnums,lang),tag=block['id']))
   else:
    # CommonMark parses the prose boundary; shared inline identities resolve before rendering.
    inline=[t.content for t in parsed if t.type=='inline'];links=[dict(text='('+str(nums['equation'][key])+')',tag=key,markdown=ed+'_'+lang+'.md#'+key) for key in re.findall(r'\{\{eqref:([\w]+)\}\}',text)]
    cells.append(dict(type='text',text=display_text('\n'.join(inline),nums,quantities,refnums,lang),id=block['id'],links=links))
 return {'id':ch['id'],'title':ch['title'][lang],'cells':cells,'block_ids':[b['id'] for b in ast],'references':list(dict.fromkeys(refs)),'source':ch['sources'][lang],'source_sha256':sha(ROOT/ch['sources'][lang])}

def markdown_cells(cells):
 out=[]
 for c in cells:
  t=c['type']
  if t=='heading':out+=['<a id="'+c['tag']+'"></a>','#'*(c['level']+1)+' '+c['text'],'']
  elif t=='text':
   text=c['text']
   for link in c.get('links',[]):text=text.replace(link['text'],'['+link['text']+']('+link['markdown']+')')
   out+=[text,'']
  elif t=='equation':out+=['<a id="'+c['id']+'"></a>','$$',c['latex']+r'\tag{'+str(c['number'])+'}','$$','']
  elif t=='figure':out+=['<a id="fig-'+c['id']+'"></a>','![Fig. '+str(c['number'])+'](../../../'+c['png']+')','','<p align="center">'+c['title']+'</p>','',c['description'],'']
  elif t=='table':
   rs=c['rows'];out+=[c['title'],'','| '+' | '.join(rs[0])+' |','| '+' | '.join(['---']*len(rs[0]))+' |']+['| '+' | '.join(r)+' |' for r in rs[1:]]+['']
 return '\n'.join(out)

def build_documents(run,m,args):
 quantities=read(run/'quantities.json');docs=[];nb=[]
 for ed in (['report','paper'] if args.edition=='all' else [args.edition]):
  from litz_research.references import publication_references,citation_order
  keys=citation_order(ROOT,m,ed)
  m['references']=publication_references(ROOT,keys+[r['id'] for r in m['references'] if r['id'] not in keys])
  maps=read(run/'citation_maps.json') if (run/'citation_maps.json').exists() else {}
  maps[ed]={r['id']:i+1 for i,r in enumerate(m['references'])};write(run/'citation_maps.json',maps)
  nums=numbering(m,ed)
  for lang in (['zh-CN','en'] if args.language=='all' else [args.language]):
   chapters=[chapter(run,m,ed,lang,ch,nums,quantities) for ch in m['edition'][ed]['chapters']]
   merged_id=ed+'_'+lang;common={'edition':ed,'language':lang,'author':m['author'][lang],'affiliation':m['affiliation'][lang]}
   refnums={r['id']:i+1 for i,r in enumerate(m['references'])}
   def refcells(keys):return [dict(type='heading',level=1,text='参考文献' if lang=='zh-CN' else 'References',tag='references')]+[dict(type='text',text=reference_text(r,refnums[r['id']])) for r in m['references'] if r['id'] in keys]
   abstract=display_text(m['edition'][ed]['abstract'][lang],nums,quantities,refnums,lang)
   merged=dict(id=merged_id,title=m['edition'][ed]['title'][lang],form='merged',**common,cells=[dict(type='heading',level=1,text='摘要' if lang=='zh-CN' else 'Abstract',tag='abstract'),dict(type='text',text=abstract),dict(type='text',text=('关键词：' if lang=='zh-CN' else 'Keywords: ')+m['keywords'][lang])]+[c for ch in chapters for c in ch['cells']],block_ids=[x for ch in chapters for x in ch['block_ids']],references=list(dict.fromkeys(x for ch in chapters for x in ch['references'])),chapters=chapters,numbering=nums)
   selected=[]
   if args.form in ['all','merged']:selected.append(merged)
   if args.form in ['all','chapters']:
    for ch in chapters:selected.append(dict(id=merged_id+'_'+ch['id'],title=m['edition'][ed]['title'][lang]+' · '+ch['id']+' '+ch['title'],form='chapter',**common,cells=ch['cells'],block_ids=ch['block_ids'],references=ch['references'],parent=merged_id,chapter=ch['id'],numbering=nums))
   for d in selected:
    folder=run/'documents'/ed/lang;folder.mkdir(parents=True,exist_ok=True);md=folder/(d['id']+'.md')
    d['markdown']=md.relative_to(run).as_posix();d['notebook']='notebooks/publication/'+run.name+'/'+ed+'/'+lang+'/'+d['id']+'.nb'
    content=markdown_cells(d['cells']);d['content_sha256']=hashlib.sha256(content.encode()).hexdigest()
    header='# '+d['title']+'\n\n'+d['author']+' · '+d['affiliation']+'\n\n'
    if d['form']=='chapter':header+='['+('合并稿' if lang=='zh-CN' else 'Merged manuscript')+']('+d['parent']+'.md#chapter-'+d['chapter']+')\n\n'
    else:header+='\n'.join('- ['+ch['id']+' '+ch['title']+'](#chapter-'+ch['id']+')' for ch in chapters)+'\n\n'
    md.write_text(header+content+markdown_cells(refcells(d['references'])),encoding='utf-8');d['markdown_sha256']=sha(md)
    d['references_cells']=refcells(d['references']);docs.append(d)
    nb.append(dict(id=d['id'],title=d['title'],language=lang,edition=ed,path=os.path.relpath(ROOT/d['notebook'],run).replace('\\','/'),cells=[dict(type='text',text=d['author']+' · '+d['affiliation'])]+d['cells']+d['references_cells']))
 write(run/'document_structure.json',docs)
 write(run/'document_request.json',dict(run_id=run.name,output_directory=str(run),documents=nb,composites=[]))
 write(run/'document_manifest.json',{'run_id':run.name,'documents':[{k:v for k,v in d.items() if k not in ['cells','chapters','references_cells']} for d in docs],'notebook_count':len(nb),'source_manifest_sha256':sha(ROOT/args.source_manifest)})
 print('documents',len(docs),flush=True)

def equations_tex(c):
 # Semantic line boundaries keep the traditional mathematical font at reading size.
 source=c['latex'].rstrip('.')
 if c['id'] in ['E01','E02','E03','E05','E08','E09']:
  parts=re.split(r',?\s*\\(?:qquad|quad)\s*',source)
  return '\n'.join([r'\hypertarget{'+c['id']+'}{}',r'\begin{equation}',r'\begin{gathered}',(r' \\'+'\n').join(parts),r'\end{gathered}',r'\tag{'+str(c['number'])+'}'+r'\label{eq:'+c['id']+'}',r'\end{equation}'])
 return r'\hypertarget{'+c['id']+'}{}'+r'\begin{equation}'+source+r'\tag{'+str(c['number'])+'}'+r'\label{eq:'+c['id']+'}'+r'\end{equation}'

def layout_cells(cells,layout):
 """Place adjacent independent single-column figures side by side in reading PDFs."""
 i=0
 while i<len(cells):
  c=cells[i]
  if layout=='single' and c['type']=='figure' and c['width_mm']<90 and i+1<len(cells) and cells[i+1]['type']=='figure' and cells[i+1]['width_mm']<90:
   yield dict(type='figure_pair',figures=[c,cells[i+1]])
   i+=2
  else:
   yield c
   i+=1

def figure_tex(c):
 return [r'\centering',r'\setcounter{figure}{'+str(c['number']-1)+'}',r'\refstepcounter{figure}\label{fig:'+c['id']+'}',r'\hypertarget{fig-'+c['id']+'}{}',r'\includegraphics[width='+str(c['width_mm'])+'mm]{../../../'+c['pdf']+'}',r'\par\vspace{4pt}{\small\centering '+tex_escape(c['title'])+r'\par}',r'\vspace{3pt}{\small\raggedright '+tex_escape(c['description'])+r'\par}']

def latex_source(run,m,d,layout):
 ieee=layout=='ieee';tex=[]
 if ieee:tex+=[r'\documentclass[journal,10pt]{IEEEtran}',r'\setlength{\textwidth}{182mm}',r'\setlength{\columnsep}{4.2mm}']
 else:tex+=[r'\documentclass[11pt]{article}',r'\usepackage[paperwidth=210mm,paperheight=297mm,textwidth=182mm,top=20mm,bottom=22mm]{geometry}']
 tex += [r'\usepackage{amsmath,amssymb,newtxmath}',r'\usepackage[no-math]{fontspec}',r'\setmainfont{Times New Roman}',r'\usepackage{xeCJK}',r'\setCJKmainfont[AutoFakeBold=2]{SimSun}',r'\usepackage{graphicx,booktabs,array,hyperref,placeins}',r'\hypersetup{hidelinks,unicode=true}',r'\raggedbottom',r'\setlength{\emergencystretch}{2em}',r'\renewcommand{\arraystretch}{1.15}',r'\begin{document}',r'\title{'+tex_escape(d['title'])+'}']
 # Reading layout keeps text, equations and floats in a shared visual rhythm.
 preamble=[r'\renewcommand{\topfraction}{0.92}',r'\renewcommand{\bottomfraction}{0.82}',r'\renewcommand{\textfraction}{0.08}',r'\renewcommand{\floatpagefraction}{0.65}',r'\setcounter{topnumber}{3}',r'\setcounter{bottomnumber}{2}',r'\setcounter{totalnumber}{4}',r'\setlength{\textfloatsep}{12pt plus 3pt minus 2pt}',r'\setlength{\floatsep}{10pt plus 2pt minus 2pt}',r'\setlength{\intextsep}{12pt plus 2pt minus 2pt}',r'\makeatletter',r'\setlength{\@fptop}{0pt}',r'\setlength{\@fpsep}{14pt}',r'\setlength{\@fpbot}{0pt plus 1fil}',r'\makeatother']
 if not ieee:preamble += [r'\linespread{1.16}',r'\setlength{\parindent}{2em}',r'\setlength{\parskip}{3pt plus 1pt}',r'\makeatletter',r'\renewcommand{\section}{\@startsection{section}{1}{0pt}{2.0ex plus .4ex}{.9ex}{\normalfont\large\bfseries}}',r'\renewcommand{\subsection}{\@startsection{subsection}{2}{0pt}{1.5ex plus .3ex}{.6ex}{\normalfont\normalsize\bfseries}}',r'\makeatother']
 tex[tex.index(r'\begin{document}'):tex.index(r'\begin{document}')]=preamble
 tex += [r'\author{'+tex_escape(d['author'])+(r'\\' if not ieee else r'\thanks{')+tex_escape(d['affiliation'])+('}' if ieee else '')+'}',r'\date{}' if not ieee else '',r'\maketitle']
 if d['form']=='chapter':tex += [r'\noindent '+tex_escape('合并稿对应章节 / Chapter in merged manuscript: ')+r'\href{'+d['parent']+'_'+layout+'.pdf#chapter-'+d['chapter']+'}{'+tex_escape(d['chapter'])+r'}\par']
 for c in layout_cells(d['cells'],layout):
  t=c['type']
  if t=='heading':
   if c['level']==1:tex += [r'\clearpage' if c['tag']=='chapter-S1' else r'\FloatBarrier']
   command='section' if c['level']==1 else 'subsection';tex += ['\\'+command+'*{'+tex_escape(c['text'])+'}',r'\hypertarget{'+c['tag']+'}{}',r'\pdfbookmark['+str(c['level']-1)+']{'+tex_escape(c['text'])+'}{bookmark-'+c['tag']+'}']
  elif t=='text':
   text=tex_escape(c['text'])
   for link in c.get('links',[]):
    destination=d.get('parent',d['id'])+'_'+layout+'.pdf#'+link['tag']
    text=text.replace(link['text'],r'\href{'+destination+'}{'+link['text']+'}')
   tex += [text+'\n\n']
  elif t=='equation':tex += [equations_tex(c)]
  elif t=='figure_pair':
   tex += [r'\begin{figure}[!htbp]',r'\centering']
   for index,panel in enumerate(c['figures']):
    if index:tex += [r'\hfill']
    tex += [r'\begin{minipage}[t]{88.9mm}',r'\vspace{0pt}']+figure_tex(panel)+[r'\end{minipage}']
   tex += [r'\end{figure}']
  elif t=='figure':
   full=c['width_mm']>90;env='figure*' if ieee and full else 'figure';path='../../../'+c['pdf']
   tex += [r'\begin{'+env+'}[!htbp]']+figure_tex(c)+[r'\end{'+env+'}']
  elif t=='table':
   # Table values retain source units. Source hashes are typeset as breakable strings.
   rs=c['rows'];n=len(rs[0]);env='table*' if ieee else 'table';width=r'\textwidth'
   tex += [r'\begin{'+env+'}[!htbp]',r'\centering{\footnotesize '+tex_escape(c['title'])+r'}\par',r'\begingroup\footnotesize\begin{tabular}{'+('|'.join('p{'+str((177.8-4*n)/n)+'mm}' for _ in range(n)))+'}',r'\toprule']
   def breakable(v):return r'\seqsplit{'+tex_escape(v)+'}' if re.fullmatch('[0-9a-f]{64}',v) else tex_escape(v).replace(r'\_',r'\_\allowbreak ')
   tex += [' & '.join(breakable(v) for v in row)+r'\\' for row in rs];tex += [r'\bottomrule\end{tabular}\endgroup',r'\end{'+env+'}']
 refnums={r['id']:i+1 for i,r in enumerate(m['references'])}
 if d['references']:
  tex += [r'\clearpage',r'\renewcommand{\refname}{'+('参考文献' if d['language']=='zh-CN' else 'References')+'}',r'\begin{thebibliography}{99}']
  for r in m['references']:
   if r['id'] in d['references']:tex += [r'\bibitem['+str(refnums[r['id']])+']{'+r['id']+'} '+tex_escape(reference_text(r,refnums[r['id']]).split('] ',1)[1])]
  tex += [r'\end{thebibliography}']
 tex += [r'\end{document}']
 # seqsplit is used only for fixed-length integrity strings.
 tex.insert(tex.index(r'\begin{document}'),r'\usepackage{seqsplit}')
 return '\n'.join(tex)+'\n'

def prepare_latex(run,m,args):
 shutil.copy2(ROOT/'latex/IEEEtran.cls',run/'IEEEtran.cls');shutil.copy2(ROOT/m['bibtex'],run/'references.bib')
 docs=read(run/'document_structure.json');records=[]
 for d in docs:
  folder=run/'documents'/d['edition']/d['language'];shutil.copy2(ROOT/'latex/IEEEtran.cls',folder/'IEEEtran.cls')
  for layout in (['single','ieee'] if args.layout=='all' else [args.layout]):
   p=folder/(d['id']+'_'+layout+'.tex');p.write_text(latex_source(run,m,d,layout),encoding='utf-8');records.append(dict(document=d['id'],layout=layout,tex=p.relative_to(run).as_posix(),pdf=p.with_suffix('.pdf').relative_to(run).as_posix(),source_sha256=sha(p)))
 write(run/'pdf_manifest.json',records)

def compile_pdfs(run):
 from BuildLaTexSmoke import environment
 env=environment();env['CUDA_VISIBLE_DEVICES']=''
 from litz_research.common import tool
 xe=tool(ROOT,'xelatex');mk=tool(ROOT,'latexmk')
 if not all([xe,mk]):raise RuntimeError('Persisted XeLaTeX and latexmk environment required')
 write(run/'compiler_versions.json',{name:subprocess.check_output([p,'--version'] if name!='latexmk' else [p,'-v'],env=env,text=True,errors='replace').splitlines()[:5] for name,p in [('xelatex',xe),('latexmk',mk)]})
 # Reference lists are rendered from the canonical parsed library and shared citation maps.
 state=read(run/'compile_status.json') if (run/'compile_status.json').exists() else {};records=read(run/'pdf_manifest.json')
 for i,record in enumerate(records):
  p=run/record['tex'];key=p.stem;prior=state.get(key,{})
  if prior.get('source_sha256')==sha(p) and (run/record['pdf']).exists() and prior.get('pdf_sha256')==sha(run/record['pdf']):continue
  start=time.monotonic();cmd=[mk,'-xelatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','-silent','-e',r'$xelatex=q/xelatex --enable-installer --no-shell-escape %O %S/;',p.name]
  with (p.parent/(key+'_compile.txt')).open('w',encoding='utf-8') as f:r=subprocess.run(cmd,cwd=p.parent,env=env,stdout=f,stderr=subprocess.STDOUT)
  state[key]=dict(actual_exit_code=r.returncode,elapsed_seconds=time.monotonic()-start,source_sha256=sha(p),pdf_sha256=sha(run/record['pdf']) if (run/record['pdf']).exists() else None)
  write(run/'compile_status.json',state);print('PDF',i+1,'/',len(records),key,'exit',r.returncode,flush=True)
  if r.returncode:raise RuntimeError('PDF compile failed '+key+'; diagnostic '+str(p.parent/(key+'_compile.txt')))

def verify(run,m):
 checks=[]
 def check(name,v):checks.append(dict(name=name,passed=bool(v)))
 for path,h in m['scientific_hashes'].items():check('science/'+path,sha(input_path(path))==h)
 exported_quantities=read(run/'quantities.json')
 for key,expected in metrics(m).items():check('quantity/'+key,exported_quantities[key]==expected)
 docs=read(run/'document_structure.json')
 for d in docs:
  check(d['id']+'/markdown_hash',sha(run/d['markdown'])==d['markdown_sha256'])
  check(d['id']+'/tokens_resolved','{{' not in (run/d['markdown']).read_text(encoding='utf-8'))
  if d['form']=='chapter':
   parent=next(x for x in docs if x['id']==d['parent']);ch=next(x for x in parent['chapters'] if x['id']==d['chapter']);check(d['id']+'/verbatim_cells',d['cells']==ch['cells'])
   check(d['id']+'/verbatim_markdown',markdown_cells(d['cells']) in (run/parent['markdown']).read_text(encoding='utf-8'))
  else:
   ids=[c['id'] for c in d['cells'] if c['type']=='figure'];check(d['id']+'/figure_display_unique',len(ids)==len(set(ids)))
 for ed in ['report','paper']:
  ds=[d for d in docs if d['edition']==ed and d['form']=='merged']
  if len(ds)==2:check(ed+'/paired_blocks',ds[0]['block_ids']==ds[1]['block_ids']);check(ed+'/paired_numbering',ds[0]['numbering']==ds[1]['numbering'])
 if (run/'compile_status.json').exists():
  from pypdf import PdfReader
  pdfchecks=[];previews=run/'pdf_previews';previews.mkdir(exist_ok=True)
  import pypdfium2 as pdfium
  for r in read(run/'pdf_manifest.json'):
   path=run/r['pdf'];key=path.stem;reader=PdfReader(path);log=path.with_suffix('.log').read_text(encoding='utf-8',errors='replace');text='\n'.join(p.extract_text() for p in reader.pages)
   compiled=read(run/'compile_status.json')[key]
   check(key+'/source_hash',sha(run/r['tex'])==r['source_sha256']==compiled['source_sha256']);check(key+'/compiled_hash',sha(path)==compiled['pdf_sha256'] and compiled['actual_exit_code']==0)
   check(key+'/exists',len(reader.pages)>0);check(key+'/resolved_references','??' not in text and not re.search(r'undefined references|Citation .* undefined|Missing character:',log));check(key+'/boxes',not re.search(r'Overfull \\[hv]box',log))
   source_doc=next(d for d in docs if d['id']==r['document'])
   for eq in [c['id'] for c in source_doc['cells'] if c['type']=='equation']:check(key+'/destination/'+eq,eq in reader.named_destinations)
   fonts=[];seen=set()
   def resources(res):
    if not res:return
    res=res.get_object()
    for f in res.get('/Font',{}).get_object().values() if hasattr(res.get('/Font',{}),'get_object') else res.get('/Font',{}).values():
     f=f.get_object();des=[f['/FontDescriptor'].get_object()] if '/FontDescriptor' in f else []
     for df in f.get('/DescendantFonts',[]):
      df=df.get_object()
      if '/FontDescriptor' in df:des.append(df['/FontDescriptor'].get_object())
     fonts.append(dict(name=str(f.get('/BaseFont')),embedded=any(any(k in d for k in ['/FontFile','/FontFile2','/FontFile3']) for d in des)))
    for f in res.get('/XObject',{}).get_object().values() if hasattr(res.get('/XObject',{}),'get_object') else res.get('/XObject',{}).values():
     uid=getattr(f,'idnum',id(f))
     if uid in seen:continue
     seen.add(uid);resources(f.get_object().get('/Resources'))
   for p in reader.pages:resources(p.get('/Resources'))
   check(key+'/embedded_fonts',all(f['embedded'] for f in fonts))
   doc=pdfium.PdfDocument(str(path));pages=[]
   for n in range(len(doc)):
    p=doc[n];bmp=p.render(scale=100/72);im=bmp.to_pil();dest=previews/(key+f'_page_{n+1:03}.png');im.save(dest);pages.append(dest.relative_to(run).as_posix());bmp.close();p.close()
   doc.close();pdfchecks.append(dict(id=key,pages=len(reader.pages),fonts=fonts,rendered_pages=pages,pdf_sha256=sha(path)))
  write(run/'pdf_verification_details.json',pdfchecks)
 if (run/'notebook_verification.json').exists():
  v=read(run/'notebook_verification.json')
  check('notebook/count',len(v['notebooks'])==len(docs));check('notebook/failures',not v['failures'])
  for n in v['notebooks']:
   check(n['id']+'/frontend',n['saved_reopened'] and n['all_cells_rendered'] and n['viewpoint_roundtrip']);check(n['id']+'/saved_hash',sha(run/n['path'])==n['sha256'])
 write(run/'edition_verification.json',dict(checks=checks,failed_checks=sum(not c['passed'] for c in checks),physical_solver_calls=0))
 if any(not c['passed'] for c in checks):raise RuntimeError('Edition verification diagnostics: '+str(run/'edition_verification.json'))

def package(run,m):
 if read(run/'edition_verification.json')['failed_checks']:raise ValueError('Verified edition required')
 selected=[]
 for folder in ['documents','panels','composites','tables','annotations','source_snapshot','stage_sources']:
  selected.extend(p for p in (run/folder).rglob('*') if p.is_file() and p.suffix in ['.md','.tex','.pdf','.nb','.wl','.svg','.png','.csv','.json','.bib','.py','.wls','.cls'])
 metadata=['input_manifest.json','environment.json','source_provenance.json','asset_sources.json','quantities.json','document_manifest.json','document_structure.json','document_request.json','pdf_manifest.json','compiler_versions.json','compile_status.json','notebook_verification.json','pdf_verification_details.json','edition_verification.json','panel_manifest.json','composite_manifest.json','visual_sheet_manifest.json','visual_review.json','caption_verification.json']
 selected+=[run/name for name in metadata if (run/name).is_file()]+[run/'references.bib']
 archive=run/'Litz_publication_package.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  for p in selected:z.write(p,p.relative_to(run).as_posix())
  for d in read(run/'document_structure.json'):z.write(ROOT/d['notebook'],'notebooks/'+d['id']+'.nb')
  source_files=[p for p in (ROOT/'manuscript').rglob('*') if p.is_file()]+[p for p in (ROOT/'src').iterdir() if p.is_file() and p.suffix in ['.py','.wl','.wls','.ps1']]
  source_files += [p for p in (ROOT/'python/litz_research').rglob('*.py')]+[ROOT/p for p in ['pyproject.toml','README.zh-CN.md','LICENSE','CITATION.cff','requirements-windows-py312.lock']]+[p for p in (ROOT/'LICENSES').iterdir() if p.is_file()]+[p for p in (ROOT/'docs').rglob('*.md')]
  source_files += [p for folder in ['models','adapters','shared','automation','tools','references','configs'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.wl','.wls','.wlt','.ps1','.json','.md','.toml','.bib','.nb']]
  source_files += [ROOT/'data/catalog.json',ROOT/'AGENTS.md']
  source_files=list(dict.fromkeys(source_files))
  source_files += [p for p in (ROOT/'latex').iterdir() if p.is_file()]
  for p in source_files:z.write(p,p.relative_to(ROOT).as_posix())
  portable=json.loads(json.dumps(m));portable.update(panel_run='.',panel_overrides={},frozen_bundle='datasets/closure',package_run_id=run.name+'__portable')
  portable_manifest=json.dumps(portable,ensure_ascii=False,indent=2)+'\n';z.writestr('manuscript/publication_portable.json',portable_manifest)
  extra_files=[]
  for relative,identity in m['scientific_hashes'].items():
   z.write(input_path(relative),relative);extra_files.append(dict(path=relative,sha256=identity))
  frozen=input_path(m['frozen_bundle'])/'routes/coax640/data.json';z.write(frozen,'datasets/closure/routes/coax640/data.json');extra_files.append(dict(path='datasets/closure/routes/coax640/data.json',sha256=sha(frozen)))
  for p in (input_path(m['panel_run'])/'field_data').glob('*'):
   if p.is_file():z.write(p,'field_data/'+p.name);extra_files.append(dict(path='field_data/'+p.name,sha256=sha(p)))
  extra_files.append(dict(path='manuscript/publication_portable.json',sha256=hashlib.sha256(portable_manifest.encode()).hexdigest()))
  instructions='# Litz portable publication edition\n\nMiao Yuxuan · Huainan Normal University.\n\nMerged texts and chapter excerpts are in documents/; native notebooks are in notebooks/. Independent panels and compositions are in panels/ and composites/. Field samples and complete numeric tables are in field_data/ and tables/.\n\nInstall the package in a Python virtual environment and configure Wolfram and XeLaTeX for the corresponding stages:\n\n```powershell\npython -m pip install -e ".[documents,figures]"\n./src/RunPublicationEdition.ps1 -RunId portable_YYYYMMDD_01 -SourceManifest manuscript/publication_portable.json -Stage all\n```\n\nCanonical Markdown sources and shared identities are in manuscript/. Research datasets retain original solver projects, checkpoint arrays and execution logs, with identities recorded in the source catalog.\n'
  z.writestr('README.md',instructions);extra_files.append(dict(path='README.md',sha256=hashlib.sha256(instructions.encode()).hexdigest()))
 write(run/'package_manifest.json',dict(archive=archive.name,sha256=sha(archive),files=[dict(path=p.relative_to(run).as_posix(),sha256=sha(p)) for p in selected]+[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in source_files]+extra_files,notebooks=[dict(path=d['notebook'],sha256=sha(ROOT/d['notebook'])) for d in read(run/'document_structure.json')],portable_source_manifest='manuscript/publication_portable.json',raw_archive_scope='Original solver projects, checkpoint arrays and logs are indexed in the complete repository archive.'))

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--edition',choices=['report','paper','all'],default='all');p.add_argument('--language',choices=['zh-CN','en','all'],default='all');p.add_argument('--source-manifest',default='manuscript/publication.json');p.add_argument('--form',choices=['merged','chapters','all'],default='all');p.add_argument('--layout',choices=['single','ieee','all'],default='all');p.add_argument('--stage',choices=['preflight','specimen','panels','compose','documents','notebooks','pdf','verify','package','all'],default='all');a=p.parse_args(argv)
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):p.error('Run ID: letters, digits, underscore and hyphen')
 run=ROOT/'outputs'/a.run_id;m=read(ROOT/a.source_manifest);run.mkdir(exist_ok=True)
 from litz_research.references import publication_references
 m['references']=publication_references(ROOT,[r['id'] for r in m['references']])
 input_hash=sha(ROOT/a.source_manifest)
 if (run/'input_manifest.json').exists() and sha(run/'input_manifest.json')!=input_hash:raise ValueError('Input manifest changed: select a new run ID')
 if not (run/'input_manifest.json').exists():shutil.copy2(ROOT/a.source_manifest,run/'input_manifest.json')
 for file,h in m['scientific_hashes'].items():
  if sha(input_path(file))!=h:raise ValueError('Frozen source integrity '+file)
 from BuildLaTexSmoke import environment
 import PreManuscriptClosure as control
 hardware=control.hardware();write(run/'environment.json',hardware)
 if hardware['free_RAM_bytes']<8*control.GIB:raise RuntimeError('System free-memory reserve: 8 GiB required')
 snapshot=run/'source_snapshot';snapshot.mkdir(exist_ok=True)
 for file in list((ROOT/'tools/publication').glob('Publication*.py'))+[ROOT/'tools/publication/BuildPublicationEdition.py',ROOT/'tools/publication/BuildPublicationDocuments.wls',ROOT/'tools/publication/PublicationStyles.wl']:
  dest=snapshot/file.name
  if not dest.exists():shutil.copy2(file,dest)
 stage_sources=run/'stage_sources'/a.stage;stage_sources.mkdir(parents=True,exist_ok=True)
 source_bindings={}
 for source in list((ROOT/'tools/publication').glob('Publication*.py'))+[ROOT/'tools/publication/BuildPublicationEdition.py',ROOT/'tools/publication/BuildPublicationDocuments.wls',ROOT/'tools/publication/PublicationStyles.wl']:
  identity=sha(source);destination=stage_sources/(identity[:12]+'_'+source.name)
  if not destination.exists():shutil.copy2(source,destination)
  source_bindings[source.relative_to(ROOT).as_posix()]=dict(sha256=identity,snapshot=destination.relative_to(run).as_posix())
 write(stage_sources/'bindings.json',source_bindings)
 sourcefiles=[ROOT/a.source_manifest,ROOT/m['bibtex']]+[ROOT/path for ed in m['edition'].values() for ch in ed['chapters'] for path in ch['sources'].values()]
 write(run/'source_provenance.json',{f.relative_to(ROOT).as_posix():sha(f) for f in sourcefiles})
 if a.stage in ['all','panels','compose','documents','specimen']:
  copy_assets(run,m);write(run/'quantities.json',metrics(m));build_documents(run,m,a);prepare_latex(run,m,a)
 if a.stage in ['all','notebooks']:
  native_run(run,run/'document_request.json',script='BuildPublicationDocuments.wls',suffix='_native')
 if a.stage in ['all','pdf']:compile_pdfs(run)
 if a.stage in ['all','verify']:verify(run,m)
 if a.stage in ['all','package']:package(run,m)
 print(json.dumps(dict(run_id=a.run_id,stage=a.stage,output=str(run)),ensure_ascii=False),flush=True)
 return 0

if __name__=='__main__':raise SystemExit(main())
