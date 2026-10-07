"""Publication panel catalog. Uses frozen numerical sources and field maps only."""
import hashlib
import json
import shutil
import BuildPublicationEdition as b

def prepare(run,languages):
    evidence=b.read(run/'field_reconstruction_verification.json')
    if any(not c['passed'] for c in evidence['checks']):raise ValueError('Field reconstruction not verified')
    b.prepare_specimen(run,languages)
    request=b.read(run/'render_request.json');panels=request['panels'];sources=dict(evidence['sources_sha256'])
    def table(name):
        p=b.OLD_DOC/'figure_data'/name;sources[p.relative_to(b.ROOT).as_posix()]=b.sha(p);return b.csv_rows(p)
    def add(lang,id,kind,caption,model,origin,acceptance='scoped_passed',**opts):
        digest=hashlib.sha256(json.dumps(opts,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        panels.append(dict(id=id,language=lang,kind=kind,caption=caption,source_model=model,source_run_id=origin,
            data_sha256=digest,source_physical_acceptance_status=acceptance,**opts))
    def curve(lang,id,x,y,series,caption,model,origin,**opts):add(lang,id,'curve',caption,model,origin,x_label=x,y_label=y,series=series,**opts)
    def series(label,points,color='#265B8F'):return dict(label=label,points=points,color=color)
    fem=table('q1_fem2_convergence.csv');strand=table('coax640_currents.csv');length=table('peec_length.csv')
    sensitivities=table('peec_sensitivity.csv');gpu=table('gpu_equivalence.csv');resources=table('valid_resource_curves.csv')
    aphi=table('aphi_original_gates.csv');ansys=table('ansys_seven_currents.csv')
    coax_path=b.BUNDLE/'routes/coax640/data.json';geometry_path=b.BUNDLE/'routes/closure_geometry/data.json'
    sources[coax_path.relative_to(b.ROOT).as_posix()]=b.sha(coax_path);sources[geometry_path.relative_to(b.ROOT).as_posix()]=b.sha(geometry_path)
    coax=b.read(coax_path)['cases'];geometries=b.read(geometry_path)['geometries']
    (run/'tables').mkdir(exist_ok=True)
    for p in (b.OLD_DOC/'tables').glob('*.csv'):
        sources[p.relative_to(b.ROOT).as_posix()]=b.sha(p);shutil.copy2(p,run/'tables'/p.name)
    for p in (b.OLD_DOC/'figure_data').glob('*.csv'):
        sources[p.relative_to(b.ROOT).as_posix()]=b.sha(p);shutil.copy2(p,run/'tables'/p.name)
    for lang in languages:
        zh=lang=='zh-CN';t=lambda z,e:z if zh else e
        from PublicationDiagrams import diagram
        add(lang,'model_hierarchy','schematic',b.read(b.ROOT/'manuscript/publication.json')['figures']['model_hierarchy']['title'][lang],'explicit_physical_model_relationships','publication_design',acceptance='conceptual_diagram',**diagram('model_hierarchy',lang))
        from PublicationDiagrams import diagram
        add(lang,'common_terminal','schematic',b.read(b.ROOT/'manuscript/publication.json')['figures']['common_terminal']['title'][lang],'explicit_physical_model_relationships','publication_design',acceptance='conceptual_diagram',**diagram('common_terminal',lang))
        curve(lang,'q1_fem_error',t('节点数','Nodes'),t('相对误差','Relative error'),
            [series('Rac',[[int(r['nodes']),float(r['Rac_relative_error'])] for r in fem]),series(t('功率积分差','Power-integral difference'),[[int(r['nodes']),float(r['power_relative_error'])] for r in fem],'#B86C35')],
            t('孤立圆盘二维扩散三档校准；有限端场缺失。','Three-level isolated-disk 2D diffusion calibration; finite end fields are absent.'),'2D_diffusion_FEM',fem[0]['source_run_id'],scaling=['Log10','Log10'])
        for id,key,y in [('coax640_current','Abs_I_RMS_A','|ik| (A RMS)'),('coax640_phase','phase_deg',t('主值相位 (°)','Principal phase (°)'))]:
            curve(lang,id,t('物理股线身份','Physical strand ID'),y,[series('640',[[int(r['strand_id']),float(r[key])] for r in strand])],
                t('最细冻结二维网格的逐股复电流；身份序列不是路径，主值相位跳跃不是导体断续。','Complex strand currents on the finest frozen 2D mesh; identity order is not a path, and phase wrapping does not denote broken conductors.'),
                '2D_common_voltage_coax_FEM','full_20261005_coax640',reference_lines=[20/640] if key=='Abs_I_RMS_A' else [])
        source=run/'field_data/coax640.json';field=b.read(source)
        for id,key,cyclic,label in [('coax640_field','values',False,'|Jz| (A/mm²)'),('coax640_field_phase','phase_values',True,t('相位 (°)','Phase (°)'))]:
            add(lang,id,'mesh_field',t('二维共端 Jz 按原三角形重构。图示束内；回流参与独立电流/功率核查。颜色取单元质心值。','2D common-terminal Jz reconstructed on original triangles. The view shows the bundle; the return participates in independent current/power checks. Color samples cell centroids.'),field['source_model'],field['source_run_id'],
                data_file=str(source),value_key=key,x_label='x (mm)',y_label='y (mm)',color_label=label,minimum=-180 if cyclic else 0,maximum=180 if cyclic else max(field[key]),cyclic=cyclic)
        curve(lang,'coax640_mesh',t('节点数','Nodes'),'Rac (mΩ/m)',[series('640',[[int(c['nodes']),1000*c['bundle_Rac_ohm_per_m']] for c in coax[:3]])],
            t('固定回流与外域的原三档网格；边界敏感性另列。','Three original grids with fixed return and exterior; boundary sensitivity is reported separately.'),'640_strand_area_and_convergence_coax_FEM','full_20261005_coax640')
        for kind,label in [('straight',t('直束','Straight bundle')),('single',t('单级','Single-level')),('crosslayer',t('跨层','Cross-layer'))]:
            g=next(g for g in geometries if g['kind']==kind and g['axial_sample_segments']==1600)
            paths=b.array_from_descriptor(g['paths']);source_array=b.BUNDLE/g['paths']['path'];sources[source_array.relative_to(b.ROOT).as_posix()]=b.sha(source_array)
            cropped=[[[1000*v for v in p] for k,p in enumerate(line) if p[2]<=.003+1e-12 and k%4==0] for line in paths]
            add(lang,'geometry_'+kind,'geometry',t(f'{label}保存中心线的真实 3 mm 局部。铜径 0.100 mm；小股数几何不作电磁性能排名。',f'An actual 3 mm detail of archived {label.lower()} centerlines, copper diameter 0.100 mm. Small-strand geometry does not establish an electromagnetic ranking.'),'archived_physical_strand_centerlines','closure_20261005_geometry_01',
                acceptance='geometry_only; historical_native_exit_unknown',paths_mm=cropped,radius_mm=.05,highlight_ids=[1])
        length_series=[series('m'+m,[[float(r['length_m']),1000*float(r['Rac_ohm_per_axial_m'])] for r in length if r['m']==m and r['q']=='4' and r['ag']=='10'],color) for m,color in [('40','#265B8F'),('80','#B86C35')]]
        curve(lang,'peec_length',t('轴向长度 Lz (m)','Axial length Lz (m)'),'Rac (mΩ/m)',length_series,
            t('固定纵向基函数；各 m 使用自身实际铜面积。横向环流与端部重分布缺失。','Fixed longitudinal basis; each m uses its actual copper area. Transverse loops and end redistribution remain absent.'),'finite_length_longitudinal_volume_filament_PEEC','closure_20261005_peec_m80_l064_self12p10_01')
        selected=[r for r in sensitivities if r.get('acceptance_metric') and r['execution_status']=='passed']
        curve(lang,'peec_sensitivity',t('敏感性试验编号','Sensitivity case index'),t('相对变化 (%)','Relative change (%)'),[series(t('已运行比较','Executed comparisons'),[[k+1,100*float(r['acceptance_metric'])] for k,r in enumerate(selected)])],
            t('每次只改变一个因素；编号见原数据表。未运行档保留为空，不画成零。','One factor changes per comparison; indices map to the original table. Unexecuted cases remain missing and are not drawn as zero.'),'prewrite_longitudinal_PEEC_sensitivity','closure_20261005_peec_m80_l064_self12p10_01',scaling=[None,'Log10'],reference_lines=[1],joined=False)
        source=run/'field_data/peec_cross_section.json';field=b.read(source)
        add(lang,'peec_cross_section','cell_field',t('5024 个体积细丝的冻结 Jz；方形离散截面。自由度不等于绝缘股数。','Frozen Jz of 5024 volume filaments on a square-cell cross-section; degrees of freedom are not insulated strands.'),field['source_model'],field['source_run_id'],
            data_file=str(source),value_key='values',x_label='x (mm)',y_label='y (mm)',color_label='|Jz| (A/mm²)',minimum=0,maximum=max(field['values']))
        source=run/'field_data/rt0_slice.json';field=b.read(source)
        for id,key,label in [('rt0_loss_slice','values','p (W/cm³)'),('rt0_J_slice','J_magnitude_A_per_mm2','|J| (A/mm²)')]:
            add(lang,id,'cell_field',t(f'面通量重构切面 z={field["z_mm"]:.6f} mm；零净输运、1 mT RMS 外场。损耗取完整局部 RT0 积分。',f'Face-flux reconstructed section at z={field["z_mm"]:.6f} mm; zero net transport, 1 mT RMS imposed field. Loss uses the exact local RT0 integral.'),field['source_model'],field['source_run_id'],
                data_file=str(source),value_key=key,x_label='x (mm)',y_label='y (mm)',color_label=label,minimum=0,maximum=max(field[key]))
        add(lang,'rt0_vectors','field3d',t('RT0 抽样三维电流；箭头为相位零实部，统一长度缩放，颜色为复 RMS 范数。','Sampled RT0 current; arrows show the real part at phase zero with a common length scale, while color gives the complex RMS norm.'),field['source_model'],field['source_run_id'],
            data_file=str(source),points_mm=field['centers_mm'],value_key='vector_magnitudes_A_per_mm2',color_label='|J| (A/mm²)',minimum=0,maximum=max(field['vector_magnitudes_A_per_mm2']))
        cases=b.csv_rows(run/'tables/rt0_cases.csv');q14=[r for r in cases if r['q']=='14']
        curve(lang,'rt0_spatial',t('体素单元数','Voxel cells'),t('外场损耗 (mW)','Imposed-field loss (mW)'),[series('q14',[[int(r['cells']),1000*float(r['recomputed_loss_W'])] for r in q14])],
            t('固定 1×1×2 mm 铜长方体，200 kHz、1 mT RMS 外场、零净输运；此损耗不是 Litz 输运 Rac。','Fixed 1×1×2 mm copper cuboid, 200 kHz, 1 mT RMS imposed field, zero net transport; this loss is not Litz transport Rac.'),'frozen_RT0_CSV_campaign_arithmetic','closure_20261005_rt0_campaign_collect_01')
        source=run/'field_data/aphi_samples.json';field=b.read(source)
        for id,key,label in [('aphi_J_samples','J_magnitude_A_per_mm2','|J| (A/mm²)'),('aphi_A_samples','A_magnitude_T_m','|A| (T m)'),('aphi_phi_samples','phi_magnitude_V','|φ| (V)'),('aphi_gradient_samples','gradient_phi_V_per_m','|∇φ| (V/m)')]:
            add(lang,id,'field3d',t('原保存场的 128 个指定节点样本；物理验收未通过。样本不插值成连续表面，不称为全场最大值。','128 explicitly identified preserved-field samples; physical acceptance remains failed. Samples are neither interpolated into a continuous surface nor treated as a whole-field maximum.'),field['source_model'],field['source_run_id'],acceptance='failed_numerical',
                data_file=str(source),value_key=key,color_label=label,minimum=0,maximum=max(field[key]))
        comparisons=[series(metric,[[int(r['nodes']),float(r['actual_over_tolerance'])] for r in aphi if r['metric']==metric],color) for metric,color in [('J_Bessel','#265B8F'),('phi','#B86C35'),('gauge','#57775B')]]
        curve(lang,'aphi_gates',t('节点数','Nodes'),t('误差 / 门槛','Error / threshold'),comparisons,t('原门槛保持；三档 φ 与规范均未通过，制造解通过不升级物理解。','Original thresholds retained; φ and gauge fail on all three meshes, and manufactured-solution success does not upgrade physical acceptance.'),'actual_preserved_A_phi_cylinder_fields','rerun_20261005_fem3_cylinder_report',acceptance='failed_numerical',scaling=['Log10','Log10'],reference_lines=[1])
        curve(lang,'gpu_equivalence',t('自由度','Degrees of freedom'),t('相对差','Relative difference'),[series('L',[[int(r['filaments']),float(r['L_matrix_relative_error'])] for r in gpu]),series(t('复电流','Complex current'),[[int(r['filaments']),float(r['current_relative_error'])] for r in gpu],'#B86C35')],
            t('历史同模型 CPU/GPU 比较，门槛 10⁻¹⁰；本轮只读数据。算法等价不证明物理完整。','Archived same-model CPU/GPU comparison at 10⁻¹⁰; this build reads data only. Algorithmic equivalence does not establish physical completeness.'),'physical_longitudinal_PEEC_CPU_GPU_cross_validation',[r['source_run_id'] for r in gpu],scaling=[None,'Log10'],reference_lines=[1e-10])
        origins=sorted({r['source_run_id'] for r in resources})
        names={'closure_20261005_gpu_m80_01':'CPU/GPU 5024','closure_20261005_peec_m80_l064_self12p10_01':'PEEC 5024','closure_20261005_rt0_n24_q14_01':'RT0 27648'}
        resource_series=[dict(series(names.get(origin,origin),[[float(r['elapsed_seconds']),float(r['working_GiB'])] for r in resources if r['source_run_id']==origin],['#265B8F','#B86C35','#57775B'][k%3]),source_run_id=origin) for k,origin in enumerate(origins)]
        curve(lang,'resource_memory',t('用时 (s)','Elapsed time (s)'),t('采样内存 (GiB)','Sampled working set (GiB)'),resource_series,
            t('仅有效所属进程树采样；短峰值可能遗漏，混合 PID 记录排除。不同路线不作速度排名。','Only valid owned-process-tree samples; short peaks may be missed and mixed-PID records are excluded. Different routes are not ranked by speed.'),'sampled_owned_process_tree_resource_observation',origins)
        curve(lang,'ansys_seven_current',t('物理股线身份','Physical strand ID'),'|ik| (A RMS)',[series('7',[[int(r['strand_id']),float(r['Abs_I_RMS_A'])] for r in ansys])],
            t('历史有效七股共端短测，704 单元；单档有限验证。新三档/接口失败另列。','Historical valid seven-strand common-port short test, 704 cells; single-level limited validation. Failed new precision/interface attempts remain separate.'),'Ansys_Maxwell2D_common_voltage_port_short_test',ansys[0]['source_run_id'],acceptance='limited_single_mesh_validation')
        from PublicationDiagrams import diagram
        add(lang,'ansys_limits','schematic',b.read(b.ROOT/'manuscript/publication.json')['figures']['ansys_limits']['title'][lang],'explicit_physical_model_relationships','publication_design',acceptance='conceptual_diagram',**diagram('ansys_limits',lang))
    request['panels']=panels;request['publication_scope']='full panel collection; frozen physical status unchanged'
    request['composition_groups']=[['q1_profile',['q1_magnitude','q1_phase']],['coax640_currents',['coax640_current','coax640_phase']],['coax640_fields',['coax640_field','coax640_field_phase']],['peec_validation',['peec_length','peec_sensitivity']],['rt0_sections',['rt0_loss_slice','rt0_J_slice']],['aphi_preserved',['aphi_A_samples','aphi_phi_samples','aphi_J_samples','aphi_gradient_samples']],['geometry_comparison',['geometry_straight','geometry_single','multilevel_detail','geometry_crosslayer']]]
    b.write(run/'render_request.json',request)
    manifest=b.read(run/'source_manifest.json');manifest.update(field_sources_sha256=evidence['sources_sha256'],additional_sources_sha256=sources,reconstructed_fields_sha256=evidence['outputs_sha256'],style_reference_run_id='publication_20261006_specimen_08',user_revision='调整每个图的宽一致',single_panel_width_mm=88.9,composite_width_mm=182,notebook_single_panel_width_pt=310)
    b.write(run/'source_manifest.json',manifest)
