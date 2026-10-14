"""Index claims and validate paired scholarly source identities before building."""
from pathlib import Path
import argparse, collections, json, re, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/publication'))
from PublicationManuscripts import blocks, read, sha, references_in

def audit():
    m=read(ROOT/'manuscript/publication.json'); records=[]; failures=[]
    known={r['id'] for r in m['references']}
    pattern=r'\{\{(metric|equation|eqref|figure|figref|cite):([^}]+)\}\}'
    for ed,work in m['edition'].items():
        for chapter in work['chapters']:
            pair={lang:blocks(ROOT/path) for lang,path in chapter['sources'].items()}
            if [x['id'] for x in pair['en']] != [x['id'] for x in pair['zh-CN']]:
                failures.append(ed+'/'+chapter['id']+'/block identities')
                continue
            rows=[]
            for en,zh in zip(pair['en'],pair['zh-CN']):
                identity=en['id']; tokens={lang:collections.Counter(re.findall(pattern,b['markdown'])) for lang,b in [('en',en),('zh-CN',zh)]}
                if tokens['en'] != tokens['zh-CN']:failures.append(ed+'/'+identity+'/paired scientific tokens')
                citations=references_in(en['markdown'])
                if citations!=references_in(zh['markdown']):failures.append(ed+'/'+identity+'/paired citations')
                if not set(citations)<=known:failures.append(ed+'/'+identity+'/unknown reference')
                figures=list(dict.fromkeys(key for kind,key in tokens['en'] if kind in ['figure','figref']))
                metrics=list(dict.fromkeys(key for kind,key in tokens['en'] if kind=='metric'))
                equations=list(dict.fromkeys(key for kind,key in tokens['en'] if kind in ['equation','eqref']))
                rows.append(dict(id=identity,claim={lang:b['markdown'] for lang,b in [('en',en),('zh-CN',zh)]},equations=equations,quantities=metrics,figures={key:m['figures'][key]['source_models'] for key in figures},references=citations))
            records.append(dict(edition=ed,chapter=chapter['id'],title=chapter['title'],sources={lang:dict(path=path,sha256=sha(ROOT/path)) for lang,path in chapter['sources'].items()},claims=rows))
    evidence=ROOT/'automation/examples/verification.json'
    result=dict(schema_version=1,chapters=records,automation_cases=dict(path=evidence.relative_to(ROOT).as_posix(),sha256=sha(evidence)),bibliography=dict(path=m['bibtex'],sha256=sha(ROOT/m['bibtex'])),failures=failures)
    out=ROOT/'provenance/editorial/claim-evidence-map.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(chapters=len(records),paired_blocks=sum(len(r['claims']) for r in records),failures=failures),ensure_ascii=False))
    if failures:raise SystemExit(1)

if __name__=='__main__':audit()
