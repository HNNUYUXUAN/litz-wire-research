(* Independent verification of ORIGINAL stage archives, not exporter self-readback.
   No model packages, field solvers, kernels, quadrature, FEM or GPU are loaded.
   One explicit case WXF is read at a time; original sources are never rewritten. *)
$HistoryLength=0;$CharacterEncoding="UTF8";
vfRoot=DirectoryName[DirectoryName[$InputFileName]];
vfArg[key_String]:=Module[{positions=Flatten[Position[$ScriptCommandLine,key]]},If[Length[positions]==1&&First[positions]<Length[$ScriptCommandLine],$ScriptCommandLine[[First[positions]+1]],Missing["Argument"]]];
vfReferences=vfArg["--reference-runs"];If[!StringQ[vfReferences],vfReferences=Environment["LITZ_CLOSURE_REFERENCE_RUNS"]];
vfOutput=vfArg["--output"];If[!StringQ[vfOutput],vfOutput=Environment["LITZ_FROZEN_VERIFY_OUTPUT_DIR"]];
If[!StringQ[vfReferences]||vfReferences===""||!StringQ[vfOutput]||vfOutput==="",Print["Explicit --reference-runs and fresh --output are required (or LITZ_CLOSURE_REFERENCE_RUNS / LITZ_FROZEN_VERIFY_OUTPUT_DIR)"];Exit[2]];
vfRunIDs=DeleteDuplicates[DeleteCases[StringTrim/@StringSplit[vfReferences,","],""]];
If[Length[vfRunIDs]==0||!AllTrue[vfRunIDs,StringMatchQ[#,RegularExpression["[A-Za-z0-9_-]+"]]&],Print["Invalid explicit ReferenceRuns"];Exit[2]];
If[!StringMatchQ[vfOutput,LetterCharacter~~":"~~Alternatives["\\","/"]~~___]&&!StringStartsQ[vfOutput,{"\\\\","/"}],vfOutput=FileNameJoin[{vfRoot,vfOutput}]];
vfOutput=ExpandFileName[vfOutput];
If[DirectoryQ[vfOutput]||FileExistsQ[vfOutput],Print["Use a new unique validation output directory"];Exit[2]];
If[!StringStartsQ[ToLowerCase[StringReplace[vfOutput,"\\"->"/"]],ToLowerCase[StringReplace[FileNameJoin[{vfRoot,"outputs"}],"\\"->"/"]]<>"/"],Print["Validation output must be inside project outputs"];Exit[2]];
CreateDirectory[vfOutput];CreateDirectory[FileNameJoin[{vfOutput,"cases"}]];
vfBudgetText=vfArg["--memory-budget-bytes"];If[!StringQ[vfBudgetText],vfBudgetText=Environment["LITZ_FROZEN_VERIFY_RAM_BYTES"]];
vfBudget=If[StringQ[vfBudgetText]&&StringMatchQ[vfBudgetText,DigitCharacter..],ToExpression[vfBudgetText],4 1024^3];
If[!IntegerQ[vfBudget]||vfBudget<=0||vfBudget>8 1024^3,Print["Read-only verifier budget must be positive and <=8 GiB; PEEC/RT0 cases remain capped at4 GiB"];Exit[2]];
vfAbs=10.^-30;vfRel=2.*^-14;vfStart=AbsoluteTime[];
vfRelPath[p_String]:=StringReplace[FileNameDrop[p,FileNameDepth[vfRoot]],"\\"->"/"];
vfJSON[p_,v_]:=If[Quiet[Check[Export[p,v,"RawJSON"],$Failed]]===$Failed,Print["JSON report write failed: ",p];Exit[2]];
vfFiniteQ[x_]:=NumberQ[x]&&FreeQ[x,Indeterminate|_DirectedInfinity];
vfNumber[x_?NumberQ]:=x;
vfNumber[x_String]:=If[StringMatchQ[x,RegularExpression["[-+]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][-+]?[0-9]+|\\*\\^[-+]?[0-9]+)?"]],ToExpression[StringReplace[x,RegularExpression["[eE]"]->"*^"]],$Failed];
vfNumber[_]:=$Failed;
vfPointer[p_]:=Module[{stream=OpenRead[p,BinaryFormat->True],prefix},prefix=BinaryReadList[stream,"Byte",Min[256,FileByteCount[p]]];Close[stream];StringStartsQ[FromCharacterCode[prefix],"version https://git-lfs.github.com/spec/v1"]];
vfFile[p_,role_]:=Module[{record,hash},If[!FileExistsQ[p]||DirectoryQ[p],Throw[<|"reason"->"missing_original_source_file","path"->vfRelPath[p]|>]];
 If[vfPointer[p],Throw[<|"reason"->"unresolved_original_LFS_pointer","path"->vfRelPath[p]|>]];
 hash=Quiet[Check[FileHash[p,"SHA256","HexString"],$Failed]];If[!StringQ[hash],Throw[<|"reason"->"original_source_hash_read_failed","path"->vfRelPath[p]|>]];
 record=<|"path"->vfRelPath[p],"role"->role,"sha256"->hash,"bytes"->FileByteCount[p]|>;
 If[!AnyTrue[vfSources,#["path"]===record["path"]&],AppendTo[vfSources,record]];record];
vfReadJSON[p_,role_]:=Module[{value},vfFile[p,role];value=Quiet[Check[Import[p,"RawJSON"],$Failed]];If[!AssociationQ[value],Throw[<|"reason"->"invalid_original_JSON","path"->vfRelPath[p]|>]];value];
vfReadCSV[p_,header_]:=Module[{value},vfFile[p,"original_stage_numeric_CSV"];value=Quiet[Check[Import[p,"CSV"],$Failed]];
 If[!ListQ[value]||Length[value]<1||First[value]=!=header,Throw[<|"reason"->"original_CSV_header_mismatch","path"->vfRelPath[p]|>]];
 value=Map[vfNumber,Rest[value],{2}];If[!MatrixQ[value,vfFiniteQ]||!AllTrue[value,Length[#]===Length[header]&],Throw[<|"reason"->"original_CSV_not_numeric_or_wrong_column_count","path"->vfRelPath[p]|>]];value];
vfPairs[v_List]:=Transpose[{Re[v],Im[v]}];vfPair[v_]:={Re[v],Im[v]};
vfRequired[a_Association,key_]:=If[KeyExistsQ[a,key],a[key],Throw[<|"reason"->"missing_original_numerical_field","key"->key|>]];
vfRequired[a_,key_]:=Throw[<|"reason"->"original_field_parent_not_Association","key"->key,"parent_head"->ToString[Head[a]]|>];
vfCheckIdentity[id_,expected_,actual_,source_]:=Module[{pass=expected===actual},AppendTo[vfChecks,<|"id"->id,"execution_status"->If[pass,"passed","failed"],"kind"->"exact_identity","expected"->expected,"actual"->actual,"source"->source|>]];
vfCompare[id_,expected_,actual_,unit_,source_,abs_:vfAbs,rel_:vfRel,exact_:False]:=Module[{a,b,errors,normalized,passed,record,bad},
 If[Dimensions[expected]=!=Dimensions[actual],AppendTo[vfChecks,<|"id"->id,"execution_status"->"failed","kind"->"numerical_agreement","reason"->"shape_mismatch","expected_dimensions"->Dimensions[expected],"actual_dimensions"->Dimensions[actual],"unit"->unit,"source"->source|>];Return[Null]];
 a=Flatten[{expected}];b=Flatten[{actual}];If[!AllTrue[Join[a,b],vfFiniteQ],Throw[<|"reason"->"nonfinite_or_nonnumeric_original_field","check_id"->id|>]];
 errors=Abs[a-b];normalized=MapThread[#1/(abs+rel Abs[#2])&,{errors,a}];
 passed=If[TrueQ[exact],a===b,TrueQ[Max[Append[normalized,0.]]<=1.]];
 bad=Take[Flatten[Position[If[TrueQ[exact],MapThread[SameQ,{a,b}],Thread[normalized<=1.]],False]],UpTo[8]];
 record=<|"id"->id,"execution_status"->If[passed,"passed","failed"],"kind"->If[TrueQ[exact],"exact_numerical_identity","numerical_agreement"],"values_compared"->Length[a],"dimensions"->Dimensions[expected],"unit"->unit,"source"->source,
  "maximum_absolute_error"->Max[Append[errors,0.]],"maximum_relative_error"->Max[Append[MapThread[#1/Max[Abs[#2],10.^-300]&,{errors,a}],0.]],"maximum_normalized_error"->Max[Append[normalized,0.]],"absolute_tolerance"->abs,"relative_tolerance"->rel,
  "first_mismatch_values"->Map[<|"flat_index_1based"->#,"original"->a[[#]],"saved_output"->b[[#]]|>&,bad]|>;
 AppendTo[vfChecks,record]];
vfSavedScalar[id_,expected_,summary_,key_,unit_,source_]:=vfCompare[id,expected,vfRequired[summary,key],unit,source<>" vs case.json:"<>key];
vfRunProvenance[source_,kind_]:=Module[{paths,manifest,snap,name,result,process,critical,names,operatorSnapshot},
 paths=Select[FileNameJoin[{source,#}]&/@{"environment.json","process_status.json","run_manifest.json","dispatch_manifest.json","results.json","test_report.json","model_assumptions.md","wrapper_resource_observation.json"},FileExistsQ];
 Scan[vfFile[#,"original_run_provenance"]&,paths];
 If[!FileExistsQ[FileNameJoin[{source,"run_manifest.json"}]],Throw[<|"reason"->"missing_original_before_stage_source_manifest"|>]];
 manifest=Import[FileNameJoin[{source,"run_manifest.json"}],"RawJSON"];
 If[!AssociationQ[manifest],Throw[<|"reason"->"invalid_original_before_stage_source_manifest"|>]];
 critical=Switch[kind,"PEEC",{"src/PEEC.wl","src/NotebookPhysics.wl","src/stages/closure_peec.wl"},"GPU",{"src/PEEC.wl","src/NotebookPhysics.wl","src/stages/closure_gpu.wl","src/GPUVolumeFarKernel.wl"},_,{"src/VoxelOperator.wl","src/VoxelPEEC.wl","src/stages/closure_rt0.wl"}];
 If[kind==="RT0",operatorSnapshot=FileNameJoin[{source,"source_snapshot","src","VoxelOperator.wl"}];
  If[FileExistsQ[operatorSnapshot]&&StringContainsQ[Import[operatorSnapshot,"Text"],"VoxelOperatorParallel.wl"],AppendTo[critical,"src/VoxelOperatorParallel.wl"]]];
 names=StringReplace[Lookup[#,"path",""],"\\"->"/"]&/@Lookup[manifest,"sources",{}];
 vfCheckIdentity["required_model_source_snapshot_declarations",True,AllTrue[critical,MemberQ[names,#]&],"original run_manifest.json"];
  Do[name=StringReplace[Lookup[item,"path",""],"\\"->"/"];
   If[MemberQ[critical,name],
    snap=FileNameJoin[{source,"source_snapshot",Sequence@@StringSplit[name,"/"]}];vfFile[snap,"original_model_source_before_stage"];vfCheckIdentity["snapshot_hash_"<>StringReplace[name,"/"->"_"],ToLowerCase[Lookup[item,"sha256",""]],ToLowerCase[FileHash[snap,"SHA256","HexString"]],"original run_manifest.json declaration"]],
   {item,Lookup[manifest,"sources",{}]}];
 result=If[FileExistsQ[FileNameJoin[{source,"results.json"}]],Import[FileNameJoin[{source,"results.json"}],"RawJSON"],<||>];
 process=If[FileExistsQ[FileNameJoin[{source,"process_status.json"}]],Import[FileNameJoin[{source,"process_status.json"}],"RawJSON"],<||>];
 If[!AssociationQ[result],result=<||>];If[!AssociationQ[process],process=<||>];
 <|"original_run_execution_status"->Lookup[result,"execution_status","not_recorded"],"original_run_physical_acceptance_status"->Lookup[result,"physical_acceptance_status","not_recorded"],"original_run_failure_reason"->Lookup[result,"failure_reason",Null],"original_process_exit_code"->Lookup[process,"process_exit_code",Null],"original_process_exit_missing"->!KeyExistsQ[process,"process_exit_code"]||Lookup[process,"process_exit_code",Null]===Null|>];

vfVerifyPEEC[payload_,summary_,parameters_,runParameters_,caseDir_]:=Module[{model,solution,currents,centers,h,len,area,sigma,total,voltage,csv,rdc,resistance,diagonal,joule,source},
 model=vfRequired[payload,"model"];solution=vfRequired[model,"solution"];
 currents=vfRequired[solution,"currents"];centers=vfRequired[model,"centers_m"];h=vfRequired[model,"cell_width_m"];len=vfRequired[model,"length_m"];area=vfRequired[model,"area_m2"];
 sigma=vfRequired[runParameters,"conductivity_S_per_m"];total=vfRequired[runParameters,"total_current_RMS_A"];voltage=vfRequired[solution,"voltage"];source="original model.wxf:model";
 vfCheckIdentity["source_model_identity",vfRequired[model,"source_model"],vfRequired[summary,"source_model"],source];
 vfCompare["SI_conductivity",5.8*^7,sigma,"S/m","closure_peec_parameters.json"];
 vfCompare["RMS_total_current",20,total,"A RMS","closure_peec_parameters.json"];
 vfCompare["SI_frequency",200000,vfRequired[runParameters,"frequency_Hz"],"Hz","closure_peec_parameters.json"];
 vfCompare["mu_r",1,vfRequired[runParameters,"relative_permeability"],"dimensionless","closure_peec_parameters.json"];
 vfCompare["temperature",20,vfRequired[runParameters,"temperature_C"],"degC","closure_peec_parameters.json"];
 vfCheckIdentity["phasor_convention","exp(+j omega t)",vfRequired[runParameters,"phasor"],"closure_peec_parameters.json"];
 vfCompare["filament_count",Length[currents],vfRequired[model,"filaments"],"count",source,vfAbs,vfRel,True];
 vfCompare["filament_count_JSON",Length[currents],vfRequired[summary,"filaments"],"count",source,vfAbs,vfRel,True];
 vfCompare["filament_centers_shape",{Length[currents],2},Dimensions[centers],"count",source,vfAbs,vfRel,True];
 vfCompare["cross_divisions",vfRequired[model,"cross_divisions"],vfRequired[summary,"m"],"count",source,vfAbs,vfRel,True];
 vfCompare["quadrature_order",vfRequired[model,"mutual_quadrature_order"],vfRequired[summary,"q"],"count",source,vfAbs,vfRel,True];
 vfCompare["self_accuracy_goal",vfRequired[model,"self_accuracy_goal"],vfRequired[summary,"ag"],"digits",source,vfAbs,vfRel,True];
 vfCompare["self_precision_goal",vfRequired[model,"self_precision_goal"],vfRequired[summary,"pg"],"digits",source,vfAbs,vfRel,True];
 vfCompare["axial_length_parameter",len,vfRequired[parameters,"length_m"],"m axial",source];
 vfSavedScalar["axial_length_JSON",len,summary,"axial_length_m","m axial",source];
 vfSavedScalar["cell_width_JSON",h,summary,"cell_width_m","m",source];
 vfSavedScalar["copper_area_JSON",area,summary,"nominal_copper_area_m2","m^2",source];
 vfCompare["original_square_filament_area_identity",Length[currents] h^2,area,"m^2",source];
 vfSavedScalar["copper_volume_JSON",area len,summary,"copper_volume_m3","m^3",source];
 vfSavedScalar["uniform_longitudinal_arc_length",1.,summary,"arc_length_growth","dimensionless",source];
 vfCompare["every_current_ReIm_WXF_to_JSON",vfPairs[currents],vfRequired[summary,"currents_RMS_A_ReIm"],"A RMS",source<>".solution.currents vs case.json"];
 csv=vfReadCSV[FileNameJoin[{caseDir,"currents.csv"}],{"x_m","y_m","current_RMS_A_real","current_RMS_A_imag","Jz_RMS_A_per_m2_real","Jz_RMS_A_per_m2_imag"}];
 vfCompare["every_center_WXF_to_CSV",centers,csv[[All,1;;2]],"m",source<>".centers_m vs currents.csv"];
 vfCompare["every_current_ReIm_WXF_to_CSV",vfPairs[currents],csv[[All,3;;4]],"A RMS",source<>".solution.currents vs currents.csv"];
 vfCompare["every_Jz_WXF_to_CSV",vfPairs[currents/h^2],csv[[All,5;;6]],"A RMS/m^2",source<>".solution.currents / original h^2 vs currents.csv"];
 vfSavedScalar["port_voltage_ReIm_WXF_to_JSON",vfPair[voltage],summary,"port_voltage_RMS_V_ReIm","V RMS",source<>".solution.voltage"];
 vfSavedScalar["loss_WXF_to_JSON",vfRequired[solution,"loss_W"],summary,"loss_W_segment","W",source<>".solution.loss_W"];
 vfSavedScalar["loss_per_axial_m_identity",vfRequired[solution,"loss_W"]/len,summary,"loss_W_per_axial_m","W/axial_m",source];
 rdc=len/(sigma area);
 vfSavedScalar["Rdc_segment_identity",rdc,summary,"Rdc_segment_ohm","ohm",source<>" length/(sigma*area)"];
 vfSavedScalar["Rdc_per_axial_m_identity",rdc/len,summary,"Rdc_ohm_per_axial_m","ohm/axial_m",source];
 vfSavedScalar["Rac_WXF_to_JSON",vfRequired[model,"Rac_ohm_per_axial_m"],summary,"Rac_ohm_per_axial_m","ohm/axial_m",source];
 vfCompare["transport_Rac_from_loss_identity",vfRequired[solution,"loss_W"]/(Abs[total]^2 len),vfRequired[model,"Rac_ohm_per_axial_m"],"ohm/axial_m",source];
 vfSavedScalar["Rac_over_Rdc_identity",vfRequired[model,"Rac_ohm_per_axial_m"]/(rdc/len),summary,"Rac_over_Rdc","dimensionless",source];
 vfSavedScalar["complex_current_deviation_identity",Norm[currents-total/Length[currents]]/Norm[currents],summary,"complex_filament_current_deviation_L2","dimensionless",source];
 vfSavedScalar["stored_Bessel_comparison",vfRequired[model,"Bessel_equal_area_Rac_ohm_per_m"],summary,"Bessel_equal_area_Rac_ohm_per_m","ohm/axial_m",source<>" stored Bessel reference; no new analytic evaluation"];
 vfSavedScalar["stored_Bessel_relative_error",vfRequired[model,"Bessel_Rac_relative_error"],summary,"Bessel_Rac_relative_error","dimensionless",source];
 Scan[vfCompare["residual_"<>#,vfRequired[solution,#],vfRequired[vfRequired[summary,"residuals"],#],"dimensionless",source<>".solution vs case.json.residuals"]&,{"linear_residual","current_residual","common_voltage_residual","power_residual"}];
 resistance=vfRequired[model,"resistance_matrix_ohm"];
 vfCheckIdentity["resistance_is_saved_sparse_diagonal",True,Head[resistance]===SparseArray&&Length[resistance["NonzeroValues"]]===Length[currents],source<>".resistance_matrix_ohm"];
 If[Head[resistance]===SparseArray,diagonal=Normal[Diagonal[resistance]];
  vfCompare["every_saved_filament_resistance_identity",ConstantArray[len/(sigma h^2),Length[currents]],diagonal,"ohm",source<>".resistance_matrix_ohm diagonal"];
  joule=Re[Conjugate[currents].(diagonal currents)];
  vfCompare["independent_Joule_from_saved_R_and_currents",joule,vfRequired[solution,"loss_W"],"W",source<>" sum R_i |I_i|^2",10.^-20,10.^-10]];
 vfCompare["transport_sum_current_identity",{total,0.},vfPair[Total[currents]],"A RMS",source<>" sum saved currents",10.^-12,10.^-8];
 vfCompare["stored_port_impedance_identity",vfPair[voltage/total],vfPair[vfRequired[solution,"impedance"]],"ohm",source];
 vfCompare["stored_input_power_identity",Re[voltage Conjugate[total]],vfRequired[solution,"input_W"],"W",source,10.^-20,10.^-10];
 vfCompare["no_independent_external_source",0.,vfRequired[solution,"external_source_absorbed_W"],"W",source,10.^-20,10.^-10];
 Clear[model,solution,currents,centers,resistance,diagonal,csv];
 <|"basis"->"longitudinal volume filaments","phasor"->"exp(+j omega t)","current_convention"->"RMS","JSON_vector_coverage"->"every original filament current Re/Im; original CSV additionally includes centre/Jz","Rac_status"->"transport P/(|I|^2 axial_length) is applicable in this saved zero-external-source model","new_physics_solved"->False|>
];

vfVerifyGPU[cpu_,gpu_,summary_,parameters_,caseDir_]:=Module[{solution,cpuCurrents,gpuCurrents,cpuL,gpuL,centers,h,len,area,sigma=5.8*^7,total,freq,voltage,cpuVoltage,csv,resistance,diagonal,power,cpuPower,rdc,difference2=0.,reference2=0.,matrixError,currentError,powerResidual,linearResidual,first,last,block,baseBlock,maxDifference=0.,source="original CPU_model.wxf and GPU_solution.wxf",n},
 solution=vfRequired[cpu,"solution"];cpuCurrents=vfRequired[solution,"currents"];gpuCurrents=vfRequired[gpu,"currents_RMS_A"];voltage=vfRequired[gpu,"voltage_RMS_V"];
 centers=vfRequired[cpu,"centers_m"];h=vfRequired[cpu,"cell_width_m"];len=vfRequired[cpu,"length_m"];area=vfRequired[cpu,"area_m2"];total=vfRequired[parameters,"total_current_RMS_A"];freq=vfRequired[parameters,"frequency_Hz"];n=Length[cpuCurrents];cpuVoltage=vfRequired[solution,"voltage"];
 vfCheckIdentity["parameter_units","SI",vfRequired[parameters,"units"],"original parameters.json"];
 vfCheckIdentity["summary_units","SI RMS",vfRequired[summary,"units"],"original gpu_case.json"];
 vfCheckIdentity["phasor_convention","exp(+j omega t)",vfRequired[parameters,"phasor"],"original parameters.json"];
 vfCompare["frequency_Hz",200000.,freq,"Hz","original parameters.json"];
 vfCompare["total_current_RMS_A",20.,total,"A RMS","original parameters.json"];
 vfCompare["CPU_GPU_filament_count",n,Length[gpuCurrents],"count",source,vfAbs,vfRel,True];
 vfSavedScalar["filaments_WXF_to_JSON",n,summary,"filaments","count",source];
 vfCompare["cross_divisions_WXF_to_JSON",vfRequired[cpu,"cross_divisions"],vfRequired[summary,"cross_divisions"],"count",source,vfAbs,vfRel,True];
 vfCompare["cross_divisions_parameter",vfRequired[cpu,"cross_divisions"],vfRequired[parameters,"cross_divisions"],"count",source,vfAbs,vfRel,True];
 vfCompare["quadrature_order_parameter",vfRequired[cpu,"mutual_quadrature_order"],vfRequired[parameters,"mutual_quadrature_order"],"count",source,vfAbs,vfRel,True];
 vfCompare["length_parameter",len,vfRequired[parameters,"length_m"],"m axial",source];
 vfSavedScalar["length_WXF_to_JSON",len,summary,"length_m","m axial",source];
 vfSavedScalar["actual_area_WXF_to_JSON",area,summary,"actual_area_m2","m^2",source];
 vfSavedScalar["copper_volume_identity",area len,summary,"copper_volume_m3","m^3",source];
 vfCompare["all_GPU_currents_WXF_to_JSON",vfPairs[gpuCurrents],vfRequired[summary,"currents_Re_Im_A"],"A RMS","original GPU_solution.wxf currents_RMS_A vs gpu_case.json"];
 csv=vfReadCSV[FileNameJoin[{caseDir,"currents.csv"}],{"filament_id","x_m","y_m","GPU_current_real_RMS_A","GPU_current_imag_RMS_A","GPU_current_abs_RMS_A","GPU_current_phase_rad","CPU_current_real_RMS_A","CPU_current_imag_RMS_A"}];
 vfCompare["every_original_filament_id",Range[n],csv[[All,1]],"1-based integer index",source<>" vs currents.csv",vfAbs,vfRel,True];
 vfCompare["every_original_center",centers,csv[[All,2;;3]],"m","original CPU_model.wxf centers_m vs currents.csv"];
 vfCompare["every_GPU_current_ReIm",vfPairs[gpuCurrents],csv[[All,4;;5]],"A RMS","original GPU_solution.wxf currents_RMS_A vs currents.csv"];
 vfCompare["every_GPU_current_abs",Abs[gpuCurrents],csv[[All,6]],"A RMS","original GPU_solution.wxf currents_RMS_A vs currents.csv"];
 vfCompare["every_GPU_current_phase",Arg[gpuCurrents],csv[[All,7]],"rad","original GPU_solution.wxf currents_RMS_A vs currents.csv"];
 vfCompare["every_CPU_current_ReIm",vfPairs[cpuCurrents],csv[[All,8;;9]],"A RMS","original CPU_model.wxf solution.currents vs currents.csv"];
 vfCompare["GPU_voltage_ReIm_WXF_to_JSON",vfPair[voltage],{vfRequired[summary,"voltage_real_RMS_V"],vfRequired[summary,"voltage_imag_RMS_V"]},"V RMS","original GPU_solution.wxf voltage_RMS_V vs gpu_case.json"];
 resistance=vfRequired[cpu,"resistance_matrix_ohm"];
 vfCheckIdentity["saved_CPU_R_is_sparse_diagonal",True,Head[resistance]===SparseArray&&Length[resistance["NonzeroValues"]]===n,source];
 If[Head[resistance]=!=SparseArray,Throw[<|"reason"->"original_GPU_CPU_resistance_not_sparse"|>]];diagonal=Normal[Diagonal[resistance]];
 vfCompare["every_saved_CPU_filament_resistance_identity",ConstantArray[len/(sigma h^2),n],diagonal,"ohm",source<>" frozen src/PEEC.wl sigma and geometry"];
 cpuPower=Re[Conjugate[cpuCurrents].(diagonal cpuCurrents)];power=Re[Conjugate[gpuCurrents].(diagonal gpuCurrents)];
 vfCompare["CPU_saved_Joule_power_identity",cpuPower,vfRequired[solution,"loss_W"],"W",source,10.^-20,10.^-10];
 vfCompare["CPU_saved_input_power_identity",Re[cpuVoltage Conjugate[total]],vfRequired[solution,"input_W"],"W",source,10.^-20,10.^-10];
 vfCompare["CPU_saved_impedance_voltage_identity",vfPair[cpuVoltage/total],vfPair[vfRequired[solution,"impedance"]],"ohm",source];
 vfSavedScalar["GPU_Joule_power_identity_to_JSON",power,summary,"loss_W","W",source<>" saved diagonal R and GPU currents"];
 rdc=len/(sigma area);vfSavedScalar["Rdc_identity_to_JSON",rdc,summary,"Rdc_ohm","ohm",source];
 vfSavedScalar["GPU_Rac_identity_to_JSON",power/(Abs[total]^2 len),summary,"Rac_ohm_per_axial_m","ohm/axial_m",source];
 vfCompare["CPU_saved_Rac_identity",cpuPower/(Abs[total]^2 len),vfRequired[cpu,"Rac_ohm_per_axial_m"],"ohm/axial_m",source,10.^-20,10.^-10];
 vfSavedScalar["CPU_Bessel_comparison_WXF_to_JSON",vfRequired[cpu,"Bessel_Rac_relative_error"],summary,"Bessel_Rac_relative_error","dimensionless",source];
 currentError=Norm[gpuCurrents-cpuCurrents]/Norm[cpuCurrents];vfSavedScalar["saved_CPU_GPU_current_error_identity",currentError,summary,"current_relative_error","dimensionless",source];
 powerResidual=Abs[Re[voltage Conjugate[total]]-power]/power;
 (* Near roundoff, changing the summation implementation changes the tiny
    residual. Preserve the saved value and compare using an absolute FP64 bound. *)
 vfCompare["saved_GPU_power_residual_identity",powerResidual,vfRequired[summary,"power_residual"],"dimensionless",source,10.^-13,10.^-10];
 vfCompare["GPU_total_current_identity",{total,0.},vfPair[Total[gpuCurrents]],"A RMS",source,10.^-12,10.^-8];
 cpuL=vfRequired[cpu,"partial_inductance_matrix_H"];gpuL=vfRequired[gpu,"partial_inductance_matrix_H"];
 vfCompare["saved_CPU_L_dimensions",{n,n},Dimensions[cpuL],"count",source,vfAbs,vfRel,True];
 vfCompare["saved_GPU_L_dimensions",{n,n},Dimensions[gpuL],"count",source,vfAbs,vfRel,True];
 If[Dimensions[cpuL]=!={n,n}||Dimensions[gpuL]=!={n,n},Throw[<|"reason"->"saved_inductance_matrix_shape_mismatch"|>]];
 (* Bounded row blocks compare ALL saved L entries. No integral or solve. *)
 Do[last=Min[n,first+127];baseBlock=cpuL[[first;;last]];block=gpuL[[first;;last]]-baseBlock;
  difference2+=Norm[Flatten[block]]^2;reference2+=Norm[Flatten[baseBlock]]^2;maxDifference=Max[maxDifference,Max[Abs[Flatten[block]]]];Clear[block,baseBlock],{first,1,n,128}];
 matrixError=Sqrt[difference2/reference2];
 (* This recomputes a norm ratio; it is not a direct serialized scalar readback.
    Original stage: Norm[Flatten[GPU_L-CPU_L]]/Norm[Flatten[CPU_L]].
    Here bounded 128-row blocks sum squared norms before the square root.
    Machine-real reduction order differs; relative 1e-12 applies ONLY here.
    Direct WXF/JSON/CSV agreement remains vfRel=2e-14 and the saved physical
    CPU/GPU L-matrix acceptance threshold remains 1e-10. *)
 vfCompare["saved_CPU_GPU_full_L_matrix_error_identity",matrixError,vfRequired[summary,"L_matrix_relative_error"],"dimensionless",source<>" all original n*n H entries; bounded row-block Frobenius norm vs case.json:L_matrix_relative_error",10.^-30,10.^-12];
 vfChecks[[-1]]=Join[Last[vfChecks],<|"kind"->"arithmetic_reduction_agreement","original_formula"->"Norm[Flatten[GPU_L-CPU_L]]/Norm[Flatten[CPU_L]]","verification_formula"->"Sqrt[Sum[Norm[Flatten[128_row_difference_block]]^2]/Sum[Norm[Flatten[128_row_CPU_block]]^2]]","tolerance_reason"->"Machine-real floating-point norm reduction order differs; this tolerance does not apply to direct stored values or physical matrix acceptance","direct_value_relative_tolerance"->vfRel,"saved_physical_matrix_error_threshold"->10.^-10|>];
 linearResidual=Norm[Join[diagonal gpuCurrents+I 2 Pi freq (gpuL.gpuCurrents)-voltage,{Total[gpuCurrents]-total}]]/Abs[total];
 vfCompare["saved_GPU_linear_residual_identity",linearResidual,vfRequired[summary,"linear_residual"],"dimensionless",source<>" saved R/L/current/V multiplication only; no solve",10.^-13,10.^-8];
 Clear[cpuL,gpuL,solution,cpuCurrents,gpuCurrents,centers,csv,resistance,diagonal];
 <|"basis"->"saved CPU/GPU longitudinal volume-filament PEEC","phasor"->"exp(+j omega t)","current_convention"->"RMS","conductivity_origin"->"5.8e7 S/m in hashed before-stage src/PEEC.wl; original GPU parameters do not have a numeric conductivity field","JSON_vector_coverage"->"GPU every Re/Im; CPU every Re/Im is preserved only in original CSV, no full CPU current vector in gpu_case.json",
  "matrix_entries_compared"->n^2,"recomputed_saved_L_relative_error"->matrixError,"maximum_saved_CPU_GPU_L_difference_H"->maxDifference,"CPU_scalar_evidence"-><|"port_voltage_RMS_V_ReIm"->vfPair[cpuVoltage],"loss_W"->cpuPower,"Rac_ohm_per_axial_m"->cpuPower/(Abs[total]^2 len),"Rdc_ohm"->rdc,"GPU_loss_W"->power|>,"original_WXF_run_case_ID_fields"->"not_stored_in_raw_CPU_model_or_GPU_solution; bind by explicit source directory, case JSON/parameters and SHA256","physical_scope"->"CPU_GPU_equivalence_only; CPU singular self/near reused; no new field or topology conclusion","new_physics_solved"->False|>
];

vfVerifyRT0[payload_,summary_,parameters_,runParameters_,caseDir_]:=Module[{metadata,solution,currents,phi,h,sigma,freq,field,faces,cells,local,padded,minus,plus,j,csv,faceCoordinates,joule,input,emf,source,history},
 metadata=vfRequired[payload,"operator_metadata"];solution=vfRequired[payload,"solution"];currents=vfRequired[solution,"currents_RMS_A"];phi=vfRequired[solution,"cell_potentials_V"];
 h=vfRequired[metadata,"cell_width_m"];faces=vfRequired[metadata,"faces"];cells=vfRequired[metadata,"cells_coordinates"];local=vfRequired[metadata,"local_face_ids"];
 sigma=vfRequired[runParameters,"conductivity_S_per_m"];freq=vfRequired[runParameters,"frequency_Hz"];field=vfRequired[runParameters,"uniform_external_Bz_RMS_T"];source="original solution.wxf";
 vfCompare["SI_conductivity",5.8*^7,sigma,"S/m","closure_rt0_parameters.json"];
 vfCompare["SI_frequency",200000,freq,"Hz","closure_rt0_parameters.json"];
 vfCompare["mu_r",1,vfRequired[runParameters,"relative_permeability"],"dimensionless","closure_rt0_parameters.json"];
 vfCompare["temperature",20,vfRequired[runParameters,"temperature_C"],"degC","closure_rt0_parameters.json"];
 vfCheckIdentity["phasor_convention","exp(+j omega t)",vfRequired[runParameters,"phasor"],"closure_rt0_parameters.json"];
 vfCheckIdentity["field_excitation_identity","field",vfRequired[metadata,"excitation"],source<>".operator_metadata"];
 vfCheckIdentity["source_model_identity",vfRequired[metadata,"source_model"],vfRequired[summary,"source_model"],source];
 vfCompare["frequency_metadata",freq,vfRequired[metadata,"frequency_Hz"],"Hz",source];
 vfCompare["grid_dimensions",vfRequired[metadata,"dimensions"],vfRequired[summary,"dimensions"],"count",source,vfAbs,vfRel,True];
 vfCompare["parameter_grid_dimensions",vfRequired[metadata,"dimensions"],vfRequired[parameters,"dimensions"],"count",source,vfAbs,vfRel,True];
 vfCompare["quadrature_order",vfRequired[metadata,"quadrature_order"],vfRequired[summary,"q"],"count",source,vfAbs,vfRel,True];
 vfSavedScalar["cell_width_WXF_to_JSON",h,summary,"cell_width_m","m",source];
 vfCompare["cell_width_parameter",h,vfRequired[parameters,"cell_width_m"],"m",source];
 vfCompare["face_DOF_count",Length[currents],vfRequired[metadata,"face_flux_DOF"],"count",source,vfAbs,vfRel,True];
 vfCompare["face_DOF_count_JSON",Length[currents],vfRequired[summary,"face_flux_DOF"],"count",source,vfAbs,vfRel,True];
 vfCompare["cell_count",Length[phi],vfRequired[metadata,"cells"],"count",source,vfAbs,vfRel,True];
 vfCompare["cell_count_JSON",Length[phi],vfRequired[summary,"cells"],"count",source,vfAbs,vfRel,True];
 vfCompare["local_face_index_shape",{Length[cells],3,2},Dimensions[local],"count",source,vfAbs,vfRel,True];
 If[!ArrayQ[local,3,IntegerQ]||Min[Flatten[local]]<0||Max[Flatten[local]]>Length[currents],Throw[<|"reason"->"invalid_saved_local_face_indices"|>]];
 csv=vfReadCSV[FileNameJoin[{caseDir,"face_fluxes.csv"}],{"axis_1x_2y_3z","grid_i","grid_j","grid_k","face_flux_RMS_A_real","face_flux_RMS_A_imag"}];
 faceCoordinates=Map[Join[{#[[1]]},#[[2]]]&,faces];
 vfCompare["every_face_axis_grid_WXF_to_CSV",faceCoordinates,csv[[All,1;;4]],"axis/grid integer index",source<>".operator_metadata.faces vs face_fluxes.csv",vfAbs,vfRel,True];
 vfCompare["every_face_flux_ReIm_WXF_to_CSV",vfPairs[currents],csv[[All,5;;6]],"A RMS",source<>".solution.currents_RMS_A vs face_fluxes.csv"];
 Clear[csv,faceCoordinates];padded=Prepend[currents,0.+0.I];
 minus=Transpose[Table[padded[[local[[All,axis,1]]+1]],{axis,3}]];plus=Transpose[Table[padded[[local[[All,axis,2]]+1]],{axis,3}]];
 j=(minus+plus)/(2 h^2);
 csv=vfReadCSV[FileNameJoin[{caseDir,"cell_fields.csv"}],{"x_m","y_m","z_m","Jx_RMS_A_per_m2_real","Jx_RMS_A_per_m2_imag","Jy_RMS_A_per_m2_real","Jy_RMS_A_per_m2_imag","Jz_RMS_A_per_m2_real","Jz_RMS_A_per_m2_imag","phi_RMS_V_real","phi_RMS_V_imag"}];
 vfCompare["every_cell_center_WXF_to_CSV",(cells-.5) h,csv[[All,1;;3]],"m",source<>".operator_metadata.cells_coordinates vs cell_fields.csv"];
 vfCompare["every_cell_J_from_original_face_flux_to_CSV",Map[Flatten[Map[vfPair,#]]&,j],csv[[All,4;;9]],"A RMS/m^2",source<>" local_face_ids and saved face currents; RT0 midpoint average / h^2"];
 vfCompare["every_cell_phi_ReIm_WXF_to_CSV",vfPairs[phi],csv[[All,10;;11]],"V RMS",source<>".solution.cell_potentials_V vs cell_fields.csv"];
 vfSavedScalar["loss_WXF_to_JSON",vfRequired[solution,"loss_W"],summary,"loss_W","W",source];
 vfSavedScalar["input_WXF_to_JSON",vfRequired[solution,"input_W"],summary,"input_W","W",source];
 vfSavedScalar["port_current_ReIm_WXF_to_JSON",vfPair[vfRequired[solution,"port_current_A"]],summary,"port_current_RMS_A_ReIm","A RMS",source];
 vfSavedScalar["port_voltage_ReIm_WXF_to_JSON",vfPair[vfRequired[solution,"port_voltage_V"]],summary,"port_voltage_RMS_V_ReIm","V RMS",source];
 vfCompare["field_RMS_T",field,vfRequired[summary,"uniform_external_Bz_RMS_T"],"T RMS","closure_rt0_parameters.json vs case.json"];
 vfCompare["zero_net_transport",0,vfRequired[runParameters,"net_transport_current_RMS_A"],"A RMS","closure_rt0_parameters.json",vfAbs,vfRel,True];
 vfCompare["stored_source_port_current_identity",vfPair[Total[currents[[vfRequired[metadata,"source_face_rows"]]]]],vfPair[vfRequired[solution,"port_current_A"]],"A RMS",source<>" saved source_face_rows",10.^-12,10.^-8];
 (* Exact integral of the saved RT0 resistive bilinear form, NOT midpoint |J|^2.
    Each cell/axis has side fluxes a,b: (|a|^2+|b|^2+Re[a* b])/(3 sigma h). *)
 joule=Total[Flatten[(Abs[minus]^2+Abs[plus]^2+Re[Conjugate[minus] plus])/(3 sigma h)]];
 vfCompare["independent_RT0_Joule_mass_identity",joule,vfRequired[solution,"loss_W"],"W",source<>" saved local RT0 face coefficients and frozen sigma/h",10.^-20,10.^-10];
 emf=Map[With[{axis=#[[1]],k=#[[2]]},Which[axis==1,I 2 Pi freq (-field (k[[2]]-.5) h/2) h,axis==2,I 2 Pi freq (field (k[[1]]-.5) h/2) h,True,0.]]&,faces];
 input=Re[-Conjugate[currents].emf];
 vfCompare["independent_imposed_field_input_identity",input,vfRequired[solution,"input_W"],"W",source<>" saved faces with frozen uniform Bz/f/h, zero net transport",10.^-20,10.^-10];
 Scan[vfCompare["residual_"<>#,vfRequired[solution,#],vfRequired[vfRequired[summary,"residuals"],#],"dimensionless",source<>".solution vs case.json.residuals"]&,{"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","port_current_relative_residual","power_residual"}];
 vfSavedScalar["GMRES_iterations_WXF_to_JSON",vfRequired[solution,"iterations"],summary,"GMRES_iterations","count",source];
 vfCheckIdentity["GMRES_stop_reason_WXF_to_JSON",vfRequired[solution,"stop_reason"],vfRequired[summary,"GMRES_stop_reason"],source];
 vfCheckIdentity["side_wall_scope_preserved",vfRequired[solution,"side_wall_flux_status"],vfRequired[summary,"side_wall_flux_status"],source];
 If[FileExistsQ[FileNameJoin[{caseDir,"residual_history.csv"}]],history=vfRequired[solution,"history"];
  csv=vfReadCSV[FileNameJoin[{caseDir,"residual_history.csv"}],{"iteration","restart_cycle","true_relative_residual","elapsed_seconds"}];
  vfCompare["every_saved_GMRES_history_value",({#["iteration"],#["restart_cycle"],#["true_relative_residual"],#["elapsed_seconds"]}&/@history),csv,"count/count/dimensionless/s",source<>".solution.history vs residual_history.csv"]];
 Clear[metadata,solution,currents,phi,faces,cells,local,padded,minus,plus,j,csv,emf,history];
 <|"basis"->"RT0 face flux, three current components","phasor"->"exp(+j omega t)","current_convention"->"RMS","JSON_vector_coverage"->"original case JSON has scalar power/port/residuals, not complete face-current or cell-phi vectors; every original face-current and cell-phi/J Re/Im is checked against original CSV","Rac_Rdc_status"->"not_applicable_zero_net_transport_imposed_field_case; loss is absorbed power, not intrinsic P/I^2 resistance","side_wall_boundary_status"->"preserve original structurally_zero_by_omitted_insulating_faces; not independently verified boundary flux","new_physics_solved"->False|>
];

vfValidateCase[run_,casePath_]:=Module[{source,caseDir,summary,parameters,runParameters,runStatus=<||>,kind,wxf,gpuWxf,gpuRecord,gpuPayload,caseBudget,record,payload,result,outcome,scope=<||>,before,estimate,fileAfter,report,caseID},
 source=FileNameJoin[{vfRoot,"outputs",run}];caseDir=DirectoryName[casePath];vfSources={};vfChecks={};before=MemoryInUse[];
 outcome=Catch[
  summary=vfReadJSON[casePath,"original_case_scalar_and_current_JSON"];caseID=vfRequired[summary,"case_id"];
  If[!StringQ[caseID]||!StringMatchQ[caseID,RegularExpression["[A-Za-z0-9_-]+"]],Throw[<|"reason"->"invalid_original_case_id"|>]];
  kind=Which[StringContainsQ[Lookup[summary,"source_model",""],"CPU_GPU"],"GPU",StringContainsQ[Lookup[summary,"source_model",""],"longitudinal"],"PEEC",StringContainsQ[Lookup[summary,"source_model",""],"RT0"],"RT0",True,"unsupported"];
  If[kind==="unsupported",Throw[<|"reason"->"unsupported_original_source_model"|>]];
  parameters=vfReadJSON[FileNameJoin[{caseDir,"parameters.json"}],"original_case_input_parameters"];
  runParameters=If[kind==="GPU",parameters,vfReadJSON[FileNameJoin[{source,If[kind==="PEEC","closure_peec_parameters.json","closure_rt0_parameters.json"]}],"original_run_SI_RMS_phasor_parameters"]];
  runStatus=vfRunProvenance[source,kind];wxf=FileNameJoin[{caseDir,Switch[kind,"GPU","CPU_model.wxf","PEEC","model.wxf",_,"solution.wxf"]}];record=vfFile[wxf,"original_complete_saved_model_or_solution"];
  caseBudget=If[kind==="GPU",vfBudget,Min[vfBudget,4 1024^3]];
  gpuRecord=If[kind==="GPU",gpuWxf=FileNameJoin[{caseDir,"GPU_solution.wxf"}];vfFile[gpuWxf,"original_saved_GPU_matrix_and_solution"],<|"bytes"->0|>];
  estimate=before+3 (record["bytes"]+gpuRecord["bytes"])+256 1024^2;
  If[estimate>caseBudget,Throw[<|"reason"->"blocked_estimated_read_memory","estimated_heap_bytes"->estimate,"budget_bytes"->caseBudget,"measured_allocation"->False|>]];
  Print["READ ORIGINAL ",run," ",caseID," ",kind," bytes=",record["bytes"]];
  payload=MemoryConstrained[Quiet[Check[Import[wxf,"WXF"],$Failed]],Max[1,Floor[caseBudget-MemoryInUse[]]],$Failed];
  If[!AssociationQ[payload],Throw[<|"reason"->"original_WXF_import_failed_or_memory_constrained"|>]];
  If[kind=!="GPU",vfCheckIdentity["WXF_run_identity",run,vfRequired[payload,"run_id"],record["path"]];vfCheckIdentity["WXF_case_identity",caseID,vfRequired[payload,"case_id"],record["path"]]];
  vfCheckIdentity["JSON_run_identity",run,vfRequired[summary,"run_id"],vfRelPath[casePath]];
  If[KeyExistsQ[parameters,"run_id"],vfCheckIdentity["parameters_run_identity",run,parameters["run_id"],"original parameters.json"]];
  vfCheckIdentity["parameters_case_identity",caseID,vfRequired[parameters,"case_id"],"original parameters.json"];
  If[kind==="GPU",gpuPayload=MemoryConstrained[Quiet[Check[Import[gpuWxf,"WXF"],$Failed]],Max[1,Floor[caseBudget-MemoryInUse[]]],$Failed];If[!AssociationQ[gpuPayload],Throw[<|"reason"->"original_GPU_WXF_import_failed_or_memory_constrained"|>]]];
  scope=MemoryConstrained[Switch[kind,"GPU",vfVerifyGPU[payload,gpuPayload,summary,parameters,caseDir],"PEEC",vfVerifyPEEC[payload,summary,parameters,runParameters,caseDir],_,vfVerifyRT0[payload,summary,parameters,runParameters,caseDir]],Max[1,Floor[caseBudget-MemoryInUse[]]],$Failed];
  If[scope===$Failed,Throw[<|"reason"->"verification_memory_constrained"|>]];
  "completed"
 ];
 Clear[payload,gpuPayload];ClearSystemCache[];
 Do[fileAfter=FileNameJoin[{vfRoot,Sequence@@StringSplit[item["path"],"/"]}];
  If[!FileExistsQ[fileAfter]||FileHash[fileAfter,"SHA256","HexString"]=!=item["sha256"],AppendTo[vfChecks,<|"id"->"original_source_unchanged_"<>item["path"],"execution_status"->"failed","reason"->"source_changed_during_verification"|>]],{item,vfSources}];
 result=If[outcome==="completed"&&!AnyTrue[vfChecks,Lookup[#,"execution_status",""]==="failed"&],"passed_original_numeric_agreement",If[outcome==="completed","failed_original_numeric_agreement","not_verified_incomplete_original_evidence"]];
 report=<|"run_id"->run,"case_id"->If[StringQ[caseID],caseID,FileNameTake[caseDir]],"source_model"->If[AssociationQ[summary],Lookup[summary,"source_model","unknown"],"unknown"],"validation_status"->result,
  "source_case_execution_status"->If[AssociationQ[summary],Lookup[summary,"execution_status","unknown"],"unknown"],"source_physical_acceptance_status"->If[AssociationQ[summary],Lookup[summary,"physical_acceptance_status","not_recorded"],"not_recorded"],
  "source_run_status"->runStatus,"physical_acceptance_status"->"not_applicable_original_cache_agreement_only","checks"->vfChecks,"source_files"->vfSources,"missing_or_error"->If[outcome==="completed",Null,outcome],"scope"->scope,
  "solver_executed"->False,"kernel_heap_before_bytes"->before,"kernel_heap_after_release_bytes"->MemoryInUse[],"kernel_peak_heap_so_far_bytes"->MaxMemoryUsed[],"budget_bytes"->If[IntegerQ[caseBudget],caseBudget,vfBudget],"memory_measurement_scope"->"Wolfram kernel heap; OS process working set requires caller observation","estimated_import_heap_bytes"->If[NumberQ[estimate],estimate,Null]|>;
 vfJSON[FileNameJoin[{vfOutput,"cases",run<>"__"<>report["case_id"]<>".json"}],report];
 Print["VALIDATED ",run," ",report["case_id"]," ",result," checks=",Length[vfChecks]];report
];

vfCases={};vfReferenceReports={};
Do[vfCaseFiles=Sort@Join[FileNames["case.json",FileNameJoin[{vfRoot,"outputs",vfRun,"cases"}],Infinity],Select[{FileNameJoin[{vfRoot,"outputs",vfRun,"gpu_case.json"}]},FileExistsQ]];
 If[vfCaseFiles=={},AppendTo[vfReferenceReports,<|"run_id"->vfRun,"validation_status"->"not_verified_no_original_cases","solver_executed"->False|>],
  Do[AppendTo[vfCases,vfValidateCase[vfRun,vfCaseFile]],{vfCaseFile,vfCaseFiles}]],{vfRun,vfRunIDs}];
vfPassed=Length[vfCases]>0&&Length[vfReferenceReports]==0&&AllTrue[vfCases,#["validation_status"]==="passed_original_numeric_agreement"&];
vfFinal=<|"schema_version"->1,"source_model"->"independent_saved_PEEC_RT0_CPU_GPU_WXF_JSON_CSV_numeric_and_unit_verifier","execution_status"->If[vfPassed,"passed_original_numeric_agreement","not_verified_or_failed_original_evidence"],"physical_acceptance_status"->"not_applicable_cache_integrity_only",
 "ReferenceRuns"->vfRunIDs,"cases"->vfCases,"unverified_reference_runs"->vfReferenceReports,"elapsed_seconds"->AbsoluteTime[]-vfStart,"solver_executed"->False,"new_physics_solved"->False,
 "verifier_source_sha256"->FileHash[$InputFileName,"SHA256","HexString"],"WolframVersion"->$Version,"budget_bytes"->vfBudget,"kernel_peak_heap_bytes"->MaxMemoryUsed[],
 "memory_measurement_scope"->"Kernel heap only; caller must record actual child process exit and OS working-set/resource guard",
 "tolerances"-><|"saved_value_relative"->vfRel,"saved_value_absolute"->vfAbs,"independent_energy_identity_relative"->10.^-10,"independent_energy_identity_absolute"->10.^-20,"saved_integer_indices"->"exact","saved_full_L_Frobenius_arithmetic_reduction_relative"->10.^-12,"saved_full_L_Frobenius_arithmetic_reduction_absolute"->10.^-30,"original_physical_CPU_GPU_L_matrix_threshold"->10.^-10|>,
 "source_status_policy"->"Original physical limitations, failed/wrapper exit evidence and campaign uncertainty remain unchanged. This checks original cached numerical agreement and controlled SI/RMS identities only.","process_exit_evidence"->"caller_must_record_actual_child_exit"|>;
vfJSON[FileNameJoin[{vfOutput,"frozen_physics_validation.json"}],vfFinal];
vfJSON[FileNameJoin[{vfOutput,"test_report.json"}],<|"execution_status"->If[vfPassed,"passed","failed_or_incomplete"],"solver_executed"->False,"physical_acceptance_status"->"not_applicable_cache_agreement","tests"->Map[<|"id"->(#["run_id"]<>"/"<>#["case_id"]),"execution_status"->If[#["validation_status"]==="passed_original_numeric_agreement","passed","failed_or_incomplete"],"check_count"->Length[#["checks"]]|>&,vfCases]|>];
Print["FINISH independent original cache verification cases=",Length[vfCases]," ",vfFinal["execution_status"]];
Exit[If[vfPassed,0,1]];
