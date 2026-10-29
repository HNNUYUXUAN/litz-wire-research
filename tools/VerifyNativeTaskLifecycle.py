"""Actual submit/status/cancel/restart of the shared native Maxwell MCP task."""
from pathlib import Path
import argparse,json,os,subprocess,time,sys

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);p.add_argument('--project-python');a=p.parse_args()
    root=Path(a.project).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root/'python'))
    from litz_research.common import read,write,constrain
    constrain();python=Path(a.project_python).resolve() if a.project_python else root/'.conda/project/python.exe';cli=[str(python),'-m','litz_research'];records=[]
    def call(*args):
        result=subprocess.run(cli+list(args),cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        record={'command':list(args),'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr};records.append(record);write(out/'commands.json',records)
        if result.returncode:raise RuntimeError(result.stderr)
        return json.loads(result.stdout)
    stamp=time.strftime('%Y%m%d_%H%M%S');cancelled='native_cancel_'+stamp;restarted='native_restart_'+stamp
    submitted=call('jobs','submit','ansys','--case','maxwell-seven','--run-id',cancelled)
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        state=call('jobs','status',cancelled)
        if (root/'outputs'/cancelled/'owned_session/aedt_session.json').exists():break
        if state['execution_status'] not in {'submitted','running'}:raise RuntimeError('Native task ended before cancellation: '+str(state))
        time.sleep(1)
    else:raise TimeoutError('Owned native session did not start')
    call('jobs','cancel',cancelled)
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        state=call('jobs','status',cancelled)
        if state['execution_status']=='cancelled':break
        time.sleep(1)
    else:raise TimeoutError('Native task did not cancel')
    closed=read(root/'outputs'/cancelled/'owned_session/aedt_session_closed.json')
    resumed=call('jobs','resume',cancelled,'--new-run-id',restarted)
    deadline=time.monotonic()+240
    while time.monotonic()<deadline:
        state=call('jobs','status',restarted)
        if state['execution_status']=='completed':break
        if state['execution_status'] not in {'submitted','running'}:raise RuntimeError('Native restart failed: '+str(state))
        time.sleep(2)
    else:raise TimeoutError('Native restart did not finish')
    if state['physical_acceptance_status']!='passed_port_and_power_scope_only':raise RuntimeError('Native physical checks failed')
    receipt={'status':'passed','cancelled_run_id':cancelled,'restarted_run_id':restarted,'submitted':submitted,'resumed':resumed,'cancellation_closed_session':closed,'result':state,'repository_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'scope':'Actual Student session; asynchronous submission, live status, cooperative cancellation with owned-session closure, verified-input restart under a new ID and complete native MCP Maxwell solve.'}
    write(out/'receipt.json',receipt);print('NATIVE TASK LIFECYCLE PASSED',flush=True)

if __name__=='__main__':main()
