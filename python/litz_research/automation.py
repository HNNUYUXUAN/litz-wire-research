"""Portable setup and protocol checks for the two upstream MCP servers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import re
import tomllib
from .common import read, write, tool, run_directory,native_path

def server_environment(root,server):
    """Make native launch settings explicit, including GUI-client-safe encoding."""
    local=read(root/'litz.config.json') if (root/'litz.config.json').exists() else {}
    configured=local.get('mcp_servers',{}).get(server,{}).get('env',{})
    env={key:os.environ[key] for key in ('APPDATA','LOCALAPPDATA') if os.environ.get(key)}
    if server=='ansys':
        env.update(LITZ_AEDT_EDITION='student',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
        for key,value in os.environ.items():
            if re.fullmatch(r'ANSYSEM(?:SV)?_ROOT\d{3}',key):
                names=('ansysedtsv.exe','ansysedt.exe','ansysedt','Win64/ansysedt.exe','Win64/ansysedtsv.exe')
                if any((Path(value)/name).is_file() for name in names):env[key]=value
    else:
        for key in ('APPDATA','WOLFRAM_BASE','WOLFRAM_LOCALBASE','WOLFRAM_USERBASE'):
            if os.environ.get(key):env[key]=os.environ[key]
        env['MCP_SERVER_NAME']='WolframLanguage'
    env.update(configured)
    env['LITZ_PROJECT']=str(root)
    return env

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
    ap=ansys_python or tool(root,'ansys_python') or str(root/'.conda/ansys/python.exe')
    if not Path(ap).is_absolute():ap=str((root/ap).resolve())
    if transport=='stdio' and not Path(ap).is_file():diagnostics.append('Select the installed Ansys MCP Python executable with --ansys-python.')
    servers={
        'wolfram':{'command':ws,'args':['-run','PacletSymbol["Wolfram/AgentTools","Wolfram`AgentTools`StartMCPServer"]["WolframLanguage"]','-noinit','-noprompt'],'env':server_environment(root,'wolfram'),'cwd':str(root)},
        'ansys':{'command':ap,'args':[str(root/'adapters/ansys/StartMCP.py'),'--transport','stdio'],'env':server_environment(root,'ansys'),'cwd':str(root)},
    }
    for server in servers.values():server['env']['LITZ_PYTHON']=sys.executable
    if transport=='stdio' and not any(re.fullmatch(r'ANSYSEM(?:SV)?_ROOT\d{3}',k) for k in servers['ansys']['env']):
        diagnostics.append('Configure a verified ANSYSEM_ROOTxxx or ANSYSEMSV_ROOTxxx in the Ansys server environment; desktop clients may not inherit it.')
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

def probe_environment(root,clean=False):
    if clean:
        keep={'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC','PATHEXT','USERPROFILE',
              'HOMEDRIVE','HOMEPATH','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA','ALLUSERSPROFILE'}
        env={k:v for k,v in os.environ.items() if k.upper() in keep}
    else:env=dict(os.environ)
    env['LITZ_PROJECT']=str(root)
    return env

def candidate_server(path, name):
    """Read an explicit candidate without falling back to the live configuration."""
    path=Path(path)
    text=path.read_text(encoding='utf-8-sig')
    data=tomllib.loads(text) if path.suffix.lower()=='.toml' else json.loads(text)
    if not isinstance(data,dict):raise ValueError('Client configuration must be an object.')
    servers=data.get('mcp_servers',data.get('mcpServers',{}))
    if not isinstance(servers,dict):raise ValueError('MCP servers must be an object.')
    matches=[value for key,value in servers.items() if key.lower()==name.lower()]
    if len(matches)!=1 or not isinstance(matches[0],dict):
        raise ValueError('Candidate must contain exactly one '+name+' server.')
    server=matches[0]
    if server.get('enabled') is False:raise ValueError('Candidate server is disabled.')
    if not (server.get('command') or server.get('url')):raise ValueError('Candidate server requires command or url.')
    return server

def probe(root,server,run_id,sequence=None,parent_run_id=None,clean_environment=False,client_config=None):
    client_config=client_config or os.environ.get('LITZ_MCP_CLIENT_CONFIG')
    configured=candidate_server(client_config,server) if client_config else None
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
    if client_config is None:configured=local.get('mcp_servers',{}).get(server)
    if configured is None:
        configure(root,out/'configuration',tool(root,'ansys_python'))
        configured=read(out/'configuration/mcp.json')['mcpServers'][server]
    if sequence:
        calls=read(sequence)
    else:
        calls=[{'name':'WolframLanguageContext','arguments':{'context':'Minimal local Wolfram MCP readiness check: arithmetic and installed AgentTools version, with no solver or file changes.'}},
               {'name':'WolframLanguageEvaluator','arguments':{'code':'<|"arithmetic_passed" -> TrueQ[2+2==4], "version" -> $Version, "agenttools_version" -> PacletObject["Wolfram/AgentTools"]["Version"]|>'}}] if server=='wolfram' else [{'name':'check_aedt_installed','arguments':{}}]
    write(out/'mcp_request.json',{'server':configured,'calls':calls,'upstreams':read(root/'automation/mcp/upstreams.lock.json'),'client_environment_policy':'system_basics_only' if clean_environment else 'inherited'})
    write(out/'run_manifest.json',{'run_id':run_id,'source_snapshot_timing':'before_mcp_initialization','sources':sources,'request_sha256':sha(out/'mcp_request.json'),
          'candidate_config_sha256':sha(Path(client_config)) if client_config else None})
    env=probe_environment(root,clean_environment)
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
    if args.action=='readiness':
        from .readiness import check
        return check(root,args.run_id,args.client_config,args.verify_data)
    if args.action=='configure':return configure(root,args.output,args.ansys_python,args.transport)
    if args.action=='doctor':return doctor(root)
    if args.action=='probe':return probe(root,args.server,args.run_id,args.sequence,clean_environment=args.clean_environment,client_config=args.client_config)
    files=sorted((root/'automation/examples').glob('*/task.json'))
    examples=[read(p) for p in files]
    return {'execution_status':'completed','examples':[x for x in examples if not args.name or x['id']==args.name]}
