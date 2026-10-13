"""A single bibliographic source and an explicit source-use registry."""
from pathlib import Path
import re
from .common import read,write

def entries(root):
    import bibtexparser
    return bibtexparser.loads((root/'references/library.bib').read_text(encoding='utf-8')).entries

def publication_references(root,keys):
    by_id={x['ID']:x for x in entries(root)}
    return [dict(id=k,title=by_id[k]['title'],authors=by_id[k].get('author','').split(' and '),year=int(by_id[k]['year']) if by_id[k].get('year','').isdigit() else by_id[k].get('year',''),doi=by_id[k].get('doi',''),venue=', '.join(by_id[k][f] for f in ['journal','volume','number','pages'] if by_id[k].get(f)),url=by_id[k].get('url','')) for k in keys]

def citation_order(root,manifest,edition):
    keys=[]
    for ch in manifest['edition'][edition]['chapters']:
        path=root/ch['sources'][manifest.get('numbering_language','en')]
        for group in re.findall(r'\[@([^\]]+)\]',path.read_text(encoding='utf-8')):
            for key in re.findall(r'@?([A-Za-z][A-Za-z0-9_-]*)',group):
                if key not in keys:keys.append(key)
    return keys

def verify(root):
    es=entries(root);ids=[x['ID'] for x in es];sources=read(root/'references/sources.json')['sources'];errors=[]
    if len(ids)!=len(set(ids)):errors.append('duplicate citation keys')
    source_ids=[s['key'] for s in sources]
    if len(source_ids)!=len(set(source_ids)):errors.append('duplicate source-use keys')
    if set(ids)!=set(source_ids):errors.append('bibliography and source-use registry differ')
    dois={}
    for entry in es:
        doi=entry.get('doi','').lower().removeprefix('https://doi.org/')
        if doi and doi in dois:errors.append('duplicate DOI: '+doi)
        if doi:dois[doi]=entry['ID']
        if not entry.get('title'):errors.append('title missing: '+entry['ID'])
    for source in sources:
        if source['key'] not in ids:errors.append('source has no bibliography entry: '+source['key'])
        if not source.get('role') or not source.get('use_status'):errors.append('source role missing: '+source['key'])
    for path in (root/'manuscript').rglob('*.md'):
        for group in re.findall(r'\[@([^\]]+)\]',path.read_text(encoding='utf-8')):
            for key in re.findall(r'@?([A-Za-z][A-Za-z0-9_-]*)',group):
                if key not in ids:errors.append(path.relative_to(root).as_posix()+': unknown citation '+key)
    return {'entries':len(es),'sources':len(sources),'failed_checks':len(errors),'errors':errors}

def build(root):
    es=entries(root);by_id={x['ID']:x for x in es};sources=read(root/'references/sources.json')['sources']
    for lang in ['en','zh-CN']:
        title='Sources, software and acknowledgments' if lang=='en' else '来源、软件与致谢'
        lines=['# '+title,'','Miao Yuxuan · Huainan Normal University','',('| Key | Source | Role | Use | Version / commit |' if lang=='en' else '| 引用 key | 来源 | 作用 | 使用状态 | 版本 / 提交 |'),'| --- | --- | --- | --- | --- |']
        for s in sources:
            e=by_id[s['key']];url=e.get('url') or ('https://doi.org/'+e['doi'] if e.get('doi') else '')
            lines.append('| '+s['key']+' | ['+e['title']+']('+url+') | '+s['role']+' | '+s['use_status']+' | '+s.get('version',s.get('commit','recorded per run'))+' |')
        lines+=['',('Each entry identifies its actual contribution. Runtime versions are bound to individual runs. Scientific claims are supported by the cited methods and validation evidence.' if lang=='en' else '逐项记录实际贡献与使用状态。运行版本绑定各次记录；科学结论以方法来源和验收证据为依据。题录由 library.bib 统一维护，作用、位置、提交及许可见 sources.json。'),'']
        (root/'references'/('README.md' if lang=='en' else 'README.zh-CN.md')).write_text('\n'.join(lines),encoding='utf-8')
        ack=['# '+('Acknowledgments' if lang=='en' else '致谢'),'']
        for s in sources:
            if s['category']!='literature':ack+=['- **'+by_id[s['key']]['title']+'** — '+s['role']+'; '+s['use_status']+'.']
        ack+=['',('AI assistance supported source inspection, modeling code, simulation orchestration, diagnostics and editorial preparation. The author is responsible for the scientific assumptions, evidence and conclusions.' if lang=='en' else 'AI 协助来源核查、模型代码、仿真调度、诊断与成稿整理。科学假设、验收证据及结论由作者负责。Codex 与标准 MCP 客户端桥接已实测；其他智能体客户端按实际验收程度另行标注。'),'']
        (root/('ACKNOWLEDGMENTS.md' if lang=='en' else 'ACKNOWLEDGMENTS.zh-CN.md')).write_text('\n'.join(ack),encoding='utf-8')
    notices=['# Third-party notices','','| Source | License / terms | Distribution |','| --- | --- | --- |']
    for s in sources:
        if s['category']!='literature':notices.append('| '+s['key']+' | '+s.get('license','upstream terms')+' | '+s.get('distribution','external dependency')+' |')
    (root/'THIRD_PARTY_NOTICES.md').write_text('\n'.join(notices)+'\n',encoding='utf-8')
    csl=[]
    for e in es:
        item={'id':e['ID'],'type':'article-journal' if e['ENTRYTYPE']=='article' else 'chapter' if e['ENTRYTYPE']=='incollection' else 'software' if e['ENTRYTYPE']=='software' else 'webpage','title':e['title']}
        for src,dst in [('doi','DOI'),('url','URL'),('journal','container-title'),('volume','volume'),('number','issue'),('pages','page'),('version','version')]:
            if src in e:item[dst]=e[src]
        if 'booktitle' in e:item['container-title']=e['booktitle']
        item['author']=[{'literal':n.strip()} for n in e.get('author','').split(' and ') if n.strip()]
        if e.get('year','').isdigit():item['issued']={'date-parts':[[int(e['year'])]]}
        csl.append(item)
    write(root/'references/library.csl.json',csl)
    for legacy in ['manuscript/references.bib','latex/references.bib']:
        (root/legacy).write_text('% Generated compatibility export from references/library.bib.\n'+(root/'references/library.bib').read_text(encoding='utf-8'),encoding='utf-8')
    return verify(root)
