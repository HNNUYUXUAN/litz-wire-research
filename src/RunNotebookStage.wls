$HistoryLength=0;$CharacterEncoding="UTF8";
stageThreadBudget=Quiet[Check[ToExpression[Environment["LITZ_CLOSURE_CPU_THREADS"]],8]];
If[!IntegerQ[stageThreadBudget]||stageThreadBudget<1,stageThreadBudget=8];
SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->Min[stageThreadBudget,$ProcessorCount]];
stageRoot=DirectoryName[DirectoryName[$InputFileName]];
stageName=Environment["LITZ_STAGE"];stageID=Environment["LITZ_RUN_ID"];
If[!StringQ[stageID]||!StringMatchQ[stageID,RegularExpression["[A-Za-z0-9_-]+"]],Exit[2]];
stageDir=FileNameJoin[{stageRoot,"outputs",stageID}];
If[FileExistsQ[FileNameJoin[{stageDir,"environment.json"}]],Print["Run already exists"];Exit[2]];
If[!DirectoryQ[stageDir],CreateDirectory[stageDir,CreateIntermediateDirectories->True]];
CreateDirectory[FileNameJoin[{stageDir,"figures"}]];
stageStart=AbsoluteTime[];stageChecks={};stageFigures=<||>;stageData=<||>;
stageCheck[id_String,actual_,tol_,model_String]:=Module[{ok=TrueQ[NumericQ[actual]&&actual<=tol]},
 AppendTo[stageChecks,<|"id"->id,"execution_status"->If[ok,"passed","failed"],"actual"->If[NumericQ[actual],N[actual],ToString[actual,InputForm]],"tolerance"->tol,"source_model"->model|>];
 Print[id," ",If[ok,"passed","failed"]," ",InputForm[actual]];ok];
stageSave[]:=(Export[FileNameJoin[{stageDir,"checkpoint.wxf"}],<|"data"->stageData,"figures"->stageFigures,"checks"->stageChecks|>,"WXF"];
 Export[FileNameJoin[{stageDir,"test_report.json"}],<|"run_id"->stageID,"execution_status"->"running","tests"->stageChecks|>,"RawJSON"]);
