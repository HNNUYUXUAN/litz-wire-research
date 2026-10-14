"""Compile every manuscript and template in an extracted standalone source package."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,time

def main():
    root=Path(__file__).resolve().parent
    compiler=os.getenv('LITZ_LATEXMK') or shutil.which('latexmk')
    if not compiler:raise RuntimeError('Set LITZ_LATEXMK or put latexmk and xelatex on PATH')
    env=dict(os.environ,OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8')
    files=sorted((root/'documents').glob('*/*/*.tex'))+sorted((root/'templates').glob('*/*.tex'))
    if len(files)!=24:raise RuntimeError('Expected eighteen manuscripts and six templates')
    results=[]
    for source in files:
        start=time.monotonic()
        with source.with_suffix('.compile.txt').open('w',encoding='utf-8') as log:
            result=subprocess.run([compiler,'-xelatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','-silent',source.name],cwd=source.parent,env=env,stdout=log,stderr=subprocess.STDOUT)
        pdf=source.with_suffix('.pdf');log=source.with_suffix('.log')
        diagnostics=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
        passed=result.returncode==0 and pdf.is_file() and not re.search(r'Overfull \\[hv]box|Missing character:|undefined references',diagnostics)
        results.append(dict(source=source.relative_to(root).as_posix(),exit_code=result.returncode,passed=passed,elapsed_seconds=time.monotonic()-start,pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf.exists() else None))
        (root/'compile-receipt.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
        print(source.stem, 'passed' if passed else 'failed',flush=True)
        if not passed:raise RuntimeError('Inspect '+str(source.with_suffix('.compile.txt')))

if __name__=='__main__':main()
