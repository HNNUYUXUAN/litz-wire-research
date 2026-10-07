(* Sequentially evaluate this project's saved input cells without claiming a frontend run. *)
nbRunRoot = DirectoryName[DirectoryName[$InputFileName]];
nbRunFile = FileNameJoin[{nbRunRoot, "notebooks", "01_Q1_Analytical.nb"}];
nbRunNotebook = Get[nbRunFile];
nbRunInputs = Cases[nbRunNotebook, Cell[BoxData[boxes_], "Input", ___] :> boxes, Infinity];
If[Length[nbRunInputs] < 1, Print["No analytical notebook inputs"]; Exit[2]];
nbRunHeldInputs = (ToExpression[#, StandardForm, HoldComplete] & /@ nbRunInputs) /.
  HoldPattern[NotebookDirectory[]] -> DirectoryName[nbRunFile];
Print["Mode: fresh-process headless sequential input evaluation; NotebookDirectory supplied from the saved file path. No interactive frontend claim."];
Print["Wolfram version: " <> $Version];
Scan[ReleaseHold, nbRunHeldInputs];
