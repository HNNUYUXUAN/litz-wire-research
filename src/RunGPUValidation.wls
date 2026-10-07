(* Run in a new process: wolframscript -file src/RunGPUValidation.wls *)
gpuRunRoot = DirectoryName[DirectoryName[$InputFileName]];
gpuRunID = Environment["LITZ_RUN_ID"];
If[!StringQ[gpuRunID], gpuRunID = "gpu_" <> DateString[{"Year", "Month", "Day", "_", "Hour24", "Minute", "Second"}]];
Get[FileNameJoin[{gpuRunRoot, "src", "GPUValidation.wl"}]];
gpuRunResult = LitzGPU`RunGPUValidation[gpuRunRoot, gpuRunID];
If[FailureQ[gpuRunResult], Print[InputForm[gpuRunResult]]; Exit[1]];
gpuAcceptanceReport = TestReport[FileNameJoin[{gpuRunRoot, "tests", "GPUValidation.wlt"}]];
gpuAcceptanceSummary = <|"run_id" -> gpuRunID, "source_model" -> "GPU_runtime_acceptance_tests",
  "execution_status" -> If[gpuAcceptanceReport["TestsFailedCount"] == 0, "passed", "failed"],
  "tests_succeeded" -> gpuAcceptanceReport["TestsSucceededCount"], "tests_failed" -> gpuAcceptanceReport["TestsFailedCount"]|>;
Export[FileNameJoin[{gpuRunRoot, "outputs", gpuRunID, "acceptance_report.json"}], gpuAcceptanceSummary, "RawJSON"];
Print[InputForm[gpuAcceptanceSummary]];
If[gpuRunResult["execution_status"] =!= "passed" || gpuAcceptanceReport["TestsFailedCount"] > 0, Exit[1]];
