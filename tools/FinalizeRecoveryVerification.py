"""Continue saved recovery verification after completed MCP steps."""
from pathlib import Path
import argparse,subprocess,shutil,os
from litz_research.common import read,write,sha,constrain,native_path
from litz_research.tasks import bounded_process

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--control',required=True);p.add_argument('--historical-source',required=True);p.add_argument('--native-lifecycle',required=True);a=p.parse_args()
    root=Path(a.project).resolve();control=Path(a.control).resolve();historical=Path(a.historical_source).resolve();constrain()
    records=read(control/'verification.json')
    required_steps={'clone_update','install','dependencies','analytic','fetch','verify','corruption_detection','protect_independent_edit','offline_restore','configuration','wolfram_MCP','ansys_MCP'}
    if not required_steps.issubset({r['step'] for r in records if r['passed']}):raise ValueError('Completed recovery step evidence is incomplete')
    lifecycle=read(Path(a.native_lifecycle)/'receipt.json')
    if lifecycle['status']!='passed':raise ValueError('Native task lifecycle did not pass')
    catalog=read(root/'data/catalog.json');required={r['path'] for r in catalog['datasets']['publication-inputs']['files']}
    required.update(['outputs/full_20261005_handoff/field_case_005/port_and_loss.json','outputs/full_20261005_handoff/geometry_manifest.json','outputs/closure_20261005_ansys_probe_r2/results.json','outputs/closure_20261005_ansys_2dmesh_01/results.json'])
    identities={r['path']:r for d in catalog['datasets'].values() for r in d['files']}
    for relative,identity in read(root/'manuscript/publication.json')['scientific_hashes'].items():
        if (root/relative).is_file() and sha(root/relative)!=identity:raise ValueError('Git-restored frozen metadata identity: '+relative)
    for relative in sorted(required):
        source=historical/relative
        if sha(source)!=identities[relative]['sha256']:raise ValueError('Historical fixture identity: '+relative)
        destination=native_path(root/'data/evidence'/catalog['tag']/relative);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    write(control/'historical_fixtures.json',{'source_version':catalog['tag'],'source':'independently hash-verified immutable local evidence mount','files':[identities[r] for r in sorted(required)]})
    dependencies=control/'test_dependencies';dependencies.mkdir(exist_ok=False)
    policy={'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':600}
    installed=bounded_process([str(root/'.venv/Scripts/python.exe'),'-m','pip','install','-e',str(root)+'[figures,documents,ansys,audit]','-c',str(root/'automation/mcp/project-environment.lock')],root,dependencies,dict(os.environ),policy)
    if installed['actual_exit_code']!=0:raise RuntimeError('Full regression dependencies could not be installed')
    out=control/'regression_final';out.mkdir(exist_ok=False)
    process=bounded_process([str(root/'.venv/Scripts/python.exe'),'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],root,out,dict(os.environ),{'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':120})
    if process['actual_exit_code']!=0:raise RuntimeError('Recovered source regression failed; see '+str(out))
    receipt={'status':'passed','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'path_contains_spaces':' ' in str(root),'steps':records+[{'step':'regression','process':process,'passed':True}],'files_restored':len(catalog['datasets']['automation-rc2']['files']),'remote_part_hashes':[r['sha256'] for r in catalog['datasets']['automation-rc2']['parts']],'historical_fixtures':len(required),'historical_fixture_origin':'verified immutable rc.1 mount; not represented as a fresh remote download','native_lifecycle':lifecycle,'continuation':'Completed MCP steps retained; the historical fixture list was corrected to use Git-restored prewrite metadata and catalogued data separately.','scope':'Independent clone/venv in a path containing spaces; remote data, corruption/edit protection, offline restore, five-tool Wolfram MCP, native Ansys MCP, actual shared-task cancel/restart and complete current Python regression.'}
    write(control/'recovery_receipt.json',receipt);print('INDEPENDENT RECOVERY PASSED',flush=True)

if __name__=='__main__':main()
