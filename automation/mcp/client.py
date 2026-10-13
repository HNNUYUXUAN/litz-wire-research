"""A minimal standard MCP client, with actual request/response event recording."""
import argparse
import asyncio
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import traceback

async def run(request,out):
    from mcp import ClientSession,StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamablehttp_client
    from contextlib import AsyncExitStack
    events=[];calls=request['calls'];server=request['server']
    def event(kind,value):
        record={'timestamp_UTC':datetime.now(timezone.utc).isoformat(),'kind':kind,'value':value};events.append(record)
        with (out/'mcp_events.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record,ensure_ascii=False)+'\n')
    async with AsyncExitStack() as stack:
        if 'url' in server:
            read,write,*_=await stack.enter_async_context(streamablehttp_client(server['url']))
        else:
            error=stack.enter_context((out/'server_stderr.txt').open('w',encoding='utf-8'))
            params=StdioServerParameters(command=server['command'],args=server.get('args',[]),cwd=server.get('cwd'),env=dict(os.environ,**server.get('env',{})))
            read,write=await stack.enter_async_context(stdio_client(params,errlog=error))
        session=await stack.enter_async_context(ClientSession(read,write))
        initialized=await session.initialize();event('initialize',initialized.model_dump(mode='json'))
        tools=await session.list_tools();event('tools/list',tools.model_dump(mode='json'))
        available={t.name for t in tools.tools}
        results=[]
        for call in calls:
            if call['name'] not in available:raise ValueError('Tool not available: '+call['name'])
            event('tools/call/request',call)
            result=await session.call_tool(call['name'],call.get('arguments',{}))
            encoded=result.model_dump(mode='json');event('tools/call/result',encoded);results.append(encoded)
            messages=[c.text for c in result.content if getattr(c,'type',None)=='text']
            semantic_error=any(s.startswith(('Error ','Error:','Failed to ','No AEDT connection','Traceback ')) for s in messages)
            if result.isError or semantic_error:raise RuntimeError('MCP tool returned an error: '+call['name']+'; '+str(messages)[:1000])
        report={'execution_status':'completed','protocol_status':'passed','tool_call_status':'passed','tool_calls':len(results),'tools':sorted(available),'physical_acceptance_status':'not_evaluated_by_protocol_probe','upstreams':request['upstreams']}
        (out/'mcp_completion.json').write_text(json.dumps(report|{'status':'completed_mcp_calls'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);request=json.loads(Path(a.request).read_text(encoding='utf-8'))
    try:result=asyncio.run(run(request,out));code=0
    except Exception as exc:
        def leaves(e):return '; '.join(leaves(x) for x in e.exceptions) if hasattr(e,'exceptions') else str(e)
        events=[json.loads(line) for line in (out/'mcp_events.jsonl').read_text(encoding='utf-8').splitlines()] if (out/'mcp_events.jsonl').exists() else []
        result={'execution_status':'failed','protocol_status':'passed' if {'initialize','tools/list'}.issubset({x['kind'] for x in events}) else 'failed','tool_call_status':'failed','error':leaves(exc)}
        (out/'protocol_error.txt').write_text(traceback.format_exc(),encoding='utf-8');code=1
    (out/'protocol_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(code)

if __name__=='__main__':main()
