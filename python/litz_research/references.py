"""A single bibliographic source and an explicit source-use registry."""
from pathlib import Path
import re
from .common import read,write

def entries(root):
    import bibtexparser
    return bibtexparser.loads((root/'references/library.bib').read_text(encoding='utf-8')).entries

def publication_references(root,keys):
    by_id={x['ID']:x for x in entries(root)}
    return [dict(id=k,title=by_id[k]['title'],authors=by_id[k].get('author','').split(' and '),year=int(by_id[k]['year']) if by_id[k].get('year','').isdigit() else by_id[k].get('year',''),doi=by_id[k].get('doi',''),venue=', '.join(by_id[k][f] for f in ['journal','booktitle','publisher','volume','number','pages'] if by_id[k].get(f)),version=by_id[k].get('version',''),url=by_id[k].get('url','')) for k in keys]

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
        for field in ['role','use_status']:
            if not isinstance(source.get(field),dict) or not all(source[field].get(lang) for lang in ['en','zh-CN']):
                errors.append('bilingual '+field+' missing: '+source['key'])
    for path in (root/'manuscript').rglob('*.md'):
        for group in re.findall(r'\[@([^\]]+)\]',path.read_text(encoding='utf-8')):
            for key in re.findall(r'@?([A-Za-z][A-Za-z0-9_-]*)',group):
                if key not in ids:errors.append(path.relative_to(root).as_posix()+': unknown citation '+key)
    for path in (root/'manuscript').rglob('*.tex'):
        text=re.sub(r'(?<!\\)%[^\n]*', '', path.read_text(encoding='utf-8'))
        for group in re.findall(r'\\cite(?:[tp]|author|year)?\*?(?:\[[^\]]*\]){0,2}\{([^{}]+)\}',text):
            for key in group.split(','):
                key=key.strip()
                if key not in ids:errors.append(path.relative_to(root).as_posix()+': unknown citation '+key)
    return {'entries':len(es),'sources':len(sources),'failed_checks':len(errors),'errors':errors}

def build(root):
    es=entries(root);by_id={x['ID']:x for x in es};sources=read(root/'references/sources.json')['sources']
    def localized(source, field, language):
        value=source[field]
        if isinstance(value,dict):return value[language]
        return value
    for lang in ['en','zh-CN']:
        title='Sources, software and acknowledgments' if lang=='en' else '来源、软件与致谢'
        lines=['# '+title,'','Miao Yuxuan · Huainan Normal University' if lang=='en' else '缪雨轩 · 淮南师范学院','',('| Key | Source | Role | Use | Version / commit |' if lang=='en' else '| 引用 key | 来源 | 作用 | 使用状态 | 版本 / 提交 |'),'| --- | --- | --- | --- | --- |']
        for s in sources:
            e=by_id[s['key']];url=e.get('url') or ('https://doi.org/'+e['doi'] if e.get('doi') else '')
            lines.append('| '+s['key']+' | ['+e['title']+']('+url+') | '+localized(s,'role',lang)+' | '+localized(s,'use_status',lang)+' | '+s.get('version',s.get('commit','recorded per run' if lang=='en' else '见对应运行记录'))+' |')
        lines+=['',('Each entry identifies its actual contribution. Runtime versions are bound to individual runs. Scientific claims are supported by the cited methods and validation evidence.' if lang=='en' else '逐项记录实际贡献与使用状态。运行版本绑定各次记录；科学结论以方法来源和验收证据为依据。题录由 library.bib 统一维护，作用、位置、提交及许可见 sources.json。'),'']
        (root/'references'/('README.md' if lang=='en' else 'README.zh-CN.md')).write_text('\n'.join(lines),encoding='utf-8')
        ack=['# '+('Acknowledgments' if lang=='en' else '致谢'),'',('We thank the researchers, software authors and maintainers whose work supports the modeling, computation and presentation in this project.' if lang=='en' else '感谢为本项目的建模、计算与成果表达提供支持的研究者、软件作者和维护者。'),'']
        for s in sources:
            if s['category']!='literature':
                e=by_id[s['key']];url=e.get('url') or ('https://doi.org/'+e['doi'] if e.get('doi') else '')
                ack+=['- **['+e['title']+']('+url+')** — '+localized(s,'role',lang)+('.' if lang=='en' else '。')]
        ack+=['',('AI assistance supported source inspection, modeling code, simulation orchestration, diagnostics, translation, conceptual illustrations and editorial preparation. The author is responsible for the scientific assumptions, evidence and conclusions. Codex with the standard MCP client bridge has been tested; other clients retain their recorded validation status.' if lang=='en' else 'AI 协助来源核查、模型代码、仿真调度、诊断、翻译、概念插图与成稿整理。科学假设、验收证据及结论由作者负责。Codex 与标准 MCP 客户端桥接已实测；其他智能体客户端按实际验收程度另行标注。'),'']
        (root/('ACKNOWLEDGMENTS.md' if lang=='en' else 'ACKNOWLEDGMENTS.zh-CN.md')).write_text('\n'.join(ack),encoding='utf-8')
    translations={
        'Original copyright and LICENSE retained; byte-identical source snapshot':'保留原版权与 LICENSE；源码快照与上游逐字节一致',
        'IEEEtran class with retained license':'随附 IEEEtran 文档类及原许可',
        'bibliographic metadata':'题录与来源信息',
        'external dependency; upstream copyright retained':'外部依赖，保留上游版权',
        'fixed upstream source archive attachment and external runtime; Apache notice retained':'固定版本源码归档附件与外部运行环境，保留 Apache 声明',
        'metadata and configuration; software installed separately':'提供来源信息与配置，软件单独安装',
        'external dependency':'外部依赖'}
    for lang in ['en','zh-CN']:
        zh=lang=='zh-CN'
        notices=['# '+('第三方声明' if zh else 'Third-party notices'),'','| 来源 | 许可 / 条款 | 分发形式 |' if zh else '| Source | License / terms | Distribution |','| --- | --- | --- |']
        for s in sources:
            if s['category']!='literature':
                distribution=s.get('distribution','external dependency')
                notices.append('| '+s['key']+' | '+s.get('license','上游条款' if zh else 'upstream terms')+' | '+(translations[distribution] if zh else distribution)+' |')
        notices+=['',('上游许可原文见 LICENSES/third-party；题录、固定提交与实际使用记录见 references/sources.json。商业软件及字体按其各自许可安装和使用。' if zh else 'Original upstream notices are retained in LICENSES/third-party. Bibliography, pinned revisions and use records are indexed in references/sources.json. Commercial software and fonts are installed and used under their respective licenses.'),'']
        (root/('THIRD_PARTY_NOTICES.zh-CN.md' if zh else 'THIRD_PARTY_NOTICES.md')).write_text('\n'.join(notices),encoding='utf-8')
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
    return verify(root)
