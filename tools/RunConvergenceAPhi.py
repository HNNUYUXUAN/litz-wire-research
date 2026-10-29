"""Serial, bounded remaining paired A-phi calibration runs."""
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from litz_research.tasks import execute

if __name__=='__main__':
    campaign=ROOT/'outputs/convergence_20261030_01'
    rows=[]
    for h,code in [(.22,'022'),(.14,'014')]:
        for case,mode in [('cylinder-calibration','c'),('extrusion-control','d')]:
            rid=f'convergence_20261030_aphi_{mode}{code}_01'
            before=time.monotonic()
            try:
                result=execute(ROOT,'aphi',rid,case,{'mesh_h':h})
                rows.append({'run_id':rid,'execution_status':result['execution_status'],
                             'physical_acceptance_status':result['physical_acceptance_status'],
                             'elapsed_seconds':time.monotonic()-before})
            except Exception as error:
                rows.append({'run_id':rid,'execution_status':'failed','error':str(error),
                             'elapsed_seconds':time.monotonic()-before})
            (campaign/'aphi_execution.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
            print(json.dumps(rows[-1]),flush=True)
