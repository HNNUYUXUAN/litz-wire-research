(* Local kernel, file and Notebook frontend checks in an independent run directory. *)
$HistoryLength=0;$CharacterEncoding="UTF8";
probeRoot=DirectoryName[DirectoryName[$InputFileName]];
probeID=Replace[Environment["LITZ_RUN_ID"],Except[_String]:>"environment_"<>DateString[{"Year","Month","Day","_","Hour24","Minute","Second"}]];
If[!StringMatchQ[probeID,RegularExpression["[A-Za-z0-9_-]+"]],Exit[2]];
probeDirectory=FileNameJoin[{probeRoot,"outputs",probeID}];
If[DirectoryQ[probeDirectory],Print["Run ID already exists"];Exit[2]];
CreateDirectory[probeDirectory,CreateIntermediateDirectories->True];
probeSpace=FileNameJoin[{probeDirectory,"path with spaces"}];CreateDirectory[probeSpace];
probeText=FileNameJoin[{probeSpace,"probe.txt"}];Export[probeText,"Local write/read test","Text"];
probeNotebook=FileNameJoin[{probeSpace,"environment.nb"}];
probeFrontend=Quiet[Check[UsingFrontEnd[Module[{nb,readback},
 nb=NotebookPut[Notebook[{Cell["Environment verification","Title"],Cell[BoxData[ToBoxes[1+1]],"Output"]},Visible->False]];
 NotebookSave[nb,probeNotebook];NotebookClose[nb];nb=NotebookOpen[probeNotebook,Visible->False];readback=NotebookGet[nb];NotebookClose[nb];MatchQ[readback,_Notebook]
]],False]];
probeResult=<|"run_id"->probeID,"source_model"->"local_environment_probe","WolframVersion"->$Version,"SystemID"->$SystemID,
 "kernel_arithmetic_passed"->TrueQ[1+1==2],"space_path_readback_passed"->TrueQ[Import[probeText,"Text"]=="Local write/read test"],
 "frontend_notebook_save_readback_passed"->TrueQ[probeFrontend],"execution_status"->"completed","physical_acceptance_status"->"environment_only",
 "timestamp_UTC"->DateString[TimeZoneConvert[Now,0],"ISODateTime"]|>;
Export[FileNameJoin[{probeDirectory,"environment.json"}],probeResult,"RawJSON"];
Print[InputForm[probeResult]];Exit[If[TrueQ[probeFrontend],0,1]];