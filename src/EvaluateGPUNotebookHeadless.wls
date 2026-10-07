gpuNBRoot = DirectoryName[DirectoryName[$InputFileName]];
gpuNBFile = FileNameJoin[{gpuNBRoot, "notebooks", "00_GPU_Runtime_Check.nb"}];
gpuNBSaved = Get[gpuNBFile];
gpuNBInputs = Cases[gpuNBSaved, Cell[BoxData[boxes_], "Input", ___] :> boxes, Infinity];
If[Length[gpuNBInputs] =!= 1, Print["Unexpected GPU notebook input count"]; Exit[2]];
gpuNBHeld = (ToExpression[#, StandardForm, HoldComplete]& /@ gpuNBInputs) /.
  HoldPattern[NotebookDirectory[]] -> DirectoryName[gpuNBFile];
Print["Mode: saved GPU notebook input, sequential evaluation in a new kernel; no frontend claim."];
Scan[ReleaseHold, gpuNBHeld];
