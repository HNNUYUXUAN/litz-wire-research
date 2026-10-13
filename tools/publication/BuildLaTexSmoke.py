"""Compile the pinned IEEE specimen with local XeLaTeX/BibTeX and verify its PDF."""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path
from BuildPublicationEdition import ROOT, read, write, sha
import PreManuscriptClosure as control

def environment():
    env=dict(os.environ,OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',PYTHONIOENCODING='utf-8',LANG='C',LC_ALL='C')
    if os.name != 'nt':return env
    import winreg
    paths=[env.get('PATH','')]
    for hive,key in [(winreg.HKEY_CURRENT_USER,'Environment'),(winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')]:
        with winreg.OpenKey(hive,key) as handle:
            paths.append(os.path.expandvars(winreg.QueryValueEx(handle,'Path')[0]))
    env['PATH']=';'.join(paths)
    return env

def child(run, driver):
    env=environment();xe=shutil.which('xelatex',path=env['PATH']);bib=shutil.which('bibtex',path=env['PATH'])
    if not xe or not bib:raise RuntimeError('XeLaTeX and BibTeX must be available on the persisted PATH')
    shutil.copy2(ROOT/'latex/references.bib',run/'references.bib')
    versions={name:subprocess.check_output([path,'--version'],env=env,encoding='utf-8',errors='replace').splitlines()[:3] for name,path in [('xelatex',xe),('bibtex',bib)]}
    write(run/'compiler_versions.json',versions)
    args=[xe,'--enable-installer','--interaction=nonstopmode','--halt-on-error','--file-line-error','--no-shell-escape','--output-directory='+str(run),'--include-directory='+str(run),'--record-package-usages='+str(run/'packages.txt'),'ieee_journal_smoke.tex']
    records=[]
    commands=[('xelatex_1',args,ROOT/'latex'),('bibtex',[bib,'ieee_journal_smoke'],run),('xelatex_2',args,ROOT/'latex'),('xelatex_3',args,ROOT/'latex')]
    if driver=='latexmk':
        mk=shutil.which('latexmk',path=env['PATH'])
        if not mk:raise RuntimeError('latexmk must be available on the persisted PATH')
        versions['latexmk']=subprocess.check_output([mk,'-version'],env=env,encoding='utf-8',errors='replace').splitlines()
        commands=[('latexmk',[mk,'-xelatex','-outdir='+str(run),'-interaction=nonstopmode','-halt-on-error','-file-line-error','ieee_journal_smoke.tex'],ROOT/'latex')]
    write(run/'compiler_versions.json',versions)
    for name,cmd,cwd in commands:
        start=time.monotonic()
        with (run/(name+'.txt')).open('w',encoding='utf-8') as log:
            result=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        records.append(dict(step=name,command=cmd,working_directory=str(cwd),actual_exit_code=result.returncode,elapsed_seconds=time.monotonic()-start))
        write(run/'compile_steps.json',records)
        print(name,'exit',result.returncode,flush=True)
        if result.returncode:return result.returncode
    return 0

def verify(run):
    from pypdf import PdfReader
    pdf=run/'ieee_journal_smoke.pdf';reader=PdfReader(pdf);text='\n'.join(p.extract_text() for p in reader.pages)
    log=(run/'ieee_journal_smoke.log').read_text(encoding='utf-8',errors='replace')
    checks=[]
    def check(name,value):checks.append(dict(name=name,passed=bool(value)))
    check('page_count_1_to_3',1<=len(reader.pages)<=3)
    for needle in ['20.016203628','8.006481451','宋体','端部并联','6710','3.647199980']:
        check('text/'+needle,needle in text)
    check('resolved_cross_references','??' not in text and not re.search(r'undefined references|Citation .* undefined|Reference .* undefined',log))
    check('no_missing_glyphs_or_overfull_boxes',not re.search(r'Missing character:|Overfull \\[hv]box',log))
    body_log=log[log.index('ieee_journal_smoke.aux'):] if 'ieee_journal_smoke.aux' in log else log
    check('no_document_font_substitution',not re.search(r'Font shape .* undefined',body_log))
    check('BibTeX_bibliography_generated',(run/'ieee_journal_smoke.bbl').is_file() and 'Cruciani' in (run/'ieee_journal_smoke.bbl').read_text(encoding='utf-8'))
    check('exact_upstream_class_bytes',sha(ROOT/'latex/IEEEtran.cls')==sha(ROOT/'references/templates/ieee-transactions/IEEEtran.cls'))
    check('compiled_IEEEtran_1_8b','V1.8b by Michael Shell' in log)
    fonts=[];forms=[];visited=set()
    def resources(r):
        r=r.get_object() if hasattr(r,'get_object') else r
        if not r:return
        for reference in r.get('/Font',{}).get_object().values() if hasattr(r.get('/Font',{}),'get_object') else r.get('/Font',{}).values():
            f=reference.get_object();name=str(f.get('/BaseFont',''));descriptors=[]
            if '/FontDescriptor' in f:descriptors.append(f['/FontDescriptor'].get_object())
            for d in f.get('/DescendantFonts',[]):
                d=d.get_object()
                if '/FontDescriptor' in d:descriptors.append(d['/FontDescriptor'].get_object())
            fonts.append(dict(name=name,embedded=any(any(k in d for k in ['/FontFile','/FontFile2','/FontFile3']) for d in descriptors)))
        for reference in r.get('/XObject',{}).get_object().values() if hasattr(r.get('/XObject',{}),'get_object') else r.get('/XObject',{}).values():
            f=reference.get_object();identity=getattr(reference,'idnum',id(f))
            if identity in visited:continue
            visited.add(identity)
            if f.get('/Subtype')=='/Form':forms.append(identity)
            resources(f.get('/Resources'))
    for p in reader.pages:resources(p.get('/Resources'))
    for family,pattern in [('SimSun',r'SimSun'),('Times New Roman',r'TimesNewRoman')]:
        matched=[f for f in fonts if re.search(pattern,f['name'],re.I)]
        check('embedded_font/'+family,matched and all(f['embedded'] for f in matched))
    check('Wolfram_PDF_panels_embedded_as_forms',len(forms)>=2)
    for item in read(run/'input_manifest.json')['inputs']:
        check('unchanged_source/'+item['path'],sha(ROOT/item['path'])==item['sha256'])
    import pypdfium2 as pdfium
    with pdfium.PdfDocument(str(pdf)) as rendered:
        for n in range(len(rendered)):
            page=rendered[n];bitmap=page.render(scale=150/72)
            bitmap.to_pil().save(run/f'page-{n+1}.png');bitmap.close();page.close()
    check('all_pages_rendered',len(list(run.glob('page-*.png')))==len(reader.pages))
    result=dict(status='passed' if all(c['passed'] for c in checks) else 'failed',checks=checks,failed_checks=sum(not c['passed'] for c in checks),pages=len(reader.pages),fonts=fonts,pdf_sha256=sha(pdf),physical_solver_calls=0,source_model='local_XeLaTeX_typesetting_of_frozen_Litz_evidence')
    write(run/'verification.json',result)
    if result['failed_checks']:raise RuntimeError('PDF verification failed: '+str([c['name'] for c in checks if not c['passed']]))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);parser.add_argument('--child',action='store_true');parser.add_argument('--driver',choices=['manual','latexmk'],default='latexmk');args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):parser.error('Safe unique run ID required')
    run=ROOT/'outputs'/args.run_id
    if args.child:return child(run,args.driver)
    run.mkdir(exist_ok=False);snapshot=run/'source_snapshot';snapshot.mkdir()
    inputs=[ROOT/'latex/ieee_journal_smoke.tex',ROOT/'latex/IEEEtran.cls',ROOT/'latex/references.bib',ROOT/'src/BuildLaTexSmoke.py',ROOT/'latex/.latexmkrc',ROOT/'src/RunLaTexSmoke.ps1',ROOT/'outputs/publication_20261006_full_05/panels/en/q1_magnitude.pdf',ROOT/'outputs/publication_20261006_full_05/panels/en/multilevel_detail.pdf']
    for p in inputs[:6]:shutil.copy2(p,snapshot/p.name)
    frozen=[ROOT/'docs/总控/当前运行索引.json',ROOT/'outputs/prewrite_closure_state.json']
    write(run/'input_manifest.json',dict(driver=args.driver,inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in inputs+frozen],physical_solver_calls=0))
    actual=control.hardware();budget=min(24*control.GIB,actual['free_RAM_bytes']-8*control.GIB)
    if budget<=0:raise RuntimeError('System free reserve preflight failed')
    monitor=run/'monitor';monitor.mkdir();write(monitor/'environment.json',actual)
    result=control.run_custom_monitored([sys.executable,'-B',str(Path(__file__).resolve()),'--run-id',args.run_id,'--driver',args.driver,'--child'],monitor,environment(),budget)
    if result.returncode:raise RuntimeError('Compilation failed; actual exit '+str(result.returncode))
    proof=verify(run);print(json.dumps(dict(run_id=args.run_id,status=proof['status'],pages=proof['pages'],pdf=str(run/'ieee_journal_smoke.pdf'))))
    return 0

if __name__=='__main__':raise SystemExit(main())
