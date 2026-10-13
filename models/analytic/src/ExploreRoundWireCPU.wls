(* Independent light CPU analytical entry. SI, exp(+j omega t), RMS.
   Only Q1Analytical.wl is loaded; no field, PEEC, NotebookPhysics or GPU code. *)
$HistoryLength=0;$CharacterEncoding="UTF8";
BeginPackage["LitzRoundWireCPU`"];
RunRoundWireCPU::usage="RunRoundWireCPU[runID,inputs] archives one bounded isolated-round-wire Bessel exploration. Inputs: diameter_m, frequency_Hz, current_RMS_A, conductivity_S_per_m.";
SkipCommandLine::usage="Set True before Get to call RunRoundWireCPU explicitly in a fresh isolated MCP kernel.";
Begin["`Private`"];
rcRoot=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
rcEntryPath=$InputFileName;
rcDefaults=<|"diameter_m"->0.002,"frequency_Hz"->200000,"current_RMS_A"->20,"conductivity_S_per_m"->58000000|>;
rcBounds=<|"diameter_m"->{10^-6,0.02},"frequency_Hz"->{0.001,2000000},"current_RMS_A"->{10^-6,100},"conductivity_S_per_m"->{10^6,65000000}|>;
rcFinitePositiveQ[x_]:=NumberQ[x]&&Im[x]==0&&TrueQ[x>0]&&FreeQ[x,Indeterminate|_DirectedInfinity];
rcRelative[a_,b_]:=Abs[a-b]/Max[Abs[b],10^-300];
rcJSON[path_,value_]:=Module[{written},written=Quiet[Check[Export[path,value,"RawJSON"],$Failed]];If[written===$Failed||!FileExistsQ[path]||FileByteCount[path]==0,Throw[Failure["JSONExportFailed",<|"file"->FileNameTake[path]|>],"RoundWireCPUFailure"]];written];
rcRuleCheck[id_,value_,tolerance_,passed_]:=<|"id"->id,"value"->N[value,MachinePrecision],"tolerance"->tolerance,"passed"->TrueQ[passed]|>;

