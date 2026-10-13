"""Portable setup and protocol checks for the two upstream MCP servers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
from .common import read, write, tool, run_directory,native_path

def configure(root,output,ansys_python=None,transport='stdio'):
    ws=tool(root,'wolfram_kernel') or shutil.which('wolfram')
    if not ws and tool(root,'wolframscript'):
        try:
            discovered=subprocess.run([tool(root,'wolframscript'),'-local','-code','$InstallationDirectory'],capture_output=True,text=True,encoding='utf-8',timeout=30)
            installation=Path(discovered.stdout.strip().strip('"'))
            candidates=[installation/'wolfram.exe',installation/'WolframKernel.exe',installation/'Executables/WolframKernel',installation/'MacOS/WolframKernel']
            ws=next((str(p) for p in candidates if p.is_file()),None)
        except (OSError,subprocess.TimeoutExpired):pass
    diagnostics=[]
    if not ws:diagnostics.append('Set LITZ_WOLFRAM_KERNEL to the licensed kernel executable.')
    ws=ws or 'wolfram'
    ap=ansys_python or tool(root,'ansys_python') or str(root/'.venv/ansys/Scripts/python.exe')
    if not Path(ap).is_absolute():ap=str((root/ap).resolve())
    if transport=='stdio' and not Path(ap).is_file():diagnostics.append('Select the installed Ansys MCP Python executable with --ansys-python.')
    servers={
        'wolfram':{'command':ws,'args':['-run','PacletSymbol["Wolfram/AgentTools","Wolfram`AgentTools`StartMCPServer"]["WolframLanguage"]','-noinit','-noprompt'],'cwd':str(root)},
        'ansys':{'command':ap,'args':[str(root/'adapters/ansys/StartMCP.py'),'--transport','stdio'],'env':{'LITZ_AEDT_EDITION':'student'},'cwd':str(root)},
    }
    if transport=='http':servers['ansys']={'url':'http://127.0.0.1:8080/mcp'}
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    write(output/'mcp.json',{'mcpServers':servers})
    lines=[]
    for name,server in servers.items():
        lines.append('[mcp_servers.'+name+']')
        for k,v in server.items():
            encoded='{'+', '.join(json.dumps(a)+' = '+json.dumps(b,ensure_ascii=False) for a,b in v.items())+'}' if isinstance(v,dict) else json.dumps(v,ensure_ascii=False)
            lines.append(k+' = '+encoded)
        lines+=['startup_timeout_sec = 120','tool_timeout_sec = 120','']
    (output/'config.toml').write_text('\n'.join(lines),encoding='utf-8')
    return {'execution_status':'completed','configuration_directory':str(output),'servers':list(servers),'configuration_status':'local_paths_located' if not diagnostics else 'local_paths_required','diagnostics':diagnostics,'scope':'Generated inspectable project configuration; live connection and scientific acceptance require the separate probes.'}

def doctor(root):
    local=read(root/'litz.config.json') if (root/'litz.config.json').exists() else {}
    ap=tool(root,'ansys_python');ws=tool(root,'wolframscript')
    return {'execution_status':'completed','upstreams':read(root/'automation/mcp/upstreams.lock.json'),'servers':{'wolfram':{'launcher_found':bool(ws),'protocol_status':'not_probed'},'ansys':{'launcher_found':bool(ap),'protocol_status':'not_probed'}},'commands':['litz-research automation probe wolfram --run-id wolfram_mcp_01','litz-research automation probe ansys --run-id ansys_mcp_01'],'harnesses':{'codex':'see automation/harnesses/codex','generic_mcp':'see automation/harnesses/generic'}}

def probe(root,server,run_id,sequence=None,parent_run_id=None):
    out=run_directory(root,run_id)
    import psutil
    write(out/'process_status.json',{'run_id':run_id,'source_model':'MCP_'+server,'execution_status':'running','pid':os.getpid(),'process_created':psutil.Process().create_time()})
    import shutil
    from .tasks import source_manifest
    from .common import sha
    sources=source_manifest(root)
    for relative in sources:
        target=native_path(out/'source_snapshot'/relative);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/relative,target)
    local=read(root/'litz.config.json') if (root/'litz.config.json').exists() else {}
    configured=local.get('mcp_servers',{}).get(server)
    if configured is None:
        configure(root,out/'configuration',tool(root,'ansys_python'))
        configured=read(out/'configuration/mcp.json')['mcpServers'][server]
    if sequence:
        calls=read(sequence)
    else:
        calls=[{'name':'WolframLanguageEvaluator','arguments':{'code':'2+2'}}] if server=='wolfram' else [{'name':'check_aedt_installed','arguments':{}}]
    write(out/'mcp_request.json',{'server':configured,'calls':calls,'upstreams':read(root/'automation/mcp/upstreams.lock.json')})
    write(out/'run_manifest.json',{'run_id':run_id,'source_snapshot_timing':'before_mcp_initialization','sources':sources,'request_sha256':sha(out/'mcp_request.json')})
    env=dict(os.environ,LITZ_PROJECT=str(root))
    if parent_run_id:env['LITZ_PARENT_RUN_ID']=parent_run_id
    from .tasks import bounded_process
    result=bounded_process([sys.executable,str(root/'automation/mcp/client.py'),'--request',str(out/'mcp_request.json'),'--output',str(out)],root,out,env,{'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':1800,'completion_file':str(out/'mcp_completion.json')})
    if (out/'protocol_report.json').exists():result.update(read(out/'protocol_report.json'))
    elif (out/'mcp_completion.json').exists():
        result.update(read(out/'mcp_completion.json'));write(out/'protocol_report.json',read(out/'mcp_completion.json'))
    write(out/'results.json',result)
    write(out/'process_status.json',{k:result.get(k) for k in ['execution_status','actual_exit_code','failure_reason']})
    return {k:v for k,v in result.items() if k!='events'}|{'run_id':run_id,'event_log':'outputs/'+run_id+'/mcp_events.jsonl'}

def dispatch(root,args):
    if args.action=='configure':return configure(root,args.output,args.ansys_python,args.transport)
    if args.action=='doctor':return doctor(root)
    if args.action=='probe':return probe(root,args.server,args.run_id,args.sequence)
    files=sorted((root/'automation/examples').glob('*/task.json'))
    examples=[read(p) for p in files]
    return {'execution_status':'completed','examples':[x for x in examples if not args.name or x['id']==args.name]}
