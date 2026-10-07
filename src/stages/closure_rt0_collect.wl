(* Frozen arithmetic collector. It deliberately loads no operator, FFT,
   field assembly, preconditioner, GMRES or physical solver package. *)
Get[FileNameJoin[{stageRoot,"src","ClosureCSV.wl"}]];
ccReferenceText=Environment["LITZ_CLOSURE_REFERENCE_RUNS"];
ccReferences=If[StringQ[ccReferenceText],DeleteCases[StringTrim/@StringSplit[ccReferenceText,","],""],{}];
ccExpected={"rt0_n16_q14","rt0_n20_q14","rt0_n24_q14","rt0_n24_q18"};
ccRows={};ccFluxes=<||>;ccTolerance=<|"spatial"->.01,"quadrature"->.001,"residual"->10.^-8,"power"->.001,"GMRES"->10.^-11|>;
stageCheck["four_explicit_RT0_source_runs",If[Length[ccReferences]==4&&Length[DeleteDuplicates[ccReferences]]==4&&And@@(StringMatchQ[#,RegularExpression["[A-Za-z0-9_-]+"]]&/@ccReferences),0,1],0,"frozen_source_selection"];
ccKey[x_]:=ToString[x,InputForm];
Do[
 ccCaseFiles=FileNames["case.json",FileNameJoin[{stageRoot,"outputs",ccRun,"cases"}],Infinity];
 If[Length[ccCaseFiles]!=1,stageCheck[ccRun<>"_single_source_case",1,0,"frozen_source_selection"];Continue[]];
 ccFile=First[ccCaseFiles];ccCase=Quiet[Check[Import[ccFile,"RawJSON"],$Failed]];
 If[!AssociationQ[ccCase]||Lookup[ccCase,"run_id",None]!=ccRun||!MemberQ[ccExpected,Lookup[ccCase,"case_id",None]],stageCheck[ccRun<>"_source_identity",1,0,"frozen_source_selection"];Continue[]];
 ccID=ccCase["case_id"];ccCSVFile=FileNameJoin[{DirectoryName[ccFile],"face_fluxes.csv"}];ccCSV=LitzClosureCSV`NumericCSV[ccCSVFile];
 If[!AssociationQ[ccCSV],stageCheck[ccID<>"_finite_numeric_CSV",1,0,"frozen_CSV_arithmetic"];Continue[]];
 ccCSVData=ccCSV["data"];ccDims=ccCase["dimensions"];ccH=ccCase["cell_width_m"];ccN=ccCase["n"];ccQ=ccCase["q"];
 ccParameters=Import[FileNameJoin[{stageRoot,"outputs",ccRun,"closure_rt0_parameters.json"}],"RawJSON"];
 ccSigma=ccParameters["conductivity_S_per_m"];ccF=ccParameters["frequency_Hz"];ccB=ccParameters["uniform_external_Bz_RMS_T"];
 stageCheck[ccID<>"_fixed_physical_parameters",If[ccDims=={ccN,ccN,2 ccN}&&Abs[ccH ccN-.001]<10.^-14&&ccSigma==5.8*^7&&ccF==200000&&ccB==.001&&ccParameters["net_transport_current_RMS_A"]==0,0,1],0,"frozen_physical_inputs"];
 stageCheck[ccID<>"_original_case_checks",If[ccCase["execution_status"]=="passed_case_checks",0,1],0,"original_archived_case_status"];
 ccCells=Tuples[Range/@ccDims];
 ccFaces=Join[Flatten[Table[If[k[[ax]]<ccDims[[ax]],{{ax,k}},{}],{k,ccCells},{ax,3}],2],({3,ReplacePart[#,3->0]}&/@Select[ccCells,#[[3]]==1&]),({3,#}&/@Select[ccCells,#[[3]]==ccDims[[3]]&])];
 ccCSVFaces=({#[[1]],#[[2;;4]]}&/@ccCSVData);
 stageCheck[ccID<>"_face_identity_and_order",If[ccCSVFaces===ccFaces,0,1],0,"frozen_flux_bookkeeping"];
 If[ccCSVFaces=!=ccFaces,Continue[]];
 ccCurrent=Developer`ToPackedArray[N[ccCSVData[[All,5]]+I ccCSVData[[All,6]]]];
 ccFluxMap=Association[MapThread[ccKey[#1]->#2&,{ccFaces,ccCurrent}]];
 ccLocal=Table[Table[Lookup[ccFluxMap,ccKey[{ax,ReplacePart[k,ax->k[[ax]]-1+side]}],0.+0. I],{ax,3},{side,0,1}],{k,ccCells}];
 ccDivergence=Total[Table[-ccLocal[[All,ax,1]]+ccLocal[[All,ax,2]],{ax,3}]];
 ccNorm=Max[Norm[ccCurrent],$MinMachineNumber];ccContinuity=Norm[ccDivergence]/ccNorm;
 ccPort=Total[Pick[ccCurrent,(If[#[[1]]==3&&#[[2,3]]==0,1,0]&/@ccFaces),1]];
 ccPortResidual=Abs[ccPort]/ccNorm;
 ccJoule=Total[Flatten[Table[(Abs[ccLocal[[All,ax,1]]]^2+Abs[ccLocal[[All,ax,2]]]^2+Re[Conjugate[ccLocal[[All,ax,1]]] ccLocal[[All,ax,2]]])/(3 ccSigma ccH),{ax,3}]]];
 ccExternal=Table[With[{ax=face[[1]],k=face[[2]]},If[ax==1,-I 2 Pi ccF ccB (k[[2]]-.5) ccH^2/2,If[ax==2,I 2 Pi ccF ccB (k[[1]]-.5) ccH^2/2,0.]]],{face,ccFaces}];
 ccInput=-Re[Conjugate[ccCurrent].ccExternal];ccPower=Abs[ccInput-ccJoule]/Max[Abs[ccJoule],$MinMachineNumber];
 ccLossDelta=Abs[ccJoule/ccCase["loss_W"]-1];ccInputDelta=Abs[ccInput/ccCase["input_W"]-1];
 stageCheck[ccID<>"_CSV_continuity",ccContinuity,ccTolerance["residual"],"independent_CSV_cell_divergence"];
 stageCheck[ccID<>"_CSV_zero_net_port",ccPortResidual,ccTolerance["residual"],"independent_CSV_common_port"];
 stageCheck[ccID<>"_CSV_power_balance",ccPower,ccTolerance["power"],"independent_CSV_RT0_overlap_and_imposed_field_work"];
 stageCheck[ccID<>"_CSV_Joule_matches_archive",ccLossDelta,10.^-10,"independent_CSV_RT0_overlap"];
 stageCheck[ccID<>"_CSV_input_matches_archive",ccInputDelta,10.^-10,"independent_CSV_imposed_field_work"];
 Scan[stageCheck[ccID<>"_archived_"<>#,ccCase["residuals"][#],ccTolerance["residual"],"archived_solver_residual_not_reassembled"]&,Keys[ccCase["residuals"]]];
 stageCheck[ccID<>"_measured_GMRES_target",ccCase["residuals"]["linear_residual"],ccTolerance["GMRES"],"archived_measured_true_residual"];
 AppendTo[ccRows,<|"case_id"->ccID,"run_id"->ccRun,"n"->ccN,"q"->ccQ,"source_case_file"->ccFile,"source_face_fluxes_file"->ccCSVFile,
  "cells"->Length[ccCells],"faces"->Length[ccFaces],"recomputed_loss_W"->ccJoule,"recomputed_input_W"->ccInput,
  "recomputed_continuity_residual"->ccContinuity,"recomputed_port_current_relative_residual"->ccPortResidual,"recomputed_power_residual"->ccPower,
  "loss_match_relative_error"->ccLossDelta,"input_match_relative_error"->ccInputDelta,"archived_residuals"->ccCase["residuals"],
  "archived_GMRES_iterations"->ccCase["GMRES_iterations"],"archived_assembly_seconds"->ccCase["assembly_seconds"],"archived_solve_seconds"->ccCase["solve_seconds"]|>];
 AssociateTo[ccFluxes,ccID->ccCurrent];Clear[ccCSV,ccCSVData,ccFluxMap,ccLocal,ccDivergence,ccExternal,ccCurrent];
 stageData=<|"source_model"->"frozen_RT0_CSV_campaign_arithmetic","source_run_ids"->ccReferences,"recomputed_cases"->ccRows|>;stageSave[],{ccRun,ccReferences}];
stageCheck["four_distinct_expected_cases_collected",If[Sort[Lookup[ccRows,"case_id"]]===Sort[ccExpected],0,1],0,"frozen_source_selection"];
ccFind[id_]:=SelectFirst[ccRows,#["case_id"]==id&,Missing["NotCollected",id]];
ccComparisons={};
Do[ccA=ccFind[pair[[1]]];ccBRow=ccFind[pair[[2]]];If[AssociationQ[ccA]&&AssociationQ[ccBRow],
 ccDelta=Abs[ccBRow["recomputed_loss_W"]/ccA["recomputed_loss_W"]-1];
 stageCheck[pair[[1]]<>"_to_"<>pair[[2]]<>"_spatial",ccDelta,ccTolerance["spatial"],"frozen_RT0_spatial_loss"];
 AppendTo[ccComparisons,<|"kind"->"spatial","before_case_id"->pair[[1]],"after_case_id"->pair[[2]],"loss_relative_change"->ccDelta,"tolerance"->ccTolerance["spatial"],"execution_status"->If[ccDelta<=ccTolerance["spatial"],"passed","failed"]|>]],
 {pair,{{"rt0_n16_q14","rt0_n20_q14"},{"rt0_n20_q14","rt0_n24_q14"}}}];
ccA=ccFind["rt0_n24_q14"];ccBRow=ccFind["rt0_n24_q18"];
If[AssociationQ[ccA]&&AssociationQ[ccBRow],ccDelta=Abs[ccBRow["recomputed_loss_W"]/ccA["recomputed_loss_W"]-1];
 ccCurrentDelta=Norm[ccFluxes["rt0_n24_q18"]-ccFluxes["rt0_n24_q14"]]/Max[Norm[ccFluxes["rt0_n24_q18"]],$MinMachineNumber];
 stageCheck["n24_q14_to_q18_loss",ccDelta,ccTolerance["quadrature"],"frozen_RT0_quadrature_loss"];
 stageCheck["n24_q14_to_q18_complex_current",ccCurrentDelta,ccTolerance["quadrature"],"frozen_RT0_quadrature_complex_face_current"];
 AppendTo[ccComparisons,<|"kind"->"quadrature","before_case_id"->"rt0_n24_q14","after_case_id"->"rt0_n24_q18","loss_relative_change"->ccDelta,
  "complex_face_current_relative_change"->ccCurrentDelta,"tolerance"->ccTolerance["quadrature"],"execution_status"->If[Max[ccDelta,ccCurrentDelta]<=ccTolerance["quadrature"],"passed","failed"]|>]];
ccPassed=Length[ccRows]==4&&Length[ccComparisons]==3&&!AnyTrue[stageChecks,#["execution_status"]=="failed"&];
stageData=<|"source_model"->"frozen_RT0_CSV_campaign_arithmetic","execution_status"->If[ccPassed,"executed","failed"],
 "physical_acceptance_status"->If[ccPassed,"passed_cuboid_imposed_field_scope_only","failed_numerical"],"source_run_ids"->ccReferences,"recomputed_cases"->ccRows,"comparisons"->ccComparisons,
 "original_summary_status"->"Original q18 summary remains failed_numerical with null current metric; this new collector evaluates preserved face CSV data using strict e-notation parsing.",
 "resource_scope"->"q18 original raw resource aggregate includes non-physics reused-PID branches; precise full physics peak remains unknown. See its resource_identity_exclusions.json.",
 "physical_solver_calls"->0,"operator_or_FFT_calls"->0,"scope"->"Fixed1x1x2mm cuboid,1mT RMS imposed Bz,zero transport. CSV bookkeeping reconstructs continuity/common port and original RT0 local resistive overlap power independently; external-work power and spatial/quadrature sensitivities are recomputed. Solver voltage/true residuals are archived evidence, not reassembled. No masked-curved-geometry or independent boundary-flux validation."|>;
Export[FileNameJoin[{stageDir,"closure_rt0_collect_summary.json"}],stageData,"RawJSON"];stageSave[];Clear[ccFluxes];
