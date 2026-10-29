(* Hardware tests consume actual GPU run metrics and independently specified tolerances. *)
gpuTestRoot = SelectFirst[{If[ValueQ[stageRoot],stageRoot,""],Environment["LITZ_PROJECT"],DirectoryName[DirectoryName[$InputFileName]],Directory[]},StringQ[#]&&FileExistsQ[FileNameJoin[{#,"configs","reference_parameters.json"}]]&];
If[MissingQ[gpuTestRoot],Print["Set LITZ_PROJECT to the research checkout."];Abort[]];
gpuTestID = Environment["LITZ_RUN_ID"];
gpuTestEnvironment = Import[FileNameJoin[{gpuTestRoot, "outputs", gpuTestID, "environment.json"}], "RawJSON"];
gpuTestReport = Import[FileNameJoin[{gpuTestRoot, "outputs", gpuTestID, "test_report.json"}], "RawJSON"];
gpuTestResults = Import[FileNameJoin[{gpuTestRoot, "outputs", gpuTestID, "results.json"}], "RawJSON"];
gpuTestCases = Association[Map[#["test_id"] -> #&, gpuTestReport["tests"]]];
VerificationTest[TrueQ[gpuTestEnvironment["CUDAQ"]] && gpuTestEnvironment["CUDA_device_count"] >= 1, True, TestID -> "NVIDIA_runtime_available"]
VerificationTest[And @@ Map[TrueQ[NumericQ[#["relative_L2_error"]] && #["relative_L2_error"] <= 10.^-10]&, Values[gpuTestCases]], True, TestID -> "All_GPU_numerical_errors_within_tolerance"]
VerificationTest[TrueQ[gpuTestCases["Custom_CUDA_FP64_kernel_tail_and_copyback"]["relative_L2_error"] <= 10.^-12], True, TestID -> "Compiled_custom_kernel_FP64_accuracy"]
VerificationTest[Length[gpuTestCases], 7, TestID -> "All_required_workloads_executed"]
VerificationTest[{gpuTestResults["GPUArray_real_element_type"], gpuTestResults["GPUArray_complex_element_type"]}, {"Real64", "ComplexReal64"}, TestID -> "Explicit_double_precision_preserved"]
