"""Command-line access to models, archived evidence and scholarly builds."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from . import __version__
from .common import constrain, project, read, run_directory, tool

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version",action="version",version=__version__)
    p.add_argument("--project",help="Research checkout directory (or LITZ_PROJECT)")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor",help="Inspect interpreters, solvers, fonts, and resource conditions")
    data=sub.add_parser("data",help="Select and verify release datasets").add_subparsers(dest="action",required=True)
    data.add_parser("list")
    for action in ["fetch","verify"]:
        d=data.add_parser(action);d.add_argument("dataset",nargs="?" if action=="verify" else None)
        if action=="fetch":
            d.add_argument("--cache",default=os.getenv("LITZ_CACHE",str(Path.home()/".cache/litz-research")))
            d.add_argument("--offline",action="store_true")
    r=sub.add_parser("run",help="Run a model into a distinct output directory")
    r.add_argument("model",choices=["analytic","wolfram-analytic","fem2","coax","coax640","circuits","geometry","copper","peec","voxel","gpu"])
    r.add_argument("--run-id",default=None)
    b=sub.add_parser("build",help="Build the bilingual academic editions")
    b.add_argument("--run-id",required=True)
    for name,choices in {"edition":["report","paper","all"],"language":["zh-CN","en","all"],"form":["merged","chapters","all"],"layout":["single","ieee","all"],"stage":["preflight","panels","compose","documents","notebooks","pdf","verify","package","all"]}.items():
        b.add_argument("--"+name,choices=choices,default="all")
    b.add_argument("--source-manifest",default="manuscript/publication.json")
    v=sub.add_parser("verify",help="Check release data and manuscript input identities")
    v.add_argument("--run-id")
    return p

def doctor(root):
    found={name:bool(tool(root,name)) for name in ["wolframscript","xelatex","bibtex","latexmk","gh"]}
    fonts=Path(os.environ.get("WINDIR","/nonexistent"))/"Fonts"
    report=dict(version=__version__,python=platform.python_version(),system=platform.system(),tools=found,
                fonts={"SimSun":(fonts/"simsun.ttc").is_file(),"Times New Roman":(fonts/"times.ttf").is_file()},
                resource_policy=dict(logical_processors=8,task_memory_GiB=24,system_reserve_GiB=8),
                solver_requirements={"wolfram":"Licensed Wolfram kernel; frontend for Notebook rendering", "ansys":"Licensed Maxwell/PyAEDT; Student mesh and core limits apply", "gpu":"CUDA-compatible Wolfram CUDALink environment"})
    versions={}
    for name in ["wolframscript","xelatex","bibtex","latexmk","gh"]:
        executable=tool(root,name)
        if executable:
            try:
                flag="-version" if name in ["wolframscript","latexmk"] else "--version"
                probe=subprocess.run([executable,flag],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=15)
                versions[name]={"exit_code":probe.returncode,"version_lines":(probe.stdout+probe.stderr).splitlines()[:3]}
            except subprocess.TimeoutExpired:versions[name]={"status":"version_probe_timeout"}
    report["versions"]=versions
    if os.name=="nt":
        import ctypes
        class Memory(ctypes.Structure):
            _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ["total","available","page_total","page_available","virtual_total","virtual_available","extended"]]
        memory=Memory();memory.length=ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            report["actual_resources"]={"logical_processors":os.cpu_count(),"total_RAM_bytes":memory.total,"free_RAM_bytes":memory.available,"system_reserve_satisfied":memory.available>=8*2**30}
    return report

def main(argv=None):
    p=parser();a=p.parse_args(argv)
    try:
        root=project(a.project);constrain()
        from . import data
        if a.command=="doctor":result=doctor(root)
        elif a.command=="data":
            if a.action=="list":result=[dict(id=k,description=v.get("description"),files=len(v["files"]),bytes=sum(x["bytes"] for x in v["objects"])) for k,v in data.catalog(root)["datasets"].items()]
            elif a.action=="fetch":result=data.fetch(root,a.dataset,Path(a.cache).resolve(),a.offline)
            else:result=data.verify(root,a.dataset)
        elif a.command=="run":
            run_id=a.run_id or datetime.now(timezone.utc).strftime(a.model.replace('-','_')+"_%Y%m%dT%H%M%SZ")
            if a.model=="analytic":
                from .analytical import execute
                result=execute(root,run_directory(root,run_id))
            else:
                wolfram=tool(root,"wolframscript")
                if not wolfram:raise ValueError("This model requires wolframscript. Set LITZ_WOLFRAMSCRIPT or tools.wolframscript in litz.config.json; use run analytic for the Python calibration.")
                if os.name!="nt":raise ValueError("The retained solver process supervisor requires Windows; run analytic is portable.")
                stage="analytic" if a.model=="wolfram-analytic" else a.model
                env=dict(os.environ,LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES=str(8*2**30),LITZ_CLOSURE_MAX_WORKING_BYTES=str(24*2**30),LITZ_WOLFRAMSCRIPT=wolfram)
                return subprocess.run(["powershell","-NoProfile","-File",str(root/"src/RunNotebookStage.ps1"),"-Stage",stage,"-RunId",run_id],cwd=root,env=env).returncode
        elif a.command=="build":
            required=root/"data/publication/panel_manifest.json"
            if not required.is_file():raise ValueError("Publication assets required: litz-research data fetch publication-inputs")
            args=[sys.executable,str(root/"src/RunPublicationBuild.py")]
            for k in ["run_id","edition","language","form","layout","stage","source_manifest"]:args.extend(["--"+k.replace('_','-'),getattr(a,k)])
            return subprocess.run(args,cwd=root).returncode
        elif a.command=="verify":
            from .common import sha
            m=read(root/"manuscript/publication.json")
            result={"scientific_inputs":[dict(path=f,passed=(root/f).is_file() and sha(root/f)==h) for f,h in m["scientific_hashes"].items()],"datasets":data.verify(root)}
            if a.run_id:
                return subprocess.run([sys.executable,str(root/"src/RunPublicationBuild.py"),"--run-id",a.run_id,"--stage","verify"],cwd=root).returncode
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if a.command=="data" and a.action in ["verify","fetch"]:return int(any(x["status"]!="passed" for x in result))
        if a.command=="verify":return int(any(not x["passed"] for x in result["scientific_inputs"]) or any(x["status"]!="passed" for x in result["datasets"]))
        if a.command=="run":return int(result["physical_acceptance_status"]!="passed")
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError,ImportError) as e:
        print(f"litz-research: {e}",file=sys.stderr);return 1

if __name__=="__main__":raise SystemExit(main())
