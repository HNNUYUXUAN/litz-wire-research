"""Fail-closed, repeatable preparation checks; no licensed solver is started."""
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import unquote,urlparse

from . import __version__
from .common import read, run_directory, sha, tool, write


def normalized(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def lock_mismatches(versions, lock_text, required=()):
    installed={normalized(k):v for k,v in versions.items()}
    pinned={normalized(k.strip()):v.strip() for line in lock_text.splitlines()
            if '==' in line and not line.startswith('#') for k,v in [line.split('==',1)]}
    errors=[f'{name}: installed {version}, locked {pinned[name]}'
            for name,version in installed.items() if name in pinned and pinned[name]!=version]
    errors += [f'{name}: not installed' for name in required if normalized(name) not in installed]
    return errors


def inspect_runtime(python, modules, lock, required):
    code=('import importlib,importlib.metadata as m,json,sys; '
          '[importlib.import_module(n) for n in sys.argv[1:]]; '
          'print(json.dumps({"versions":{d.metadata["Name"]:d.version for d in m.distributions()},'
          '"direct_urls":{d.metadata["Name"]:json.loads(d.read_text("direct_url.json")) for d in m.distributions() '
          'if d.metadata["Name"].lower()=="ansys-aedt-mcp" and d.read_text("direct_url.json")},'
          '"python":sys.version,"executable":sys.executable}))')
    try:
        probe=subprocess.run([python,'-X','utf8','-c',code,*modules],capture_output=True,
                             text=True,encoding='utf-8',errors='replace',timeout=45)
        if probe.returncode:
            return {'status':'failed','error':probe.stderr[-3000:],'exit_code':probe.returncode}
        result=json.loads(probe.stdout.splitlines()[-1])
        result['lock_mismatches']=lock_mismatches(result['versions'],lock.read_text(encoding='utf-8'),required)
        pip=subprocess.run([python,'-m','pip','check'],capture_output=True,text=True,
                           encoding='utf-8',errors='replace',timeout=30)
        result['pip_check']={'exit_code':pip.returncode,'output':(pip.stdout+pip.stderr).strip()}
        result['status']='passed' if not result['lock_mismatches'] and pip.returncode==0 else 'failed'
        return result
    except (OSError,subprocess.TimeoutExpired,ValueError,IndexError) as error:
        return {'status':'failed','error':str(error)}


def inspect_upstream(runtime,expected):
    versions={normalized(k):v for k,v in runtime.get('versions',{}).items()}
    origin=next(iter(runtime.get('direct_urls',{}).values()),{})
    commit=origin.get('vcs_info',{}).get('commit_id')
    result={'expected_commit':expected['commit'],'actual_commit':commit,
            'expected_version':expected['version'],'actual_version':versions.get('ansys-aedt-mcp')}
    try:
        editable=origin.get('dir_info',{}).get('editable') is True
        result['installation_kind']='editable' if editable else 'fixed'
        if editable and not origin.get('url','').startswith('file:'):
            return result|{'status':'failed','error':'Editable installation requires a local source directory.'}
        if editable:
            source=unquote(urlparse(origin['url']).path)
            if os.name=='nt' and re.match(r'^/[A-Za-z]:',source):source=source[1:]
            command=['git','-c','safe.directory='+source,'-C',source]
            commit_probe=subprocess.run([*command,'rev-parse','HEAD'],capture_output=True,text=True,timeout=15,check=True)
            dirty=subprocess.run([*command,'status','--porcelain','--untracked-files=no'],capture_output=True,text=True,timeout=15,check=True)
            result.update(actual_commit=commit_probe.stdout.strip(),tracked_source_modified=bool(dirty.stdout.strip()))
        result['status']='passed' if result['actual_commit']==expected['commit'] and result['actual_version']==expected['version'] and not result.get('tracked_source_modified',False) else 'failed'
    except (OSError,subprocess.SubprocessError) as error:result.update(status='failed',error=str(error))
    return result


def inspect_server(name, server):
    errors=[]
    if 'url' in server:
        return {'status':'not_probed','errors':['HTTP must be verified by automation probe.']}
    for key in ('command','cwd'):
        value=server.get(key)
        if not value or not Path(value).exists():errors.append(f'{key}: missing path')
    env=server.get('env',{})
    if name=='ansys':
        if os.name=='nt' and (not env.get('APPDATA') or not Path(env['APPDATA']).is_dir()):
            errors.append('PyAEDT requires an explicit existing APPDATA directory on Windows.')
        if env.get('PYTHONUTF8')!='1' or env.get('PYTHONIOENCODING','').lower()!='utf-8':
            errors.append('Explicit UTF-8 settings are required for desktop MCP pipes.')
        roots={k:v for k,v in env.items() if re.fullmatch(r'ANSYSEM(?:SV)?_ROOT\d{3}',k)}
        if not roots:errors.append('AEDT installation roots are absent from the explicit MCP environment.')
        for key,value in roots.items():
            names=('ansysedtsv.exe','Win64/ansysedtsv.exe') if 'SV' in key else ('ansysedt.exe','ansysedt','Win64/ansysedt.exe')
            if not any((Path(value)/exe).is_file() for exe in names):errors.append(key+': executable missing')
        args=server.get('args',[])
        if not args or not Path(args[0]).is_file():errors.append('Ansys launcher source is missing.')
    return {'status':'failed' if errors else 'passed','errors':errors}


def check(root, run_id, client_config=None, verify_data=False):
    out=run_directory(root,run_id)
    inputs=['pyproject.toml','automation/mcp/project-environment.lock',
            'automation/mcp/ansys-environment.lock','automation/mcp/upstreams.lock.json']
    if (root/'litz.config.json').exists():inputs.append('litz.config.json')
    write(out/'request.json',{'run_id':run_id,'kind':'research_readiness','verify_data':verify_data,
                             'client_config':str(client_config) if client_config else None})
    from .tasks import source_manifest
    sources=source_manifest(root)
    write(out/'run_manifest.json',{'run_id':run_id,'sources':sources,
                                  'inputs':{p:sha(root/p) for p in inputs},
                                  'request_sha256':sha(out/'request.json')})
    checks={}
    local=read(root/'litz.config.json') if (root/'litz.config.json').exists() else {}
    servers=local.get('mcp_servers',{})
    for name in ('wolfram','ansys'):
        checks[name+'_configuration']=inspect_server(name,servers.get(name,{}))
    checks['project_runtime']=inspect_runtime(sys.executable,['mcp','mpmath','psutil','bibtexparser'],
        root/'automation/mcp/project-environment.lock',('mcp','mpmath','psutil','bibtexparser'))
    try:installed=importlib.metadata.version('litz-research')
    except importlib.metadata.PackageNotFoundError:installed=None
    checks['package_identity']={'status':'passed' if installed==__version__ else 'failed',
                                'source_version':__version__,'installed_version':installed}
    ap=tool(root,'ansys_python')
    checks['ansys_runtime']=inspect_runtime(ap,['ansys.aedt.core','ansys.aedt.mcp','mcp'],
        root/'automation/mcp/ansys-environment.lock',('ansys-aedt-mcp','pyaedt','ansys-common-mcp','fastmcp','mcp')) if ap else {'status':'failed','error':'Configure tools.ansys_python.'}
    checks['ansys_upstream']=inspect_upstream(checks['ansys_runtime'],read(root/'automation/mcp/upstreams.lock.json')['ansys'])
    if client_config:
        try:
            configured=tomllib.loads(Path(client_config).read_text(encoding='utf-8-sig')).get('mcp_servers',{})
            differences={}
            for name in ('wolfram','ansys'):
                candidates=[v for k,v in configured.items() if k.lower()==name]
                if len(candidates)!=1:
                    differences[name]=['missing or duplicate server'];continue
                actual=candidates[0];expected=servers.get(name,{})
                fields=[k for k in ('command','args','cwd','env','url') if actual.get(k)!=expected.get(k)]
                if actual.get('enabled') is False:fields.append('disabled')
                if fields:differences[name]=fields
            checks['desktop_configuration']={'status':'failed' if differences else 'passed','differences':differences}
        except (OSError,ValueError) as error:checks['desktop_configuration']={'status':'failed','error':str(error)}
    from .tasks import plan,ROUTES
    plans={name:plan(root,name,run_id+'_'+name.replace('-','_'),
             case='diagnostic' if name=='aphi' else 'maxwell-seven' if name=='ansys' else 'tutorial')
           for name in ROUTES}
    checks['route_inputs']={'status':'passed' if all(p['dispatch_status']=='ready' for p in plans.values()) else 'failed',
                           'plans':plans,'scope':'Input/executable discovery only, not solver acceptance.'}
    import psutil
    memory=psutil.virtual_memory()
    checks['resource_reserve']={'status':'passed' if memory.available>=8*2**30 else 'failed',
                                'available_bytes':memory.available,'required_bytes':8*2**30}
    source=subprocess.run([sys.executable,'-B',str(root/'tools/CheckSourceCheckout.py'),
                           '--output',str(out/'source_checkout.json')],cwd=root,capture_output=True,
                          text=True,encoding='utf-8',errors='replace',timeout=120)
    (out/'source_checkout.log').write_text(source.stdout+source.stderr,encoding='utf-8')
    checks['source_checkout']={'status':'passed' if source.returncode==0 else 'failed','exit_code':source.returncode}
    if verify_data:
        from .data import verify
        datasets=verify(root)
        checks['datasets']={'status':'passed' if all(x['status']=='passed' for x in datasets) else 'failed','datasets':datasets}
    failures=[k for k,v in checks.items() if v['status']!='passed']
    result={'run_id':run_id,'timestamp_UTC':datetime.now(timezone.utc).isoformat(),
            'execution_status':'failed' if failures else 'completed',
            'readiness_status':'blocked' if failures else 'passed_preflight',
            'physical_acceptance_status':'not_evaluated','checks':checks,'failed_checks':failures,
            'scope':'Dependencies, explicit launch configuration, source tests and route inputs. Run fresh MCP probes and selected solver tutorials after changes.'}
    write(out/'results.json',result)
    return {k:v for k,v in result.items() if k!='checks'}|{'report':str(out/'results.json')}
