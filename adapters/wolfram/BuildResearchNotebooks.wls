$CharacterEncoding="UTF8";
root=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
requests=Import[FileNameJoin[{root,"configs","research_notebooks.json"}],"RawJSON"];
reports={};
Do[
 path=FileNameJoin[Prepend[StringSplit[r["path"],"/"],root]];
 params=r["parameters"];model=r["model_id"];
 init=RowBox[{"root","=","LitzNotebook`FindProject[NotebookDirectory[]]"}];
 initialization=With[{modelID=model},HoldComplete[
   projectRoot=NestWhile[DirectoryName,NotebookDirectory[],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&&DirectoryName[#]=!=#&];
   Get[FileNameJoin[{projectRoot,"shared","wolfram","ResearchNotebook.wl"}]];
 ]];
 inputs=With[{values=params},HoldComplete[parameters=values;parameters]];
 evaluation=With[{modelID=model},HoldComplete[research=LitzNotebook`RunResearch[projectRoot,modelID,parameters];LitzNotebook`ResearchSummary[research]]];
 view=HoldComplete[LitzNotebook`DisplayResearch[research]];
 (* Display constructors are called inside ResearchNotebook.wl so authored input
    boxes retain executable syntax rather than preformatted display grids. *)
 toBoxes[h_HoldComplete]:=ToBoxes[Defer@@h,StandardForm];
 cells={Cell[r["title"],"Title"],Cell["\:7f2a\:96e8\:8f69 / Miao Yuxuan \:00b7 \:6dee\:5357\:5e08\:8303\:5b66\:9662 / Huainan Normal University","Subtitle"],
 Cell[If[r["language"]==="zh-CN","\:6a21\:578b\:3001\:8f93\:5165\:4e0e\:9002\:7528\:8303\:56f4","Model, inputs and scope"],"Section"],Cell[r["equation"],"Text"],Cell[r["fixed_conventions"],"Text"],Cell[r["usage"],"Text"],
 Cell[BoxData[toBoxes[initialization]],"Input",InitializationCell->True],
 Cell[If[r["language"]==="zh-CN","\:53ef\:7f16\:8f91\:53c2\:6570","Editable parameters"],"Section"],Cell[BoxData[toBoxes[inputs]],"Input"],
 Cell[If[r["language"]==="zh-CN","\:72ec\:7acb\:8fdb\:7a0b\:6267\:884c\:4e0e\:7ed3\:679c","Independent execution and results"],"Section"],Cell[BoxData[toBoxes[evaluation]],"Input"],Cell[BoxData[toBoxes[view]],"Input"],
 Cell[If[r["language"]==="zh-CN","\:9a8c\:6536\:4e0e\:63a5\:7eed","Acceptance and continuation"],"Section"],
 Cell[If[r["language"]==="zh-CN","\:6838\:5bf9\:7ed3\:679c\:4e2d\:7684 checks\:3001execution_status \:548c physical_acceptance_status\:3002\:5b8c\:6574\:6536\:655b\:4e0e\:7ed3\:6784\:7814\:7a76\:6309\:8def\:7ebf README \:7ee7\:7eed\:3002","Inspect checks, execution_status and physical_acceptance_status. Continue full convergence and structural studies through the route README."],"Text"],
 Cell["Sources: "<>StringRiffle[r["references"],", "]<>"; references/library.bib and references/sources.json","Text"]};
 cells=cells/.Cell[data_,"Input",opts___]:>Cell[data,"Input",Evaluatable->True,CellTags->"research-input",opts];
 cells=Join[Take[cells,6],{Cell[If[r["language"]==="en","Derivation and interpretation","\:63a8\:5bfc\:4e0e\:7ed3\:679c\:89e3\:91ca"],"Section"]},(Cell[#,"Text"]&/@r["derivation"][r["language"]]),Drop[cells,6]];
 cells=Join[cells,{Cell[If[r["language"]==="en","Historical evidence","\:5386\:53f2\:8bc1\:636e"],"Section"],Cell[r["history"],"Text"]}];
 cells=cells/.Cell[data_,style_String,opts___]/;style=!="Input":>Cell[data,style,Evaluatable->False,opts];
 nb=Notebook[cells,StyleDefinitions->"Default.nb",WindowSize->{1100,850},TaggingRules-><|"route"->r["route"],"language"->r["language"],"source"->"configs/research_notebooks.json"|>,DefaultNewCellStyle->"Input"];
 Put[nb,path];AppendTo[reports,<|"path"->r["path"],"sha256"->FileHash[path,"SHA256","HexString"],"input_cells"->4|>],{r,requests}];
Export[FileNameJoin[{root,"outputs","automation_20261013_rc2","notebook_build.json"}],reports,"RawJSON"];
Print["BUILT_RESEARCH_NOTEBOOKS ",Length[reports]];
