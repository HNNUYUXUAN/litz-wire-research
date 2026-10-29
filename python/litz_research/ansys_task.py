"""Own a native Maxwell MCP case through the shared asynchronous task contract."""
from pathlib import Path
import json,os,subprocess,time
from .common import read,write,tool,constrain

def execute(root,out,parameters):
    from .automation import probe,server_environment,candidate_server
    constrain();local=read(root/'litz.config.json') if (root/'litz.config.json').exists() else {}
    python=tool(root,'ansys_python') or local.get('mcp_servers',{}).get('ansys',{}).get('command')
    candidate=os.environ.get('LITZ_MCP_CLIENT_CONFIG')
    configured=candidate_server(candidate,'ansys') if candidate else None
    if configured:python=configured.get('command')
    if not python or not Path(python).is_file():raise ValueError('Configure the Ansys MCP Python executable before case maxwell-seven')
    session=out/'owned_session';session.mkdir()
    log=(out/'session_log.txt').open('w',encoding='utf-8')
    env=dict(os.environ,**(configured.get('env',{}) if configured else server_environment(root,'ansys')))
    owner=subprocess.Popen([python,str(root/'adapters/ansys/OwnedAEDTSession.py'),'--output',str(session),'--timeout','1200'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    cancel=root/'outputs/.jobs'/(out.name+'.cancel')
    try:
        deadline=time.monotonic()+60;receipt=None
        while time.monotonic()<deadline and owner.poll() is None:
            if cancel.exists():return {'run_id':out.name,'source_model':'Ansys_Maxwell2D_native_seven_strand_common_voltage','execution_status':'cancelled','physical_acceptance_status':'not_run','solver_started':False}
            if (session/'aedt_session.json').exists():
                try:receipt=read(session/'aedt_session.json');break
                except json.JSONDecodeError:pass
            time.sleep(.25)
        if not receipt:raise RuntimeError('Owned AEDT session produced no valid receipt')
        port=receipt['port']
        code='from ansys.aedt.core import settings;settings.release_on_exception=False;settings.pyedb_use_grpc=True;import sys;sys.path.insert(0,'+repr(str(root/'adapters/ansys'))+');from MCPMaxwellCase import execute;result=execute('+repr(str(root))+','+repr(str(out))+','+str(port)+','+repr(parameters)+');print(result["execution_status"])'
        calls=[{'name':'check_aedt_installed','arguments':{}},{'name':'connect_to_aedt','arguments':{'port':port,'version':'2025.2','non_graphical':True}},{'name':'run_python_code','arguments':{'code':code}},{'name':'get_model_info','arguments':{}}]
        write(out/'mcp_sequence.json',calls)
        protocol=probe(root,'ansys',out.name+'_mcp',out/'mcp_sequence.json',parent_run_id=out.name)
        result=read(out/'results.json') if (out/'results.json').exists() else {'run_id':out.name,'source_model':'Ansys_Maxwell2D_native_seven_strand_common_voltage','physical_acceptance_status':'not_run'}
        result['mcp_run_id']=out.name+'_mcp';result['protocol_status']=protocol.get('protocol_status')
        if protocol['execution_status']!='completed':
            result['execution_status']=protocol['execution_status']
            result.setdefault('physical_acceptance_status','not_verified')
            result['protocol_failure_reason']=protocol.get('failure_reason',protocol.get('error'))
        elif not result.get('execution_status'):result.update(execution_status='failed',failure_reason='no_native_result')
        return result
    finally:
        (session/'stop_session').touch()
        try:owner.wait(timeout=30)
        except subprocess.TimeoutExpired:
            import psutil
            from .processes import stop_owned,owned_tree
            if (session/'aedt_session.json').exists():
                receipt=read(session/'aedt_session.json');stop_owned(receipt['pid'],receipt['process_created'])
            process=psutil.Process(owner.pid)
            for child in reversed(owned_tree(process)):stop_owned(child.pid,child.create_time())
        log.close()