stageFigure[id_String,g_]:=(AssociateTo[stageFigures,id->g];Export[FileNameJoin[{stageDir,"figures",id<>".svg"}],g,"SVG"]);
Get[FileNameJoin[{stageRoot,"src","NotebookPhysics.wl"}]];
stageEnv=<|"run_id"->stageID,"stage"->stageName,"WolframVersion"->$Version,"SystemID"->$SystemID,"process_id"->$ProcessID,
 "paclets"->Map[<|"name"->#["Name"],"version"->#["Version"]|>&,Select[PacletFind[],MemberQ[{"WolframGPUSDK","CUDALink","Wolfram/AgentTools"},#["Name"]]&]],
 "ProcessorCount"->$ProcessorCount,"frontend_connected"->($FrontEnd=!=Null),"notebooks_supported"->$Notebooks,
 "RAM_budget_bytes"->Environment["LITZ_RAM_BUDGET"],"thread_options"->ToString[SystemOptions["ParallelOptions"],InputForm],
 "execution_status"->"running","timestamp_UTC"->DateString[DateObject[Now,TimeZone->0],"ISODateTime"]|>;
Export[FileNameJoin[{stageDir,"environment.json"}],stageEnv,"RawJSON"];
Export[FileNameJoin[{stageDir,"parameters.json"}],<|"stage"->stageName,"conductivity_S_per_m"->5.8*^7,"relative_permeability"->1,"frequency_Hz"->200000,"current_RMS_A"->20,"temperature_C"->20,"phasor"->"exp(+j omega t)","length_convention"->"axial metre"|>,"RawJSON"];
Print["START ",stageName," ",stageID];
stageSources=Join[FileNames["*.wl",FileNameJoin[{stageRoot,"src"}],Infinity],FileNames["*.wls",FileNameJoin[{stageRoot,"src"}]],FileNames["*.ps1",FileNameJoin[{stageRoot,"src"}]],FileNames["*.py",FileNameJoin[{stageRoot,"src"}]],FileNames["*.json",FileNameJoin[{stageRoot,"configs"}]],FileNames["*.wlt",FileNameJoin[{stageRoot,"tests"}]]];
CreateDirectory[FileNameJoin[{stageDir,"source_snapshot"}]];
stageManifest=Map[Function[file,With[{rel=FileNameDrop[file,FileNameDepth[stageRoot]]},With[{target=FileNameJoin[{stageDir,"source_snapshot",rel}]},If[!DirectoryQ[DirectoryName[target]],CreateDirectory[DirectoryName[target],CreateIntermediateDirectories->True]];CopyFile[file,target];<|"path"->rel,"sha256"->FileHash[file,"SHA256","HexString"]|>]]],stageSources];
Export[FileNameJoin[{stageDir,"run_manifest.json"}],<|"run_id"->stageID,"snapshot_time"->"before_stage_execution","sources"->stageManifest|>,"RawJSON"];
stageFile=FileNameJoin[{stageRoot,"src","stages",stageName<>".wl"}];
Block[{$MessageList={}},stageOutcome=If[TrueQ[SyntaxQ[Import[stageFile,"Text"]]],CheckAbort[Get[stageFile],$Aborted],Print["Stage syntax invalid"]; $Failed];stageMessages=ToString[#,InputForm]&/@$MessageList];
stageFailed=stageOutcome===$Failed||stageOutcome===$Aborted||AnyTrue[stageChecks,#["execution_status"]==="failed"&]||AnyTrue[stageMessages,StringContainsQ[#,"Syntax::"]&];
stageStatus=If[stageFailed,"failed",If[stageName==="build"||stageName==="handoff","constructed","executed"]];
stagePhysical=Lookup[stageData,"physical_acceptance_status",If[Length[stageChecks]==0,"not_verified",If[stageFailed,"failed_numerical","passed_test_scope_only"]]];
stageEnv["execution_status"]=stageStatus;stageEnv["elapsed_seconds"]=AbsoluteTime[]-stageStart;
Export[FileNameJoin[{stageDir,"environment.json"}],stageEnv,"RawJSON"];
stageSave[];
Export[FileNameJoin[{stageDir,"results.wxf"}],<|"run_id"->stageID,"stage"->stageName,"source_model"->Lookup[stageData,"source_model",stageName],"execution_status"->stageStatus,"data"->stageData,"figures"->stageFigures,"checks"->stageChecks|>,"WXF"];
Export[FileNameJoin[{stageDir,"results.json"}],<|"run_id"->stageID,"stage"->stageName,"source_model"->Lookup[stageData,"source_model",stageName],"execution_status"->stageStatus,"physical_acceptance_status"->stagePhysical,"failure_reason"->Lookup[stageData,"failure_reason",If[stageFailed,"see_test_report_and_messages",Null]],"elapsed_seconds"->AbsoluteTime[]-stageStart,"check_count"->Length[stageChecks],"failed_checks"->Count[Lookup[stageChecks,"execution_status"],"failed"],"messages"->stageMessages,"data_files"->{"results.wxf","checkpoint.wxf"}|>,"RawJSON"];
Export[FileNameJoin[{stageDir,"test_report.json"}],<|"run_id"->stageID,"execution_status"->If[Length[stageChecks]==0,"not_tested",If[stageFailed,"failed","passed"]],"tests"->stageChecks|>,"RawJSON"];
Export[FileNameJoin[{stageDir,"model_assumptions.md"}],Lookup[stageData,"assumptions","SI; exp(+j omega t); RMS; 20 C. Source model and applicable limits are recorded in results.wxf and the notebook."],"Text"];
Print["FINISH ",stageStatus," elapsed=",AbsoluteTime[]-stageStart];
If[stageFailed,Exit[1]];
Exit[0];

