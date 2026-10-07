(* Parent stage owns snapshots, one-hour/process-tree monitoring and exit evidence.
   This wrapper executes only the independent original-cache verifier child. *)
fvReferences=Environment["LITZ_CLOSURE_REFERENCE_RUNS"];
fvBudgetText=Environment["LITZ_RAM_BUDGET"];
fvBudget=If[StringQ[fvBudgetText]&&StringMatchQ[fvBudgetText,DigitCharacter..],Min[ToExpression[fvBudgetText],8 1024^3],0];
fvOutput=FileNameJoin[{stageDir,"frozen_validation"}];
fvValid=StringQ[fvReferences]&&fvReferences=!=""&&fvBudget>0;
stageCheck["frozen_verifier_explicit_references_and_budget",If[fvValid,0,1],0,"frozen_cache_validation_configuration"];
If[fvValid,
 (* Local wolframscript -file does not forward CLI args to $ScriptCommandLine.
    Its documented -script mode does; environment-only -file also works. *)
 fvCommand={If[$OperatingSystem==="Windows","wolframscript.exe","wolframscript"],"-script",FileNameJoin[{stageRoot,"src","VerifyFrozenPhysics.wls"}],"--output",fvOutput,"--reference-runs",fvReferences,"--memory-budget-bytes",ToString[fvBudget,InputForm]};
 fvProcess=Quiet[Check[RunProcess[fvCommand],$Failed]];
 If[AssociationQ[fvProcess],
  Export[FileNameJoin[{stageDir,"frozen_verifier_stdout.txt"}],fvProcess["StandardOutput"],"Text"];
  Export[FileNameJoin[{stageDir,"frozen_verifier_stderr.txt"}],fvProcess["StandardError"],"Text"];
  Export[FileNameJoin[{stageDir,"frozen_verifier_child_process.json"}],<|"process_exit_code"->fvProcess["ExitCode"],"ReferenceRuns"->StringSplit[fvReferences,","],"effective_verifier_budget_bytes"->fvBudget,"parent_stage_RAM_budget_text"->fvBudgetText,"solver_executed"->False|>,"RawJSON"];
  stageCheck["independent_frozen_verifier_child_exit",If[fvProcess["ExitCode"]===0,0,1],0,"original_WXF_JSON_CSV_readonly_verifier"],
  stageCheck["independent_frozen_verifier_child_exit",1,0,"original_WXF_JSON_CSV_readonly_verifier"]];
 fvReportPath=FileNameJoin[{fvOutput,"frozen_physics_validation.json"}];
 fvReport=If[FileExistsQ[fvReportPath],Quiet[Check[Import[fvReportPath,"RawJSON"],$Failed]],$Failed];
 stageCheck["independent_frozen_verifier_complete_report",If[AssociationQ[fvReport]&&Lookup[fvReport,"execution_status",""]==="passed_original_numeric_agreement",0,1],0,"original_WXF_JSON_CSV_readonly_verifier"];
 stageData=If[AssociationQ[fvReport],Join[fvReport,<|"source_model"->"prewrite_independent_original_frozen_physics_validation","child_process_exit"->If[AssociationQ[fvProcess],fvProcess["ExitCode"],Null],"physical_acceptance_status"->"not_applicable_original_cache_agreement_only","report_file"->"frozen_validation/frozen_physics_validation.json"|>],<|"source_model"->"prewrite_independent_original_frozen_physics_validation","execution_status"->"failed_or_incomplete_verification","physical_acceptance_status"->"not_applicable_cache_agreement","failure_reason"->"child_process_or_original_evidence_verification_failed","solver_executed"->False|>],
 stageData=<|"source_model"->"prewrite_independent_original_frozen_physics_validation","physical_acceptance_status"->"not_applicable_cache_agreement","failure_reason"->"missing_explicit_ReferenceRuns_or_positive_budget","solver_executed"->False|>];
