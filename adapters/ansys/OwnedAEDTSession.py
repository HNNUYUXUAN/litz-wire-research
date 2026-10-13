"""Own one explicit Student gRPC session until a stop file or time limit."""
import argparse,json,time,os
from pathlib import Path
from datetime import datetime,timezone
from ansys.aedt.core import Desktop

def main():
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'python'))
    from litz_research.common import constrain
    constrain()
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--version',default='2025.2');p.add_argument('--timeout',type=int,default=1800);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    desktop=None;owned={}
    try:
        desktop=Desktop(version=a.version,non_graphical=True,new_desktop=True,student_version=True,close_on_exit=True)
        import psutil
        aedt=psutil.Process(desktop.aedt_process_id);owned[aedt.pid]=aedt.create_time()
        (out/'aedt_session.json').write_text(json.dumps({'port':desktop.port,'version':desktop.aedt_version,'student_version':True,'pid':aedt.pid,'process_created':aedt.create_time(),'started_UTC':datetime.now(timezone.utc).isoformat()},indent=2))
        owner=psutil.Process();samples=[];start=time.monotonic();reason='stop_requested'
        while time.monotonic()-start<a.timeout and not (out/'stop_session').exists():
            children=owner.children(recursive=True)
            try:
                if aedt.create_time()==owned[aedt.pid]:children+=[aedt,*aedt.children(recursive=True)]
            except psutil.Error:pass
            children=list({child.pid:child for child in children}.values());rss=owner.memory_info().rss
            for child in children:
                try:owned[child.pid]=child.create_time();rss+=child.memory_info().rss;child.cpu_affinity(child.cpu_affinity()[:8])
                except psutil.Error:pass
            free=psutil.virtual_memory().available
            samples.append({'seconds':time.monotonic()-start,'owned_rss_bytes':rss,'system_free_bytes':free})
            (out/'resource_samples.json').write_text(json.dumps(samples))
            if rss>24*2**30 or free<8*2**30:reason='resource_budget';break
            time.sleep(1)
        (out/'session_stop_reason.json').write_text(json.dumps({'reason':reason}))
    finally:
        failure=sys.exc_info()[1]
        from litz_research.processes import stop_owned
        cleanup=[{'pid':pid,'created':created,'terminated':stop_owned(pid,created)} for pid,created in reversed(list(owned.items()))]
        (out/'aedt_session_closed.json').write_text(json.dumps({'closed_UTC':datetime.now(timezone.utc).isoformat(),'shutdown_method':'creation-bound owned-process cleanup after caller has saved results','owned_cleanup':cleanup,'owner_error':str(failure) if failure else None}))
        # PyAEDT registers a second interpreter-exit release. After terminating
        # this owned session its callback can recurse while logging stale RPCs.
        # The receipt above is durable before bypassing those exit callbacks.
        sys.stdout.flush();sys.stderr.flush();os._exit(1 if failure else 0)

if __name__=='__main__':main()
