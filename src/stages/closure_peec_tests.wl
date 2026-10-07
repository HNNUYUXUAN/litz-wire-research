ctPath=FileNameJoin[{stageRoot,"tests","ClosurePEEC.wlt"}];
Export[FileNameJoin[{stageDir,"parameters.json"}],<|"source_model"->"small_independent_PEEC_regression","test_file"->"tests/ClosurePEEC.wlt","test_file_SHA256"->FileHash[ctPath,"SHA256","HexString"],"model_file_SHA256"->FileHash[FileNameJoin[{stageRoot,"src","PEEC.wl"}],"SHA256","HexString"],"scope"->"Default compatibility, Pairwise/GridOffsets matrices and common-voltage complex currents/power; no large model or GPU"|>,"RawJSON"];
ctReport=TestReport[ctPath];
ctObjects=Values[ctReport["TestResults"]];
Do[stageCheck[ToString[t["TestID"]],If[t["Outcome"]==="Success",0,1],0,"independent_small_PEEC_regression"],{t,ctObjects}];
stageData=<|"source_model"->"small_independent_pairwise_vs_grid_offset_PEEC_regression","tests_succeeded"->ctReport["TestsSucceededCount"],"tests_failed"->ctReport["TestsFailedCount"],"test_report"->ctReport,"physical_acceptance_status"->If[ctReport["TestsFailedCount"]==0,"passed_test_scope_only","failed_numerical"],"assumptions"->"Small default/operator/port equivalence regression with before-execution source snapshots and recorded process resources. Does not establish large-scale physical convergence."|>;
stageSave[];
