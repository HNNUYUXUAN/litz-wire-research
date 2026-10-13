BeginPackage["LitzGPU`"];
RunGPUValidation::usage = "RunGPUValidation[root, runID] verifies the existing local NVIDIA GPU runtime without installing packages.";
Begin["`Private`"];

SetAttributes[runCase, HoldRest];
runCase[id_, expression_, reference_, dimensions_, tolerance_] := Module[
  {value, expected, seconds, messages, valid, error},
  Print["GPU validation: " <> id];
  Block[{$MessageList = {}},
    {seconds, value} = AbsoluteTiming[TimeConstrained[Check[expression, $Failed], 180, $Aborted]];
    messages = ToString[#, InputForm]& /@ $MessageList;
  ];
  expected = reference;
  valid = ArrayQ[value, _, NumericQ] && Dimensions[value] === dimensions;
  error = If[valid, N[Norm[Flatten[value - expected]]/Max[Norm[Flatten[expected]], $MinMachineNumber]], Null];
  <|"test_id" -> id, "execution_status" -> If[valid && TrueQ[error <= tolerance], "passed", "failed"],
    "source_model" -> "GPU_runtime_synthetic_numerical_validation", "relative_L2_error" -> error,
    "relative_tolerance" -> tolerance, "dimensions" -> dimensions, "elapsed_seconds" -> seconds,
    "messages" -> messages, "result_head" -> ToString[Head[value], InputForm]|>
];

RunGPUValidation[root_String, runID_String] := Module[
  {dir, start, environment, parameters, cases = {}, sdk, init, initSeconds, info, ga, gb,
   a, b, cpuProduct, cpuSeconds, uploadSeconds, residentSeconds, gpuProduct, realType,
   mat, known, rhs, gmat, grhs, solveCPU, solveGPU, solveResult, residual, signal, gsignal,
   kernel, kernelSeconds, kernelData, kernelInput, summary, report, sourceFiles, manifest,
   log, passed, addCase, memA, memB, memProduct, fftMem, fftOut, fftInv, toolkitVersion, complexType},
  If[!StringMatchQ[runID, RegularExpression["[A-Za-z0-9_-]+"]], Return[Failure["InvalidRunID", <||>]]];
  dir = FileNameJoin[{root, "outputs", runID}];
  If[DirectoryQ[dir], Return[Failure["RunDirectoryAlreadyExists", <|"run_id" -> runID|>]]];
  CreateDirectory[dir, CreateIntermediateDirectories -> True];
  log = OpenWrite[FileNameJoin[{dir, "kernel_log.txt"}]];
  Block[{$Output = Append[$Output, log], $Messages = Append[$Messages, log], $ProgressReporting = False},
    start = AbsoluteTime[];
    parameters = <|"run_id" -> runID, "source_model" -> "local_GPU_runtime_validation",
      "execution_status" -> "running", "seed" -> 20261004, "real_precision" -> "Real64",
      "complex_precision" -> "ComplexReal64", "matrix_dimension" -> 512,
      "solve_dimension" -> 128, "fft_length" -> 4096, "kernel_length" -> 4099,
      "relative_tolerance" -> 10.^-10, "kernel_tolerance" -> 10.^-12|>;
    Export[FileNameJoin[{dir, "parameters.json"}], parameters, "RawJSON"];
    addCase[entry_] := (
      AppendTo[cases, entry];
      Export[FileNameJoin[{dir, "test_report_partial.json"}],
        <|"run_id" -> runID, "source_model" -> "GPU_runtime_synthetic_numerical_validation", "execution_status" -> "running", "tests" -> cases|>, "RawJSON"];
      Print[entry["test_id"], ": ", entry["execution_status"], "; relative L2 error = ", entry["relative_L2_error"]]
    );
    sdk = PacletFind["WolframGPUSDK"];
    environment = <|"run_id" -> runID, "source_model" -> "local_environment_probe",
      "execution_status" -> "running", "WolframVersion" -> $Version, "SystemID" -> $SystemID,
      "timestamp_UTC" -> DateString[DateObject[Now, TimeZone -> 0], "ISODateTime"],
      "process_id" -> $ProcessID, "frontend_connected" -> ($FrontEnd =!= Null),
      "paclets" -> Map[<|"Name" -> #["Name"], "Version" -> #["Version"]|>&,
        Select[PacletFind[], MemberQ[{"WolframGPUSDK", "CUDALink", "CUDATools", "CUDACompileTools", "Wolfram/AgentTools"}, #["Name"]]&]],
      "automatic_installation" -> False|>;
    If[sdk === {},
      environment["execution_status"] = "failed_missing_SDK";
      Export[FileNameJoin[{dir, "environment.json"}], environment, "RawJSON"];
      Close[log]; Return[Failure["MissingGPUSDK", <|"run_id" -> runID|>]]
    ];
    Needs["CUDALink`"];
    (* Per-kernel guard, no persistent user/system settings. *)
    CUDALink`$DisableWLGPUSDKDownload = True;
    {initSeconds, init} = AbsoluteTiming[CUDALink`CUDAQ[]];
    environment["CUDAQ"] = TrueQ[init];
    environment["initialization_seconds"] = initSeconds;
    If[!TrueQ[init],
      environment["execution_status"] = "failed_initialization";
      Export[FileNameJoin[{dir, "environment.json"}], environment, "RawJSON"];
      Close[log]; Return[Failure["CUDAInitializationFailed", <|"run_id" -> runID|>]]
    ];
    info = CUDALink`CUDAInformation[];
    toolkitVersion = Import[FileNameJoin[{First[sdk]["Location"], "CUDAResources", $SystemID, "version.json"}], "RawJSON"];
    environment["CUDA_toolkit_version"] = toolkitVersion["cuda"]["version"];
    environment["GPU"] = Association[1 /. info];
    environment["CUDA_information"] = ToString[info, InputForm];
    environment["CUDA_driver_version"] = CUDALink`CUDADriverVersion[];
    environment["CUDA_device_count"] = CUDALink`$CUDADeviceCount;
    environment["selected_CUDALink_device"] = ToString[CUDALink`$CUDADevice, InputForm];
    environment["execution_status"] = "passed";
    Export[FileNameJoin[{dir, "environment.json"}], environment, "RawJSON"];
    BlockRandom[
      SeedRandom[parameters["seed"]];
      a = RandomReal[{-1, 1}, {512, 512}]; b = RandomReal[{-1, 1}, {512, 512}];
      {cpuSeconds, cpuProduct} = AbsoluteTiming[a . b];
      {uploadSeconds, {ga, gb}} = AbsoluteTiming[{GPUArray[NumericArray[a, "Real64"]], GPUArray[NumericArray[b, "Real64"]]}];
      realType = ga["ElementType"];
      addCase[runCase["FP64_GPUArray_matrix_product", Normal[ga . gb], cpuProduct, {512, 512}, 10.^-10]];
      {residentSeconds, gpuProduct} = AbsoluteTiming[Normal[ga . gb]];
      addCase[runCase["FP64_CUDALink_matrix_product",
        memA = CUDALink`CUDAMemoryLoad[a, "Double"];
        memB = CUDALink`CUDAMemoryLoad[b, "Double"];
        memProduct = CUDALink`CUDADot[memA, memB];
        CUDALink`CUDAMemoryGet[memProduct], cpuProduct, {512, 512}, 10.^-10]];
      If[Head[memA] === CUDALink`CUDAMemory, CUDALink`CUDAMemoryUnload[memA]];
      If[Head[memB] === CUDALink`CUDAMemory, CUDALink`CUDAMemoryUnload[memB]];
      If[Head[memProduct] === CUDALink`CUDAMemory, CUDALink`CUDAMemoryUnload[memProduct]];
      mat = RandomReal[{-1, 1}, {128, 128}] + I RandomReal[{-1, 1}, {128, 128}] + 256. IdentityMatrix[128];
      known = Table[Sin[k/17.] + I Cos[k/19.], {k, 128}]; rhs = mat . known;
      gmat = GPUArray[NumericArray[mat, "ComplexReal64"]]; grhs = GPUArray[NumericArray[rhs, "ComplexReal64"]];
      complexType = gmat["ElementType"];
      addCase[runCase["Complex_FP64_linear_solve_known_solution", solveGPU = Normal[LinearSolve[gmat, grhs]], known, {128}, 10.^-10]];
      addCase[runCase["Complex_FP64_linear_solve_residual", mat . solveGPU, rhs, {128}, 10.^-10]];
      signal = Table[Sin[2 Pi 13 k/4096.] + I Cos[2 Pi 29 k/4096.], {k, 0, 4095}];
      (* GPUArray Fourier crashes in this installed CUDAArrays_Fourier.dll; use the independently verified CUDALink/cuFFT path. *)
      fftMem = CUDALink`CUDAMemoryLoad[signal, "ComplexDouble"];
      addCase[runCase["Complex_FP64_FFT_CPU_comparison", fftOut = CUDALink`CUDAFourier[fftMem]; CUDALink`CUDAMemoryGet[fftOut], Fourier[signal], {4096}, 10.^-10]];
      addCase[runCase["Complex_FP64_FFT_round_trip", fftInv = CUDALink`CUDAInverseFourier[fftOut]; CUDALink`CUDAMemoryGet[fftInv], signal, {4096}, 10.^-10]];
      Scan[If[Head[#] === CUDALink`CUDAMemory, CUDALink`CUDAMemoryUnload[#]]&, {fftMem, fftOut, fftInv}];
      kernelInput = N[Range[4099]/4096];
      kernelData = GPUArray[NumericArray[kernelInput, "Real64"]];
      {kernelSeconds, kernel} = AbsoluteTiming[Check[ExternalEvaluate["CUDA", Get[FileNameJoin[{root, "src", "GPUAffineKernel.wl"}]]], $Failed]];
      addCase[runCase["Custom_CUDA_FP64_kernel_tail_and_copyback", kernel[kernelData, Length[kernelInput]]; Normal[kernelData], 2 kernelInput + 1., {4099}, 10.^-12]];
    ];
    passed = AllTrue[cases, #["execution_status"] === "passed"&] && TrueQ[environment["CUDAQ"]];
    summary = <|"run_id" -> runID, "source_model" -> "GPU_runtime_synthetic_numerical_validation",
      "execution_status" -> If[passed, "passed", "failed"], "tests_succeeded" -> Count[Lookup[cases, "execution_status"], "passed"],
      "tests_failed" -> Count[Lookup[cases, "execution_status"], "failed"],
      "elapsed_seconds" -> N[AbsoluteTime[] - start], "GPUArray_real_element_type" -> realType,
      "GPUArray_complex_element_type" -> complexType,
      "benchmark" -> <|"matrix_dimension" -> 512, "precision" -> "Real64", "CPU_dot_seconds" -> cpuSeconds,
        "GPUArray_first_upload_including_backend_initialization_seconds" -> uploadSeconds, "GPU_first_dot_and_copyback_seconds" -> First[cases]["elapsed_seconds"],
        "GPU_warm_dot_and_copyback_seconds" -> residentSeconds, "custom_kernel_compile_seconds" -> kernelSeconds,
        "timing_scope" -> "wall time; Normal forces synchronization and includes device-to-host copy; no general speedup claim"|>,
      "scope" -> "Runtime, synthetic dense linear algebra, FFT and custom kernel only. No FEM/PEEC or physical model execution."|>;
    report = <|"run_id" -> runID, "source_model" -> summary["source_model"], "execution_status" -> summary["execution_status"], "tests" -> cases|>;
    Export[FileNameJoin[{dir, "results.json"}], summary, "RawJSON"];
    Export[FileNameJoin[{dir, "test_report.json"}], report, "RawJSON"];
    Export[FileNameJoin[{dir, "test_report.wl"}], report, "WL"];
    Export[FileNameJoin[{dir, "model_assumptions.md"}],
      "# GPU runtime verification\n\nSynthetic numerical validation; no electromagnetic/thermal result. NVIDIA GPU required; CPU fallback is not accepted. Explicit Real64/ComplexReal64. Seed 20261004. Relative L2 tolerance 1e-10 (custom kernel 1e-12). CPU comparison and known complex solution provide references. Fourier uses the same Wolfram default normalization/sign on both devices. Wall time includes synchronization and copyback. No automatic installation by this runner.\n", "Text"];
    sourceFiles = {"src/GPUValidation.wl", "src/RunGPUValidation.wls", "src/GPUAffineKernel.wl", "src/RunGPUValidation.ps1",
      "src/BuildGPUNotebook.wls", "src/EvaluateGPUNotebookHeadless.wls", "tests/GPUValidation.wlt"};
    CreateDirectory[FileNameJoin[{dir, "source_snapshot"}]];
    manifest = Map[Function[rel, With[{file = FileNameJoin[Prepend[StringSplit[rel, "/"], root]]},
      CopyFile[file, FileNameJoin[{dir, "source_snapshot", FileNameTake[file]}]];
      <|"path" -> rel, "sha256" -> FileHash[file, "SHA256", "HexString"]|>]], sourceFiles];
    Export[FileNameJoin[{dir, "run_manifest.json"}], <|"run_id" -> runID, "execution_status" -> summary["execution_status"], "sources" -> manifest|>, "RawJSON"];
    Print[InputForm[summary]];
  ];
  Close[log];
  summary
];
End[];
EndPackage[];
