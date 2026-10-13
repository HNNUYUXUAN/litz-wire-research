"""Assemble the canonical bibliography from reviewed local metadata and used tools."""
from pathlib import Path
import json,re
import bibtexparser

ROOT=Path(__file__).resolve().parents[1]

def main():
    if (ROOT/'references/library.bib').exists():
        raise SystemExit('Bibliography migration is complete. Maintain references/library.bib; run litz-research references build.')
    original=ROOT/'outputs/automation_20261013_rc2/baseline/manuscript/references.bib'
    base=original if original.exists() else ROOT/'manuscript/references.bib'
    entries=bibtexparser.loads(base.read_text(encoding='utf-8')).entries
    sources=[];seen={x.get('doi','').lower():x['ID'] for x in entries if x.get('doi')}
    for x in entries:
        j=x.get('journal','');m=re.match(r'(.+?) (\d+)\((\d+)\):(.+)',j)
        if m:x.update(journal=m[1],volume=m[2],number=m[3],pages=m[4].replace('–','--'))
        x['url']='https://doi.org/'+x['doi']
        sources.append({'key':x['ID'],'category':'literature','role':'Litz-wire modeling method and comparison','use_status':'reviewed literature','locations':['manuscript/','models/'],'license':'publisher terms','distribution':'bibliographic metadata'})
    # Metadata-only recovery from the sealed source archive, never article PDFs.
    origin=ROOT.parent/'litz-wire-modeling-src'
    for path in sorted((origin/'references').glob('literature*/manifest.json')):
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        for x in obj.get('items',[]):
            doi=(x.get('doi') or '').lower();key=x.get('id')
            if not key or not x.get('title') or (doi and doi in seen) or any(e['ID']==key for e in entries):continue
            entry={'ENTRYTYPE':'article','ID':key,'title':x['title'],'author':' and '.join(x.get('authors',[])),'year':str(x.get('year','')),'journal':x.get('venue',''),'url':x.get('canonical_url','')}
            if doi:entry['doi']=doi;seen[doi]=key
            entries.append(entry);sources.append({'key':key,'category':'literature','role':'Research literature index','use_status':'historically reviewed; see dated source record','locations':['references/'],'license':'publisher terms','distribution':'bibliographic metadata','metadata_origin':path.relative_to(origin).as_posix()})
    tools=[
      ('WOLFRAM','Wolfram Language and Notebook','https://www.wolfram.com/language/','Wolfram Research','Symbolic/numerical modeling and native Notebooks','proprietary','15.0.0'),
      ('AGENTTOOLS','Wolfram AgentTools','https://github.com/WolframResearch/AgentTools','Wolfram Research','Wolfram MCP tools','MIT','2.2.0'),
      ('PYAEDTMCP','PyAEDT-MCP','https://github.com/ansys/pyaedt-mcp','ANSYS, Inc.','AEDT MCP automation','Apache-2.0','0.2.dev0'),
      ('PYAEDT','PyAEDT','https://github.com/ansys/pyaedt','ANSYS, Inc.','AEDT modeling and postprocessing','MIT','1.8.0'),
      ('CODEX','Codex','https://developers.openai.com/codex/','OpenAI','Research agent harness and coding assistance','service/software terms','recorded per session'),
      ('MCP','Model Context Protocol','https://modelcontextprotocol.io/','Model Context Protocol contributors','Tool transport and discovery protocol','upstream specification terms','recorded per connection'),
      ('AEDT','Ansys Electronics Desktop / Maxwell','https://www.ansys.com/products/electronics/ansys-maxwell','ANSYS, Inc.','Independent electromagnetic field solver','proprietary','2025.2 Student'),
      ('CUDA','Wolfram CUDALink and WolframGPUSDK','https://reference.wolfram.com/language/CUDALink/guide/CUDALink.html','Wolfram Research','GPU numerical execution and CPU comparison','upstream software terms','recorded per run'),
      ('PYTHON','Python','https://www.python.org/','Python Software Foundation','CLI and orchestration runtime','PSF','3.12'),
      ('MATH','mpmath','https://mpmath.org/','mpmath developers','Independent high-precision Bessel calibration','BSD-3-Clause','1.3.0'),
      ('NUMPY','NumPy','https://numpy.org/','NumPy developers','Arrays and port calibration','BSD-3-Clause','2.3.3'),
      ('MATPLOTLIB','Matplotlib','https://matplotlib.org/','Matplotlib developers','Data visualization','Matplotlib license','3.10.6'),
      ('PILLOW','Pillow','https://python-pillow.org/','Pillow contributors','Image processing and inspection','HPND','11.3.0'),
      ('PYPDF','pypdf','https://pypdf.readthedocs.io/','pypdf contributors','PDF structure and verification','BSD-3-Clause','6.1.1'),
      ('PDFIUM','pypdfium2','https://github.com/pypdfium2-team/pypdfium2','pypdfium2 contributors','PDF rendering','upstream component licenses','4.30.0'),
      ('REPORTLAB','ReportLab','https://www.reportlab.com/','ReportLab contributors','Document production','BSD-style','4.4.3'),
      ('MARKDOWNIT','markdown-it-py and mdit-py-plugins','https://github.com/executablebooks/markdown-it-py','Executable Books contributors','Markdown and mathematical document parsing','MIT','4.2.0 / 0.5.0'),
      ('MDURL','mdurl','https://github.com/executablebooks/mdurl','mdurl contributors','Markdown URL parsing','MIT','0.1.2'),
      ('SETUPTOOLS','setuptools','https://setuptools.pypa.io/','Python Packaging Authority','Package installation','MIT','80.9.0'),
      ('PSUTIL','psutil','https://github.com/giampaolo/psutil','Giampaolo Rodola and contributors','Process ownership and resource monitoring','BSD-3-Clause','7.2.2'),
      ('BIBTEXPARSE','bibtexparser','https://github.com/sciunto-org/python-bibtexparser','bibtexparser contributors','Canonical bibliography parsing','BSD-3-Clause','1.4.3'),
      ('MCPSDK','MCP Python SDK','https://github.com/modelcontextprotocol/python-sdk','Model Context Protocol contributors','Standard client protocol acceptance','MIT','1.17.0'),
      ('FAST_MCP','FastMCP and ansys-common-mcp','https://github.com/ansys/ansys-common-mcp','FastMCP and PyAnsys contributors','Ansys MCP runtime','upstream component licenses','4.0.10 / 0.3.5'),
      ('WOLFRAMCLIENT','Wolfram Client Library for Python','https://github.com/WolframResearch/WolframClientForPython','Wolfram Research','WXF and Wolfram interoperability','MIT','1.4.0'),
      ('POWERSHELL','PowerShell','https://github.com/PowerShell/PowerShell','Microsoft and contributors','Windows process supervision','MIT','recorded per run'),
      ('TEX','XeLaTeX, BibTeX, latexmk and MiKTeX','https://miktex.org/','TeX ecosystem contributors','Academic document compilation','component-specific terms','recorded per build'),
      ('IEEE','IEEEtran','https://github.com/bardsoftware/template-ieee-transactions','Michael Shell and copyright holders','IEEE-style document class','LPPL-1.3-or-later','f90a1b28035a7e7530cf313267ea3487ee68d5df'),
      ('FONTS','SimSun and Times New Roman','https://learn.microsoft.com/en-us/typography/fonts/','Microsoft and font copyright holders','Chinese and Latin document typography','proprietary font terms','installed separately'),
      ('BESSEL','NIST Digital Library of Mathematical Functions, Modified Bessel Functions','https://dlmf.nist.gov/10.25','NIST','Bessel definitions and conventions','NIST website terms','accessed 2026-10-13'),
      ('FEMDOC','Wolfram quasistatic magnetic field models','https://reference.wolfram.com/language/PDEModels/tutorial/Electromagnetics/QuasistaticMagneticFields.html','Wolfram Research','FEM and A-phi method documentation','documentation terms','accessed 2026-10-13'),
    ]
    for key,title,url,author,role,license,version in tools:
        entries.append({'ENTRYTYPE':'misc','ID':key,'title':title,'author':'{'+author+'}','year':'2026','url':url,'note':version})
        sources.append({'key':key,'category':'method' if key in {'BESSEL','FEMDOC'} else 'software','role':role,'use_status':'method reference' if key in {'BESSEL','FEMDOC'} else 'used dependency or research tool','locations':['automation/','models/','tools/'],'license':license,'version':version,'distribution':'IEEEtran class with retained license' if key=='IEEE' else 'metadata and configuration; software installed separately'})
    repos=json.loads((origin/'references/github_repository_metadata_2026-10-03.json').read_text(encoding='utf-8'))
    for i,r in enumerate(repos['repositories']):
        if r['repository']=='ansys/pyaedt':continue
        key='REPO'+str(i+1)
        entries.append({'ENTRYTYPE':'misc','ID':key,'title':r.get('description') or r['repository'],'author':'{'+r['repository'].split('/')[0]+'}','year':'2026','url':r['url'],'note':'Read-only review on 2026-10-03'})
        sources.append({'key':key,'category':'repository','role':'Published method and implementation reference','use_status':'read-only reviewed','license':r.get('license','upstream terms'),'version':'reviewed 2026-10-03','distribution':'bibliographic metadata','locations':['references/']})
    db=bibtexparser.bibdatabase.BibDatabase();db.entries=entries
    (ROOT/'references/library.bib').write_text(bibtexparser.dumps(db),encoding='utf-8')
    (ROOT/'references/sources.json').write_text(json.dumps({'schema_version':1,'sources':sources},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for path in [ROOT/'manuscript/publication.json',ROOT/'manuscript/specimens/publication.paper-zh-CN.json']:
        m=json.loads(path.read_text(encoding='utf-8-sig'));m['references']=[{'id':x['id']} for x in m['references']];m['bibtex']='references/library.bib';m['reference_numbering']='first_appearance_shared_bilingual'
        path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from litz_research.references import build
    print(json.dumps(build(ROOT),ensure_ascii=False))

if __name__=='__main__':main()
