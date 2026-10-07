rpName=Environment["LITZ_NOTEBOOK"];
If[!StringQ[rpName]||!MemberQ[FileNameTake/@FileNames["*.nb",FileNameJoin[{stageRoot,"notebooks"}]],rpName],Print["Notebook must be one existing basename"]; $Failed,
 rpFile=FileNameJoin[{stageRoot,"notebooks",rpName}];rpSnapshot=FileNameJoin[{stageDir,rpName}];CopyFile[rpFile,rpSnapshot];rpNBHash=FileHash[rpSnapshot,"SHA256","HexString"];rpNB=Get[rpSnapshot];
 rpInputs=Cases[rpNB,Cell[BoxData[b_],"Input",___]:>b,Infinity];rpResults={};
 Do[rpHeld=ToExpression[b,StandardForm,HoldComplete]/.HoldPattern[NotebookDirectory[]]->DirectoryName[rpFile];
  rpValue=TimeConstrained[Check[ReleaseHold[rpHeld],$Failed],600,$Aborted];
  AppendTo[rpResults,<|"input_index"->Length[rpResults]+1,"result_head"->ToString[Head[rpValue]],"failure"->(rpValue===$Failed||rpValue===$Aborted)|>];
  stageCheck["saved_input_"<>ToString[Length[rpResults]],If[Last[rpResults]["failure"],1,0],0,"fresh_kernel_headless_notebook_replay"],{b,rpInputs}];
 stageData=<|"source_model"->"fresh_kernel_headless_notebook_replay","notebook"->rpName,"notebook_sha256"->rpNBHash,"saved_input_snapshot"->rpName,"input_results"->rpResults,"frontend_validation"->"not_implied","assumptions"->"Sequential saved input boxes evaluated from an archived notebook snapshot in a fresh CLI kernel with NotebookDirectory supplied from the original project file. Frontend GUI interaction is independently pending. Cache dashboard inputs reconstruct plots from archived data; heavy solver execution is validated by separate fresh-process runs."|>;
];
