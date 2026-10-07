(* Fresh-kernel small-model regression stage. Parent runner owns logs,
   snapshots, resource monitoring, result archive and process exit status. *)
voTestStarted=AbsoluteTime[];
voTestFile=FileNameJoin[{stageRoot,"tests","VoxelOperator.wlt"}];
voRegression=TimeConstrained[TestReport[voTestFile],600.,$Aborted];
If[Head[voRegression]===TestReportObject,
 voRegressionRows=Map[Function[item,<|"id"->item["TestID"],"outcome"->ToString[item["Outcome"]],
   "execution_status"->If[item["Outcome"]==="Success","passed","failed"],
   "actual_output"->ToString[item["ActualOutput"],InputForm],"expected_output"->ToString[item["ExpectedOutput"],InputForm],
   "messages"->ToString[item["ActualMessages"],InputForm]|>],Values[voRegression["TestResults"]]];
 Scan[stageCheck[#["id"],If[#["execution_status"]=="passed",0,1],0,"small_RT0_FFT_GMRES_independent_regression"]&,voRegressionRows];
 stageCheck["required_RT0_operator_regressions_executed",Abs[Length[voRegressionRows]-13],0,"required_regression_count"];
 voRegressionStatus=If[voRegression["TestsFailedCount"]==0&&Length[voRegressionRows]==13,"passed","failed_numerical"],
 voRegressionRows={};voRegressionStatus="failed_process_or_timeout";
 stageCheck["RT0_operator_TestReport_completed",1,0,"TestReport_runtime"]];
voRegressionSummary=<|"run_id"->stageID,"source_model"->"small_RT0_matrix_free_original_dense_regression", "execution_status"->voRegressionStatus,
 "test_file"->FileNameJoin[{"tests","VoxelOperator.wlt"}],"test_file_sha256"->FileHash[voTestFile,"SHA256","HexString"],
 "elapsed_seconds"->AbsoluteTime[]-voTestStarted,"required_tests"->13,"completed_tests"->Length[voRegressionRows],
 "tests"->voRegressionRows,"failure"->If[Head[voRegression]===TestReportObject,Null,ToString[voRegression,InputForm]]|>;
Export[FileNameJoin[{stageDir,"voxel_operator_regression_report.json"}],voRegressionSummary,"RawJSON"];
stageData=<|"source_model"->"small_RT0_matrix_free_original_dense_regression","regression"->voRegressionSummary,
 "assumptions"->"13 fresh-kernel small-model regressions: original RT0 volume-integral matrix/face ordering and dense solve compared with exact zero-padded CPU FFT/Schur-GMRES; end impulses detect wrap-around; unequal masked conductor areas test autonomous common-port current division against a DC closed form. Passing these tests does not establish 32/128/1024-cell equivalence, spatial/quadrature convergence, curved geometry, finite-end electromagnetic calibration or topology performance."|>;
stageSave[];
