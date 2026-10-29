(* Independent serial/parallel regression; kept separate from the existing
   thirteen-test operator acceptance stage. *)
crpReport=TestReport[FileNameJoin[{stageRoot,"tests","VoxelOperatorParallel.wlt"}]];
crpRows=Map[Function[t,<|"id"->t["TestID"],"execution_status"->If[t["Outcome"]==="Success","passed","failed"],
 "expected"->ToString[t["ExpectedOutput"],InputForm],"actual"->ToString[t["ActualOutput"],InputForm]|>],Values[crpReport["TestResults"]]];
Scan[stageCheck[#["id"],If[#["execution_status"]=="passed",0,1],0,"serial_parallel_RT0_regression"]&,crpRows];
stageData=<|"source_model"->"small_serial_parallel_axis_group_RT0_regression","execution_status"->If[crpReport["TestsFailedCount"]==0,"executed","failed"],
 "physical_acceptance_status"->If[crpReport["TestsFailedCount"]==0,"passed_test_scope_only","failed"],
 "tests_succeeded"->crpReport["TestsSucceededCount"],"tests_failed"->crpReport["TestsFailedCount"],"tests"->crpRows,
 "scope"->"Original q6 pair/Duffy integral and floating summation order retained per pair. Small full inductance matrix, complex face currents and loss compared between serial and three axis workers. Original operator tests remain separate."|>;
Export[FileNameJoin[{stageDir,"parallel_regression.wxf"}],crpReport,"WXF"];stageSave[];
