(* Explicitly authorized one-time installation; never called by the verification runner. *)
gpuInstallRoot = DirectoryName[DirectoryName[$InputFileName]];
gpuInstallID = Environment["LITZ_RUN_ID"];
If[!StringQ[gpuInstallID] || !StringMatchQ[gpuInstallID, RegularExpression["[A-Za-z0-9_-]+"]], Exit[2]];
gpuInstallDir = FileNameJoin[{gpuInstallRoot, "outputs", gpuInstallID}];
If[!DirectoryQ[gpuInstallDir], CreateDirectory[gpuInstallDir, CreateIntermediateDirectories -> True]];
If[Environment["LITZ_ALLOW_GPU_SDK_INSTALL"] =!= "1", Print["Explicit SDK installation authorization is required."]; Exit[2]];
gpuInstallStarted = AbsoluteTime[];
Print["Installing the official WolframGPUSDK paclet. No driver, license or MCP configuration change."];
gpuInstallResult = If[PacletFind["WolframGPUSDK"] === {}, PacletInstall["WolframGPUSDK"], First[PacletFind["WolframGPUSDK"]]];
gpuInstallPaclets = PacletFind["WolframGPUSDK"];
gpuInstallSummary = <|"run_id" -> gpuInstallID, "source_model" -> "official_local_GPU_SDK_installation",
  "execution_status" -> If[gpuInstallPaclets === {}, "failed", "passed"],
  "WolframVersion" -> $Version, "SystemID" -> $SystemID,
  "timestamp_UTC" -> DateString[DateObject[Now, TimeZone -> 0], "ISODateTime"],
  "elapsed_seconds" -> N[AbsoluteTime[] - gpuInstallStarted],
  "paclets" -> Map[<|"Name" -> #["Name"], "Version" -> #["Version"]|>&, gpuInstallPaclets],
  "result_head" -> ToString[Head[gpuInstallResult], InputForm]|>;
Export[FileNameJoin[{gpuInstallDir, "installation.json"}], gpuInstallSummary, "RawJSON"];
Print[InputForm[gpuInstallSummary]];
If[gpuInstallPaclets === {}, Exit[1]];
