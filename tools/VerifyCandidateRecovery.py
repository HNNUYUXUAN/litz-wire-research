"""Recover the private candidate into a fresh path containing spaces."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,shutil
from litz_research.common import constrain,read,write,sha
from litz_research.tasks import bounded_process

def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--ansys-python',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--cache');p.add_argument('--historical-source');a=p.parse_args()
    host=Path(__file__).resolve().parents[1];target=Path(a.directory).resolve()
    if target.exists() and not a.resume:raise FileExistsError('Choose a new recovery directory or explicitly resume this owned clone')
    attempt=time.strftime('%Y%m%d_%H%M%S');constrain();control=target.parent/('recovery_verification_'+attempt);control.mkdir(exist_ok=False)
    cache=Path(a.cache).resolve() if a.cache else control/'cache';records=[]
    policy={'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':600}
    def step(name,cmd,cwd,expected=0,env=None):
        out=control/name;out.mkdir(exist_ok=False)
        result=bounded_process([str(v) for v in cmd],cwd,out,env or dict(os.environ),policy)
        record={'step':name,'process':result,'passed':result['actual_exit_code']==expected}
        records.append(record);write(control/'verification.json',records);print(name,record['passed'],flush=True)
        if not record['passed']:raise RuntimeError('Recovery step failed: '+name+'; see '+str(out))
        return out
    if a.resume:
        remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=target,text=True).strip()
        if remote!='https://github.com/HNNUYUXUAN/litz-wire-research.git':raise ValueError('Recovery repository identity differs')
        subprocess.run(['git','diff','--quiet'],cwd=target,check=True)
        step('clone_update',['git','pull','--ff-only'],target)
    else:step('clone',['git','clone','--depth','1','https://github.com/HNNUYUXUAN/litz-wire-research.git',target],host)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=target,text=True).strip()
    if not (target/'.venv').exists():step('venv',[sys.executable,'-m','venv',target/'.venv'],target)
    python=target/'.venv/Scripts/python.exe'
    step('install',[python,'-m','pip','install','-e',str(target)+'[automation]','-c',target/'automation/mcp/project-environment.lock'],target)
    step('dependencies',[python,'-m','pip','check'],target)
    cli=[python,'-m','litz_research']
    step('analytic',cli+['run','analytic','--case','tutorial','--run-id','restore_analytic_'+attempt],target)
    step('fetch',cli+['data','fetch','automation-rc2','--cache',cache],target)
    step('verify',cli+['data','verify','automation-rc2'],target)
    catalog=read(target/'data/catalog.json');spec=catalog['datasets']['automation-rc2']
    entry=next(r for r in spec['files'] if r['path']=='outputs/rc2_maxwell_mcp_verified_01/results.json')
    restored=target/'data/evidence'/spec['source_version']/entry['path']
    assert restored.resolve().is_relative_to(target)
    restored.write_bytes(restored.read_bytes()+b'corrupt fixture')
    step('corruption_detection',cli+['data','verify','automation-rc2'],target,expected=1)
    step('protect_independent_edit',cli+['data','fetch','automation-rc2','--offline','--cache',cache],target,expected=1)
    restored.unlink()
    step('offline_restore',cli+['data','fetch','automation-rc2','--offline','--cache',cache],target)
    if sha(restored)!=entry['sha256']:raise ValueError('Offline result identity differs')
    step('configuration',cli+['automation','configure','--output','build/client','--ansys-python',a.ansys_python],target)
    import tomllib
    config=tomllib.loads((target/'build/client/config.toml').read_text(encoding='utf-8'))
    if set(config['mcp_servers'])!={'wolfram','ansys'}:raise ValueError('Invalid generated configuration')
    write(target/'litz.config.json',{'mcp_servers':read(target/'build/client/mcp.json')['mcpServers']})
    step('wolfram_sequence',[python,'automation/examples/wolfram-calibration/build_sequence.py','--run-id','restore_wolfram_study_'+attempt,'--output','build/wolfram_sequence.json'],target)
    step('wolfram_MCP',cli+['automation','probe','wolfram','--run-id','restore_wolfram_mcp_'+attempt,'--sequence','build/wolfram_sequence.json'],target)
    owner_out=target/('outputs/restore_aedt_owner_'+attempt);owner_out.mkdir();owner_log=(control/'owner_launch.log').open('w',encoding='utf-8')
    owner=subprocess.Popen([a.ansys_python,str(target/'adapters/ansys/OwnedAEDTSession.py'),'--output',str(owner_out),'--timeout','300'],cwd=target,stdout=owner_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:
        deadline=time.monotonic()+60
        while not (owner_out/'aedt_session.json').exists() and time.monotonic()<deadline:
            if owner.poll() is not None:raise RuntimeError('AEDT owner exited before its session receipt')
            time.sleep(.5)
        if not (owner_out/'aedt_session.json').exists():raise TimeoutError('AEDT session receipt')
        step('ansys_sequence',[python,'automation/examples/ansys-native/build_sequence.py','--session',owner_out/'aedt_session.json','--run-id','restore_maxwell_'+attempt,'--output','build/ansys_sequence.json'],target)
        step('ansys_MCP',cli+['automation','probe','ansys','--run-id','restore_ansys_mcp_'+attempt,'--sequence','build/ansys_sequence.json'],target)
    finally:
        (owner_out/'stop_session').touch();owner.wait(timeout=30);owner_log.close()
    maxwell=read(target/'outputs'/('restore_maxwell_'+attempt)/'results.json')
    if maxwell['physical_acceptance_status']!='passed_port_and_power_scope_only':raise ValueError('Restored native Maxwell case failed')
    if a.historical_source:
        historical=Path(a.historical_source).resolve();required={r['path'] for r in catalog['datasets']['publication-inputs']['files']}
        required.update(['outputs/full_20261005_handoff/field_case_005/port_and_loss.json','outputs/full_20261005_handoff/geometry_manifest.json','outputs/closure_20261005_ansys_probe_r2/results.json','outputs/closure_20261005_ansys_2dmesh_01/results.json','outputs/prewrite_closure_state.json'])
        identities={r['path']:r for d in catalog['datasets'].values() for r in d['files']}
        for relative in sorted(required):
            source=historical/relative
            if sha(source)!=identities[relative]['sha256']:raise ValueError('Historical fixture checksum: '+relative)
            destination=target/'data/evidence'/catalog['tag']/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
        write(control/'historical_fixtures.json',{'source_version':catalog['tag'],'source':'previously verified immutable evidence mount','files':[identities[path] for path in sorted(required)]})
    else:
        for dataset in ['publication-inputs','ansys','research-records']:step('fixtures_'+dataset,cli+['data','fetch',dataset,'--cache',cache],target)
    step('regression',[python,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],target)
    receipt={'status':'passed','source_commit':commit,'path_contains_spaces':' ' in str(target),'steps':records,'files_restored':len(spec['files']),'remote_part_hashes':[r['sha256'] for r in spec['parts']],'native_maxwell':{k:maxwell[k] for k in ['current_constraint_relative_error','power_relative_error','bundle_Rac_ohm_per_m']},'owned_session_closed':read(owner_out/'aedt_session_closed.json'),'scope':'Independent fresh clone/venv; remote attachment recovery, damage detection, edit protection, offline restore, parsed client config, five Wolfram MCP tools and native Maxwell MCP solve in a path containing spaces.'}
    write(control/'recovery_receipt.json',receipt);print('RECOVERY PASSED',flush=True)

if __name__=='__main__':main()
