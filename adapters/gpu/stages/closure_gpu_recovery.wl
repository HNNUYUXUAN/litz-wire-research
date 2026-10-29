(* Pure restoration of one completed cached case. No stage/PEEC/GPU source is evaluated. *)
grID="full_20261005_gpu_scale";
grDir=LitzEvidence`ReadPath[stageRoot,FileNameJoin[{stageRoot,"outputs",grID}]];
grExpected=<|"checkpoint.wxf"->"cf049efa53931b16e5c9cd3ebf0f2d7cfbeea083366087ce89b4518e33db322a",
 "results.wxf"->"3d101ebc363f52f3665eb804adb686dc29fe52740f89870385d7a52f120848f8"|>;
grModel="cached_longitudinal_PEEC_9856_evidence_recovery";
grStop[reason_]:=(stageData=<|"source_model"->grModel,"source_run_id"->grID,"failure_reason"->reason,
 "physical_acceptance_status"->"not_verified","solver_started"->False,"GPU_started"->False|>;stageSave[];Abort[]);
grRead[name_]:=Quiet[Check[Import[FileNameJoin[{grDir,name}],"RawJSON"],$Failed]];
grHash[path_]:=If[FileExistsQ[path],ToLowerCase[FileHash[path,"SHA256","HexString"]],"missing"];
grFinite[x_]:=NumericQ[x]&&FreeQ[x,Indeterminate|_DirectedInfinity];
grJSON[name_,value_]:=If[Quiet[Check[Export[FileNameJoin[{stageDir,name}],value,"RawJSON"],$Failed]]===$Failed,grStop["JSON_export_failed_"<>name]];
grHashes=Association@KeyValueMap[#1->grHash[FileNameJoin[{grDir,#1}]]&,grExpected];
stageCheck["pinned_cached_WXF_SHA256",If[grHashes===grExpected,0,1],0,"archived_file_identity"];
If[grHashes=!=grExpected,grStop["pinned_cached_file_hash_mismatch"]];
grManifest=grRead["run_manifest.json"];
If[!AssociationQ[grManifest]||!ListQ[Lookup[grManifest,"sources",None]],grStop["historical_source_manifest_unreadable"]];
grSources=Map[Function[row,With[{file=FileNameJoin[{grDir,"source_snapshot",row["path"]}]},
 <|"path"->row["path"],"expected_sha256"->ToLowerCase[row["sha256"]],"actual_sha256"->grHash[file],
 "execution_status"->If[grHash[file]===ToLowerCase[row["sha256"]],"passed","failed"]|>]],grManifest["sources"]];
stageCheck["historical_source_snapshot_SHA256",Count[Lookup[grSources,"execution_status"],"failed"],0,"archived_file_identity"];
grJSON["historical_source_hash_check.json",<|"source_run_id"->grID,"sources"->grSources|>];
If[AnyTrue[grSources,#["execution_status"]==="failed"&],grStop["historical_source_snapshot_hash_mismatch"]];
grPayload=Quiet[Check[Import[FileNameJoin[{grDir,"results.wxf"}],"WXF"],$Failed]];
If[!AssociationQ[grPayload]||!AssociationQ[Lookup[grPayload,"data",None]],grStop["cached_payload_unreadable"]];
grCases=Select[Lookup[grPayload["data"],"cases",{}],AssociationQ[#]&&Lookup[#,"cross_divisions",0]==112&&Lookup[#,"filaments",0]==9856&];
stageCheck["one_explicit_cached_9856_case",Abs[Length[grCases]-1],0,"cached_case_selection"];
If[Length[grCases]=!=1,grStop["cached_case_selection_is_not_unique"]];
grCase=First[grCases];grCurrents=Lookup[grCase,"currents",None];
stageCheck["cached_current_count_9856",If[ListQ[grCurrents],Abs[Length[grCurrents]-9856],1],0,"cached_current_restoration"];
stageCheck["cached_currents_are_finite",If[ListQ[grCurrents]&&AllTrue[grCurrents,grFinite],0,1],0,"cached_current_restoration"];
If[!ListQ[grCurrents]||Length[grCurrents]=!=9856||!AllTrue[grCurrents,grFinite],grStop["cached_currents_missing_or_invalid"]];
grParameters=grRead["parameters.json"];grTests=grRead["test_report.json"];grProcess=grRead["process_status.json"];
grStopRecord=grRead["resource_stop.json"];grResult=grRead["results.json"];
If[!AllTrue[{grParameters,grTests,grProcess,grStopRecord,grResult},AssociationQ],grStop["historical_evidence_unreadable"]];
stageCheck["source_parameters_match_project_conventions",If[Lookup[grParameters,"conductivity_S_per_m",0]==5.8*^7&&
 Lookup[grParameters,"frequency_Hz",0]==200000&&Lookup[grParameters,"current_RMS_A",0]==20&&
 Lookup[grParameters,"relative_permeability",0]==1&&Lookup[grParameters,"phasor",""]==="exp(+j omega t)",0,1],0,"cached_source_conventions"];
grOriginalChecks=Select[grTests["tests"],StringEndsQ[#["id"],"_9856"]&];
stageCheck["four_original_9856_checks_retained",Abs[Length[grOriginalChecks]-4],0,"historical_check_restoration"];
stageCheck["original_9856_case_checks_passed",Count[Lookup[grOriginalChecks,"execution_status"],Except["passed"]],0,"historical_check_restoration"];
grTotal=Total[grCurrents];grPortError=Abs[grTotal-20.]/20.;
stageCheck["cached_complex_current_total_20A_RMS",grPortError,10.^-10,"arithmetic_on_cached_currents"];
grN=9856;grM=112;grWidth=.002/grM;grArea=grN grWidth^2;
stageCheck["generated_basis_area_matches_cached_area",Abs[grArea/grCase["actual_area_m2"]-1],10.^-12,"generated_geometry_metadata"];
grCenters=Select[Flatten[Table[{x,y},{x,-.001+grWidth/2,.001-grWidth/2,grWidth},{y,-.001+grWidth/2,.001-grWidth/2,grWidth}],1],Norm[#]<=.001&];
stageCheck["generated_center_count_matches_cached_filaments",Abs[Length[grCenters]-grN],0,"generated_geometry_metadata"];
grCurrentRows=MapIndexed[{First[#2],N[Re[#1],17],N[Im[#1],17]}&,grCurrents];
Export[FileNameJoin[{stageDir,"currents_RMS_A.csv"}],Prepend[grCurrentRows,{"filament_id_1based","real_A_RMS","imag_A_RMS"}],"CSV"];
Export[FileNameJoin[{stageDir,"generated_geometry_centers_SI.csv"}],Prepend[MapIndexed[Prepend[#1,First[#2]]&,grCenters],{"filament_id_1based","x_m","y_m"}],"CSV"];
grRdc=1/(grParameters["conductivity_S_per_m"] grCase["actual_area_m2"]);
grLoss=grCase["length_m"]/(grParameters["conductivity_S_per_m"] grWidth^2) Total[Abs[grCurrents]^2];
grCachedLoss=grCase["Rac_ohm_per_axial_m"] 20.^2 grCase["length_m"];
stageCheck["cached_current_uniform_filament_loss_consistency",Abs[grLoss/grCachedLoss-1],10.^-10,"arithmetic_on_cached_currents_and_archived_uniform_basis"];
grCaseJSON=Join[KeyDrop[grCase,"currents"],<|"source_run_id"->grID,"source_model"->grPayload["source_model"],
 "execution_status"->"recovered_completed_cached_case","historical_case_checks"->grOriginalChecks,
 "historical_case_check_status"->If[AllTrue[grOriginalChecks,#["execution_status"]==="passed"&],"passed","failed"],
 "currents_RMS_A_re_im"->grCurrentRows,"current_total_RMS_A_re_im"->{Re[grTotal],Im[grTotal]},
 "cached_current_total_relative_error"->grPortError,"Rdc_ohm_per_axial_m_derived"->grRdc,
 "Rac_over_Rdc_derived"->grCase["Rac_ohm_per_axial_m"]/grRdc,"loss_W_segment_from_cached_Rac"->grCachedLoss,
 "loss_W_segment_from_cached_currents_uniform_basis"->grLoss,"copper_volume_m3_derived"->grCase["actual_area_m2"] grCase["length_m"],
 "arc_length_growth"->1.,"solver_started"->False,"GPU_started"->False|>];
grJSON["recovered_case_9856.json",grCaseJSON];
grJSON["recovery_parameters.json",Join[grParameters,<|"source_run_id"->grID,"cross_divisions"->112,"filaments"->9856,
 "axial_length_m"->grCase["length_m"],"actual_copper_area_m2"->grCase["actual_area_m2"],"cell_width_m_generated"->grWidth,
 "basis"->"Uniform axial Jz in centre-selected square cross sections; finite longitudinal PEEC.",
 "geometry_provenance"->"generated_geometry: deterministic grid formula transcribed from the SHA-verified archived PEEC.wl without evaluating that file. Coordinates were absent from the cached case."|>]];
grCopyDir=FileNameJoin[{stageDir,"historical_evidence"}];CreateDirectory[grCopyDir];
grFiles=Select[FileNameJoin[{grDir,#}]&/@{"checkpoint.wxf","results.wxf","results.json","parameters.json","test_report.json","process_status.json","resource_stop.json","resource_curve.csv","stderr.txt","run_log.txt","run_manifest.json","environment.json"},FileExistsQ];
Scan[CopyFile[#,FileNameJoin[{grCopyDir,FileNameTake[#]}]]&,grFiles];
grHistorySourcesDir=FileNameJoin[{stageDir,"historical_source_snapshot"}];
CopyDirectory[FileNameJoin[{grDir,"source_snapshot"}],grHistorySourcesDir];
grSourceFiles=Map[Function[file,<|"source_file"->FileNameDrop[file,FileNameDepth[stageRoot]],"bytes"->FileByteCount[file],
 "sha256"->grHash[file],"copied_file"->FileNameJoin[{"historical_evidence",FileNameTake[file]}],
 "copied_sha256"->grHash[FileNameJoin[{grCopyDir,FileNameTake[file]}]]|>],grFiles];
stageCheck["copied_historical_evidence_SHA256",Count[grSourceFiles,row_/;row["sha256"]=!=row["copied_sha256"]],0,"archive_copy_identity"];
grLog=Import[FileNameJoin[{grDir,"run_log.txt"}],"Text"];
grHistory=<|"source_run_id"->grID,"whole_source_run_execution_status"->grResult["execution_status"],
 "whole_source_run_process_exit"->grProcess["process_exit_code"],"resource_stop"->grStopRecord,
 "subsequent_case"-><|"cross_divisions"->160,"filaments"->20108,"execution_status"->"stopped_resource_budget_without_cached_completed_case",
 "solver_result_available"->False,"provenance"->"The archived run log starts cross_divisions160 after saving112/9856. Process/resource-stop records retain the later abort."|>,
 "resumed_prior_run_id"->"nb_gpu_scale_20261004_211853_922",
 "resumed_prior_cases"->{56,80},"resume_provenance"->"Explicit prior run ID printed in SHA-retained run_log.txt; recovery selects only112/9856.",
 "resource_memory_scope"->"The stop sample belongs to the subsequent20108 computation and is not a measured9856 peak.",
 "historical_9856_checks"->grOriginalChecks,"historical_all_checks"->grTests["tests"]|>;
stageCheck["known_subsequent_160_case_log_retained",If[StringContainsQ[grLog,"Physical PEEC GPU cross divisions=160"],0,1],0,"historical_log_identity"];
stageCheck["known_source_process_abort_retained",If[grProcess["process_exit_code"]==-1&&grResult["execution_status"]==="failed_process_exit",0,1],0,"historical_lifecycle_identity"];
grMissing={"cached_resistance_matrix_ohm","cached_partial_inductance_matrix_H","cached_augmented_impedance_matrix","cached_common_voltage_complex_RMS_V","cached_centers_m","cached_continuous_J_or_B_fields","9856_case_isolated_peak_working_memory","completed_20108_case"};
grProvenance=<|"recovery_run_id"->stageID,"source_run_id"->grID,"pinned_WXF_SHA256"->grHashes,"source_files"->grSourceFiles,
 "historical_source_hashes"->grSources,"selection"-><|"cross_divisions"->112,"filaments"->9856|>,
 "missing_fields"->grMissing,"known_history"->grHistory,"generated_geometry_file"->"generated_geometry_centers_SI.csv",
 "preservation_scope"->"Restores preserved scalar/timing/error/current values and verifies file identity and arithmetic. It neither regenerates absent matrices nor reruns their historical comparisons."|>;
grJSON["recovery_provenance.json",grProvenance];grJSON["historical_checks.json",grTests];
grJSON["recovery_summary.json",<|"source_model"->grModel,"source_run_id"->grID,"recovery_run_id"->stageID,
 "cached_case"->KeyDrop[grCaseJSON,"currents_RMS_A_re_im"],"known_history"->grHistory,"missing_fields"->grMissing,
 "source_provenance_file"->"recovery_provenance.json","solver_started"->False,"GPU_started"->False|>];
stageData=<|"source_model"->grModel,"source_run_id"->grID,"cases"->{grCase},"recovery_provenance"->grProvenance,
 "recovery_summary"->KeyDrop[grCaseJSON,"currents_RMS_A_re_im"],"physical_acceptance_status"->"passed_cached_9856_case_checks_and_recovery_arithmetic_only",
 "solver_started"->False,"GPU_started"->False,"assumptions"->"Pure cached evidence restoration: fixed112/9856 case from full_20261005_gpu_scale. SI, exp(+j omega t), RMS20A, sigma5.8e7,200kHz,20C,finite longitudinal length0.16m. Historical CPU/GPU operator/current/residual/power checks are copied as historical evidence. New checks validate source/copy hashes, saved currents and arithmetic only. Whole source run remains failed_process_exit -1; later160/20108 computation stopped on RAM reserve. No archived PEEC/stage/GPU source is evaluated. Generated centre-selected square geometry is metadata from the verified historical formula. Full vector PEEC, true transposition/end regions, spatial/length convergence and whole-run completion are separate evidence."|>;
stageSave[];
