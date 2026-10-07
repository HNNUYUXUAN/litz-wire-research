"""Verify publication sources, bilingual numbers, fonts, links and portability."""
import argparse, json, math, re, statistics, xml.etree.ElementTree as ET, hashlib
from pathlib import Path
from BuildPublicationEdition import ROOT, read, write, sha, verify_panels, asset_path

def numeric_tree(value):
    if isinstance(value,bool):return None
    if isinstance(value,(int,float)):return value
    if isinstance(value,list):return [numeric_tree(v) for v in value]
    if isinstance(value,dict):return {k:numeric_tree(v) for k,v in value.items() if k not in {'caption','language','label','color_label','x_label','y_label','source_run_id','source_model','data_sha256','data_file'}}
    return None

def verify_supplement(run):
    from pypdf import PdfReader
    child=run/'supplement_figures'
    verify_panels(child)
    checks=list(read(child/'panel_verification.json')['checks'])
    specs=read(child/'render_request.json')['panels']
    for spec in specs:
        if spec['language']=='zh-CN':
            other=next((s for s in specs if s['id']==spec['id'] and s['language']=='en'),None)
            if other:checks.append(dict(name=spec['id']+'/bilingual_numbers',passed=numeric_tree(spec)==numeric_tree(other)))
    for panel in read(child/'panel_manifest.json')['panels']:
        sizes=[]
        def visitor(text,cm,tm,font,size):
            if text.strip():sizes.append(size*math.hypot(tm[2]*cm[0]+tm[3]*cm[2],tm[2]*cm[1]+tm[3]*cm[3]))
        pdf=next(asset_path(child,a) for a in panel['assets'] if a['format']=='pdf')
        PdfReader(pdf).pages[0].extract_text(visitor_text=visitor)
        med=statistics.median(sizes) if sizes else None
        checks.append(dict(name=panel['language']+'/'+panel['id']+'/physical_font_size',passed=not sizes or 8.7<=med<=10.3,median_pt=med))
        checks.append(dict(name=panel['language']+'/'+panel['id']+'/expression',passed=(child/'panels'/panel['language']/(panel['id']+'.wl')).exists()))
    for book in read(child/'notebook_verification.json')['notebooks']:
        checks.append(dict(name=book['id']+'/native_frontend',passed=book['saved_reopened'] and book['all_cells_rendered'] and book['panel_equal_width'] and book['viewpoint_roundtrip'] and book['input_count']==0 and book['dynamic_count']==0))
        checks.append(dict(name=book['id']+'/copy_sha256',passed=sha(run/book['path'])==book['sha256']==sha(child/book['path'])))
    for composite in read(child/'composite_manifest.json')['composites']:
        sources=[sha(child/'panels'/composite['language']/(id+'.pdf')) for id in composite['panel_ids']]
        checks.append(dict(name=composite['language']+'/'+composite['id']+'/composition',passed=sources==composite['source_pdf_sha256'] and composite['plotting_calls']==0 and composite['layout']['panel_width_mm']==88.9))
    write(child/'extended_verification.json',dict(checks=checks,failed_checks=sum(not c['passed'] for c in checks),physical_solver_calls=0))
    return [dict(c,name='supplement/'+c['name']) for c in checks]

