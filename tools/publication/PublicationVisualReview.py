"""Prepare page contact sheets and verify caption geometry in compiled editions."""
import argparse,json,re
from pathlib import Path
from PIL import Image,ImageDraw
from BuildPublicationEdition import ROOT,read,write,sha

def render(run):
 from pypdf import PdfReader
 import pypdfium2 as pdfium
 folder=run/'pdf_previews';folder.mkdir(exist_ok=True);details=[]
 for row in read(run/'pdf_manifest.json'):
  path=run/row['pdf'];d=pdfium.PdfDocument(str(path));pages=[]
  for i in range(len(d)):
   page=d[i];bitmap=page.render(scale=100/72);out=folder/(path.stem+f'_page_{i+1:03}.png');bitmap.to_pil().save(out);bitmap.close();page.close();pages.append(out.relative_to(run).as_posix())
  d.close();details.append(dict(id=path.stem,rendered_pages=pages))
 write(run/'pdf_review_pages.json',details)
 print('Rendered pages',sum(len(d['rendered_pages']) for d in details),flush=True)

def prepare(run):
 details=read(run/'pdf_review_pages.json');pages=[p for d in details for p in d['rendered_pages']];target=run/'visual_sheets';target.mkdir(exist_ok=True);records=[]
 for start in range(0,len(pages),8):
  canvas=Image.new('RGB',(2000,1500),'#dedede')
  for k,p in enumerate(pages[start:start+8]):
   im=Image.open(run/p);im.thumbnail((485,710));x=(k%4)*500;y=(k//4)*750;canvas.paste(im,(x+(500-im.width)//2,y+26));ImageDraw.Draw(canvas).text((x+6,y+5),Path(p).name,fill='black')
  path=target/f'sheet_{start//8+1:03}.png';canvas.save(path);records.append(dict(path=path.relative_to(run).as_posix(),sha256=sha(path),pages=pages[start:start+8]))
 write(run/'visual_sheet_manifest.json',records)
 checks=[]
 for d in read(run/'document_structure.json'):
  md=(run/d['markdown']).read_text(encoding='utf-8')
  for c in d['cells']:
   if c['type']!='figure':continue
   checks.append(dict(document=d['id'],figure=c['id'],title_paragraph=('<p align="center">'+c['title']+'</p>\n\n'+c['description']) in md,title=c['title'],description=c['description']))
   for layout in ['single','ieee']:
    tex=(run/d['markdown']).with_name(d['id']+'_'+layout+'.tex').read_text(encoding='utf-8')
    checks[-1][layout+'_alignment']=r'\small\centering' in tex and r'\small\raggedright' in tex
 write(run/'caption_verification.json',dict(figures=checks,failed_checks=sum(not all(c[k] for k in ['title_paragraph','single_alignment','ieee_alignment']) for c in checks)))
 print(json.dumps(dict(sheets=len(records),pages=len(pages),figure_occurrences=len(checks))))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--render',action='store_true');a=p.parse_args();run=ROOT/'outputs'/a.run_id
 if a.render:render(run)
 prepare(run)
