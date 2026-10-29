"""Execute finite tutorial cases sequentially under the shared resource policy."""
from pathlib import Path
import json,time
from litz_research.tasks import execute
from litz_research.common import write

def main():
    root=Path(__file__).resolve().parents[1];records=[]
    for model in ['wolfram-analytic','fem2','circuits','coax','geometry','copper','peec','rt0','aphi','gpu','wolfram','ansys']:
        rid='rc2_route_'+model.replace('-','_')+'_01'
        if (root/'outputs'/rid/'results.json').exists():
            result=json.loads((root/'outputs'/rid/'results.json').read_text(encoding='utf-8'))
        else:
            try:result=execute(root,model,rid,'diagnostic' if model=='aphi' else 'preflight' if model=='ansys' else 'tutorial')
            except Exception as exc:result={'execution_status':'failed','error':str(exc)}
        records.append({'model':model,'run_id':rid,'execution_status':result.get('execution_status'),'physical_acceptance_status':result.get('physical_acceptance_status'),'actual_exit_code':result.get('actual_exit_code'),'error':result.get('error')})
        write(root/'outputs/automation_20261013_rc2/route_verification.json',records)
        print(model,records[-1],flush=True)

if __name__=='__main__':main()
