"""Fresh kernel per native Notebook, bounded execution and frontend read-back."""
from pathlib import Path
import os,json,subprocess,shutil,uuid
from litz_research.common import constrain,write,sha

def main():
    root=Path(__file__).resolve().parents[1];constrain();requests=json.loads((root/'configs/research_notebooks.json').read_text(encoding='utf-8'));records=[]
    out=root/'outputs/automation_20261013_rc2/notebook_frontend';out.mkdir(exist_ok=True)
    runtime={p.relative_to(root).as_posix():sha(p) for folder in ['models','adapters','shared','python','configs'] for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.wl','.wls','.json'}}
    for r in requests:
        key=r['route']+'_'+r['language'];record_path=out/(key+'.json')
        if record_path.exists():
            prior=json.loads(record_path.read_text(encoding='utf-8'))
            if prior.get('status')=='passed_frontend_scope' and prior.get('sha256')==sha(root/r['path']) and prior.get('runtime_sources')==runtime:records.append(prior);continue
            history=out/'history';history.mkdir(exist_ok=True);shutil.copy2(record_path,history/(key+'_'+prior.get('sha256','unknown')[:12]+'.json'))
        env=dict(os.environ,LITZ_NOTEBOOK_QA_PATH=r['path'],LITZ_PYTHON=str(root/'.venv/Scripts/python.exe'))
        from litz_research.tasks import bounded_process
        leaf=out/'runs'/(key+'_'+uuid.uuid4().hex[:8]);leaf.mkdir(parents=True)
        process=bounded_process(['wolframscript','-local','-file',str(root/'adapters/wolfram/VerifyResearchNotebooks.wls')],root,leaf,env,{'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':1500,'completion_file':str(record_path)})
        record=json.loads(record_path.read_text(encoding='utf-8')) if record_path.exists() else {'path':r['path'],'status':'failed','actual_exit_code':process['actual_exit_code']}
        record['process']=process
        record['runtime_sources']=runtime;write(record_path,record)
        records.append(record);write(out/'verification.json',records);print(key,record['status'],flush=True)
    write(out/'verification.json',records)

if __name__=='__main__':main()
