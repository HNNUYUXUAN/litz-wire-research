BeginPackage["LitzNotebook`"];
RunResearch::usage="RunResearch[root,model,parameters] executes the shared bounded case in an independent process and imports results.";
FindProject::usage="FindProject[start] locates the research checkout without fixed user paths.";
ResearchSummary::usage="ResearchSummary[result] shows the run and acceptance identities.";
DisplayResearch::usage="DisplayResearch[result] displays current checks and native computed graphics.";
Begin["`Private`"];
ResearchSummary[r_Association]:=KeyTake[r["result"],{"run_id","source_model","execution_status","physical_acceptance_status"}];
DisplayResearch[r_Association]:=Column[{Dataset[KeyTake[r["result"],{"run_id","scope","checks"}]],If[KeyExistsQ[r["native"],"figure"],r["native"]["figure"],Dataset[r["result"]]]},Spacings->1.2];
FindProject[start_String]:=NestWhile[DirectoryName,start,!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&&DirectoryName[#]=!=#&];
RunResearch[root_String,model_String,parameters_Association]:=Module[{python,id,input,command,process,result,raw},
 python=Environment["LITZ_PYTHON"];
 If[!StringQ[python]||python==="",python=FileNameJoin[{root,".venv","Scripts","python.exe"}]];
 If[!FileExistsQ[python],python=FindExecutable["python"]];
 id=Environment["LITZ_NOTEBOOK_RUN_ID"];
 If[!StringQ[id]||id==="",id="notebook_"<>StringReplace[model,"-"->"_"]<>"_"<>DateString[{"Year","Month","Day","Hour","Minute","Second"}]<>"_"<>StringTake[CreateUUID[],8]];
 input=FileNameJoin[{$TemporaryDirectory,id<>".json"}];Export[input,parameters,"RawJSON"];
 command={python,"-m","litz_research","--project",root,"run",model,"--case",If[model==="aphi","diagnostic",If[model==="ansys","preflight","tutorial"]],"--parameters",input,"--run-id",id};
 process=RunProcess[command];DeleteFile[input];
 If[!FileExistsQ[FileNameJoin[{root,"outputs",id,"results.json"}]],Return[Failure["ResearchExecution",<|"exit_code"->process["ExitCode"],"stderr"->process["StandardError"]|>]]];
 result=Import[FileNameJoin[{root,"outputs",id,"results.json"}],"RawJSON"];
 raw=If[FileExistsQ[FileNameJoin[{root,"outputs",id,"results.wxf"}]],Import[FileNameJoin[{root,"outputs",id,"results.wxf"}],"WXF"],<||>];
 <|"run_id"->id,"result"->result,"native"->raw,"exit_code"->process["ExitCode"]|>
];
End[];EndPackage[];
