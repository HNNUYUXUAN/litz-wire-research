"""Command-line access to models, archived evidence and scholarly builds."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from . import __version__
from .common import constrain, project, read, run_directory, tool, write

# Dispatchable stages and expert workflows share one discovery catalogue.
RUN_MODELS = {
    "analytic": ("Round-wire Bessel calibration (Python)", "analytic", "light", None),
    "wolfram-analytic": ("Round-wire Bessel calibration (Wolfram)", "analytic", "light", "analytic"),
    "fem2": ("Round-wire two-dimensional FEM calibration", "fem2", "field_solve", "fem2"),
    "coax": ("Common-terminal FEM calibration and scale campaign", "common-terminal", "large_field_campaign", "coax"),
    "coax640": ("640-strand FEM mesh and boundary campaign", "common-terminal", "large_field_campaign", "coax640"),
    "circuits": ("Common-terminal lumped circuit examples", "common-terminal", "light", "circuits"),
    "geometry": ("Centreline geometry and additive DTM examples", "geometry", "light", "geometry"),
    "copper": ("Equal-copper analytical and reduced predictions", "geometry", "light", "copper"),
    "peec": ("Finite-length longitudinal PEEC discretization", "peec", "field_solve", "peec"),
    "voxel": ("Dense voxel/face-flux PEEC examples", "rt0", "field_solve", "voxel"),
    "gpu": ("GPU arithmetic and synthetic solver prototypes", "gpu", "gpu_compute", "gpu"),
}


def model_catalog(root):
    """Expose implemented entry points separately from runtime acceptance."""
    rows = []
    for name, (title, dataset, workload, stage) in RUN_MODELS.items():
        files = ["configs/reference_parameters.json", "configs/reference_values.json"] if stage is None else [
            "src/RunNotebookStage.ps1", "src/RunNotebookStage.wls", "src/NotebookPhysics.wl", f"src/stages/{stage}.wl"]
        files += {
            "wolfram-analytic": ["src/Q1Analytical.wl", "tests/Q1Analytical.wlt", "configs/reference_parameters.json", "configs/reference_values.json"],
            "coax": ["src/CoaxFEM.wl"], "coax640": ["src/CoaxFEM.wl"],
            "peec": ["src/PEEC.wl"], "voxel": ["src/VoxelPEEC.wl"],
            "gpu": ["src/GPUCSRKernel.wl", "src/GPUFarKernel.wl"],
        }.get(name, [])
        rows.append(dict(id=name, title=title, interface="cli_run", workload=workload,
                         platform="Python 3.11+" if stage is None else "Windows / PowerShell / Wolfram",
                         command=f"litz-research run {name} --run-id {name.replace('-', '_')}_example_01",
                         inspect_command=f"litz-research run {name} --dry-run",
                         source_files=files, execution_datasets=[], evidence_datasets=[dataset],
                         output="outputs/<run-id>/results.json", scope=(
                             "Isolated round-wire internal impedance, SI and RMS." if name in {"analytic", "wolfram-analytic"} else
                             "See the stage's model assumptions and physical_acceptance_status; execution alone establishes no physical conclusion.")))
    rows.extend([
        dict(id="rt0", title="Matrix-free RT0 imposed-field campaign", interface="expert_script",
             workload="large_field_campaign", platform="Windows / PowerShell / Wolfram",
             command="powershell -NoProfile -File src/RunNotebookStage.ps1 -Stage closure_rt0 -RunId rt0_example_01",
             inspect_command='$env:LITZ_CLOSURE_PREFLIGHT_ONLY="1"; powershell -NoProfile -File src/RunNotebookStage.ps1 -Stage closure_rt0 -RunId rt0_preflight_01',
             source_files=["src/stages/closure_rt0.wl", "src/VoxelOperator.wl", "configs/prewrite_closure.json"],
             execution_datasets=[], evidence_datasets=["rt0"], output="outputs/<run-id>/closure_rt0_summary.json",
             scope="Fixed 1 x 1 x 2 mm cuboid, 1 mT RMS imposed field and zero net transport. Select a case and clear preflight mode before a solve; see docs/tool-workflows.md."),
        dict(id="aphi", title="Preserved three-dimensional A-phi field diagnostics", interface="expert_script",
             workload="field_postprocessing", platform="Windows / PowerShell / Wolfram",
             command="powershell -NoProfile -File src/RunNotebookStage.ps1 -Stage closure_fem3_diagnostics -RunId aphi_diagnostics_01",
             inspect_command="litz-research data verify aphi",
             source_files=["src/stages/closure_fem3_diagnostics.wl"], execution_datasets=["aphi"], evidence_datasets=["aphi"],
             required_data_files=["outputs/rerun_20261005_fem3_cylinder_report/results.wxf", "outputs/3d_20261005_fem3_mms_distinct/results.wxf"],
             output="outputs/<run-id>/diagnostic_summary.json",
             scope="Reads retained cylinder and manufactured-solution fields. The cylinder phi and gauge acceptance failures remain part of the result."),
        dict(id="ansys", title="Maxwell Q1 resource preflight and gated native/2D workflows", interface="expert_script",
             workload="resource_preflight", platform="Windows; PyAEDT/Maxwell for field solves",
             command="python src/RunClosureAnsys.py --task preflight --case q1 --budget low --run-id ansys_preflight_01",
             inspect_command="python src/RunClosureAnsys.py --help",
             source_files=["src/RunClosureAnsys.py", "src/ansys_native3d.py", "configs/native3d_q1_straight.json"],
             execution_datasets=[], evidence_datasets=["ansys", "research-records"], output="outputs/<run-id>/results.json",
             scope="The displayed command estimates the Q1 suite without starting AEDT. Two-dimensional tasks require archived handoff and interface records; see docs/tool-workflows.md."),
    ])
    rows.append(dict(id='wolfram',title='Wolfram environment tutorial',interface='cli_run',workload='light',platform='Wolfram kernel',command='litz-research run wolfram --case tutorial',inspect_command='litz-research run wolfram --case tutorial --dry-run',source_files=['adapters/wolfram/RunResearchCase.wls'],execution_datasets=[],evidence_datasets=['analytic'],output='outputs/<run-id>/results.json',scope='Actual kernel version and arithmetic. MCP protocol and Notebook operations are verified separately.'))
    for row in rows:
        from .tasks import DEFAULTS,ROUTES
        migration_path=root/'provenance/source_migration.json'
        mapping=read(migration_path)['mapping'] if migration_path.exists() else {}
        row['source_files']=[mapping.get(path,path) for path in row['source_files']]
        row['legacy_command']=row['command']
        row['legacy_scope']=row['scope']
        row['scope']={'rt0':'Small vector face-flux cuboid tutorial; imposed field or transport. Full matrix-free campaigns use legacy_command.', 'aphi':'Recompute derivatives and failed phi/gauge checks on three preserved cylinder fields; sampling changes do not solve new fields.', 'ansys':'Resource preflight only. Execute automation/examples/ansys-native for the actual MCP Maxwell case.'}.get(row['id'],row['scope'])
        row['cases']=['tutorial','diagnostic'] if row['id']=='aphi' else ['tutorial','preflight'] if row['id']=='ansys' else ['tutorial','frequency-sweep'] if row['id']=='analytic' else ['tutorial']
        row['supported_parameters']=DEFAULTS[row['id']]
        row['route']=ROUTES[row['id']]
        row['command']=f"litz-research run {row['id']} --case {row['cases'][-1] if row['id'] in {'aphi','ansys'} else 'tutorial'} --run-id {row['id'].replace('-','_')}_example_01"
        row['inspect_command']=row['command']+' --dry-run'
        row['interface']='cli_run'
        row["source_available"] = all((root / path).is_file() for path in row["source_files"])
        row["fetch_evidence_commands"] = [f"litz-research data fetch {name}" for name in row["evidence_datasets"]]
        row["fetch_execution_commands"] = [f"litz-research data fetch {name}" for name in row["execution_datasets"]]
    return rows


def run_plan(root, name, run_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]+",run_id):
        raise ValueError("Run IDs use letters, digits, underscores and hyphens.")
    row = next(item for item in model_catalog(root) if item["id"] == name)
    reasons = [f"Missing source: {path}" for path in row["source_files"] if not (root / path).is_file()]
    if RUN_MODELS[name][3] is not None:
        if os.name != "nt":
            reasons.append("This stage uses the Windows PowerShell process supervisor.")
        if not tool(root, "powershell"):
            reasons.append("PowerShell executable required: set LITZ_POWERSHELL or tools.powershell.")
        if not tool(root, "wolframscript"):
            reasons.append("Wolfram executable required: set LITZ_WOLFRAMSCRIPT or tools.wolframscript.")
    if (root / "outputs" / run_id).exists():
        reasons.append(f"Run directory already exists: outputs/{run_id}; choose a new --run-id.")
    return dict(row, run_id=run_id, execution_status="plan_only", dispatch_status="ready" if not reasons else "blocked",
                diagnostics=reasons, runtime_acceptance="Use doctor for runtime probes; a ready dispatch plan verifies files and launchers.")


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version",action="version",version=__version__)
    p.add_argument("--project",help="Research checkout directory (or LITZ_PROJECT)")
    sub=p.add_subparsers(dest="command",required=True)
    d=sub.add_parser("doctor",help="Probe executable versions, Python imports, GPU driver, fonts, and resources")
    d.add_argument("--kernel",action="store_true",help="Also start the local Wolfram kernel for a bounded arithmetic/version probe")
    m=sub.add_parser("models",help="List model entry points, workloads, datasets, and support scope")
    m.add_argument("model",nargs="?",choices=[*RUN_MODELS,"rt0","aphi","ansys","wolfram"])
    m.add_argument("--json",action="store_true",help="Emit machine-readable model records")
    data=sub.add_parser("data",help="Select and verify release datasets").add_subparsers(dest="action",required=True)
    data.add_parser("list")
    for action in ["fetch","verify"]:
        d=data.add_parser(action);d.add_argument("dataset",nargs="?" if action=="verify" else None)
        if action=="fetch":
            d.add_argument("--cache",default=os.getenv("LITZ_CACHE",str(Path.home()/".cache/litz-research")))
            d.add_argument("--offline",action="store_true")
    r=sub.add_parser("run",help="Run a model into a distinct output directory")
    r.add_argument("model",choices=[*RUN_MODELS,'rt0','aphi','ansys','wolfram'])
    r.add_argument("--run-id",default=None)
    r.add_argument("--dry-run",action="store_true",help="Show source inputs, dependencies, workload, and launch conditions")
    r.add_argument("--case",choices=['tutorial','diagnostic','frequency-sweep','preflight'])
    r.add_argument("--parameters",help="JSON file containing explicitly supported model parameters")
    jobs=sub.add_parser('jobs',help='Submit, inspect, cancel or continue a bounded local task').add_subparsers(dest='action',required=True)
    js=jobs.add_parser('submit');js.add_argument('model');js.add_argument('--run-id',required=True);js.add_argument('--case',default='tutorial');js.add_argument('--parameters')
    for action in ['status','cancel','resume']:
        q=jobs.add_parser(action);q.add_argument('run_id')
        if action=='resume':q.add_argument('--new-run-id',required=True)
    w=jobs.add_parser('worker');w.add_argument('ticket')
    auto=sub.add_parser('automation',help='Configure and verify the MCP research chain').add_subparsers(dest='action',required=True)
    auto.add_parser('doctor')
    q=auto.add_parser('configure');q.add_argument('--output',required=True);q.add_argument('--ansys-python');q.add_argument('--transport',choices=['stdio','http'],default='stdio')
    q=auto.add_parser('probe');q.add_argument('server',choices=['wolfram','ansys']);q.add_argument('--run-id',required=True);q.add_argument('--sequence')
    q=auto.add_parser('examples');q.add_argument('name',nargs='?')
    refs=sub.add_parser('references',help='Build or verify the unified source and citation index');refs.add_argument('action',choices=['build','verify'])
    b=sub.add_parser("build",help="Build the bilingual academic editions")
    b.add_argument("--run-id",required=True)
    for name,choices in {"edition":["report","paper","all"],"language":["zh-CN","en","all"],"form":["merged","chapters","all"],"layout":["single","ieee","all"],"stage":["preflight","panels","compose","documents","notebooks","pdf","verify","package","all"]}.items():
        b.add_argument("--"+name,choices=choices,default="all")
    b.add_argument("--source-manifest",default="manuscript/publication.json")
    v=sub.add_parser("verify",help="Check release data and manuscript input identities")
    v.add_argument("--run-id")
    return p

def _probe(command, timeout=15):
    """A bounded subprocess probe with an explicit observation scope."""
    try:
        probe=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
        return {"status":"passed" if probe.returncode == 0 else "failed", "exit_code":probe.returncode,
                "version_lines":probe.stdout.splitlines()[:8],"diagnostic_lines":probe.stderr.splitlines()[-4:]}
    except subprocess.TimeoutExpired:
        return {"status":"timeout","timeout_seconds":timeout}
    except OSError as error:
        return {"status":"unavailable","diagnostic":str(error)}


def _aedt_executable(root):
    configured=tool(root,"ansysedt")
    if configured:
        return configured
    for key,value in sorted(os.environ.items(),reverse=True):
        if key.startswith(("ANSYSEM_ROOT","ANSYSEMSV_ROOT")):
            for name in ("ansysedt.exe","ansysedtsv.exe","Win64/ansysedt.exe","Win64/ansysedtsv.exe"):
                candidate=Path(value)/name
                if candidate.is_file():
                    return str(candidate)
    return None


def doctor(root, kernel=False):
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
            flag="-version" if name in ["wolframscript","latexmk"] else "--version"
            versions[name]=_probe([executable,flag])
        else:
            versions[name]={"status":"missing","diagnostic":f"Set LITZ_{name.upper()} or tools.{name} in litz.config.json."}
    report["versions"]=versions
    imports={}
    for name,module in (("mpmath","mpmath"),("pyaedt","ansys.aedt.core")):
        imports[name]=_probe([sys.executable,"-c", "import importlib,sys; m=importlib.import_module(sys.argv[1]); print(getattr(m,'__version__','import passed'))",module])
        imports[name]["scope"]="Module import in the active Python environment; Desktop and field solvers are not started."
    imports["mpmath"]["setup_command"]="python -m pip install -e ."
    imports["pyaedt"]["setup_command"]='python -m pip install -e ".[ansys]"'
    report["python_imports"]=imports
    driver=tool(root,"nvidia-smi")
    report["gpu_driver"]=_probe([driver,"--query-gpu=name,driver_version,memory.total,memory.free","--format=csv,noheader,nounits"]) if driver else {"status":"missing","diagnostic":"nvidia-smi is unavailable; CPU analytical and reading workflows remain usable."}
    report["gpu_driver"]["scope"]="Driver/device query. Wolfram CUDALink compilation and numerical agreement require the GPU route."
    aedt=_aedt_executable(root)
    report["ansys_installation"]={"status":"located" if aedt else "not_located","executable":aedt,
        "license_status":"not_probed","scope":"Executable discovery through LITZ_ANSYSEDT, tools.ansysedt, PATH, and Ansys environment roots."}
    if kernel and found["wolframscript"]:
        code='ExportString[<|"version"->$Version,"system_id"->$SystemID,"arithmetic_passed"->TrueQ[1+1==2]|>,"RawJSON"]'
        report["wolfram_kernel"]=_probe([tool(root,"wolframscript"),"-local","-timeout","10","-code",code],timeout=30)
    else:
        report["wolfram_kernel"]={"status":"not_probed" if found["wolframscript"] else "missing",
                                  "command":"litz-research doctor --kernel"}
    report["wolfram_kernel"]["scope"]="Local kernel start, arithmetic and version only; frontend rendering and FEM remain separately verified."
    report["capabilities"]={
        "python_analytic":{"status":"ready" if imports["mpmath"]["status"]=="passed" else "blocked", "command":"litz-research run analytic --run-id analytic_example_01"},
        "wolfram_stages":{"status":"kernel_probed" if report["wolfram_kernel"]["status"]=="passed" else "kernel_probe_required", "command":"litz-research models wolfram-analytic"},
        "pdf_compilation":{"status":"executables_probed" if all(versions[name]["status"]=="passed" for name in ("xelatex","bibtex","latexmk")) else "dependencies_required", "scope":"A representative document compile also verifies TeX packages and fonts."},
        "ansys":{"status":"installation_and_python_import_probed" if aedt and imports["pyaedt"]["status"]=="passed" else "dependencies_required", "command":"litz-research models ansys", "scope":"Licensing, interface calls and physical acceptance belong to separate runs."},
        "gpu":{"status":"driver_probed" if report["gpu_driver"]["status"]=="passed" else "driver_required", "command":"litz-research models gpu", "scope":"Device discovery precedes Wolfram runtime and model validation."},
    }
    report["font_probe_scope"]="Font-file presence on Windows. Exported font embedding and visual rendering are document acceptance checks."
    report["inspection_status"]="completed"
    if os.name=="nt":
        import ctypes
        class Memory(ctypes.Structure):
            _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ["total","available","page_total","page_available","virtual_total","virtual_available","extended"]]
        memory=Memory();memory.length=ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            report["actual_resources"]={"logical_processors":os.cpu_count(),"total_RAM_bytes":memory.total,"free_RAM_bytes":memory.available,"system_reserve_satisfied":memory.available>=8*2**30}
    return report

def main(argv=None):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,"reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p=parser();a=p.parse_args(argv)
    try:
        root=project(a.project);constrain()
        from . import data
        if a.command=='references':
            from .references import build,verify
            result=build(root) if a.action=='build' else verify(root)
            print(json.dumps(result,ensure_ascii=False,indent=2));return int(result.get('failed_checks',0)>0)
        if a.command=='automation':
            from . import automation
            result=automation.dispatch(root,a)
            print(json.dumps(result,ensure_ascii=False,indent=2));return int(result.get('execution_status') in {'failed','blocked'})
        if a.command=='jobs':
            from . import tasks
            if a.action=='submit':result=tasks.submit(root,a.model,a.run_id,a.case,read(a.parameters) if a.parameters else None)
            elif a.action=='status':result=tasks.status(root,a.run_id)
            elif a.action=='cancel':
                tasks.status(root,a.run_id)
                (root/'outputs/.jobs').mkdir(parents=True,exist_ok=True)
                (root/'outputs/.jobs'/(a.run_id+'.cancel')).touch()
                result={'run_id':a.run_id,'execution_status':'cancellation_requested'}
            elif a.action=='resume':
                result=tasks.resume(root,a.run_id,a.new_run_id)
            else:
                request=read(a.ticket);result=tasks.execute(root,request['model'],request['run_id'],request['case'],request['parameters'])
            print(json.dumps(result,ensure_ascii=False,indent=2));return int(result.get('execution_status') in {'failed','blocked'})
        if a.command=='run' and (a.case or a.parameters or a.model not in RUN_MODELS or a.model=='analytic'):
            from . import tasks
            run_id=a.run_id or datetime.now(timezone.utc).strftime(a.model.replace('-','_')+'_%Y%m%dT%H%M%SZ')
            supplied=read(a.parameters) if a.parameters else None
            result=tasks.plan(root,a.model,run_id,a.case or 'tutorial',supplied) if a.dry_run else tasks.execute(root,a.model,run_id,a.case or 'tutorial',supplied)
            print(json.dumps(result,ensure_ascii=False,indent=2));return int(result.get('dispatch_status')=='blocked' or result.get('execution_status') in {'failed','blocked'} or result.get('actual_exit_code',0) not in (0,None))
        if a.command=="doctor":result=doctor(root,a.kernel)
        elif a.command=="models":
            result=model_catalog(root)
            if a.model:result=next(row for row in result if row["id"]==a.model)
            if not a.json:
                if a.model:
                    print(f"{result['id']}: {result['title']}\nInterface: {result['interface']}\nPlatform: {result['platform']}\nWorkload: {result['workload']}\n\nInspect: {result['inspect_command']}\nEntry: {result['command']}\nOutput: {result['output']}\n\n{result['scope']}")
                    for key in ("fetch_execution_commands","fetch_evidence_commands"):
                        print("\n"+key.replace("_"," ")+":")
                        print("\n".join(result[key]) or "Source checkout supplies the inputs.")
                    print("\nWorkflow details: docs/tool-workflows.md")
                else:
                    for row in result:print(f"{row['id']:18} {row['interface']:14} {row['workload']:22} {row['title']}")
                    print("\nUse litz-research models <id> for commands, datasets and scientific scope.")
                return 0
        elif a.command=="data":
            if a.action=="list":result=[dict(id=k,description=v.get("description"),files=len(v["files"]),bytes=sum(x["bytes"] for x in v["objects"])) for k,v in data.catalog(root)["datasets"].items()]
            elif a.action=="fetch":result=data.fetch(root,a.dataset,Path(a.cache).resolve(),a.offline)
            else:result=data.verify(root,a.dataset)
        elif a.command=="run":
            run_id=a.run_id or datetime.now(timezone.utc).strftime(a.model.replace('-','_')+"_%Y%m%dT%H%M%SZ")
            plan=run_plan(root,a.model,run_id)
            if a.dry_run:
                print(json.dumps(plan,ensure_ascii=False,indent=2));return int(plan["dispatch_status"]!="ready")
            if plan["diagnostics"]:raise ValueError(" ".join(plan["diagnostics"]))
            if a.model=="analytic":
                from .analytical import execute
                result=execute(root,run_directory(root,run_id))
            else:
                wolfram=tool(root,"wolframscript")
                if not wolfram:raise ValueError("This model requires wolframscript. Set LITZ_WOLFRAMSCRIPT or tools.wolframscript in litz.config.json; use run analytic for the Python calibration.")
                if os.name!="nt":raise ValueError("The retained solver process supervisor requires Windows; run analytic is portable.")
                stage=RUN_MODELS[a.model][3]
                env=dict(os.environ,LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES=str(8*2**30),LITZ_CLOSURE_MAX_WORKING_BYTES=str(24*2**30),LITZ_WOLFRAMSCRIPT=wolfram)
                return subprocess.run([tool(root,"powershell"),"-NoProfile","-File",str(root/"src/RunNotebookStage.ps1"),"-Stage",stage,"-RunId",run_id],cwd=root,env=env).returncode
        elif a.command=="build":
            from .common import resolve_read_path
            resolve_read_path(root,"data/publication/panel_manifest.json")
            args=[sys.executable,str(root/"src/RunPublicationBuild.py")]
            for k in ["run_id","edition","language","form","layout","stage","source_manifest"]:args.extend(["--"+k.replace('_','-'),getattr(a,k)])
            return subprocess.run(args,cwd=root).returncode
        elif a.command=="verify":
            from .common import sha
            m=read(root/"manuscript/publication.json")
            from .common import resolve_read_path
            result={"scientific_inputs":[dict(path=f,passed=sha(resolve_read_path(root,f))==h) for f,h in m["scientific_hashes"].items()],"datasets":data.verify(root)}
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
