"""Shared, bounded model execution used by CLI, MCP and research Notebooks."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import shutil
import re
from .common import constrain, read, run_directory, sha, tool, write,native_path

ROUTES = {
    'analytic':'analytic','wolfram-analytic':'analytic','fem2':'fem2',
    'circuits':'common_terminal','coax':'common_terminal','coax640':'common_terminal',
    'geometry':'geometry','copper':'geometry','peec':'peec','voxel':'rt0','rt0':'rt0',
    'aphi':'aphi','gpu':'gpu','ansys':'ansys','wolfram':'wolfram',
}
DEFAULTS = {
    'analytic':{'frequency_Hz':200000.,'current_RMS_A':20.},
    'wolfram-analytic':{'frequency_Hz':200000.,'current_RMS_A':20.},
    'fem2':{'mesh_h':0.20},'circuits':{'current_RMS_A':20.},
    'coax':{'strands':7,'diameter_m':0.0001,'mesh_factor':0.7,'return_factor':2.,'outer_factor':1.5,'minimum_segments':24},
    'coax640':{'strands':7,'diameter_m':0.0001,'mesh_factor':0.7,'return_factor':2.,'outer_factor':1.5,'minimum_segments':24},
    'geometry':{'strands':7,'length_m':0.04,'pitch_m':0.02,'diameter_m':0.0001,'kind':'multilevel'},
    'copper':{'strands':640,'diameter_m':0.0001},
    'peec':{'cross_divisions':6,'length_m':0.04,'frequency_Hz':200000.,'quadrature_order':4},
    'voxel':{'dimensions':[2,2,3],'cell_width_m':0.0005,'quadrature_order':6,'excitation':'field'},
    'rt0':{'dimensions':[2,2,3],'cell_width_m':0.0005,'quadrature_order':6,'excitation':'field'},
    'aphi':{'sampling_points':32},'gpu':{'matrix_size':128,'fft_size':4096},'ansys':{},'wolfram':{},
}

def parameters(model, supplied=None, case='tutorial'):
    if model not in ROUTES:raise ValueError('Unknown model: '+model)
    p=dict(DEFAULTS[model]);supplied=supplied or {}
    if model=='aphi' and case in {'manufactured','cylinder-calibration','extrusion-control'}:
        p={'mesh_h':0.35,'solve_timeout_seconds':600,'J_tolerance':0.01,'phi_tolerance':1e-8,'gauge_tolerance':0.001}
        if case=='manufactured':
            p.pop('mesh_h');p.pop('J_tolerance');p['cell_volumes']=[.04,.015,.0035]
    if model=='ansys' and case in {'maxwell-seven','maxwell-seven-convergence'}:p={'frequency_Hz':200000.,'current_RMS_A':20.,'diameter_m':0.0001,'return_factor':2.,'outer_factor':1.5}
    if model=='ansys' and case=='maxwell-seven-convergence':p.update(mesh_length_m=50e-6,return_mesh_length_m=150e-6,air_mesh_length_m=200e-6)
    if set(supplied)-set(p):raise ValueError('Unsupported parameters: '+', '.join(sorted(set(supplied)-set(p))))
    p.update(supplied)
    for k,v in p.items():
        if isinstance(v,(int,float)) and (not __import__('math').isfinite(v) or v<=0):raise ValueError(k+' must be finite and positive')
    if model in {'coax','coax640','geometry'} and (not isinstance(p['strands'],int) or p['strands']>24):raise ValueError('Tutorial strand count must be an integer from 1 to 24; campaigns use their explicit stage.')
    if model in {'coax','coax640'}:
        if not isinstance(p['minimum_segments'],int) or not 12<=p['minimum_segments']<=192:raise ValueError('Tutorial minimum_segments must be an integer 12..192')
        if not .2<=p['mesh_factor']<=1.5:raise ValueError('Tutorial mesh_factor must be 0.2..1.5')
        if not 1.05<=p['return_factor']<=4 or not 1.1<=p['outer_factor']<=3:raise ValueError('Tutorial return/domain factors are outside the controlled range')
    if model=='geometry' and p['kind'] not in {'straight','single','multilevel','crosslayer'}:raise ValueError('Unknown topology')
    if model=='fem2' and not 0.04<=p['mesh_h']<=0.5:raise ValueError('Tutorial mesh_h must be between 0.04 and 0.5')
    if model=='peec' and (not isinstance(p['cross_divisions'],int) or not 4<=p['cross_divisions']<=14):raise ValueError('Tutorial cross_divisions must be 4..14')
    if 'quadrature_order' in p and (not isinstance(p['quadrature_order'],int) or not 4<=p['quadrature_order']<=14):raise ValueError('Tutorial quadrature_order must be an integer 4..14')
    if model=='aphi' and 'sampling_points' in p and (not isinstance(p['sampling_points'],int) or not 4<=p['sampling_points']<=128):raise ValueError('Diagnostic sampling_points must be 4..128')
    if model=='aphi' and 'mesh_h' in p:
        if p['mesh_h'] not in {.35,.22,.14}:raise ValueError('Calibration mesh_h must be .35, .22 or .14')
    if model=='aphi' and 'solve_timeout_seconds' in p:
        if p['solve_timeout_seconds']>600:raise ValueError('A-phi solve budget is at most 600 seconds')
        if p.get('J_tolerance',.01)>.01 or p['phi_tolerance']>1e-8 or p['gauge_tolerance']>.001:raise ValueError('Calibration thresholds cannot be relaxed')
        if case=='manufactured' and p['cell_volumes']!=[.04,.015,.0035]:raise ValueError('Use the three approved manufactured meshes')
    if model in {'voxel','rt0'}:
        if len(p['dimensions'])!=3 or any(not isinstance(n,int) or not 2<=n<=4 for n in p['dimensions']):raise ValueError('Tutorial dimensions must contain three integers 2..4')
        if p['excitation'] not in {'field','transport'}:raise ValueError('Excitation must be field or transport')
    if model=='gpu' and (not isinstance(p['matrix_size'],int) or not isinstance(p['fft_size'],int) or p['matrix_size']>512 or p['fft_size']>16384):raise ValueError('GPU tutorial exceeds its validated small workload')
    if model=='ansys' and case=='maxwell-seven-convergence':
        if p['mesh_length_m'] not in {50e-6,40e-6,35e-6,30e-6,25e-6}:raise ValueError('Use an approved Maxwell mesh candidate')
        if p['diameter_m']!=.0001 or p['frequency_Hz']!=200000. or p['current_RMS_A']!=20.:raise ValueError('Convergence uses the fixed seven-strand calibration')
        if not 2<=p['return_factor']<=2.4 or not 1.5<=p['outer_factor']<=2.25:raise ValueError('Boundary study outside the approved range')
    allowed={'tutorial'}|({'diagnostic','manufactured','cylinder-calibration','extrusion-control'} if model=='aphi' else {'frequency-sweep'} if model=='analytic' else {'preflight','maxwell-seven','maxwell-seven-convergence'} if model=='ansys' else set())
    if case not in allowed:raise ValueError('Unsupported case for '+model+': '+case)
    if case=='frequency-sweep' and model!='analytic':raise ValueError('frequency-sweep belongs to the Python analytical model')
    return p

def source_manifest(root):
    roots=('models','adapters','shared','python','automation','configs','tools','tests','references')
    result={p.relative_to(root).as_posix():sha(p) for name in roots for p in (root/name).rglob('*') if p.is_file() and p.suffix in {'.py','.wl','.wls','.wlt','.ps1','.json','.md','.toml','.bib','.lock'} and '__pycache__' not in p.parts}
    result.update({name:sha(root/name) for name in ['AGENTS.md','pyproject.toml'] if (root/name).exists()})
    return result

def plan(root, model, run_id, case='tutorial', supplied=None):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',run_id):raise ValueError('Run IDs use letters, digits, underscores and hyphens.')
    p=parameters(model,supplied,case);diagnostics=[]
    if (root/'outputs'/run_id).exists():diagnostics.append('Run directory already exists; choose a new --run-id.')
    if model!='analytic' and model!='ansys' and not tool(root,'wolframscript'):diagnostics.append('Wolfram kernel required; configure LITZ_WOLFRAMSCRIPT.')
    if model=='aphi' and case in {'tutorial','diagnostic'}:
        from .common import evidence_path
        try:evidence_path(root,'outputs/rerun_20261005_fem3_cylinder_report/results.wxf')
        except FileNotFoundError:diagnostics.append('Fetch the aphi dataset.')
    if model=='ansys' and case in {'maxwell-seven','maxwell-seven-convergence'}:
        local=read(root/'litz.config.json') if (root/'litz.config.json').exists() else {}
        executable=tool(root,'ansys_python') or local.get('mcp_servers',{}).get('ansys',{}).get('command')
        if not executable or not Path(executable).is_file():diagnostics.append('Configure the Ansys MCP Python executable for maxwell-seven.')
    return dict(model=model,route=ROUTES[model],case=case,run_id=run_id,parameters=p,dispatch_status='blocked' if diagnostics else 'ready',diagnostics=diagnostics,execution_status='plan_only',resource_policy={'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':1200},output='outputs/'+run_id)

def execute(root, model, run_id, case='tutorial', supplied=None):
    if (root/'outputs/.jobs'/(run_id+'.cancel')).exists():
        out=run_directory(root,run_id)
        result={'run_id':run_id,'source_model':model,'execution_status':'cancelled','physical_acceptance_status':'not_run','solver_started':False}
        write(out/'results.json',result)
        return result
    request=plan(root,model,run_id,case,supplied)
    if request['diagnostics']:raise ValueError('; '.join(request['diagnostics']))
    out=run_directory(root,run_id);started=time.monotonic();constrain()
    write(out/'request.json',request);write(out/'parameters.json',request['parameters'])
    sources=source_manifest(root)
    for relative in sources:
        target=native_path(out/'source_snapshot'/relative);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/relative,target)
    frozen_inputs=[]
    if model=='aphi' and case in {'tutorial','diagnostic'}:
        from .common import evidence_path
        field=evidence_path(root,'outputs/rerun_20261005_fem3_cylinder_report/results.wxf')
        frozen_inputs=[{'path':'outputs/rerun_20261005_fem3_cylinder_report/results.wxf','sha256':sha(field),'use':'original saved field input; diagnostic sampling does not change it'}]
    write(out/'run_manifest.json',{'run_id':run_id,'sources':sources,'frozen_inputs':frozen_inputs,'request_sha256':sha(out/'request.json')})
    write(out/'environment.json',{'python':platform.python_version(),'platform':platform.system(),'timestamp_UTC':datetime.now(timezone.utc).isoformat(),'resource_policy':request['resource_policy']})
    write(out/'process_status.json',{'execution_status':'running','pid':os.getpid(),'started_UTC':datetime.now(timezone.utc).isoformat()})
    try:
        if model=='analytic':
            from .analytical import execute as analytical_execute
            result=analytical_execute(root,out,request['parameters'],case)
        elif model=='ansys':
            if case in {'maxwell-seven','maxwell-seven-convergence'}:
                from .ansys_task import execute as execute_native
                result=execute_native(root,out,request['parameters'])
            else:result={'run_id':run_id,'source_model':'Maxwell_resource_preflight','execution_status':'preflight_only','physical_acceptance_status':'not_run','solver_started':False,'resource_policy':request['resource_policy'],'scope':'Use case maxwell-seven or the Ansys MCP example for the actual native solve.'}
        else:
            from .automation import server_environment
            env=dict(os.environ,**server_environment(root,'wolfram'))
            env.update(LITZ_PROJECT=str(root),LITZ_RUN_ID=run_id,LITZ_TUTORIAL_MODEL=model,LITZ_CLOSURE_CPU_THREADS='8',LITZ_RAM_BUDGET=str(24*2**30))
            if model=='aphi' and case in {'tutorial','diagnostic'}:
                from .common import evidence_path
                env['LITZ_APHI_SOURCE']=str(evidence_path(root,'outputs/rerun_20261005_fem3_cylinder_report/results.wxf'))
            cmd=[tool(root,'wolframscript'),'-local','-file',str(root/'adapters/wolfram/RunResearchCase.wls')]
            if model=='aphi' and case in {'manufactured','cylinder-calibration','extrusion-control'}:
                env['LITZ_APHI_CASE']=case
                cmd[-1]=str(root/'adapters/wolfram/RunAPhiCalibration.wls')
            process=bounded_process(cmd,root,out,env,request['resource_policy'])
            result=read(out/'results.json') if (out/'results.json').exists() else {}
            result|={'actual_exit_code':process['actual_exit_code']}
            if process['execution_status']!='completed':
                result|={'execution_status':process['execution_status'],'failure_reason':process['failure_reason'],'physical_acceptance_status':'not_verified'}
            elif not result.get('source_model'):
                result|={'execution_status':'failed','failure_reason':'solver_produced_no_result','physical_acceptance_status':'not_verified'}
        result['elapsed_seconds']=time.monotonic()-started
        write(out/'results.json',result)
        write(out/'process_status.json',{'execution_status':result['execution_status'],'elapsed_seconds':result['elapsed_seconds'],'actual_exit_code':result.get('actual_exit_code',0)})
        return result
    except Exception as exc:
        result={'run_id':run_id,'source_model':model,'execution_status':'failed','physical_acceptance_status':'not_verified','error':str(exc),'elapsed_seconds':time.monotonic()-started}
        write(out/'results.json',result);(out/'error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        write(out/'process_status.json',result)
        raise

def bounded_process(cmd,root,out,env,policy):
    import psutil
    from .processes import stop_owned,owned_tree
    started=time.monotonic();started_wall=time.time();owned={};samples=[];reason=None;receipt=False
    with (out/'run_log.txt').open('w',encoding='utf-8') as log,(out/'stderr.txt').open('w',encoding='utf-8') as error:
        process=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=error,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        parent=psutil.Process(process.pid);owned[parent.pid]=parent.create_time()
        while process.poll() is None:
            try:
                children=owned_tree(parent);rss=0
                for child in children:
                    owned[child.pid]=child.create_time();rss+=child.memory_info().rss
                    if hasattr(child,'cpu_affinity'):child.cpu_affinity(child.cpu_affinity()[:8])
                free=psutil.virtual_memory().available
                samples.append({'seconds':time.monotonic()-started,'rss_bytes':rss,'system_free_bytes':free})
                if rss>policy['task_memory_bytes']:reason='task_memory_budget'
                if free<policy['system_reserve_bytes']:reason='system_memory_reserve'
                if time.monotonic()-started>policy['timeout_seconds']:reason='timeout'
                if (out/'cancel_requested.json').exists() or (root/'outputs/.jobs'/(out.name+'.cancel')).exists():reason='cancelled'
                if env.get('LITZ_PARENT_RUN_ID') and (root/'outputs/.jobs'/(env['LITZ_PARENT_RUN_ID']+'.cancel')).exists():reason='cancelled'
                completion=policy.get('completion_file')
                if completion and Path(completion).exists() and Path(completion).stat().st_mtime>=started_wall:
                    # A saved frontend receipt is the completion boundary. Some
                    # licensed frontend helpers stay alive after NotebookEvaluate.
                    # Release only this process tree after its saved receipt.
                    completion_status=read(Path(completion)).get('status')
                    receipt=completion_status in {'passed_frontend_scope','failed','timeout','completed_mcp_calls'}
                    if receipt:reason='mcp_calls_receipt_saved' if completion_status=='completed_mcp_calls' else 'frontend_receipt_saved'
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
            if reason:
                for pid,created in reversed(list(owned.items())):
                    try:
                        stop_owned(pid,created)
                    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                break
            time.sleep(.5)
        try:code=process.wait(timeout=15)
        except subprocess.TimeoutExpired:code=None
        # A completed local task releases any helper it created; no unrelated
        # frontend, MCP server or solver session is selected by executable name.
        for pid,created in reversed(list(owned.items())):
            if pid!=process.pid:stop_owned(pid,created)
    write(out/'resource_samples.json',samples);write(out/'owned_processes.json',owned)
    return {'execution_status':'completed' if receipt else 'cancelled' if reason=='cancelled' else 'blocked' if reason else 'completed' if code==0 else 'failed','actual_exit_code':code,'failure_reason':None if receipt else reason,'cleanup_reason':reason if receipt else None,'completion_receipt_observed':receipt,'physical_acceptance_status':'not_verified'}

def submit(root,model,run_id,case='tutorial',supplied=None):
    request=plan(root,model,run_id,case,supplied)
    if request['diagnostics']:raise ValueError('; '.join(request['diagnostics']))
    queue=root/'outputs/.jobs';queue.mkdir(parents=True,exist_ok=True)
    ticket=queue/(run_id+'.json')
    with ticket.open('x',encoding='utf-8') as stream:json.dump(request,stream)
    cmd=[sys.executable,'-m','litz_research','--project',str(root),'jobs','worker',str(ticket)]
    with (queue/(run_id+'.log')).open('w',encoding='utf-8') as log:
        proc=subprocess.Popen(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    import threading
    threading.Thread(target=proc.wait,daemon=True).start()
    import psutil
    write(queue/(run_id+'.process.json'),{'pid':proc.pid,'created':psutil.Process(proc.pid).create_time(),'ticket_sha256':sha(ticket)})
    return request|{'execution_status':'submitted','pid':proc.pid}

def status(root,run_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',run_id):raise ValueError('Invalid run ID')
    out=root/'outputs'/run_id
    queue=root/'outputs/.jobs'
    result=read(out/'results.json') if (out/'results.json').exists() else None
    if result and result.get('execution_status')=='cancelled' and result.get('solver_started') is False:return result
    if (queue/(run_id+'.process.json')).exists():
        import psutil
        identity=read(queue/(run_id+'.process.json'))
        try:alive=psutil.Process(identity['pid']).create_time()==identity['created']
        except (psutil.Error,KeyError):alive=False
        if result and result.get('execution_status') not in {'submitted','running'}:
            # Solvers may save a completed result before MCP/session cleanup.
            # Only publish task completion after the worker finalized its receipt.
            finalized=read(out/'process_status.json') if (out/'process_status.json').exists() else {}
            if alive:
                return result|{'execution_status':'running','result_execution_status':result['execution_status'],'worker_status':'finishing'}
            if finalized.get('execution_status') not in {None,'running','submitted'}:return result
        if not alive:return {'run_id':run_id,'execution_status':'interrupted_worker_missing','physical_acceptance_status':'not_verified'}
    if result:return result
    if (out/'process_status.json').exists():return read(out/'process_status.json')
    if (queue/(run_id+'.json')).exists():return {'run_id':run_id,'execution_status':'submitted'}
    raise FileNotFoundError('Unknown task: '+run_id)

def resume(root,run_id,new_run_id):
    state=status(root,run_id)
    if state['execution_status'] in {'submitted','running'}:raise ValueError('The original task is still active; query or cancel it before restarting.')
    out=root/'outputs'/run_id
    if not (out/'request.json').exists() and state.get('solver_started') is False:
        ticket=root/'outputs/.jobs'/(run_id+'.json');identity=read(root/'outputs/.jobs'/(run_id+'.process.json'))
        if sha(ticket)!=identity.get('ticket_sha256'):raise ValueError('Queued input identity changed')
        request=read(ticket);result=submit(root,request['model'],new_run_id,request['case'],request['parameters'])
        parent={'parent_run_id':run_id,'resume_method':'restart_from_verified_queued_inputs','original_solver_started':False}
        write(root/'outputs/.jobs'/(new_run_id+'.parent.json'),parent)
        return result|{'parent':parent}
    request=read(out/'request.json');manifest=read(out/'run_manifest.json')
    if sha(out/'request.json')!=manifest['request_sha256']:raise ValueError('Saved task input identity changed')
    for relative,identity in manifest['sources'].items():
        if sha(out/'source_snapshot'/relative)!=identity:raise ValueError('Saved source checkpoint identity changed: '+relative)
    current=source_manifest(root)
    changes=[relative for relative,identity in manifest['sources'].items() if current.get(relative)!=identity]
    result=submit(root,request['model'],new_run_id,request['case'],request['parameters'])
    parent={'parent_run_id':run_id,'resume_method':'restart_from_verified_saved_inputs','source_changes_since_parent':changes,'checkpoint_recovery':'not_supported_for_this_tutorial'}
    write(root/'outputs/.jobs'/(new_run_id+'.parent.json'),parent)
    return result|{'parent':parent}
