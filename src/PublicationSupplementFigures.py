"""Additional archived geometry and explicit triangle-mesh publication panels."""
from pathlib import Path
import json, shutil, hashlib
import BuildPublicationEdition as b

def prepare(parent,languages=('zh-CN','en')):
    run=parent/'supplement_figures';run.mkdir(exist_ok=False)
    source=b.BUNDLE/'routes/closure_geometry/data.json';geometries=b.read(source)['geometries'];coax=b.read(parent/'field_data/coax640.json')
    selected=[t for t,m in zip(coax['triangles'],coax['material_markers']) if m in {1,2,3}]
    ids=sorted({i for t in selected for i in t});mapping={i:k+1 for k,i in enumerate(ids)}
    mesh=dict(points_mm=[coax['points_mm'][i-1] for i in ids],triangles=[[mapping[i] for i in t] for t in selected],source_node_ids_1based=[coax['source_node_ids_1based'][i-1] for i in ids],selected_material_markers=[1,2,3])
    panels=[];sources={}
    for lang in languages:
        def add(id,kind,z,e,model,origin,**opts):
            digest=hashlib.sha256(json.dumps(opts,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            panels.append(dict(id=id,kind=kind,language=lang,caption=z if lang=='zh-CN' else e,source_model=model,source_run_id=origin,source_physical_acceptance_status='geometry_or_mesh_display_only',data_sha256=digest,**opts))
        for kind,labelz,labele in [('multilevel','传统多级','multilevel'),('crosslayer','跨层','cross-layer')]:
            g=next(x for x in geometries if x['kind']==kind and x['axial_sample_segments']==1600)
            paths=b.array_from_descriptor(g['paths'])
            array=b.BUNDLE/g['paths']['path'];sources[array.relative_to(b.ROOT).as_posix()]=b.sha(array)
            add('geometry_'+kind+'_overall','geometry',labelz+'保存中心线的完整 20 mm 视图，显示抽样每 8 点；铜径 0.100 mm，小股数展示不构成性能排名。','Complete archived 20 mm '+labele+' geometry, display subsampling every eight points; 0.100 mm copper diameter. Small-strand geometry does not establish a performance ranking.','archived_physical_strand_centerlines','closure_20261005_geometry_01',paths_mm=[[[v*1000 for v in point] for point in path[::8]] for path in paths],radius_mm=.05,highlight_ids=[1])
            if kind=='crosslayer':
                add('geometry_crosslayer_section','strand_section','跨层构造在 z=10 mm 的实际七股截面；数字保持物理股线 ID。','Actual seven-strand cross-layer section at z=10 mm; numbers preserve physical strand IDs.','archived_physical_strand_centerlines','closure_20261005_geometry_01',points_mm=[[v*1000 for v in path[800][:2]] for path in paths],radius_mm=.05,x_label='x (mm)',y_label='y (mm)')
        add('coax640_mesh_detail','mesh_outline','640 股最细模型的原始三角形局部，显示材料 1–3；保留源节点身份。','Original triangle-mesh detail of the finest 640-strand model, showing materials 1–3 with preserved source-node identity.','frozen_2D_FEM_triangle_connectivity',coax['source_run_id'],x_label='x (mm)',y_label='y (mm)',**mesh)
    b.write(run/'render_request.json',dict(run_id=parent.name+'_supplement',output_directory=str(run),panels=panels,composition_groups=[['geometry_overall',['geometry_multilevel_overall','geometry_crosslayer_overall']],['geometry_and_mesh_sections',['geometry_crosslayer_section','coax640_mesh_detail']]]))
    b.write(run/'source_manifest.json',dict(frozen_science_sha256=b.read(parent/'source_manifest.json')['frozen_science_sha256'],source_geometry_sha256=b.sha(source),source_field_map_sha256=b.sha(parent/'field_data/coax640.json'),source_arrays_sha256=sources,physical_solver_calls=0))
    snapshot=run/'source_snapshot';snapshot.mkdir()
    for name in ['PublicationSupplementFigures.py','BuildPublicationFigures.wls','PublicationStyles.wl']:shutil.copy2(b.ROOT/'src'/name,snapshot/name)
    return run

def build(parent,languages=('zh-CN','en')):
    run=prepare(parent,languages);b.native_run(run,run/'render_request.json');b.normalize_export_sizes(run);b.verify_panels(run);b.compose(run)
    for lang in languages:
        text=['# '+('几何整体、截面与真实网格补充图件' if lang=='zh-CN' else 'Supplementary Geometry, Sections and Actual Mesh'), '']
        for p in b.read(run/'panel_manifest.json')['panels']:
            if p['language']==lang:text +=[f'<img src="../supplement_figures/panels/{lang}/{p["id"]}.png" width="336" alt="{p["id"]}">','',p['caption'],'']
        (parent/'documents'/('supplement_figures_'+lang+'.md')).write_text('\n'.join(text),encoding='utf-8')
    request=notebook_request(parent,run,languages)
    b.write(run/'document_request.json',request)
    b.native_run(run,run/'document_request.json',script='BuildPublicationDocuments.wls',suffix='_documents')
    import PublicationDocuments
    PublicationDocuments.render_composites(run)
    for doc in request['documents']:shutil.copy2(run/doc['path'],parent/doc['path'])
    b.write(parent/'supplement_figure_manifest.json',dict(run_id=parent.name,child_run='supplement_figures',independent_panels=len(request['documents'])*4,physical_solver_calls=0,source_manifest_sha256=b.sha(run/'source_manifest.json')))

def notebook_request(parent,run,languages):
    docs=[]
    for lang in languages:
        zh=lang=='zh-CN'
        cells=[dict(type='heading',level=1,text='几何整体、截面与真实网格' if zh else 'Overall Geometry, Sections and Actual Mesh',tag='supplement_figures'),dict(type='text',text='几何展示与电磁性能验收分开。图件直接读取冻结中心线和实际三角形连接。' if zh else 'Geometry display and electromagnetic acceptance are distinct. Figures read frozen centerlines and actual triangle connectivity.')]
        for number,panel in enumerate([p for p in b.read(run/'panel_manifest.json')['panels'] if p['language']==lang],22):
            cells.append(dict(type='figure',id=panel['id'],number=number,panels=[f'panels/{lang}/{panel["id"]}.wl'],caption=panel['caption']))
        docs.append(dict(id='supplement_figures_'+lang,title='几何与网格补充图件' if zh else 'Supplementary Geometry and Mesh Figures',language=lang,edition='supplement',cells=cells,path='documents/supplement_figures_'+lang+'.nb'))
    return dict(run_id=parent.name+'_supplement',output_directory=str(run),documents=docs,composites=[])

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args();build(b.ROOT/'outputs'/a.run_id)
