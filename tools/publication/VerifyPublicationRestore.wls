$HistoryLength=0;$CharacterEncoding="UTF8";
req=Import[Last[Rest[$ScriptCommandLine]],"RawJSON"];records={};failures={};
UsingFrontEnd[
 Do[path=FileNameJoin[{req["restore_directory"],item["path"]}];doc=NotebookOpen[path,Visible->False];n=NotebookGet[doc];NotebookClose[doc];ok=MatchQ[n,_Notebook]&&Count[n,Cell[_,"Input",___],Infinity]==0&&Count[n,_DynamicBox|_DynamicModuleBox,Infinity]==0;
 AppendTo[records,<|"id"->item["id"],"actual_open_read_close"->ok,"sha256"->FileHash[path,"SHA256","HexString"]|>];Print["RESTORE ",item["id"]," ",ok];If[!ok,AppendTo[failures,item["id"]]];Clear[n],{item,req["documents"]}];
 path=FileNameJoin[{req["restore_directory"],req["roundtrip_notebook"]}];
 copied=FileNameJoin[{req["restore_directory"],"restored_roundtrip.nb"}];CopyFile[path,copied];doc=NotebookOpen[copied,Visible->False];NotebookSave[doc];NotebookClose[doc];doc=NotebookOpen[copied,Visible->False];saved=NotebookGet[doc];NotebookClose[doc];Print["SPACE PATH SAVE/READ ",MatchQ[saved,_Notebook]];
 If[!MatchQ[saved,_Notebook],AppendTo[failures,"Space-path save/read roundtrip"]];
];
Export[req["verification_file"],<|"notebooks"->records,"failures"->failures,"space_path_save_reopen"->MatchQ[saved,_Notebook],"physical_solver_calls"->0|>,"RawJSON"];
Exit[If[Length[failures]==0,0,1]];
