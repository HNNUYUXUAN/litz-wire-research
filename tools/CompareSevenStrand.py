"""Compare saved independent seven-strand solves without promoting mesh accuracy."""
from pathlib import Path
import argparse,json,math
from litz_research.common import write,sha,run_directory

def compare(wolfram,ansys):
    w=wolfram['data'];a=ansys;g=a['source_geometry']
    z=lambda v:complex(v['real'],v['imag'])
    wi=[z(v) for v in w['strand_currents_RMS_A']]
    last=next(s['data'] for s in a['solves'] if s['label']=='constrained20A')
    ai=[z(last['winding_currents_RMS_A']['W_Copper_'+str(i+1)]) for i in range(7)]
    norm=lambda values:math.sqrt(sum(abs(v)**2 for v in values))
    shape_checks={
        'strand_count':w['strands']==len(ai)==7,
        'strand_polygon':w['circle_segments']==g['strand_segments']==42,
        'strand_diameter':math.isclose(w['diameter_m'],a['parameters']['diameter_m'],rel_tol=1e-12),
        'return_inner_radius':math.isclose(w['return_inner_radius_m'],g['return_inner_radius_mm']/1000,rel_tol=1e-12),
        'return_outer_radius':math.isclose(w['return_outer_radius_m'],g['return_outer_radius_mm']/1000,rel_tol=1e-12),
        'domain_radius':math.isclose(w['outer_radius_m'],g['domain_radius_mm']/1000,rel_tol=1e-12),
        'axial_depth':a['axial_depth_m']==1 and a['environment']['model_depth']=='1000mm',
        'frequency':a['parameters']['frequency_Hz']==200000,
        'total_current':abs(sum(wi)-20)<1e-8 and abs(sum(ai)-20)<1e-8,
    }
    return {'execution_status':'completed','physical_acceptance_status':'comparison_observed_convergence_not_run',
        'aligned_conditions':shape_checks,'all_alignment_checks_passed':all(shape_checks.values()),
        'complex_current_relative_L2_difference':norm([x-y for x,y in zip(wi,ai)])/norm(wi),
        'bundle_Rac_relative_difference':abs(a['bundle_Rac_ohm_per_m']/w['bundle_Rac_ohm_per_m']-1),
        'wolfram_Rac_ohm_per_axial_m':w['bundle_Rac_ohm_per_m'],'maxwell_Rac_ohm_per_axial_m':a['bundle_Rac_ohm_per_m'],
        'wolfram_power_residual':w['power_residual'],'maxwell_power_residual':a['power_relative_error'],
        'complex_currents_RMS_A':{'wolfram':[{'real':v.real,'imag':v.imag} for v in wi],'maxwell':[{'real':v.real,'imag':v.imag} for v in ai]},
        'scope':'Straight insulated seven-strand pure transport with common terminal voltage and controlled copper return. Insufficient copper area for Q2.',
        'numerical_limits':['Independent meshes and interpolation orders differ.','Source polygons have 42 sides; return polygon segmentation may differ.','Maxwell uses one adaptive pass. Spatial and boundary convergence are not established.','Observed agreement is not an uncertainty bound or a ranking of actual Litz geometries.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--wolfram-run',required=True);p.add_argument('--ansys-run',required=True);p.add_argument('--run-id',required=True);args=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=run_directory(root,args.run_id)
    paths=[root/'outputs'/rid/'results.json' for rid in [args.wolfram_run,args.ansys_run]]
    result=compare(*[json.loads(path.read_text(encoding='utf-8')) for path in paths])
    result['inputs']=[{'run_id':rid,'sha256':sha(path)} for rid,path in zip([args.wolfram_run,args.ansys_run],paths)]
    write(out/'results.json',result);print(json.dumps(result,indent=2))
    if not result['all_alignment_checks_passed']:raise SystemExit(1)

if __name__=='__main__':main()
