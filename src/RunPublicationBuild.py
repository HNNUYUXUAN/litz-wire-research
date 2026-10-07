"""Supervise one publication stage with an owned process tree and resource limits."""
import os,sys,time,ctypes
from pathlib import Path
from BuildPublicationEdition import ROOT,write
from BuildLaTexSmoke import environment
import PreManuscriptClosure as control

args=sys.argv[1:]
run_id=args[args.index('--run-id')+1];stage=args[args.index('--stage')+1] if '--stage' in args else 'all'
folder=ROOT/'outputs'/run_id/('monitor_'+stage+'_'+time.strftime('%Y%m%d_%H%M%S'));folder.mkdir(parents=True)
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.GetCurrentProcess.restype=ctypes.c_void_p
kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
affinity=(1<<min(8,os.cpu_count() or 1))-1
if not kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),affinity):raise ctypes.WinError(ctypes.get_last_error())
write(folder/'cpu_affinity.json',{'logical_processor_limit':min(8,os.cpu_count() or 1),'inherited_affinity_mask':affinity})
actual=control.hardware();budget=min(24*control.GIB,actual['free_RAM_bytes']-8*control.GIB)
if budget<=0:raise RuntimeError('System reserve preflight: 8 GiB required')
write(folder/'environment.json',actual)
env=environment();env.update(CUDA_VISIBLE_DEVICES='',PYTHONUTF8='1',LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES=str(8*control.GIB))
result=control.run_custom_monitored([sys.executable,'-B',str(ROOT/'src/PublicationManuscripts.py')]+args,folder,env,budget)
raise SystemExit(result.returncode)
