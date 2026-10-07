(* Invoke with wolframscript -file src/RunCalibration.wls. Fresh process required. *)
q1RunRoot = DirectoryName[DirectoryName[$InputFileName]];
q1RunID = If[StringQ[Environment["LITZ_RUN_ID"]], Environment["LITZ_RUN_ID"], "q1_" <> DateString[{"Year", "Month", "Day", "_", "Hour24", "Minute", "Second"}]];
If[!StringMatchQ[q1RunID, RegularExpression["[A-Za-z0-9_-]+"]], Print["Invalid run ID"]; Exit[2]];
q1RunDirectory = FileNameJoin[{q1RunRoot, "outputs", q1RunID}];
Get[FileNameJoin[{q1RunRoot, "src", "Q1Analytical.wl"}]];
q1Run = LitzAnalytical`RunQ1Calibration[q1RunRoot, q1RunID];
If[!AssociationQ[q1Run], Print[q1Run]; Exit[2]];
q1Report = TestReport[FileNameJoin[{q1RunRoot, "tests", "Q1Analytical.wlt"}]];
q1Tests = Values[q1Report["TestResults"]];
q1Summary = <|"run_id" -> q1RunID, "source_model" -> "Wolfram_fresh_process_analytical_calibration",
  "execution_status" -> If[q1Report["TestsFailedCount"] == 0, "passed", "failed"],
  "tests_succeeded" -> q1Report["TestsSucceededCount"], "tests_failed" -> q1Report["TestsFailedCount"],
  "tolerances" -> <|"reference_relative_error" -> 10^-6, "current_and_power_integrals" -> 10^-8|>,
  "tests" -> Map[<|"id" -> #["TestID"], "outcome" -> #["Outcome"]|> &, q1Tests]|>;
Export[FileNameJoin[{q1RunDirectory, "test_report.json"}], q1Summary, "RawJSON"];
q1Saved = Import[FileNameJoin[{q1RunDirectory, "results.json"}], "RawJSON"];
q1Saved["metadata"] = Append[q1Saved["metadata"], "execution_status" -> q1Summary["execution_status"]];
Export[FileNameJoin[{q1RunDirectory, "results.json"}], q1Saved, "RawJSON"];

Print["Analytical calibration: ", q1Summary["tests_succeeded"], " passed, ", q1Summary["tests_failed"], " failed."];
Exit[If[q1Summary["tests_failed"] == 0, 0, 1]];
