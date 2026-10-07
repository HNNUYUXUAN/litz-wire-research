$HistoryLength=0;$CharacterEncoding="UTF8";
Quiet[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8]];
pubRoot=DirectoryName[DirectoryName[$InputFileName]];
Get[FileNameJoin[{pubRoot,"src","PublicationStyles.wl"}]];
req=Import[Last[Rest[$ScriptCommandLine]],"RawJSON"];out=req["output_directory"];
failures={};records={};widthChecks={};
compressRasters[expression_]:=Module[{positions,rules},positions=Position[expression,_RasterBox,Infinity];rules=Table[With[{rb=Extract[expression,at]},at->(rb/.RasterBox[a_,o___]:>With[{z=Compress[a]},RasterBox[CompressedData[z],o]])],{at,positions}];ReplacePart[expression,rules]];
textCell[s_,style_:"Text",tag_:None]:=Cell[LitzPublication`PublicationTextData[s,Switch[style,"Title",24,"Section",16,"Subsection",13,"Caption"|"FigureTitle"|"FigureDescription",10,"Reference",10,_,12]],style,Evaluatable->False,CellTags->If[tag===None,{},tag]];
linkBox[s_,file_,tag_]:=With[{box=Apply[RowBox,{First[LitzPublication`PublicationTextData[s,12]]}]},ButtonBox[box,BaseStyle->"Hyperlink",ButtonData->{file,tag}]];
linkedTextCell[c_]:=Module[{s=c["text"],links=Lookup[c,"links",{}],hits,content={},cursor=1,at,link},
 hits=SortBy[Flatten[Table[{#,l}&/@StringPosition[s,l["text"]],{l,links}],1],First[First[#]]&];
 Do[at=h[[1]];link=h[[2]];If[at[[1]]>=cursor,
   If[at[[1]]>cursor,content=Join[content,First[LitzPublication`PublicationTextData[StringTake[s,{cursor,at[[1]]-1}],12]]]];
   AppendTo[content,linkBox[link["text"],StringReplace[First[StringSplit[link["markdown"],"#"]],".md"->".nb"],link["tag"]]];cursor=at[[2]]+1],{h,hits}];
 If[cursor<=StringLength[s],content=Join[content,First[LitzPublication`PublicationTextData[StringDrop[s,cursor-1],12]]]];
 Cell[TextData[content],"Text",Evaluatable->False]
];
sizeFigure[g_]:=Module[{w,sized,actual},w=First[ImageDimensions[Rasterize[g,"Image",ImageResolution->72]]];sized=Pane[Magnify[g,N[310/w]],ImageSize->{310,Automatic},ImageSizeAction->"ResizeToFit",Alignment->Center];actual=First[ImageDimensions[Rasterize[sized,"Image",ImageResolution->72]]];AppendTo[widthChecks,actual];sized];
eqCell[c_]:=Module[{held,parts,n,grid},
 held=ToExpression[c["wolfram"],InputForm,HoldComplete];
 n=Count[held,_Equal,{3}];
 parts=If[MatchQ[held,HoldComplete[HoldForm[_List]]],Table[Extract[held,{1,1,k},HoldForm],{k,n}],{held[[1]]}];
 grid=Grid[Map[{TraditionalForm[#]}&,parts],Alignment->Left,Spacings->{1,.7},BaseStyle->{FontFamily->"Times New Roman",FontSize->13}];
 Cell[BoxData[ToBoxes[Row[{grid,Spacer[20],Style["("<>ToString[c["number"]]<>")",FontFamily->"Times New Roman",FontSize->12]}],StandardForm]],"DisplayFormula",Evaluatable->False,ShowStringCharacters->False,CellTags->c["id"]]
];
figureCells[c_]:=Module[{graphics,rows},
 graphics=sizeFigure[Get[FileNameJoin[{out,#}]]]&/@c["panels"];
 rows=Partition[graphics,UpTo[2]];
 If[Length[graphics]>1,rows=Table[MapIndexed[Column[{Style["("<>FromCharacterCode[96+(i-1)*2+First[#2]]<>")",FontFamily->"Times New Roman",FontSize->10],#1},Alignment->Center]&,rows[[i]]],{i,Length[rows]}]];
 {Cell[BoxData[ToBoxes[If[Length[graphics]==1,First[graphics],Grid[rows,Spacings->{1,.8},Alignment->Center]],StandardForm]],"Output",Evaluatable->False,TextAlignment->Center,CellTags->"fig"<>ToString[c["number"]]],textCell[c["title"],"FigureTitle"],textCell[c["description"],"FigureDescription"]}
];
makeCells[c_]:=Switch[c["type"],
 "text",{linkedTextCell[c]},
 "heading",{textCell[c["text"],If[c["level"]==1,"Section","Subsection"],c["tag"]]},
 "equation",{eqCell[c]},
 "figure",figureCells[c],
 "table",{textCell[c["title"],"Caption"],Cell[BoxData[ToBoxes[Grid[(LitzPublication`PublicationText[#,10]&/@#&)/@c["rows"],Frame->All,Background->{None,{GrayLevel[.96],White}},Alignment->Left,Spacings->{1,1}],StandardForm]],"Output",Evaluatable->False]},
 "link",{Cell[TextData[{ButtonBox[c["text"],BaseStyle->"Hyperlink",ButtonData->{c["target"],None}]}],"Text",Evaluatable->False]},
 _,AppendTo[failures,"Unknown cell type"];{}
];
renderChunkPreview[notebook_,id_]:=Module[{leafs,chunks,images,doc,image,k=0},leafs=Cases[First[notebook],c:Cell[Except[_CellGroupData],___]:>c,Infinity];chunks=Partition[leafs,UpTo[12]];images=Table[k++;doc=NotebookPut[Notebook[chunk,StyleDefinitions->LitzPublication`PublicationStylesheet[],Visible->False]];image=Quiet[Rasterize[doc,"Image",ImageResolution->72]];NotebookClose[doc];If[ImageQ[image],Export[FileNameJoin[{out,"notebook_previews",id<>"_chunk_"<>ToString[k]<>".png"}],image,"PNG"]];image,{chunk,chunks}];pubRenderScope="All saved cells rendered in actual front-end NotebookObjects in consecutive batches of at most 12 cells";If[And@@(ImageQ/@images),First[images],$Failed]];
runDocuments[]:=Module[{d,path,cells,nb,doc,restored,again,image,g3,rotation,rotationPath,rotationDoc,reread,rboxes,ok,rrimage,preview,tagLinks},
 Do[
  widthChecks={};d=item;path=FileNameJoin[{out,d["path"]}];If[!DirectoryQ[DirectoryName[path]],CreateDirectory[DirectoryName[path],CreateIntermediateDirectories->True]];
  tagLinks=Select[d["cells"],#["type"]=="heading"&&#["level"]==1&];
  cells=Join[{textCell[d["title"],"Title"],linkedTextCell[First[d["cells"]]],
   Cell[TextData[Riffle[(linkBox[#["text"],FileNameTake[path],#["tag"]]&/@tagLinks),"  \:00b7  "]],"Text",Evaluatable->False]},Flatten[makeCells/@Rest[d["cells"]],1]];
  nb=Notebook[cells,StyleDefinitions->LitzPublication`PublicationStylesheet[],WindowSize->{1100,1000},DefaultNewCellStyle->"Text",TaggingRules-><|"PublicationRunID"->req["run_id"],"PhysicalSolverExecuted"->False,"GPUComputeUsed"->False,"Language"->d["language"],"Edition"->d["edition"],"ArchiveDisplayMode"->True,"PanelWidthPt"->310|>];
  nb=compressRasters[nb];Put[nb,path];doc=NotebookOpen[path,Visible->False];NotebookSave[doc];NotebookClose[doc];
  doc=NotebookOpen[path,Visible->False];restored=NotebookGet[doc];NotebookClose[doc];If[!DirectoryQ[FileNameJoin[{out,"notebook_previews"}]],CreateDirectory[FileNameJoin[{out,"notebook_previews"}]]];image=renderChunkPreview[restored,d["id"]];
  preview=FileNameJoin[{out,"notebook_previews",d["id"]<>".png"}];If[!DirectoryQ[DirectoryName[preview]],CreateDirectory[DirectoryName[preview],CreateIntermediateDirectories->True]];
  If[ImageQ[image],Export[preview,image,"PNG"],AppendTo[failures,"Whole Notebook render failed: "<>d["id"]]];
  g3=Cases[restored,_Graphics3DBox,Infinity];ok=True;
  If[Length[g3]>0,
   rotation=restored/.b_Graphics3DBox:>Apply[Graphics3DBox,Append[DeleteCases[List@@b,HoldPattern[ViewPoint->_]],ViewPoint->{-2.5,-2.,1.4}]];
   rotationPath=FileNameJoin[{out,"rotation_roundtrips",d["id"]<>".nb"}];If[!DirectoryQ[DirectoryName[rotationPath]],CreateDirectory[DirectoryName[rotationPath],CreateIntermediateDirectories->True]];rotation=compressRasters[rotation];Put[rotation,rotationPath];
   rotationDoc=NotebookOpen[rotationPath,Visible->False];NotebookSave[rotationDoc];NotebookClose[rotationDoc];rotationDoc=NotebookOpen[rotationPath,Visible->False];reread=NotebookGet[rotationDoc];
   (* All native 3D boxes are checked after actual front-end save/reopen. *)
   rboxes=Cases[reread,_Graphics3DBox,Infinity];
   ok=Length[g3]==Length[rboxes]&&And@@(Cases[#,(ViewPoint->v_):>v,{1}]=={{-2.5,-2.,1.4}}&&FreeQ[#,_Apply|_DeleteCases|_Sequence]&/@rboxes)&&Map[First,g3]===Map[First,rboxes];
   rrimage=Quiet[Check[Rasterize[Notebook[{Cell[BoxData[First[rboxes]],"Output"]},StyleDefinitions->LitzPublication`PublicationStylesheet[]],"Image",ImageResolution->72],$Failed]];ok=ok&&ImageQ[rrimage];NotebookClose[rotationDoc];
  ];
  If[!ok,AppendTo[failures,"3D viewpoint roundtrip failed: "<>d["id"]]];
  If[!And@@(#==310&/@widthChecks),AppendTo[failures,"Panel width failed: "<>d["id"]]];
  AppendTo[records,<|"id"->d["id"],"path"->d["path"],"sha256"->FileHash[path,"SHA256","HexString"],"saved_reopened"->MatchQ[restored,_Notebook],"all_cells_rendered"->ImageQ[image],"render_scope"->pubRenderScope, "preview"->"notebook_previews/"<>d["id"]<>".png","cell_count"->Length[cells],"input_count"->Count[restored,Cell[_,"Input",___],Infinity],"dynamic_count"->Count[restored,_DynamicBox|_DynamicModuleBox,Infinity],"native_3D_count"->Length[g3],"viewpoint_roundtrip"->ok,"panel_widths_pt"->widthChecks,"panel_equal_width"->And@@(#==310&/@widthChecks)|>];
  Export[FileNameJoin[{out,"notebook_verification.json"}],<|"notebooks"->records,"failures"->failures,"WolframVersion"->$Version,"physical_solver_calls"->0|>,"RawJSON"];
  Print["NOTEBOOK ",d["id"]," cells=",Length[cells]," 3D=",Length[g3]," rendered=",ImageQ[image]," rotation=",ok];
  Clear[cells,nb,doc,restored,image,g3,rotation,reread,rboxes];ClearSystemCache[];
 ,{item,req["documents"]}];
 Do[
   path=FileNameJoin[{out,"composites",c["language"],c["id"]<>".pdf"}];image=First[Import[path,"PageImages",ImageResolution->200]];
   Export[FileNameJoin[{out,"composites",c["language"],c["id"]<>".png"}],image,"PNG"],{c,req["composites"]}];
];
UsingFrontEnd[TimeConstrained[runDocuments[],3500,AppendTo[failures,"Document export protection timeout"]]];
Export[FileNameJoin[{out,"notebook_verification.json"}],<|"notebooks"->records,"failures"->failures,"WolframVersion"->$Version,"physical_solver_calls"->0|>,"RawJSON"];
Exit[If[Length[failures]==0&&Length[records]==Length[req["documents"]],0,1]];
