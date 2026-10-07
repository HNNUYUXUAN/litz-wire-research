(* Static reading copies from frozen JSON/CSV references and PNG figures only.
   No WXF imports, original Input evaluation, physical packages or GPU calls. *)
$HistoryLength=0;$CharacterEncoding="UTF8";
Quiet[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8]];
Quiet[SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->8]];
baRoot=DirectoryName[DirectoryName[$InputFileName]];
Get[FileNameJoin[{baRoot,"src","ArchiveNotebookFormatting.wl"}]];
baDir=Environment["LITZ_CLOSURE_EXPORT_DIR"];
If[!StringQ[baDir]||!FileExistsQ[FileNameJoin[{baDir,"closure_manifest.json"}]],Print["Closure manifest missing"];Exit[2]];
baRead[p_]:=Quiet[Check[Import[p,"RawJSON"],<||>]];
baManifest=baRead[FileNameJoin[{baDir,"closure_manifest.json"}]];
baIndex=baRead[FileNameJoin[{baDir,"source_index.json"}]];
If[!AssociationQ[Lookup[baManifest,"routes",None]]||Sort[Keys[baManifest["routes"]]]=!=Sort[Keys[Lookup[baIndex,"routes",<||>]]],Print["Incomplete frozen closure export"];Exit[2]];
baIndexHash=FileHash[FileNameJoin[{baDir,"source_index.json"}],"SHA256","HexString"];
If[Lookup[baManifest,"source_index_sha256",None]=!=baIndexHash,Print["Frozen index SHA mismatch"];Exit[2]];
baCurrentIndex=Environment["LITZ_CLOSURE_INDEX"];
If[!StringQ[baCurrentIndex]||baCurrentIndex==="",baCurrentIndex=FileNameJoin[{baRoot,"docs","\:603b\:63a7","\:5f53\:524d\:8fd0\:884c\:7d22\:5f15.json"}]];
If[!FileExistsQ[baCurrentIndex]||FileHash[baCurrentIndex,"SHA256","HexString"]=!=baIndexHash,Print["Current index differs from frozen bundle"];Exit[2]];
baBundleName=FileNameTake[baDir];baNBDir=FileNameJoin[{baDir,"notebooks"}];baHTMLDir=FileNameJoin[{baDir,"viewer"}];
baReadingDir=FileNameJoin[{baRoot,"notebooks","archive",baBundleName}];
If[FileExistsQ[FileNameJoin[{baDir,"archive_notebooks.json"}]],Print["Archive build already exists; preserve it and select a new cache build directory"];Exit[2]];
baBuildSnapshot=FileNameJoin[{baDir,"archive_builder_source_snapshot","src"}];
If[DirectoryQ[baBuildSnapshot],Print["Archive builder snapshot already exists; preserve the earlier attempt"];Exit[2]];
CreateDirectory[baBuildSnapshot,CreateIntermediateDirectories->True];
baBuilderSources=Map[Function[p,With[{q=FileNameJoin[{baBuildSnapshot,FileNameTake[p]}]},CopyFile[p,q];<|"path"->StringReplace[FileNameDrop[p,FileNameDepth[baRoot]],"\\"->"/"],"snapshot_path"->StringReplace[FileNameDrop[q,FileNameDepth[baDir]],"\\"->"/"],"sha256"->FileHash[p,"SHA256","HexString"],"snapshot_sha256"->FileHash[q,"SHA256","HexString"]|>]],{$InputFileName,FileNameJoin[{baRoot,"src","ArchiveNotebookFormatting.wl"}]}];
Scan[If[!DirectoryQ[#],CreateDirectory[#,CreateIntermediateDirectories->True]]&,{baNBDir,baHTMLDir,baReadingDir}];
baEscape[s_]:=StringReplace[ToString[s],{"&"->"&amp;","<"->"&lt;",">"->"&gt;","\""->"&quot;"}];
baRel[p_]:=StringReplace[FileNameDrop[p,FileNameDepth[baDir]],"\\"->"/"];
baRootRel[p_]:=StringReplace[FileNameDrop[p,FileNameDepth[baRoot]],"\\"->"/"];
baText[x_]:=Which[x===Null,"\:672a\:8bb0\:5f55",x===True,"\:901a\:8fc7",x===False,"\:672a\:901a\:8fc7",NumberQ[x],ToString[NumberForm[N[x],8],StandardForm],ListQ[x],StringRiffle[baText/@x,", "],True,ToString[x]];
baCellText[x_]:=If[StringQ[x],x,baText[x]];
baTable[header_,rows_]:=Cell[BoxData[ToBoxes[Grid[Prepend[Map[baCellText,rows,{2}],header],Alignment->Left,Dividers->All,Background->{None,{RGBColor[.94,.96,.98]}},ItemSize->All,Spacings->{1,.7},BaseStyle->{FontSize->10}]]],"Output",Evaluatable->False];
baHTMLTable[header_,rows_]:="<table><thead><tr>"<>StringJoin[("<th>"<>baEscape[#]<>"</th>")&/@header]<>"</tr></thead><tbody>"<>StringJoin[("<tr>"<>StringJoin[("<td>"<>baEscape[baCellText[#]]<>"</td>")&/@#]<>"</tr>")&/@rows]<>"</tbody></table>";
baStatus[s_]:=Which[StringStartsQ[ToString[s],"passed"],"\:901a\:8fc7\:ff08\:9650\:5b9a\:8303\:56f4\:ff09",StringStartsQ[ToString[s],"failed"],"\:672a\:901a\:8fc7",StringStartsQ[ToString[s],"limited"],"\:8303\:56f4\:6709\:9650",StringStartsQ[ToString[s],"not_applicable"],"\:6570\:636e/\:5bfc\:51fa\:9a8c\:6536",True,"\:672a\:5b8c\:6574\:9a8c\:6536"];
baRows=Association@KeyValueMap[Function[{route,row},route->baRead[FileNameJoin[{baDir,row["metadata"]}]]],baManifest["routes"]];
baRoutesFor[stage_]:=LitzArchiveFormatting`ArchiveRoutesFor[stage,Keys[baManifest["routes"]]];

(* Optional manuscript figures have explicit route bindings and source hashes. *)
baFigureManifestPath=Environment["LITZ_CLOSURE_FIGURE_MANIFEST"];
If[!StringQ[baFigureManifestPath]||baFigureManifestPath==="",baFigureManifestPath=FileNameJoin[{baDir,"figdata","figures_manifest.json"}]];
baFigureManifest=If[FileExistsQ[baFigureManifestPath],baRead[baFigureManifestPath],<|"figures"->{}|>];
baResolveFigure[p_String]:=Module[{a=FileNameJoin[{baDir,p}],b=FileNameJoin[{baRoot,p}]},Which[FileExistsQ[a],a,FileExistsQ[b],b,True,$Failed]];
baFigureCells[st_,routes_,overview_]:=Module[{figs,priority,images={},html="",records={},path,img,caption,target,rel,figureID,sourceOK},
 figs=Select[Lookup[baFigureManifest,"figures",{}],Function[f,Length[Intersection[Lookup[f,"routes",{}],routes]]>0||MemberQ[Lookup[f,"stages",{}],st]]];
 priority=Switch[st,"boundary"|"environment",{"valid_resource_curves","gpu_equivalence","aphi_original_gates"},"peec",{"peec_length","peec_sensitivity","gpu_equivalence"},"voxel",{"rt0_spatial_quadrature","valid_resource_curves"},"fem3",{"aphi_original_gates"},"progress",{"rt0_spatial_quadrature","aphi_original_gates","valid_resource_curves"},"master"|"overview",{"peec_length","rt0_spatial_quadrature","gpu_equivalence","aphi_original_gates"},_,{}];
 figs=SortBy[figs,Function[f,First[FirstPosition[priority,Lookup[f,"figure_id",""],{100}]]]];
 If[Length[figs]==0&&!overview,figs=Flatten[Table[Map[Join[#,<|"title"->route,"caption"->"\:539f\:8fd0\:884c\:51bb\:7ed3\:56fe\:ff1a"<>baRows[route]["run_id"],"routes"->{route}|>]&,Select[Lookup[baManifest["routes"][route],"assets",{}],Lookup[#,"kind",""]==="preserved_figure"&&ToLowerCase[FileExtension[Lookup[#,"path",""]]]==="png"&]],{route,routes}]]];
 Do[path=baResolveFigure[Lookup[f,"path",""]];If[path===$Failed,Continue[]];
  sourceOK=AllTrue[Lookup[f,"source_files",{}],Function[s,With[{q=baResolveFigure[Lookup[s,"path",""]]},q=!=$Failed&&ToLowerCase[FileHash[q,"SHA256","HexString"]]===ToLowerCase[Lookup[s,"sha256",""]]]]];
  If[!sourceOK,AppendTo[baFailures,"figure source SHA mismatch: "<>Lookup[f,"figure_id",Lookup[f,"path",""]]];Continue[]];
  img=Quiet[Check[Import[path,"PNG"],$Failed]];If[!ImageQ[img],Continue[]];
  figureID=Lookup[f,"figure_id",FileBaseName[path]];target=FileNameJoin[{baDir,"figdata",figureID<>".png"}];
  If[!DirectoryQ[DirectoryName[target]],CreateDirectory[DirectoryName[target],CreateIntermediateDirectories->True]];
  If[path=!=target&&!FileExistsQ[target],CopyFile[path,target]];rel=baRel[target];
  caption=Lookup[f,"caption",Lookup[f,"title",figureID]];
  AppendTo[images,Cell[Lookup[f,"title",figureID],"Subsection"]];
  AppendTo[images,Cell[BoxData[ToBoxes[ImageResize[img,Min[680,First[ImageDimensions[img]]]]]],"Output",Evaluatable->False]];
  AppendTo[images,Cell[caption,"Text"]];
  html=html<>"<figure><img loading='lazy' src='../"<>rel<>"' alt='"<>baEscape[Lookup[f,"title",figureID]]<>"'><figcaption>"<>baEscape[caption]<>"</figcaption></figure>";
  AppendTo[records,<|"figure_id"->figureID,"path"->rel,"sha256"->FileHash[target,"SHA256","HexString"],"source_files"->Lookup[f,"source_files",{}]|>],
  {f,Take[figs,UpTo[If[overview,4,3]]]}];
 {images,html,records}];

baFiles=Sort[FileNames["*.nb",FileNameJoin[{baRoot,"notebooks"}]]];baRecords={};baFailures={};
Do[
 baSourceHash=FileHash[baFile,"SHA256","HexString"];baOriginal=Quiet[Check[Get[baFile],$Failed]];
 If[!MatchQ[baOriginal,_Notebook],AppendTo[baFailures,FileNameTake[baFile]];Continue[]];
 baTags=Replace[TaggingRules/.Options[baOriginal,TaggingRules],Except[_Association]-><||>];
 baStage=LitzArchiveFormatting`ArchiveStageFor[baFile,Lookup[baTags,"LitzStage","overview"]];baRoutes=baRoutesFor[baStage];
 baOverview=MemberQ[{"overview","master"},baStage];
 (* The legacy GPU source title has inherited mojibake. The reading-copy title
    is selected by its exact source filename; the original remains SHA-bound. *)
 baTitle=If[FileNameTake[baFile]==="00_GPU_Runtime_Check.nb","00 Wolfram NVIDIA GPU \:8fd0\:884c\:9a8c\:8bc1",FirstCase[baOriginal,Cell[s_String,"Title",___]:>s,FileBaseName[baFile],Infinity]];
 baIntro=LitzArchiveFormatting`ArchiveIntro[baStage];
 baCells={Cell[baTitle<>"\:ff5c\:6210\:7a3f\:5f52\:6863\:9605\:8bfb\:7248","Title"],Cell[baIntro,"Text"],Cell["\:7edf\:4e00\:7ea6\:5b9a\:ff1aSI \:8ba1\:7b97\:3001exp(+j\:03c9t)\:3001RMS \:76f8\:91cf\:ff1b\:03c3=5.8\:00d710\:2077 S/m\:3001\:03bcr=1\:300120 \:2103\:3002\:539f\:7814\:7a76 Notebook \:7684\:8f93\:5165\:4e0e\:5386\:53f2\:8f93\:51fa\:4fdd\:7559\:5728\:539f\:6587\:4ef6\:ff0c\:672c\:518c\:8bfb\:53d6\:51bb\:7ed3\:8bc1\:636e\:3002","Text"],
  Cell["\:51bb\:7ed3\:7d22\:5f15 SHA256\:ff1a"<>baIndexHash,"Text"],Cell["\:539f\:7814\:7a76 Notebook SHA256\:ff1a"<>baSourceHash,"Text"],Cell["\:6765\:6e90\:6587\:4ef6\:ff1anotebooks/"<>FileNameTake[baFile],"Text"],Cell["\:6a21\:578b\:516c\:5f0f\:4e0e\:9002\:7528\:8303\:56f4","Section"]};
 baCells=Join[baCells,LitzArchiveFormatting`ArchiveFormulaCells[baStage],{Cell["\:672c\:518c\:8bc1\:636e\:8def\:7ebf","Section"]}];
 baEvidenceRows=Map[Function[r,{r,baStatus[Lookup[baRows[r],"physical_acceptance_status","unknown"]],Lookup[baRows[r],"process_exit",Null]}],baRoutes];
 baChunks=Table[Take[baEvidenceRows,{i,Min[i+19,Length[baEvidenceRows]]}],{i,1,Length[baEvidenceRows],20}];
 Scan[AppendTo[baCells,baTable[{"\:51bb\:7ed3\:8def\:7ebf","\:79d1\:5b66\:9a8c\:6536\:8303\:56f4","\:539f\:8fdb\:7a0b\:9000\:51fa"},#]]&,baChunks];
 baHTML="<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>"<>baEscape[baTitle]<>"</title><style>body{max-width:1060px;margin:2rem auto;font:16px system-ui;line-height:1.65;padding:1rem;color:#1c2833}table{width:100%;border-collapse:collapse;font-size:14px}td,th{border:1px solid #cbd5df;padding:.5rem;text-align:left;overflow-wrap:anywhere}th{background:#edf2f6}img{max-width:100%;height:auto}section{margin:2rem 0;border-top:1px solid #d6dce3}a{color:#165d92}code{overflow-wrap:anywhere}</style><body><h1>"<>baEscape[baTitle]<>"\:ff5c\:6210\:7a3f\:5f52\:6863\:9605\:8bfb\:7248</h1><p>"<>baEscape[baIntro]<>"</p><p>\:51bb\:7ed3\:7d22\:5f15 SHA256\:ff1a<code>"<>baIndexHash<>"</code></p><p>\:7814\:7a76 Notebook SHA256\:ff1a<code>"<>baSourceHash<>"</code></p>"<>baHTMLTable[{"\:51bb\:7ed3\:8def\:7ebf","\:79d1\:5b66\:9a8c\:6536\:8303\:56f4","\:539f\:8fdb\:7a0b\:9000\:51fa"},baEvidenceRows];
 {baNewFigures,baFigureHTML,baFigureRecords}=baFigureCells[baStage,baRoutes,baOverview];baCells=Join[baCells,baNewFigures];baHTML=baHTML<>baFigureHTML;
 Do[
  baMeta=baRows[baRoute];baPin=baIndex["routes"][baRoute];baRow=baManifest["routes"][baRoute];baDataPath=FileNameJoin[{baDir,Lookup[baMeta,"data",""]}];
  If[!FileExistsQ[baDataPath],AppendTo[baFailures,baRoute<>" missing frozen data"];Continue[]];
  baCells=Join[baCells,{Cell[baRoute,"Section"],Cell["run_id="<>Lookup[baMeta,"run_id",""]<>"\:ff1bsource_model="<>Lookup[baMeta,"source_model",""]<>"\:ff1bphysical_acceptance_status="<>Lookup[baMeta,"physical_acceptance_status","unknown"],"Text"]}];
  baScope=Lookup[baPin,"scope",""];If[StringQ[baScope]&&baScope=!="",AppendTo[baCells,Cell[baScope,"Text"]]];
  baFailure=Lookup[baMeta,"failure_reason",Null];If[StringQ[baFailure]&&baFailure=!="",AppendTo[baCells,Cell["\:539f\:5931\:8d25\:8bb0\:5f55\:ff1a"<>StringTake[baFailure,UpTo[400]],"Text"]]];
  baData=If[baOverview,<||>,baRead[baDataPath]];
  baScalarRows=Join[LitzArchiveFormatting`ArchiveScalarRows[Lookup[baPin,"metrics",<||>],10],LitzArchiveFormatting`ArchiveScalarRows[baData,12]];
  baScalarRows=Take[DeleteDuplicatesBy[baScalarRows,First],UpTo[If[baOverview,6,14]]];
  If[Length[baScalarRows]>0,AppendTo[baCells,baTable[{"\:539f\:5b57\:6bb5\:ff08\:5355\:4f4d\:7531\:5b57\:6bb5\:4e0e\:6a21\:578b\:8bf4\:660e\:5b9a\:4e49\:ff09","\:51bb\:7ed3\:503c"},baScalarRows]]];
  baCSVAssets=Select[Lookup[baRow,"assets",{}],ToLowerCase[FileExtension[Lookup[#,"path",""]]]==="csv"&];
  baLinkRows=Join[{{"\:5b8c\:6574\:6570\:636e",Lookup[baMeta,"data",""]},{"\:9010\:9879\:68c0\:67e5",Lookup[baMeta,"numerical_roundtrip",""]}},({"\:5b8c\:6574 CSV",Lookup[#,"path",""]}&/@baCSVAssets)];
  baCells=Join[baCells,{Cell["\:5b8c\:6574\:6570\:5b57\:9644\:4ef6\:ff1a\:8def\:5f84\:76f8\:5bf9\:672c\:6210\:7a3f\:5305\:ff1bHTML \:9605\:8bfb\:7248\:63d0\:4f9b\:53ef\:70b9\:51fb\:94fe\:63a5\:3002\:6570\:7ec4\:3001\:590d\:7535\:6d41\:548c\:77e9\:9635\:4e0d\:5728\:672c\:9875\:5c55\:5f00\:3002","Text"]},(Cell[#[[1]]<>"\:ff1a"<>#[[2]],"Text"]&/@baLinkRows)];
  baHTML=baHTML<>"<section><h2>"<>baEscape[baRoute]<>"</h2><p>run_id\:ff1a<code>"<>baEscape[Lookup[baMeta,"run_id",""]]<>"</code></p><p>"<>baEscape[baScope]<>"</p><p>\:79d1\:5b66\:9a8c\:6536\:ff1a"<>baEscape[Lookup[baMeta,"physical_acceptance_status","unknown"]]<>"</p>"<>If[Length[baScalarRows]>0,baHTMLTable[{"\:539f\:5b57\:6bb5","\:51bb\:7ed3\:503c"},baScalarRows],""]<>"<ul>"<>StringJoin[("<li><a href='../"<>#[[2]]<>"'>"<>baEscape[#[[1]]]<>"\:ff1a"<>baEscape[#[[2]]]<>"</a></li>")&/@baLinkRows]<>"</ul></section>";
  Clear[baData],{baRoute,baRoutes}];
 baNB=Notebook[baCells,StyleDefinitions->"Default.nb",WindowSize->{1100,820},DefaultNewCellStyle->"Text",Editable->False,Saveable->True,
  TaggingRules-><|"ArchiveReadingCopy"->True,"SolverExecuted"->False,"GPUExecuted"->False,"CPUThreadCap"->8,"SourceNotebookSHA256"->baSourceHash,"FrozenIndexSHA256"->baIndexHash,"SourceNotebook"->FileNameTake[baFile],"LitzStage"->baStage,"SelectedRoutes"->baRoutes,"FrontendAcceptance"->"static_structure_verified_native_display_separately_recorded"|>];
 baTarget=FileNameJoin[{baNBDir,FileNameTake[baFile]}];Put[baNB,baTarget];baReadback=Get[baTarget];baCounts=LitzArchiveFormatting`ArchiveStaticCellCounts[baReadback];
 If[!MatchQ[baReadback,_Notebook]||Total[Lookup[baCounts,{"input_cell_count","dynamic_box_count","button_box_count"}]]!=0,AppendTo[baFailures,FileNameTake[baFile]<>" active or invalid notebook"]];
 If[FileHash[baFile,"SHA256","HexString"]=!=baSourceHash,AppendTo[baFailures,FileNameTake[baFile]<>" original changed"]];
 baCopy=FileNameJoin[{baReadingDir,FileNameTake[baFile]}];If[FileExistsQ[baCopy],AppendTo[baFailures,"Reading copy already exists: "<>baCopy],CopyFile[baTarget,baCopy]];
 baHTMLPath=FileNameJoin[{baHTMLDir,FileBaseName[baFile]<>".html"}];Export[baHTMLPath,baHTML<>"</body></html>","Text"];
 AppendTo[baRecords,Join[<|"source_notebook"->baRootRel[baFile],"source_sha256"->baSourceHash,"notebook"->baRel[baTarget],"notebook_sha256"->FileHash[baTarget,"SHA256","HexString"],"html"->baRel[baHTMLPath],"html_sha256"->FileHash[baHTMLPath,"SHA256","HexString"],"stage"->baStage,"routes"->baRoutes,"figures"->baFigureRecords,"solver_executed"->False,"gpu_executed"->False|>,baCounts]];
 Print["ARCHIVE ",FileNameTake[baFile]," routes=",Length[baRoutes]," output=",baCounts["output_cell_count"]];Clear[baOriginal,baNB,baReadback,baCells],{baFile,baFiles}];
Export[FileNameJoin[{baDir,"archive_notebooks.json"}],<|"schema_version"->2,"source_index_sha256"->baIndexHash,"build_source_sha256"->FileHash[$InputFileName,"SHA256","HexString"],"formatting_source_sha256"->FileHash[FileNameJoin[{baRoot,"src","ArchiveNotebookFormatting.wl"}],"SHA256","HexString"],"actual_builder_sources"->baBuilderSources,"notebooks"->baRecords,"failures"->baFailures,"frontend_acceptance"->"static_structure_verified_native_display_separately_recorded","WolframVersion"->$Version,"WolframProcessorCount"->$ProcessorCount,"CPU_thread_cap"->8,"GPU_executed"->False,"figure_manifest"->If[FileExistsQ[baFigureManifestPath],<|"path"->baFigureManifestPath,"sha256"->FileHash[baFigureManifestPath,"SHA256","HexString"]|>,Null],"process_exit_evidence"->"caller records actual child exit"|>,"RawJSON"];
Exit[If[Length[baFailures]==0,0,1]];
