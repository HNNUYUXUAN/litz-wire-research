(* Fixed-geometry RT0 spatial/quadrature campaign. Single-case invocation
   allows resource scheduling and explicit-run-ID recovery without old globals. *)
Get[FileNameJoin[{stageRoot,"src","VoxelPEEC.wl"}]];
Get[FileNameJoin[{stageRoot,"src","VoxelOperator.wl"}]];
Get[FileNameJoin[{stageRoot,"src","ClosureCSV.wl"}]];
crDefaults=<|"case_time_budget_seconds"->3600.,"GMRES_tolerance"->10.^-11,"GMRES_restart"->40,"GMRES_max_iterations"->800,
 "spatial_tolerance"->.01,"quadrature_tolerance"->.001,"physical_residual_tolerance"->10.^-8,"power_tolerance"->.001,
 "archive_full_operator"->False,"kernel_assembly_workers"->1|>;
crConfigPath=Environment["LITZ_CLOSURE_CONFIG"];
If[!StringQ[crConfigPath]||crConfigPath=="",crConfigPath=FileNameJoin[{stageRoot,"configs","prewrite_closure.json"}]];
If[!StringMatchQ[crConfigPath,LetterCharacter~~":"~~Alternatives["\\","/"]~~___]&&!StringStartsQ[crConfigPath,{"\\\\","/"}],crConfigPath=FileNameJoin[{stageRoot,crConfigPath}]];
crRawConfig=If[FileExistsQ[crConfigPath],Quiet[Check[Import[crConfigPath,"RawJSON"],$Failed]],<||>];
If[!AssociationQ[crRawConfig],stageCheck["closure_config_readable",1,0,"closure_configuration"];crRawConfig=<||>];
crSection=If[AssociationQ[Lookup[crRawConfig,"rt0",<||>]],Lookup[crRawConfig,"rt0",<||>],<||>];crAliases=<||>;
Scan[If[KeyExistsQ[crSection,#[[1]]],AssociateTo[crAliases,#[[2]]->crSection[#[[1]]]]]&,
 {{"maximum_case_seconds","case_time_budget_seconds"},{"GMRES_true_relative_tolerance","GMRES_tolerance"},{"spatial_change_tolerance","spatial_tolerance"},{"quadrature_change_tolerance","quadrature_tolerance"}}];
crConfig=Join[crDefaults,crAliases,crSection];
crWorkerText=Environment["LITZ_RT0_KERNEL_ASSEMBLY_WORKERS"];
If[StringQ[crWorkerText]&&StringMatchQ[crWorkerText,DigitCharacter..],AssociateTo[crConfig,"kernel_assembly_workers"->ToExpression[crWorkerText]]];
crConfigValid=And@@(TrueQ[NumericQ[crConfig[#]]&&crConfig[#]>0]&/@{"case_time_budget_seconds","GMRES_tolerance","spatial_tolerance","quadrature_tolerance","physical_residual_tolerance","power_tolerance"})&&
 And@@(TrueQ[IntegerQ[crConfig[#]]&&crConfig[#]>0]&/@{"GMRES_restart","GMRES_max_iterations","kernel_assembly_workers"});
If[!crConfigValid,stageCheck["closure_rt0_config_valid",1,0,"closure_configuration"];crConfig=crDefaults];
crBudgetText=Environment["LITZ_RAM_BUDGET"];crBudget=If[StringQ[crBudgetText]&&StringMatchQ[crBudgetText,DigitCharacter..],ToExpression[crBudgetText],0.];
crSelection=Environment["LITZ_CLOSURE_CASE_ID"];If[!StringQ[crSelection]||crSelection=="",crSelection="rt0_n16_q14"];
crSpecs=Flatten[Table[<|"case_id"->("rt0_n"<>ToString[n]<>"_q"<>ToString[q]),"n"->n,"q"->q,"dimensions"->{n,n,2 n},"cell_width_m"->.001/n|>,{q,{14,18}},{n,{16,20,24,32}}],1];
crSelected=If[crSelection=="all",crSpecs,Select[crSpecs,#["case_id"]==crSelection&]];
If[crSelected=={},stageCheck["closure_rt0_known_case",1,0,"closure_configuration"]];
crPreflightOnly=MemberQ[{"1","true","True"},Environment["LITZ_CLOSURE_PREFLIGHT_ONLY"]];
crRows={};crProgress=Null;crStop=Null;crRoot=FileNameJoin[{stageDir,"cases"}];If[!DirectoryQ[crRoot],CreateDirectory[crRoot]];
Export[FileNameJoin[{stageDir,"closure_rt0_parameters.json"}],<|"run_id"->stageID,"selected_case"->crSelection,"case_definitions"->crSelected,"configuration"->crConfig,
 "RAM_budget_bytes"->crBudget,"preflight_only"->crPreflightOnly,"geometry_dimensions_m"->{.001,.001,.002},"frequency_Hz"->200000,
 "uniform_external_Bz_RMS_T"->.001,"net_transport_current_RMS_A"->0,"conductivity_S_per_m"->5.8*^7,"relative_permeability"->1,"temperature_C"->20,"phasor"->"exp(+j omega t)"|>,"RawJSON"];
crCheckpoint[event_]:=(crProgress=event;stageData=<|"source_model"->"prewrite_RT0_spatial_quadrature","cases"->crRows,"progress"->event,"first_stop"->crStop|>;stageSave[];Print[event]);
Do[
 crCaseDir=FileNameJoin[{crRoot,crSpec["case_id"]}];CreateDirectory[crCaseDir];crCaseStart=AbsoluteTime[];
 crDims=crSpec["dimensions"];crNC=Times@@crDims;crNF=(crDims[[1]]-1) crDims[[2]] crDims[[3]]+crDims[[1]] (crDims[[2]]-1) crDims[[3]]+crDims[[1]] crDims[[2]] (crDims[[3]]+1);
 crPadding=2^Ceiling[Log[2,2 crDims]];crWorkerEstimate=LitzVoxelOperator`Private`kernelWorkerMemoryBytes[crDims,crPadding,crConfig["kernel_assembly_workers"]];
 crEstimate=1280. (Times@@crPadding)+32768. crNC+1024. crNF+crWorkerEstimate;
 crPreflight=<|"run_id"->stageID,"case_id"->crSpec["case_id"],"cells"->crNC,"face_flux_DOF"->crNF,"padding"->crPadding,"estimated_working_bytes"->crEstimate,
  "working_budget_bytes"->crBudget,"estimated_worker_bytes"->crWorkerEstimate,"kernel_assembly_workers_requested"->crConfig["kernel_assembly_workers"],
  "kernel_assembly_workers_effective"->If[crConfig["kernel_assembly_workers"]==1,1,Min[3,crConfig["kernel_assembly_workers"]]],
  "soft_fraction"->.7,"measured_allocation"->False,"execution_status"->If[crBudget>0&&crEstimate<=.7 crBudget,"passed","blocked_environment_resource_budget"]|>;
 Export[FileNameJoin[{crCaseDir,"resource_preflight.json"}],crPreflight,"RawJSON"];
 Export[FileNameJoin[{crCaseDir,"parameters.json"}],Join[crSpec,crConfig,<|"run_id"->stageID,"working_budget_bytes"->crBudget|>],"RawJSON"];
 If[crBudget<=0||crEstimate>.7 crBudget,
  crSummary=Join[crSpec,<|"run_id"->stageID,"source_model"->"3D_RT0_exact_Toeplitz_matrix_free_PEEC","execution_status"->"blocked_environment_resource_budget",
   "physical_acceptance_status"->"not_run","failure_reason"->If[crBudget<=0,"missing_positive_RAM_budget","predicted_working_set_exceeds_70percent_budget"],"resource_preflight"->crPreflight|>];
  AppendTo[crRows,crSummary];crStop=crSummary;Export[FileNameJoin[{crCaseDir,"case.json"}],crSummary,"RawJSON"];crCheckpoint[crSummary];Break[]];
 If[crPreflightOnly,crSummary=Join[crSpec,<|"run_id"->stageID,"source_model"->"RT0_resource_preflight","execution_status"->"preflight_only","physical_acceptance_status"->"not_run","resource_preflight"->crPreflight|>];
  AppendTo[crRows,crSummary];Export[FileNameJoin[{crCaseDir,"case.json"}],crSummary,"RawJSON"];crCheckpoint[crSummary];Continue[]];
 crCheckpoint[<|"phase"->"case_start","case_id"->crSpec["case_id"],"parameters"->crSpec|>];
 crPair=TimeConstrained[
  crOp=LitzVoxelOperator`CreateOperator[crDims,crSpec["cell_width_m"],200000.,crSpec["q"],"field","MemoryBudgetBytes"->crBudget,
   "TimeBudgetSeconds"->crConfig["case_time_budget_seconds"],"ProgressFunction"->crCheckpoint,"KernelAssemblyWorkers"->crConfig["kernel_assembly_workers"]];
  If[AssociationQ[crOp],crSol=LitzVoxelOperator`SolveOperator[crOp,"Tolerance"->crConfig["GMRES_tolerance"],"Restart"->crConfig["GMRES_restart"],
   "MaxIterations"->crConfig["GMRES_max_iterations"],"TimeBudgetSeconds"->Max[.001,crConfig["case_time_budget_seconds"]-(AbsoluteTime[]-crCaseStart)],"CheckpointFunction"->crCheckpoint];{crOp,crSol},crOp],
  crConfig["case_time_budget_seconds"],$Aborted];
 If[!MatchQ[crPair,{_Association,_Association}],
  crSummary=Join[crSpec,<|"run_id"->stageID,"source_model"->"3D_RT0_exact_Toeplitz_matrix_free_PEEC","execution_status"->If[crPair===$Aborted,"not_completed_time_budget","failed_numerical"],
   "physical_acceptance_status"->"not_verified","failure_reason"->ToString[crPair,InputForm],"case_elapsed_seconds"->AbsoluteTime[]-crCaseStart,"last_progress"->crProgress|>];
  AppendTo[crRows,crSummary];crStop=crSummary;Export[FileNameJoin[{crCaseDir,"case.json"}],crSummary,"RawJSON"];stageCheck[crSpec["case_id"]<>"_completed",1,0,"matrix_free_RT0"];crCheckpoint[crSummary];Break[]];
 {crOp,crSol}=crPair;Clear[crPair];crBefore=Length[stageChecks];
 Scan[stageCheck[crSpec["case_id"]<>"_"<>#,crSol[#],crConfig["physical_residual_tolerance"],"matrix_free_RT0"]&,
  {"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","port_current_relative_residual"}];
 stageCheck[crSpec["case_id"]<>"_power",crSol["power_residual"],crConfig["power_tolerance"],"imposed_field_energy_balance"];
 stageCheck[crSpec["case_id"]<>"_zero_net_transport",Abs[crSol["port_current_A"]],crConfig["physical_residual_tolerance"],"external_field_zero_transport"];
 stageCheck[crSpec["case_id"]<>"_GMRES_converged",If[TrueQ[crSol["converged"]],0,1],0,"measured_true_residual"];
 crPassed=!AnyTrue[Drop[stageChecks,crBefore],#["execution_status"]=="failed"&];
 crSummary=Join[crSpec,<|"run_id"->stageID,"source_model"->crOp["source_model"],"execution_status"->If[crPassed,"passed_case_checks","failed_numerical"],
  "physical_acceptance_status"->"spatial_quadrature_campaign_incomplete","geometry_dimensions_m"->{.001,.001,.002},"uniform_external_Bz_RMS_T"->.001,"net_transport_current_RMS_A"->0,
  "cells"->crOp["cells"],"face_flux_DOF"->crOp["face_flux_DOF"],"padding"->crOp["padding"],"loss_W"->crSol["loss_W"],"input_W"->crSol["input_W"],
  "port_current_RMS_A_ReIm"->{Re[crSol["port_current_A"]],Im[crSol["port_current_A"]]},"port_voltage_RMS_V_ReIm"->{Re[crSol["port_voltage_V"]],Im[crSol["port_voltage_V"]]},
  "residuals"->KeyTake[crSol,{"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","port_current_relative_residual","power_residual"}],
  "GMRES_iterations"->crSol["iterations"],"GMRES_true_residual_target"->crConfig["GMRES_tolerance"],"GMRES_stop_reason"->crSol["stop_reason"],
  "assembly_seconds"->crOp["assembly_seconds"],"solve_seconds"->crSol["elapsed_seconds"],"case_elapsed_seconds"->AbsoluteTime[]-crCaseStart,
  "kernel_assembly_workers_requested"->crOp["kernel_assembly_workers_requested"],"kernel_assembly_workers_effective"->crOp["kernel_assembly_workers_effective"],
  "kernel_assembly_method"->crOp["kernel_assembly_method"],"axis_worker_metadata"->crOp["axis_worker_metadata"],"estimated_worker_bytes"->crOp["estimated_worker_bytes"],
  "estimated_working_bytes"->crOp["estimated_working_bytes"],"working_budget_bytes"->crBudget,"side_wall_flux_status"->crSol["side_wall_flux_status"],
  "face_fluxes_file"->"face_fluxes.csv","cell_fields_file"->"cell_fields.csv","solution_file"->"solution.wxf","scope"->crOp["scope"]|>];
 Export[FileNameJoin[{crCaseDir,"face_fluxes.csv"}],Prepend[MapThread[Join[{#1[[1]]},#1[[2]],{Re[#2],Im[#2]}]&,
  {crOp["faces"],crSol["currents_RMS_A"]}],{"axis_1x_2y_3z","grid_i","grid_j","grid_k","face_flux_RMS_A_real","face_flux_RMS_A_imag"}],"CSV"];
 crCellJ=Transpose[Table[(crOp["scatter"][[ax,1]].crSol["currents_RMS_A"]+crOp["scatter"][[ax,2]].crSol["currents_RMS_A"])/(2 crSpec["cell_width_m"]^2),{ax,3}]];
 Export[FileNameJoin[{crCaseDir,"cell_fields.csv"}],Prepend[MapThread[Join[(#1-.5) crSpec["cell_width_m"],Flatten[Map[{Re[#],Im[#]}&,#2]],{Re[#3],Im[#3]}]&,
  {crOp["cells_coordinates"],crCellJ,crSol["cell_potentials_V"]}],{"x_m","y_m","z_m","Jx_RMS_A_per_m2_real","Jx_RMS_A_per_m2_imag","Jy_RMS_A_per_m2_real","Jy_RMS_A_per_m2_imag","Jz_RMS_A_per_m2_real","Jz_RMS_A_per_m2_imag","phi_RMS_V_real","phi_RMS_V_imag"}],"CSV"];
 Export[FileNameJoin[{crCaseDir,"residual_history.csv"}],Prepend[({#["iteration"],#["restart_cycle"],#["true_relative_residual"],#["elapsed_seconds"]}&/@crSol["history"]),{"iteration","restart_cycle","true_relative_residual","elapsed_seconds"}],"CSV"];
 Export[FileNameJoin[{crCaseDir,"solution.wxf"}],<|"run_id"->stageID,"case_id"->crSpec["case_id"],"operator_metadata"->LitzVoxelOperator`OperatorMetadata[crOp],"solution"->crSol|>,"WXF"];
 If[TrueQ[crConfig["archive_full_operator"]],Export[FileNameJoin[{crCaseDir,"operator.wxf"}],crOp,"WXF"]];
 Export[FileNameJoin[{crCaseDir,"case.json"}],crSummary,"RawJSON"];AppendTo[crRows,crSummary];Clear[crOp,crSol,crCellJ];crCheckpoint[crSummary];
 If[!crPassed,crStop=crSummary;Break[]],{crSpec,crSelected}];

crReferenceText=Environment["LITZ_CLOSURE_REFERENCE_RUNS"];crReferenceIDs=If[StringQ[crReferenceText],DeleteCases[StringTrim/@StringSplit[crReferenceText,","],""],{}];crReferenceRows={};
Do[If[StringMatchQ[crRefID,RegularExpression["[A-Za-z0-9_-]+"]],crFiles=FileNames["case.json",FileNameJoin[{stageRoot,"outputs",crRefID,"cases"}],Infinity];
 Do[crImported=Quiet[Check[Import[crFile,"RawJSON"],$Failed]];
  If[AssociationQ[crImported]&&Lookup[crImported,"run_id",None]==crRefID,AppendTo[crReferenceRows,Append[crImported,"case_file_absolute"->crFile]]],{crFile,crFiles}]],{crRefID,crReferenceIDs}];
crAllRows=Values[Association[(#["case_id"]->#)&/@Join[crReferenceRows,crRows]]];
crFind[id_]:=SelectFirst[crAllRows,Lookup[#,"case_id",None]==id&&Lookup[#,"execution_status",None]=="passed_case_checks"&,Missing["NotRun",id]];
crDifferences={};
Do[crA=crFind["rt0_n"<>ToString[pair[[1]]]<>"_q14"];crB=crFind["rt0_n"<>ToString[pair[[2]]]<>"_q14"];
 If[AssociationQ[crA]&&AssociationQ[crB],crDelta=Abs[crB["loss_W"]/crA["loss_W"]-1];
  AppendTo[crDifferences,<|"kind"->"spatial","before_case_id"->crA["case_id"],"after_case_id"->crB["case_id"],"before_run_id"->crA["run_id"],"after_run_id"->crB["run_id"],
   "loss_relative_change"->crDelta,"tolerance"->crConfig["spatial_tolerance"],"execution_status"->If[crDelta<=crConfig["spatial_tolerance"],"passed","failed"]|>],
  AppendTo[crDifferences,<|"kind"->"spatial","before_case_id"->("rt0_n"<>ToString[pair[[1]]]<>"_q14"),"after_case_id"->("rt0_n"<>ToString[pair[[2]]]<>"_q14"),"execution_status"->"not_run","tolerance"->crConfig["spatial_tolerance"]|>]],
 {pair,{{16,20},{20,24},{24,32}}}];
crSpatialRows=Select[crDifferences,#["kind"]=="spatial"&&#["execution_status"]!="not_run"&];
crSpatialPassed=Length[crSpatialRows]>=2&&And@@(#["execution_status"]=="passed"&/@Take[crSpatialRows,-2]);
crSpatialCases=SortBy[Select[crAllRows,Lookup[#,"q",None]==14&&Lookup[#,"execution_status",None]=="passed_case_checks"&],#["n"]&];
crFinestN=If[crSpatialCases=={},Null,Last[crSpatialCases]["n"]];crQuadratureStatus="not_run";
If[IntegerQ[crFinestN],
 crA=crFind["rt0_n"<>ToString[crFinestN]<>"_q14"];crB=crFind["rt0_n"<>ToString[crFinestN]<>"_q18"];
 If[AssociationQ[crA]&&AssociationQ[crB],
  crDelta=Abs[crB["loss_W"]/crA["loss_W"]-1];crCurrentDelta=Null;
  crSourceA=FileNameJoin[{stageRoot,"outputs",crA["run_id"],"cases",crA["case_id"],"face_fluxes.csv"}];
  crSourceB=FileNameJoin[{stageRoot,"outputs",crB["run_id"],"cases",crB["case_id"],"face_fluxes.csv"}];
  If[FileExistsQ[crSourceA]&&FileExistsQ[crSourceB],crCSV_A=LitzClosureCSV`NumericCSV[crSourceA];crCSV_B=LitzClosureCSV`NumericCSV[crSourceB];
   If[AssociationQ[crCSV_A]&&AssociationQ[crCSV_B],crCSV_A=crCSV_A["data"];crCSV_B=crCSV_B["data"];
    If[Dimensions[crCSV_A]==Dimensions[crCSV_B]&&crCSV_A[[All,{1,2,3,4}]]===crCSV_B[[All,{1,2,3,4}]],
     crCurrentDelta=Norm[Flatten[crCSV_B[[All,{5,6}]]-crCSV_A[[All,{5,6}]]]]/Max[Norm[Flatten[crCSV_B[[All,{5,6}]]]],$MinMachineNumber]]];Clear[crCSV_A,crCSV_B]];
  crQuadratureMetric=If[NumericQ[crCurrentDelta],Max[crDelta,crCurrentDelta],Infinity];
  crQuadratureStatus=If[crQuadratureMetric<=crConfig["quadrature_tolerance"],"passed","failed"];
  AppendTo[crDifferences,<|"kind"->"quadrature","before_case_id"->crA["case_id"],"after_case_id"->crB["case_id"],"before_run_id"->crA["run_id"],"after_run_id"->crB["run_id"],
   "loss_relative_change"->crDelta,"complex_face_current_relative_change"->crCurrentDelta,"acceptance_metric"->If[crQuadratureMetric===Infinity,Null,crQuadratureMetric],
   "tolerance"->crConfig["quadrature_tolerance"],"execution_status"->crQuadratureStatus|>]]];
crCampaignStatus=If[crSpatialPassed&&crQuadratureStatus=="passed","passed_cuboid_imposed_field_scope_only",
 If[AnyTrue[crDifferences,#["execution_status"]=="failed"&],"failed_numerical","not_verified_incomplete_campaign"]];
crFinal=<|"run_id"->stageID,"source_model"->"prewrite_RT0_spatial_quadrature","cases"->crRows,"reference_run_ids"->crReferenceIDs,"comparisons"->crDifferences,
 "two_successive_spatial_changes_passed"->crSpatialPassed,"finest_spatial_n"->crFinestN,"finest_quadrature_status"->crQuadratureStatus,
 "physical_acceptance_status"->crCampaignStatus,"first_stop"->crStop|>;
Export[FileNameJoin[{stageDir,"closure_rt0_summary.json"}],crFinal,"RawJSON"];
stageData=Join[crFinal,<|"configuration"->crConfig,"progress"->crProgress,"failure_reason"->If[crCampaignStatus=="failed_numerical","sensitivity_threshold_exceeded",Null],
 "assumptions"->"CPUFP64 RT0 three-component exact zero-padded Toeplitz PEEC; original volume-pair/Duffy kernel. Fixed1x1x2mm cuboid with independent1mT RMS Bz,zero net transport; loss is imposed-field absorption,not intrinsicP/I^2 Rac. q14 spatial n16/20/24/32; q18 on the finest completed geometry is an independent single-parameter sensitivity. Two successive spatial changes<=1percent and finest quadrature loss/complex-current differences<=0.1percent required. Continuity,common-port equations,power and true GMRES residuals separately checked. Insulating side flux structurallyzero by omitted faces,not an independent computed boundary-flux verification. No masked curved-wire,return,real-end,topology ranking or actuallow32GiB acceptance. Explicit archived run IDs only."|>];
stageSave[];
