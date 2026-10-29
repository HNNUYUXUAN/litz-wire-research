"""Native seven-strand Maxwell case, called inside the upstream MCP Python session."""
from pathlib import Path
import cmath,json,math,sys,time
import numpy as np
from ansys.aedt.core import Maxwell2d
from ansys.aedt.core.generic.constants import SolutionsMaxwell2D

def execute(root,output,port,parameters=None):
    root=Path(root);out=Path(output)
    if out.exists():
        request=json.loads((out/'request.json').read_text(encoding='utf-8')) if (out/'request.json').exists() else {}
        if request.get('model')!='ansys' or request.get('case') not in {'maxwell-seven','maxwell-seven-convergence'}:raise FileExistsError('Choose a new run directory')
    else:out.mkdir(parents=True)
    with (out/'native_model_started.json').open('x',encoding='utf-8') as receipt:json.dump({'run_id':out.name,'execution_status':'model_creation_started'},receipt)
    import hashlib,shutil
    sources={}
    for source in [Path(__file__),root/'adapters/ansys/ansys_validate.py',root/'adapters/ansys/StartMCP.py']:
        target=out/'source_snapshot'/source.name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
        sources[source.relative_to(root).as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
    manifest=json.loads((out/'run_manifest.json').read_text(encoding='utf-8')) if (out/'run_manifest.json').exists() else {'run_id':out.name,'sources':sources}
    manifest.update(source_snapshot_timing='before_model_creation',native_sources=sources)
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    p={'frequency_Hz':200000.,'current_RMS_A':20.,'diameter_m':0.0001,'return_factor':2.,'outer_factor':1.5}|(parameters or {})
    linked='mesh_length_m' in p
    allowed={'frequency_Hz','current_RMS_A','diameter_m','return_factor','outer_factor'}
    if linked:allowed|={'mesh_length_m','return_mesh_length_m','air_mesh_length_m'}
    if set(p)!=allowed:raise ValueError('Unsupported Maxwell parameter')
    sys.path.insert(0,str(root/'adapters/ansys'))
    from ansys_validate import read_shorttest_solution
    app=Maxwell2d(project=str(out/'seven_strand.aedt'),design='CommonTerminal7',solution_type=SolutionsMaxwell2D.ACMagnetic,version='2025.2',port=port,new_desktop=False,student_version=True,non_graphical=True,close_on_exit=False)
    if app.solution_type!=SolutionsMaxwell2D.ACMagnetic:raise RuntimeError('Wrong actual solution type: '+str(app.solution_type))
    app.modeler.model_units='mm';app.materials.add_material('litz_copper').conductivity=5.8e7
    app.materials.add_material('litz_air').permittivity=1.
    app.change_design_settings({'BackgroundMaterialName':'litz_air','ModelDepth':'1000mm'})
    from ansys.aedt.core.generic.numbers_utils import decompose_variable_value
    depth,depth_unit=decompose_variable_value(app.model_depth)
    if app.modeler.model_units!='mm' or depth_unit!='mm' or abs(float(depth)-1000)>1e-9:
        raise RuntimeError('Actual Maxwell units/depth do not match the one-metre case')
    d=p['diameter_m']*1000.;radius=d/2
    centers=[[0.,0.]]+[[1.2*d*math.cos(k*math.pi/3),1.2*d*math.sin(k*math.pi/3)] for k in range(6)]
    wires=[app.modeler.create_circle([*xy,0],radius,num_sides=42,name='Copper_'+str(i+1),material='litz_copper') for i,xy in enumerate(centers)]
    bundle_radius=1.2*d+radius;ri=p['return_factor']*bundle_radius;ro=ri+max(4*radius,.3);domain=p['outer_factor']*ro
    ret=app.modeler.create_circle([0,0,0],ro,num_sides=96,name='ReturnOuter',material='litz_copper')
    hole=app.modeler.create_circle([0,0,0],ri,num_sides=96,name='ReturnInner');app.modeler.subtract(ret,hole,keep_originals=False)
    air=app.modeler.create_circle([0,0,0],domain,num_sides=96,name='Air',material='litz_air');app.modeler.subtract(air,[x.name for x in wires]+[ret.name],keep_originals=True)
    # Apply the Dirichlet condition to every outer polygon edge.
    app.assign_vector_potential([e for e in air.edges if math.hypot(e.midpoint[0],e.midpoint[1])>domain*.99],vector_value=0)
    windings=[]
    for obj in [*wires,ret]:
        name='ReturnWinding' if obj==ret else 'W_'+obj.name
        winding=app.assign_winding(assignment=[obj.name],winding_type='Voltage',is_solid=True,voltage='1V',phase='0deg',parallel_branches=1,current=0,name=name)
        if not winding:raise RuntimeError('Voltage winding assignment failed: '+name)
        windings.append(winding)
    app.eddy_effects_on([x.name for x in wires]+[ret.name],enable_eddy_effects=True,enable_displacement_current=False)
    setup=app.create_setup('LitzSetup');setup.props['Frequency']=str(p['frequency_Hz'])+'Hz';setup.props['MaximumPasses']=1;setup.props['MinimumPasses']=1;setup.props['PercentError']=20;setup.update()
    if linked:
        for names,length in [([w.name for w in wires],p['mesh_length_m']),([ret.name],p['return_mesh_length_m']),([air.name],p['air_mesh_length_m'])]:
            if not app.mesh.assign_length_mesh(names,inside_selection=True,maximum_length=str(length*1000)+'mm',maximum_elements=None):raise RuntimeError('Mesh length assignment failed')
    report={'source_model':'Ansys_Maxwell2D_native_seven_strand_common_voltage','execution_status':'running','physical_acceptance_status':'not_verified','parameters':p,'axial_depth_m':1,'solves':[],'port':port,'mesh_scope':'One-pass polygonal mesh; full spatial and boundary convergence not_run','phasor':'exp(+j omega t), RMS; AEDT source values are peak'}
    def save(): (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    save()
    def solve(label,vs,vr):
        nonlocal setup,windings
        folder=out/label;folder.mkdir();voltages={}
        if linked and label!='mesh_source':
            app.set_active_design('CommonTerminal7')
            if not app.duplicate_design(label,save_after_duplicate=True):raise RuntimeError('Mesh partner duplication failed')
            setup=app.get_setup('LitzSetup')
            if not setup.add_mesh_link('CommonTerminal7',force_source_to_solve=False,preserve_partner_solution=True,apply_mesh_operations=False,adapt_port=False):raise RuntimeError('Official mesh link failed')
            windings=[b for b in app.boundaries if b.name in {'ReturnWinding',*[f'W_Copper_{i+1}' for i in range(7)]}]
            if len(windings)!=8:raise RuntimeError('Cloned winding identity mismatch')
        for winding in windings:
            value=vr if winding.name=='ReturnWinding' else vs
            winding.props['Voltage']=str(abs(value)*math.sqrt(2))+'V';winding.props['Phase']=str(math.degrees(cmath.phase(value)))+'deg';winding.update();voltages[winding.name]=value
        app.save_project()
        if not app.validate_simple(log_file=str(folder/'validation.log')):
            raise RuntimeError('Maxwell design validation failed: '+label)
        if not app.analyze_setup(setup.name,cores=4,use_auto_settings=False,revert_to_initial_mesh=not linked or label=='mesh_source'):raise RuntimeError('Maxwell solve failed: '+label)
        data=read_shorttest_solution(app,folder,voltages,[x.name for x in wires]+[ret.name])
        if data['errors']:raise RuntimeError('Postprocessing failed: '+str(data['errors']))
        app.export_mesh_stats(setup.name,output_file=str(folder/'mesh_stats.csv'))
        if linked:
            from RunClosureAnsys import export_mesh_records
            identity=export_mesh_records(out/'seven_strand.aedt',folder/'mesh_stats.csv',folder,2)
            from MeshIdentity import canonical
            identity['canonical']=canonical(folder)
            native_copy=folder/'native_mesh';native_copy.mkdir()
            for entry in identity['files']:
                shutil.copy2(out/'seven_strand.aedtresults'/entry['relative_path'],native_copy/entry['file'])
            identity['design']=app.design_name
            identity['materials']={obj.name:obj.material_name for obj in app.modeler.object_list}
            (folder/'mesh_identity.json').write_text(json.dumps(identity,indent=2),encoding='utf-8')
            if label!='mesh_source':
                source=json.loads((out/'mesh_source/mesh_identity.json').read_text())
                if identity['canonical']['sha256']!=source['canonical']['sha256'] or identity['materials']!=source['materials']:
                    report.update(execution_status='failed',physical_acceptance_status='failed_fixed_mesh_identity',failure_reason='Actual mesh payload or material identity changed; retained raw records require topology audit')
                    save();raise RuntimeError(report['failure_reason'])
        report['solves'].append({'label':label,'data':data,'voltage_RMS_V':{'source':{'real':vs.real,'imag':vs.imag},'return':{'real':vr.real,'imag':vr.imag}}});save()
        return data
    def currents(data):return np.array([complex(data[k]['real'],data[k]['imag']) for k in ['source_current_RMS_A','return_current_RMS_A']])
    if linked:solve('mesh_source',1+0j,0+0j)
    a=solve('basis_source',1+0j,0+0j);b=solve('basis_return',0+0j,1+0j)
    voltage=np.linalg.solve(np.column_stack([currents(a),currents(b)]),np.array([p['current_RMS_A'],-p['current_RMS_A']]))
    final=solve('constrained20A',complex(voltage[0]),complex(voltage[1]))
    current_error=float(np.linalg.norm(currents(final)-[p['current_RMS_A'],-p['current_RMS_A']])/np.linalg.norm([p['current_RMS_A'],-p['current_RMS_A']]))
    loss=sum(v for k,v in final['solid_losses_W'].items() if k not in {'ReturnWinding','total'})
    report.update(execution_status='completed',physical_acceptance_status='passed_port_and_power_scope_only' if current_error<1e-8 and final['power_relative_difference']<1e-8 else 'failed',current_constraint_relative_error=current_error,power_relative_error=final['power_relative_difference'],bundle_Rac_ohm_per_m=loss/p['current_RMS_A']**2,source_geometry={'strand_centers_mm':centers,'strand_radius_mm':radius,'return_inner_radius_mm':ri,'return_outer_radius_mm':ro,'domain_radius_mm':domain,'strand_segments':42,'return_segments':96},project='seven_strand.aedt')
    import platform,importlib.metadata
    report['environment']={'python':platform.python_version(),'pyaedt':importlib.metadata.version('pyaedt'),'aedt':app.desktop_class.aedt_version,'model_units':app.modeler.model_units,'model_depth':app.model_depth,'frequency_setting':setup.props['Frequency'],'solver_cores':4}
    app.save_project()
    project=out/'seven_strand.aedt'
    report['project_readback']={'design_present':b'CommonTerminal7' in project.read_bytes(),'sha256':hashlib.sha256(project.read_bytes()).hexdigest()}
    report['run_id']=out.name
    if linked:report.update(mesh_scope='Actual linked source/basis/final mesh payloads and material identities verified; one convergence candidate',fixed_mesh_identity_status='passed')
    copper_area=7*42/2*(p['diameter_m']/2)**2*math.sin(2*math.pi/42)
    rdc=1/(5.8e7*copper_area);mean_current=p['current_RMS_A']/7
    strand_currents=[complex(final['winding_currents_RMS_A']['W_Copper_'+str(i+1)]['real'],final['winding_currents_RMS_A']['W_Copper_'+str(i+1)]['imag']) for i in range(7)]
    report.update(bundle_Rdc_ohm_per_m=rdc,Rac_over_Rdc=report['bundle_Rac_ohm_per_m']/rdc,bundle_loss_W_per_m=loss,polygonal_copper_area_m2=copper_area,copper_volume_m3_per_axial_m=copper_area,arc_lengths_m=[1.]*7,arc_length_growth_factors=[1.]*7,current_max_relative_complex_deviation=max(abs(i-mean_current) for i in strand_currents)/mean_current,scope='Straight insulated seven-strand pure transport; controlled copper return; prescribed 20 C conductivity; no thermal solve; insufficient copper for final Q2.')
    report['checks']=[{'name':'total_complex_current','actual':current_error,'tolerance':1e-8,'passed':current_error<1e-8},{'name':'input_loss_power','actual':final['power_relative_difference'],'tolerance':1e-8,'passed':final['power_relative_difference']<1e-8},{'name':'saved_native_design','actual':report['project_readback']['design_present'],'passed':report['project_readback']['design_present']}]
    save()
    return report