RunRoundWireCPU[runID_String,inputs_Association:<||>]:=Catch[Module[
 {p,folder,start=AbsoluteTime[],startUTC,sourcePaths,sources,snapshot,path,target,reference,result,values,display,errors=<||>,checks={},messages={},log,failed=False,defaultQ,returnCode,env,report,files},
 If[!StringMatchQ[runID,RegularExpression["[A-Za-z0-9_-]+"]],Return[Failure["InvalidRunID",<|"run_id"->runID|>]]];
 If[!SubsetQ[Keys[rcDefaults],Keys[inputs]],Return[Failure["UnknownSIParameter",<|"allowed_keys"->Keys[rcDefaults]|>]]];
 p=Join[rcDefaults,inputs];
 If[!AllTrue[Keys[p],Function[k,rcFinitePositiveQ[p[k]]&&TrueQ[rcBounds[k][[1]]<=p[k]<=rcBounds[k][[2]]]]],Return[Failure["ParameterOutsideBoundedSIRange",<|"allowed_ranges_SI"->rcBounds|>]]];
 folder=FileNameJoin[{rcRoot,"outputs",runID}];
 If[DirectoryQ[folder]||FileExistsQ[folder],Return[Failure["RunDirectoryAlreadyExists",<|"run_id"->runID|>]]];
 CreateDirectory[folder,CreateIntermediateDirectories->True];
 startUTC=DateString[DateObject[Now,TimeZone->0],"ISODateTime"];
 Quiet[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8]];
 Quiet[SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->8]];
 (* Snapshot exact source bytes before loading the analytical module or evaluating it. *)
 sourcePaths={rcEntryPath,FileNameJoin[{rcRoot,"src","Q1Analytical.wl"}],FileNameJoin[{rcRoot,"configs","reference_parameters.json"}],FileNameJoin[{rcRoot,"configs","reference_values.json"}]};
 sources=Map[Function[q,With[{relative=FileNameDrop[q,FileNameDepth[rcRoot]]},target=FileNameJoin[{folder,"source_snapshot",relative}];If[!DirectoryQ[DirectoryName[target]],CreateDirectory[DirectoryName[target],CreateIntermediateDirectories->True]];CopyFile[q,target];<|"path"->StringReplace[relative,"\\"->"/"],"snapshot_path"->StringReplace[FileNameDrop[target,FileNameDepth[folder]],"\\"->"/"],"sha256"->FileHash[q,"SHA256","HexString"],"snapshot_sha256"->FileHash[target,"SHA256","HexString"]|>]],sourcePaths];
 rcJSON[FileNameJoin[{folder,"source_hashes.json"}],<|"captured_before_analytical_evaluation_UTC"->startUTC,"sources"->sources|>];
 rcJSON[FileNameJoin[{folder,"parameters.json"}],<|"inputs_SI"->p,"allowed_ranges_SI"->rcBounds,"relative_permeability"->1,"temperature_C"->20,"axial_normalization_m"->1,"phasor"->"exp(+j omega t)","amplitude"->"RMS","working_precision_digits"->50,"CPU_thread_cap"->8,"maximum_analytical_seconds"->45,"GPU_used"->False|>];
 env=<|"WolframVersion"->$Version,"SystemID"->$SystemID,"WolframProcessorCount"->$ProcessorCount,"kernel_process_ID"->$ProcessID,"CPU_thread_cap"->8,"thread_options_InputForm"->ToString[SystemOptions["ParallelOptions"],InputForm],"execution_kernel_scope"->"caller records actual fresh CLI process or newKernel TestReport evidence; MCP session ID alone does not establish a fresh native kernel","source_snapshot_before_evaluation"->True,"GPU_used"->False,"field_solver_executed"->False|>;
 rcJSON[FileNameJoin[{folder,"environment.json"}],env];
 log=OpenWrite[FileNameJoin[{folder,"run_log.txt"}],CharacterEncoding->"UTF8"];
 WriteString[log,"Isolated round-wire Bessel analytical exploration. No physical field solver or GPU is invoked.\n"];
 Block[{$Messages={log},$MessageList={}},
  Get[FileNameJoin[{rcRoot,"src","Q1Analytical.wl"}]];
  result=TimeConstrained[MemoryConstrained[LitzAnalytical`RoundWireSolution[<|"frequency_Hz"->p["frequency_Hz"],"conductivity_S_per_m"->p["conductivity_S_per_m"],"relative_permeability"->1,"current_RMS_A"->p["current_RMS_A"],"q1"-><|"solid_diameter_m"->p["diameter_m"]|>|>],256 1024^2,$Failed],45,$Failed];
  messages=ToString[#,InputForm]&/@$MessageList];
 Close[log];
 If[!AssociationQ[result],rcJSON[FileNameJoin[{folder,"results.json"}],<|"run_id"->runID,"execution_status"->"failed_analytical_evaluation","source_model"->"isolated_long_round_wire_Bessel_internal_impedance","messages"->messages,"elapsed_seconds"->(AbsoluteTime[]-start),"GPU_used"->False,"field_solver_executed"->False|>];Return[Failure["AnalyticalEvaluationFailed",<|"run_id"->runID|>]]];
 values=N[KeyDrop[result,"profile"],MachinePrecision];
 display=<|"delta_mm"->1000 result["delta_m"],"rho_ohm_m"->result["rho_ohm_m"],"Q1_Rdc_mohm_per_m"->1000 result["Rdc_ohm_per_m"],"Q1_Rac_mohm_per_m"->1000 result["Rac_ohm_per_m"],"Q1_Xint_mohm_per_m"->1000 result["Xinternal_ohm_per_m"],"Q1_Rac_Rdc"->result["Rac_Rdc"],"Q1_P_W_per_m"->result["loss_W_per_m"],"Q1_area_mm2"->10^6 result["area_m2"],"Q1_Jdc_A_per_mm2"->result["Jdc_A_per_m2"]/10^6|>;
 defaultQ=AllTrue[Keys[rcDefaults],TrueQ[p[#]==rcDefaults[#]]&];
 AppendTo[checks,rcRuleCheck["all_SI_outputs_finite",1,0,AllTrue[Values[values],NumberQ[#]&&FreeQ[#,Indeterminate|_DirectedInfinity]&]]];
 AppendTo[checks,rcRuleCheck["Rac_at_least_Rdc",result["Rac_Rdc"],1,result["Rac_Rdc"]>=1-10^-12]];
 AppendTo[checks,rcRuleCheck["independent_complex_current_integral",result["current_integral_relative_error"],10^-8,result["current_integral_relative_error"]<=10^-8]];
 AppendTo[checks,rcRuleCheck["independent_Joule_power_integral",result["power_integral_relative_error"],10^-8,result["power_integral_relative_error"]<=10^-8]];
 AppendTo[checks,rcRuleCheck["RMS_absolute_AC_loss",rcRelative[result["loss_W_per_m"],p["current_RMS_A"]^2 result["Rac_ohm_per_m"]],10^-12,rcRelative[result["loss_W_per_m"],p["current_RMS_A"]^2 result["Rac_ohm_per_m"]]<=10^-12]];
 AppendTo[checks,rcRuleCheck["DC_current_density",rcRelative[result["Jdc_A_per_m2"],p["current_RMS_A"]/result["area_m2"]],10^-12,rcRelative[result["Jdc_A_per_m2"],p["current_RMS_A"]/result["area_m2"]]<=10^-12]];
 AppendTo[checks,rcRuleCheck["no_GPU_package_loaded",0,0,!AnyTrue[$Packages,StringContainsQ[#,"CUDALink"|"GPUArray"]&]]];
 AppendTo[checks,rcRuleCheck["no_project_field_model_loaded",0,0,!AnyTrue[$Packages,StringContainsQ[#,"LitzNotebook"|"LitzPEEC"|"LitzVoxel"|"NDSolve`FEM`"]&]]];
 AppendTo[checks,rcRuleCheck["source_hashes_still_match_before_snapshot",0,0,And@@MapThread[FileHash[#1,"SHA256","HexString"]===#2["sha256"]&,{sourcePaths,sources}]]];
 If[defaultQ,reference=Import[FileNameJoin[{rcRoot,"configs","reference_values.json"}],"RawJSON"]["values"];
  errors=Association@KeyValueMap[(#1->Abs[#2-Rationalize[reference[#1],0]]/Abs[Rationalize[reference[#1],0]])&,display];
  Scan[Function[k,AppendTo[checks,rcRuleCheck["default_reference_"<>k,errors[k],10^-6,errors[k]<=10^-6]]],Keys[errors]]];
 failed=AnyTrue[checks,!TrueQ[#["passed"]]&];returnCode=If[failed,1,0];
 report=<|"run_id"->runID,"source_model"->"isolated_long_round_conductor_internal_impedance_Bessel_solution","execution_status"->"executed_light_CPU_analytic","physical_acceptance_status"->If[failed,"failed_analytical_checks","passed_analytic_formula_scope_only"],"inputs_SI"->p,"SI_values"->values,"display_values"->N[display,MachinePrecision],"units"-><|"delta_m"->"m","area_m2"->"m^2","Jdc_A_per_m2"->"A RMS/m^2","Rdc_ohm_per_m"->"ohm/axial_m","Rac_ohm_per_m"->"ohm/axial_m","Rac_Rdc"->"dimensionless","loss_W_per_m"->"W/axial_m","Xinternal_ohm_per_m"->"ohm/axial_m","Linternal_H_per_m"->"H/axial_m"|>,"default_reference_case"->defaultQ,"reference_relative_errors"->N[errors,MachinePrecision],"reference_status"->If[defaultQ,"compared_to_frozen_Q1_reference","not_default_reference_case"],"check_count"->Length[checks],"failed_checks"->(#["id"]&/@Select[checks,!TrueQ[#["passed"]]&]),"scope"->"Isolated infinitely long homogeneous nonmagnetic round conductor; internal impedance only; SI and RMS; no independent applied field, finite-end field, return inductance, temperature solution or Litz structure ranking.","Q1_calibration_note"->"The specified 2 mm/20 A case is a calibration case; its DC current density exceeds 4 A/mm^2 and its copper area is below the Q2 5 mm^2 minimum.","CPU_thread_cap"->8,"GPU_used"->False,"field_solver_executed"->False,"elapsed_seconds"->(AbsoluteTime[]-start),"messages"->messages|>;
 rcJSON[FileNameJoin[{folder,"results.json"}],report];
 rcJSON[FileNameJoin[{folder,"test_report.json"}],<|"run_id"->runID,"tests"->checks,"tests_run"->Length[checks],"tests_failed"->Count[Lookup[checks,"passed"],False],"scope"->"light analytical formula and numerical integration checks only"|>];
 Export[FileNameJoin[{folder,"radial_current_density.csv"}],Prepend[N[result["profile"],MachinePrecision],{"r_m","Re_J_A_per_m2","Im_J_A_per_m2","Abs_J_A_per_m2"}],"CSV"];
 rcJSON[FileNameJoin[{folder,"function_status.json"}],<|"analytical_function_return_code"->returnCode,"actual_native_process_exit"->Null,"process_exit_policy"->"CLI caller records actual exit; MCP response records actual tool completion separately","source_snapshot_before_evaluation"->True,"finished_UTC"->DateString[DateObject[Now,TimeZone->0],"ISODateTime"]|>];
 files=Map[<|"file"->StringReplace[FileNameDrop[#,FileNameDepth[folder]],"\\"->"/"],"bytes"->FileByteCount[#],"sha256"->FileHash[#,"SHA256","HexString"]|>&,Select[FileNames["*",folder,Infinity],FileExistsQ[#]&&!DirectoryQ[#]&]];
 rcJSON[FileNameJoin[{folder,"run_manifest.json"}],<|"run_id"->runID,"sources"->sources,"files"->files,"manifest_self_excluded"->True,"source_model"->report["source_model"],"GPU_used"->False,"field_solver_executed"->False|>];
 KeyTake[report,{"run_id","execution_status","physical_acceptance_status","default_reference_case","display_values","check_count","failed_checks","elapsed_seconds","GPU_used","field_solver_executed"}]
],"RoundWireCPUFailure"];
RunRoundWireCPU[___]:=Failure["InvalidInvocation",<|"usage"->"RunRoundWireCPU[runID_String, inputs_Association]"|>];

rcParseNumber[s_String]:=If[StringMatchQ[s,RegularExpression["[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:(?:[eE]|\\*\\^)[+-]?[0-9]+)?"]],ToExpression[StringReplace[s,RegularExpression["[eE]"]->"*^"]],$Failed];
rcCLI[]:=Module[{position,args,id="",input=<||>,key,value,result,options},
 options=<|"--diameter-m"->"diameter_m","--frequency-hz"->"frequency_Hz","--current-rms-a"->"current_RMS_A","--conductivity"->"conductivity_S_per_m"|>;
 position=FirstPosition[$ScriptCommandLine,s_String/;FileNameTake[s]==="ExploreRoundWireCPU.wls",Missing["Absent"]];
 args=If[ListQ[position],Drop[$ScriptCommandLine,First[position]],Rest[$ScriptCommandLine]];
 If[MemberQ[args,"--help"],Print["wolframscript -file src/ExploreRoundWireCPU.wls --run-id UNIQUE [--diameter-m 0.002 --frequency-hz 200000 --current-rms-a 20 --conductivity 58000000]. SI finite positive bounds: D 1e-6..0.02 m; f 0.001..2e6 Hz; I 1e-6..100 A RMS; sigma 1e6..6.5e7 S/m. CPU8; internal isolated round-wire Bessel model only."];Return[0]];
 If[OddQ[Length[args]],Print["Each CLI option requires a value"];Return[2]];
 Do[{key,value}=pair;If[key==="--run-id",id=value,If[!KeyExistsQ[options,key],Print["Unknown option: ",key];Return[2]];value=rcParseNumber[value];If[value===$Failed,Print["Strict SI numeric value required"];Return[2]];AssociateTo[input,options[key]->value]],{pair,Partition[args,2]}];
 If[id==="",Print["--run-id UNIQUE is required"];Return[2]];
 result=RunRoundWireCPU[id,input];If[FailureQ[result],Print[ToString[result,InputForm]];Return[2]];
 Print[ExportString[result,"RawJSON"]];If[Length[result["failed_checks"]]==0,0,1]
];
End[];EndPackage[];
If[!TrueQ[LitzRoundWireCPU`SkipCommandLine],Exit[LitzRoundWireCPU`Private`rcCLI[]]];
