"""Validate maintained bilingual guides without rewriting their prose."""
from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
def main():
    groups=['automation/workflows','automation/harnesses','automation/mcp']
    pairs=[]
    for group in groups:
        for path in sorted((ROOT/group).rglob('README.md')):
            translated=path.with_name('README.zh-CN.md')
            if not translated.exists(): raise FileNotFoundError(translated)
            pairs.append({'en':path.relative_to(ROOT).as_posix(),'zh-CN':translated.relative_to(ROOT).as_posix(),
                          'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [path,translated]}})
    out=ROOT/'provenance/editorial/guide-index.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'pairs':pairs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Bilingual guide pairs',len(pairs))
if __name__=='__main__': main()
