"""Compile a representative paper and redraw an independent panel after restoration."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
from BuildPublicationEdition import ROOT,read,write,sha,native_run

def check(run,target,receipt):
 receipt.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,PYTHONUTF8='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8')
 base=[sys.executable,str(target/'src/RunPublicationBuild.py'),'--run-id','portable_compile_01','--source-manifest','manuscript/publication_portable.json','--edition','paper','--language','en','--form','merged','--layout','single']
 checks=[]
 for stage in ['documents','pdf']:
  result=subprocess.run(base+['--stage',stage],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8')
  (receipt/('portable_'+stage+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8');checks.append(dict(stage=stage,exit_code=result.returncode,passed=result.returncode==0))
  if result.returncode:break
 if all(c['passed'] for c in checks):
  from pypdf import PdfReader
  pdf=target/'outputs/portable_compile_01/documents/paper/en/paper_en_single.pdf';checks.append(dict(stage='pdf_readback',passed=pdf.is_file() and len(PdfReader(pdf).pages)>0,pages=len(PdfReader(pdf).pages)))
  actual=read(target/'outputs/portable_compile_01/quantities.json');expected=read(run/'quantities.json')
  comparable=lambda data:{key:{k:v for k,v in item.items() if k!='source'} for key,item in data.items()}
  checks.append(dict(stage='portable_quantities',passed=comparable(actual)==comparable(expected)))
  request=dict(source=str(target/'panels/zh-CN/q1_magnitude.wl'),output=str(target/'restored_q1_magnitude.pdf'),verification=str(receipt/'portable_redraw.json'))
  write(receipt/'redraw_request.json',request);native_run(receipt,receipt/'redraw_request.json',script='VerifyPublicationRedraw.wls',suffix='_portable')
  checks.append(dict(stage='native_panel_redraw',passed=read(receipt/'portable_redraw.json')['passed']))
 result=dict(target=str(target),checks=checks,failed_checks=sum(not c['passed'] for c in checks),physical_solver_calls=0)
 write(receipt/'portable_compile_verification.json',result);print(json.dumps(result),flush=True)
 if result['failed_checks']:raise RuntimeError('Portable compile and redraw verification')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--target');p.add_argument('--receipt-root');a=p.parse_args();run=ROOT/'outputs'/a.run_id
 target=Path(a.target) if a.target else ROOT/read(run/'space_restore_verification.json')['target']
 check(run,target,Path(a.receipt_root) if a.receipt_root else run)
