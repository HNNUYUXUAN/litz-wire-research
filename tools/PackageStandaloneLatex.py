"""Package standalone LaTeX sources and verify archive members against their hashes."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);a=p.parse_args()
    run=ROOT/'outputs'/a.run_id; entries={}
    for folder in ['documents','panels','composites']:
        for source in (run/folder).rglob('*'):
            if source.is_file() and source.suffix in (['.tex','.cls'] if folder=='documents' else ['.pdf']):entries[source.relative_to(run).as_posix()]=source
    for source in (ROOT/'latex/templates').rglob('*'):
        if source.is_file() and source.suffix in ['.md','.tex','.cls']:entries['templates/'+source.relative_to(ROOT/'latex/templates').as_posix()]=source
    entries['compile.py']=ROOT/'tools/CompileStandaloneLatex.py'
    entries['references.bib']=ROOT/'references/library.bib'
    entries['IEEEtran-license.txt']=ROOT/'latex/IEEEtran.cls'
    rows=[dict(path=key,sha256=hashlib.sha256(source.read_bytes()).hexdigest()) for key,source in entries.items()]
    archive=run/'Litz_LaTeX_sources.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for key,source in entries.items():z.write(source,key)
        z.writestr('manifest.json',json.dumps(dict(run_id=a.run_id,files=rows),indent=2))
        z.writestr('README.md','# Standalone scholarly sources\n\nRun `python compile.py` to compile eighteen manuscripts and six editable templates. XeLaTeX, latexmk, SimSun and Times New Roman are required. Each document also compiles directly from its own directory with `latexmk -xelatex filename.tex`. Figure PDF paths are relative to this package.\n\n# 独立学术源码\n\n执行 `python compile.py` 编译十八份完整稿件和六份可编辑模板。需要 XeLaTeX、latexmk、宋体和 Times New Roman。也可在稿件目录执行 `latexmk -xelatex 文件名.tex`。图件 PDF 使用包内相对路径。\n')
    with zipfile.ZipFile(archive) as z:
        for row in rows:
            if hashlib.sha256(z.read(row['path'])).hexdigest()!=row['sha256']:raise RuntimeError(row['path'])
    (run/'standalone-source-package.json').write_text(json.dumps(dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=rows),indent=2)+'\n',encoding='utf-8')
    print(archive)
if __name__=='__main__':main()