def verify(run):
    from pypdf import PdfReader
    import PublicationDocuments
    verify_panels(run);PublicationDocuments.verify(run)
    checks=[];fonts=[];numeric_hashes=[]
    panel_manifest=read(run/'panel_manifest.json')
    request=read(run/'render_request.json');specs=request['panels']
    for spec in specs:
        numeric_hashes.append(dict(id=spec['id'],language=spec['language'],numeric_mapping_sha256=hashlib.sha256(json.dumps(numeric_tree(spec),sort_keys=True,separators=(',',':')).encode()).hexdigest()))
        if spec['language']!='zh-CN':continue
        other=next((s for s in specs if s['id']==spec['id'] and s['language']=='en'),None)
        if other:checks.append(dict(name=spec['id']+'/same_bilingual_numbers',passed=numeric_tree(spec)==numeric_tree(other)))
    for p in panel_manifest['panels']:
        vals=[]
        def visitor(text,cm,tm,font,size):
            if text.strip():vals.append(dict(text=text.strip(),physical_size_pt=size*math.hypot(tm[2]*cm[0]+tm[3]*cm[2],tm[2]*cm[1]+tm[3]*cm[3]),font=str((font or {}).get('/BaseFont',''))))
        path=next(asset_path(run,a) for a in p['assets'] if a['format']=='pdf');PdfReader(path).pages[0].extract_text(visitor_text=visitor)
        sizes=[v['physical_size_pt'] for v in vals]
        # Mathematical superscripts are conventionally smaller than the main text.
        primary=[v['physical_size_pt'] for v in vals if len(v['text'])>2 and not re.fullmatch(r'[−–\-+]?\d+',v['text'])]
        med=statistics.median(primary or sizes) if sizes else None
        good=not sizes or (8.7<=med<=10.3)
        checks.append(dict(name=p['language']+'/'+p['id']+'/actual_primary_font_size',passed=good,median_pt=med))
        fonts.append(dict(id=p['id'],language=p['language'],glyph_runs=vals,median_primary_pt=med,passed=good))
        checks.append(dict(name=p['language']+'/'+p['id']+'/native_expression',passed=(run/'panels'/p['language']/(p['id']+'.wl')).is_file()))
        svg=ET.parse(next(asset_path(run,a) for a in p['assets'] if a['format']=='svg')).getroot()
        text_count=sum(n.tag.rsplit('}',1)[-1]=='text' for n in svg.iter());path_count=sum(n.tag.rsplit('}',1)[-1]=='path' for n in svg.iter())
        checks.append(dict(name=p['language']+'/'+p['id']+'/SVG_glyph_outlines',passed=text_count==0 and (path_count>0 or p['kind']=='geometry'),text_nodes=text_count,path_nodes=path_count))
        if p['kind']=='curve':
            checks.append(dict(name=p['language']+'/'+p['id']+'/SVG_vector_curve',passed=not any(n.tag.rsplit('}',1)[-1]=='image' for n in svg.iter())))
    write(run/'physical_font_verification.json',dict(panels=fonts,method='Actual normalized PDF font and combined text/current transformation matrices; main runs approximately 9–10 pt, traditional superscripts smaller'))
    write(run/'bilingual_numeric_mapping.json',dict(panels=numeric_hashes,data_file_hashes=read(run/'field_reconstruction_verification.json')['outputs_sha256']))
    for f in (run/'documents').glob('*.md'):
        text=f.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if not target.startswith(('https:','http:','#')):checks.append(dict(name=f.name+'/'+target,passed=(f.parent/target).exists()))
        for target in re.findall(r'<img[^>]+src="([^"]+)"',text):checks.append(dict(name=f.name+'/image/'+target,passed=(f.parent/target).exists()))
    proof=read(run/'field_reconstruction_verification.json')
    for p,h in proof['outputs_sha256'].items():checks.append(dict(name='frozen_field_map/'+p,passed=sha(run/p)==h))
    for p,h in read(run/'source_manifest.json')['frozen_science_sha256'].items():checks.append(dict(name='original_science/'+p,passed=sha(ROOT/p)==h))
    # Notebook hyperlinks must target a real sibling, table or local cell tag.
    docrequest=read(run/'document_request.json')
    for doc in docrequest['documents']:
        for cell in doc['cells']:
            if cell['type']=='link' and not cell['target'].startswith(('https:','http:')):
                checks.append(dict(name=doc['id']+'/link/'+cell['target'],passed=(run/doc['path']).parent.joinpath(cell['target']).exists()))
    for c in read(run/'composite_manifest.json')['composites']:
        paths=[next(asset_path(run,a) for a in next(p for p in panel_manifest['panels'] if p['id']==id and p['language']==c['language'])['assets'] if a['format']=='pdf') for id in c['panel_ids']]
        checks.append(dict(name=c['language']+'/'+c['id']+'/compose_source_hashes',passed=[sha(p) for p in paths]==c['source_pdf_sha256'] and c['plotting_calls']==0 and c['layout']['panel_width_mm']==88.9))
    if (run/'supplement_figures/notebook_verification.json').exists():checks+=verify_supplement(run)
    result=dict(run_id=run.name,checks=checks,failed_checks=sum(not x['passed'] for x in checks),physical_solver_calls=0,source_physical_acceptance_unchanged=True)
    write(run/'publication_verification.json',result)
    if result['failed_checks']:raise RuntimeError('Publication checks failed: '+str([x for x in checks if not x['passed']]))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args();result=verify(ROOT/'outputs'/a.run_id);print(json.dumps(dict(failed_checks=result['failed_checks'],checks=len(result['checks']))))
