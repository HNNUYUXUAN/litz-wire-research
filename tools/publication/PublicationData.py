"""Read-only publication field reconstruction. No solver or operator imports."""
from __future__ import annotations
import argparse
import cmath
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

ROOT=next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
BUNDLE=ROOT/'outputs/closure_20261005_manuscript_bundle_final_02'
SCIENCE=(ROOT/'docs/总控/当前运行索引.json',ROOT/'outputs/prewrite_closure_state.json')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
class FrozenData:
    def __init__(self,run):
        self.run=Path(run);self.sources={};self.checks=[]
        self.before={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in SCIENCE}
    def bind(self,p):
        p=Path(p);self.sources[p.relative_to(ROOT).as_posix()]=sha(p);return p
    def json(self,p):return read(self.bind(p))
    def csv(self,p):
        with self.bind(p).open(encoding='utf-8-sig',newline='') as stream:
            yield from csv.DictReader(stream)
    def array(self,desc):
        p=BUNDLE/desc['path'];shape=desc['dimensions']
        values=[complex(float(r['real']),float(r['imag'])) if desc.get('complex') else float(r['value']) for r in self.csv(p)]
        if len(values)!=math.prod(shape):raise ValueError('Array shape mismatch: '+str(p))
        if len(shape)==1:return values
        def reshape(v,sh):
            if len(sh)==1:return v
            step=math.prod(sh[1:]);return [reshape(v[i:i+step],sh[1:]) for i in range(0,len(v),step)]
        return reshape(values,shape)
    def check(self,name,actual,tolerance):
        self.checks.append(dict(name=name,actual=actual,tolerance=tolerance,passed=actual<=tolerance))
        if actual>tolerance:raise ValueError(f'{name}: {actual} > {tolerance}')
    def output(self,name,obj):write(self.run/'field_data'/name,obj)

    def coax640(self):
        route=self.json(BUNDLE/'routes/coax640/data.json');case=route['cases'][2]
        coords=self.array(case['mesh']['coordinates']);u=self.array(case['u_nodes_V_per_m'])
        markers=self.array(case['element_markers']);expected=self.array(case['strand_currents_RMS_A'])
        def ri(d):return complex(d['real'],d['imag'])
        source=ri(case['source_voltage_V_per_m']);back=ri(case['return_voltage_V_per_m'])
        sigma=5.8e7;scale=.001;currents=[0j]*641;losses=[0.]*641;areas=[0.]*641
        display_points=[];display_ids={};triangles=[];values=[];phases=[];labels=[]
        connection=BUNDLE/'routes/coax640/supplements/closure_20261005_mesh_connectivity_supplement_01/arrays/case_3_mesh_connectivity.csv'
        target=self.run/'field_data/coax640_conductor_cells.csv';target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['element_id_1based','material_marker','node1','node2','node3','x_mm','y_mm','Jz_centroid_A_per_mm2_real','Jz_centroid_A_per_mm2_imag','exact_linear_triangle_loss_W_per_m'])
            count=0
            for r in self.csv(connection):
                index=int(r['element_index_1based'])-1;marker=int(markers[index]);count+=1
                if not 1<=marker<=641:continue
                ids=[int(r[f'node_{k}_ID_1based'])-1 for k in [1,2,3]]
                points=[coords[k] for k in ids];a,b,c=points
                area=abs((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1]))/2
                terminal=source if marker<=640 else back
                e=[terminal-u[k] for k in ids];total=sum(e);centroid=total/3*sigma*1e-6
                current=sigma*scale**2*area*total/3
                loss=sigma*scale**2*area/12*(sum(abs(v)**2 for v in e)+abs(total)**2)
                currents[marker-1]+=current;losses[marker-1]+=loss;areas[marker-1]+=area*scale**2
                xy=[sum(p[k] for p in points)/3*scale*1000 for k in [0,1]]
                writer.writerow([index+1,marker,*[k+1 for k in ids],*xy,centroid.real,centroid.imag,loss])
                if marker<=640:
                    mapped=[]
                    for k in ids:
                        if k not in display_ids:
                            display_ids[k]=len(display_points)+1;display_points.append([v*scale*1000 for v in coords[k]])
                        mapped.append(display_ids[k])
                    triangles.append(mapped);values.append(abs(centroid));phases.append(math.degrees(cmath.phase(centroid)));labels.append(marker)
        self.check('coax640_triangle_count',abs(count-case['triangles']),0)
        self.check('coax640_strand_complex_currents',max(abs(a-b) for a,b in zip(currents[:640],expected))/20,1e-8)
        self.check('coax640_total_source_current',abs(sum(currents[:640])-20)/20,1e-8)
        self.check('coax640_source_plus_return_current',abs(sum(currents))/20,1e-8)
        self.check('coax640_bundle_Joule',abs(sum(losses[:640])/case['bundle_loss_W_per_m']-1),1e-8)
        self.check('coax640_return_Joule',abs(losses[640]/case['return_loss_W_per_m']-1),1e-8)
        self.check('coax640_actual_copper_area',abs(sum(areas[:640])/case['polygonal_bundle_area_m2']-1),1e-8)
        self.output('coax640.json',dict(points_mm=display_points,triangles=triangles,values=values,phase_values=phases,material_markers=labels,
            source_node_ids_1based=[k+1 for k in display_ids],source_model=case['source_model'],source_run_id='full_20261005_coax640',
            coordinate_scale_m=scale,field_definition='Jz=sigma*(common terminal axial field-u); separate return axial field; air omitted from displayed conductor cells',
            color_sampling='complex J at each linear triangle centroid; exact linear-field mass integral used for power check, not centroid squared',
            displayed_materials='physical strand markers 1..640; return included in independent power/current checks and conductor_cells.csv, not the bundle view',
            recovered_bundle_loss_W_per_m=sum(losses[:640]),recovered_return_loss_W_per_m=losses[-1],actual_copper_area_m2=sum(areas[:640])))
        print('FIELD coax640 recovered and independent integrals passed',flush=True)

    def rt0(self):
        base=ROOT/'outputs/closure_20261005_rt0_n24_q14_01/cases/rt0_n24_q14'
        case=self.json(base/'case.json');h=case['cell_width_m'];dims=case['dimensions'];sigma=5.8e7
        flux={tuple(int(r[k]) for k in ['axis_1x_2y_3z','grid_i','grid_j','grid_k']):complex(float(r['face_flux_RMS_A_real']),float(r['face_flux_RMS_A_imag'])) for r in self.csv(base/'face_fluxes.csv')}
        archived=list(self.csv(base/'cell_fields.csv'));row_index=0;loss=0.;max_error=0.;norm=0.;points=[];values=[];j_values=[];centers=[];vectors=[];magnitudes=[]
        slice_k=dims[2]//2
        for i in range(1,dims[0]+1):
            for j in range(1,dims[1]+1):
                for k in range(1,dims[2]+1):
                    cell=(i,j,k);pairs=[]
                    for axis in [1,2,3]:
                        low=list(cell);low[axis-1]-=1
                        pairs.append((flux.get((axis,*low),0j),flux.get((axis,*cell),0j)))
                    current=[(a+b)/(2*h*h) for a,b in pairs]
                    local=sum((abs(a)**2+abs(b)**2+(a.conjugate()*b).real)/(3*sigma*h) for a,b in pairs);loss+=local
                    row=archived[row_index];row_index+=1
                    original=[complex(float(row[f'J{a}_RMS_A_per_m2_real']),float(row[f'J{a}_RMS_A_per_m2_imag'])) for a in 'xyz']
                    max_error=max(max_error,max(abs(a-b) for a,b in zip(current,original)));norm=max(norm,max(abs(a) for a in original))
                    center=[(v-.5)*h*1000 for v in cell]
                    if k==slice_k:
                        points.append(center[:2]);values.append(local/h**3*1e-6);j_values.append(math.sqrt(sum(abs(a)**2 for a in current))*1e-6)
                    if i%4==2 and j%4==2 and k%6==3:
                        centers.append(center);vectors.append([v.real for v in current]);magnitudes.append(math.sqrt(sum(abs(v)**2 for v in current))*1e-6)
        self.check('RT0_all_cell_center_complex_J_matches_archive',max_error/max(norm,1e-300),1e-10)
        self.check('RT0_exact_RT0_overlap_power_matches_archive',abs(loss/case['loss_W']-1),1e-10)
        self.output('rt0_slice.json',dict(points_mm=points,values=values,J_magnitude_A_per_mm2=j_values,cell_width_mm=h*1000,z_mm=(slice_k-.5)*h*1000,
            centers_mm=centers,vectors_real_phase0=vectors,vector_magnitudes_A_per_mm2=magnitudes,geometry_dimensions_mm=[1,1,2],
            source_run_id=case['run_id'],source_model=case['source_model'],recovered_loss_W=loss,
            value_definition='cell-average exact RT0 resistive overlap density in W/cm^3; differs from center |J|^2/sigma',
            vector_definition='fixed phasor phase zero real J; arrow length is display-normalized; color uses complex RMS vector norm',
            net_transport_current_RMS_A=0,external_Bz_RMS_T=.001))
        print('FIELD RT0 face flux reconstruction and all-cell archive comparison passed',flush=True)

    def peec(self):
        base=ROOT/'outputs/closure_20261005_peec_m80_l064_self12p10_01/cases/peec_m80_l064_q4_s12p10'
        rows=list(self.csv(base/'currents.csv'));currents=[complex(float(r['current_RMS_A_real']),float(r['current_RMS_A_imag'])) for r in rows]
        self.check('PEEC_5024_total_complex_current',abs(sum(currents)-20)/20,1e-8)
        self.output('peec_cross_section.json',dict(points_mm=[[1000*float(r[k]) for k in ['x_m','y_m']] for r in rows],
            values=[abs(complex(float(r['Jz_RMS_A_per_m2_real']),float(r['Jz_RMS_A_per_m2_imag'])))*1e-6 for r in rows],
            phase_values=[math.degrees(cmath.phase(i)) for i in currents],cell_width_mm=.025,
            source_run_id='closure_20261005_peec_m80_l064_self12p10_01',source_model='finite_length_longitudinal_volume_filament_PEEC',
            physical_acceptance_scope='5024 volume filaments, fixed straight round cross-section, longitudinal uniform-in-z basis; not 5024 insulated strands'))
        print('FIELD PEEC preserved 5024-filament currents',flush=True)

    def aphi(self):
        route=self.json(BUNDLE/'routes/closure_fem3_diagnostics/data.json');case=route['cases'][2]
        rows=self.array(case['nodal_field_samples']);columns=case['nodal_field_sample_columns'];fields=[dict(zip(columns,r)) for r in rows]
        def vector(r,p):return [complex(r[f'{p}{k}_real'],r[f'{p}{k}_imag']) for k in [1,2,3]]
        self.output('aphi_samples.json',dict(points_mm=[[r[k]*case['coordinate_scale_m']*1000 for k in ['x_dimensionless','y_dimensionless','z_dimensionless']] for r in fields],
            J_magnitude_A_per_mm2=[math.sqrt(sum(abs(x)**2 for x in vector(r,'J_A_per_m2_RMS_component_')))*1e-6 for r in fields],
            A_magnitude_T_m=[math.sqrt(sum(abs(x)**2 for x in vector(r,'A_T_m_component_'))) for r in fields],
            phi_magnitude_V=[abs(complex(r['phi_V_real'],r['phi_V_imag'])) for r in fields],
            gradient_phi_V_per_m=[math.sqrt(sum(abs(x)**2 for x in vector(r,'grad_phi_V_per_m_component_'))) for r in fields],
            node_ids_1based=[int(r['node_id_1based']) for r in fields],source_run_id=case['source_run_id'],source_model='actual_preserved_A_phi_cylinder_fields',
            historical_gates=case['historical_gates'],physical_acceptance_status='failed_numerical',
            coverage='128 explicitly indexed preserved mesh-node derivative samples, not a continuous field or all-node maximum'))
        print('FIELD A-phi actual 128-point A/phi/J/gradient diagnostics; physical failure preserved',flush=True)

    def finish(self):
        for p,h in self.sources.items():
            if sha(ROOT/p)!=h:raise ValueError('Source changed during reconstruction: '+p)
        self.check('frozen_science_hashes_unchanged',int(any(sha(ROOT/p)!=h for p,h in self.before.items())),0)
        write(self.run/'field_reconstruction_verification.json',dict(run_id=self.run.name,checks=self.checks,sources_sha256=self.sources,
            frozen_science_sha256=self.before,physical_solver_calls=0,operator_assemblies=0,GPU_compute_used=False,
            outputs_sha256={p.relative_to(self.run).as_posix():sha(p) for p in (self.run/'field_data').iterdir()}))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);a=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+',a.run_id):parser.error('Safe run ID required')
    run=ROOT/'outputs'/a.run_id;run.mkdir(exist_ok=False);data=FrozenData(run)
    snapshot=run/'source_snapshot';snapshot.mkdir();shutil.copy2(__file__,snapshot/'PublicationData.py');data.bind(Path(__file__))
    try:
        for operation in [data.coax640,data.rt0,data.peec,data.aphi]:operation()
        data.finish();print('FIELD DATA VERIFIED; no physical solver executed',flush=True)
    except Exception as error:
        write(run/'field_reconstruction_failure.json',dict(error_type=type(error).__name__,message=str(error),
            completed_checks=data.checks,sources_sha256=data.sources,physical_solver_calls=0,operator_assemblies=0))
        raise
if __name__=='__main__':main()
