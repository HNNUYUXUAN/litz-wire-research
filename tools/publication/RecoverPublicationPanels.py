"""Recover a publication run without redrawing unaffected, source-bound panels."""
import argparse
import copy
from pathlib import Path
import shutil
import BuildPublicationEdition as b

def recover(previous,run,only=None):
    run.mkdir(exist_ok=False)
    for name in ['field_data','tables']:
        shutil.copytree(previous/name,run/name)
    for name in ['field_reconstruction_verification.json','source_manifest.json','specimen_numeric_data.json']:
        shutil.copy2(previous/name,run/name)
    snapshot=run/'source_snapshot';snapshot.mkdir()
    for p in b.ROOT.joinpath('src').glob('Publication*.py'):shutil.copy2(p,snapshot/p.name)
    for name in ['BuildPublicationEdition.py','BuildPublicationFigures.wls','PublicationStyles.wl','RecoverPublicationPanels.py']:
        shutil.copy2(b.ROOT/'src'/name,snapshot/name)
    original=b.read(previous/'render_request.json');request=copy.deepcopy(original);request['run_id']=run.name;request['output_directory']=str(run)
    manifest=b.read(previous/'panel_manifest.json');reused=[];rerender=[]
    for spec in request['panels']:
        if 'data_file' in spec:spec['data_file']=str(run/'field_data'/Path(spec['data_file']).name)
        needs=(spec['id'] in only) if only is not None else (spec['kind'] in {'density','mesh_field','cell_field','field3d','schematic'} or spec['id'] in {'peec_sensitivity','gpu_equivalence','resource_memory'})
        if spec['id']=='rt0_loss_slice':spec['color_label']='p (W/cm³)'
        if spec['id']=='resource_memory':
            for series in spec['series']:
                origin=series.get('source_run_id',series['label']);series['source_run_id']=origin
                series['label']={'closure_20261005_gpu_m80_01':'CPU/GPU 5024','closure_20261005_peec_m80_l064_self12p10_01':'PEEC 5024','closure_20261005_rt0_n24_q14_01':'RT0 27648'}[origin]
        if needs:rerender.append(spec);continue
        record=copy.deepcopy(next(p for p in manifest['panels'] if p['id']==spec['id'] and p['language']==spec['language']))
        record['reused_from_publication_run_id']=previous.name;record['reused_without_plotting']=True
        for asset in record['assets']:
            source=previous/asset['path_relative_to_run'];dest=run/asset['path_relative_to_run'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
            if b.sha(dest)!=asset['sha256']:raise ValueError('Copied panel hash mismatch')
            asset['path']=str(dest)
        expr=Path(record['native_expression']);destination=run/'panels'/record['language']/expr.name;shutil.copy2(expr,destination);record['native_expression']=str(destination)
        if expr.with_suffix('.wxf').exists():shutil.copy2(expr.with_suffix('.wxf'),destination.with_suffix('.wxf'))
        reused.append(record)
    source_manifest=b.read(run/'source_manifest.json');source_manifest.update(run_id=run.name,previous_publication_run_id=previous.name,previous_source_manifest_sha256=b.sha(previous/'source_manifest.json'),field_reconstruction_run_id=b.read(run/'field_reconstruction_verification.json')['run_id']);b.write(run/'source_manifest.json',source_manifest)
    b.write(run/'render_request.json',request)
    partial=copy.deepcopy(request);partial['panels']=rerender;b.write(run/'recovery_render_request.json',partial)
    b.write(run/'recovery_manifest.json',{'previous_run_id':previous.name,'source_panel_manifest_sha256':b.sha(previous/'panel_manifest.json'),
        'reused_panel_count':len(reused),'redrawn_panel_count':len(rerender),'reasons':['Normalize BarLegend physical arguments to the shared normalized color map','Convert JSON null axis scaling to Wolfram None','Repair 3D label padding and schematic text fit','Replace resource run-ID legends with concise scientific labels'],
        'additional_recovery_scope':only,'physical_solver_calls':0,'reused_panels':reused})
    b.native_run(run,run/'recovery_render_request.json')
    b.normalize_export_sizes(run)
    new=b.read(run/'panel_manifest.json');new['panels']+=reused
    new['panels'].sort(key=lambda p:next(k for k,s in enumerate(request['panels']) if s['language']==p['language'] and s['id']==p['id']))
    new['recovery_manifest_sha256']=b.sha(run/'recovery_manifest.json');b.write(run/'panel_manifest.json',new)
    b.verify_panels(run);b.compose(run)
    print('Recovered all panels with untouched-panel hash preservation',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--from-run-id',required=True);p.add_argument('--run-id',required=True);p.add_argument('--only-panel-id',action='append');a=p.parse_args()
    for id in [a.from_run_id,a.run_id]:
        if not __import__('re').fullmatch('[A-Za-z0-9_-]+',id):p.error('Safe unique run ID required')
    recover(b.ROOT/'outputs'/a.from_run_id,b.ROOT/'outputs'/a.run_id,a.only_panel_id)
