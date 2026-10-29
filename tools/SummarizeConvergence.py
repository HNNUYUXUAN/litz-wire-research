"""Build auditable finite scientific conclusions from retained run evidence."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def summarize():
    records=[]
    for path in sorted((ROOT/'outputs').glob('convergence_20261030_*/results.json')):
        if path.parent.name.endswith('_mcp'):continue
        result=json.loads(path.read_text(encoding='utf-8'))
        if 'aphi_' not in path.parent.name and 'maxwell_' not in path.parent.name:continue
        record={k:result.get(k) for k in ['run_id','case','execution_status','physical_acceptance_status','elapsed_seconds','parameters']}
        record['run_id']=path.parent.name
        record['result_sha256']=digest(path)
        record['manifest_sha256']=digest(path.parent/'run_manifest.json')
        if 'aphi_' in path.parent.name:record['cases']=result['data']['cases']
        else:
            source=path.parent/'mesh_source/mesh_nodes_SI.csv';target=path.parent/'basis_source/mesh_nodes_SI.csv'
            with source.open() as f:a={r['node_id']:r for r in csv.DictReader(f)}
            with target.open() as f:b={r['node_id']:r for r in csv.DictReader(f)}
            differences=[max(abs(Decimal(a[k][v])-Decimal(b[k][v])) for v in ['x_m','y_m','z_m']) for k in a.keys()&b.keys()]
            record.update(fixed_mesh_gate='failed_exact_coordinates',changed_nodes=sum(d!=0 for d in differences),
                          maximum_coordinate_change_m=str(max(differences)),
                          coordinate_source_sha256=digest(source),coordinate_target_sha256=digest(target),
                          conclusion='Exact decimal coordinate identity failed; no coordinate tolerance was introduced. Mesh convergence and boundary/cross-solver descendants remain gated.')
        records.append(record)
    summary={'schema_version':1,'campaign':'convergence_20261030_01','runs':records,
             'simulation_elapsed_seconds':sum(x.get('elapsed_seconds') or 0 for x in records),
             'simulation_budget_seconds':172800,
             'maxwell_terminal':'fixed_mesh_gate_failed_after_one_reasoned_revision',
             'aphi_terminal':'manufactured_passed_cylinder_and_discrete_trace_controls_failed_phi_gauge',
             'next_minimum_experiments':['Capture and compare native mesh coordinates before and after importing without another solver execution; establish the solver mesh serialization contract before changing the exact-identity gate.',
             'Assemble the extruded P2 discrete operator and test the lifted 2D solution residual by equation block; separate gauge coupling, quadrature and end constraints.'],
             'scope':'Finite diagnostic conclusions; no Maxwell spatial-convergence claim and no realistic-transposition ranking.'}
    out=ROOT/'provenance/convergence';out.mkdir(parents=True,exist_ok=True)
    (out/'scientific-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary

if __name__=='__main__':print(json.dumps(summarize(),ensure_ascii=False))
