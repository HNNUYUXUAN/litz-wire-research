$HistoryLength=0;$CharacterEncoding="UTF8";
root=DirectoryName[DirectoryName[$InputFileName]];Get[FileNameJoin[{root,"src","PublicationStyles.wl"}]];
req=Import[Last[Rest[$ScriptCommandLine]],"RawJSON"];out=req["output_directory"];
ver=Import[FileNameJoin[{out,"notebook_verification.json"}],"RawJSON"];records={};failures={};
linkBox[s_,file_,tag_]:=With[{box=Apply[RowBox,{First[LitzPublication`PublicationTextData[s,12]]}]},ButtonBox[box,BaseStyle->"Hyperlink",ButtonData->{file,tag}]];
finalize[]:=Module[{path,nb,old,positions,rules,links,toc,doc,saved,img,row,backup,paneCount,leafs,chunks,images,chunkDoc,k,renderOK,scope,headerPositions,subtitle,plainTexts,expectedTexts,coverage},
 Do[
 path=FileNameJoin[{out,item["path"]}];backup=FileNameJoin[{out,"layout_before_02",item["path"]}];If[!DirectoryQ[DirectoryName[backup]],CreateDirectory[DirectoryName[backup],CreateIntermediateDirectories->True]];CopyFile[path,backup];old=Get[FileNameJoin[{out,"typography_before_02",item["path"]}]];nb=old;
 positions=Position[nb,b:StyleBox[_,o___]/;MemberQ[{o},HoldPattern[Magnification->_]],Infinity];
 rules=Table[With[{box=Extract[nb,at]},at->PaneBox[box,ImageSize->{310,Automatic},ImageSizeAction->"ResizeToFit",Alignment->Center]],{at,positions}];nb=ReplacePart[nb,rules];paneCount=Length[positions];
 links=Select[item["cells"],#["type"]=="heading"&&#["level"]==1&];
 toc=Cell[TextData[Riffle[(linkBox[#["text"],FileNameTake[path],#["tag"]]&/@links)," | "]],"Text",Evaluatable->False];
 headerPositions=Prepend[#,1]&/@Position[First[nb],HoldPattern[Cell[Except[_CellGroupData],___]],Infinity];
 If[Take[(Extract[nb,#][[2]]&/@headerPositions),3]=!={"Title","Subtitle","Text"},AppendTo[failures,"Header structure failed: "<>item["id"]]];
 subtitle=If[item["language"]=="zh-CN",req["subtitle_zh"],req["subtitle_en"]];
 nb=ReplacePart[nb,{headerPositions[[1]]->Cell[LitzPublication`PublicationTextData[item["title"],24],"Title",Evaluatable->False],headerPositions[[2]]->Cell[LitzPublication`PublicationTextData[subtitle,11],"Subtitle",Evaluatable->False],headerPositions[[3]]->toc}];
 nb=nb/.HoldPattern[Cell[BoxData[b_],"DisplayFormula",o___]]:>Cell[BoxData[b],"DisplayFormula",ShowStringCharacters->False,o];
 Put[nb,path];doc=NotebookOpen[path,Visible->False];NotebookSave[doc];NotebookClose[doc];doc=NotebookOpen[path,Visible->False];saved=NotebookGet[doc];
 img=Quiet[Rasterize[doc,"Image",ImageResolution->72]];NotebookClose[doc];renderOK=ImageQ[img];scope="Complete final saved and reopened NotebookObject";
 If[!renderOK,
  leafs=Cases[First[saved],c:Cell[Except[_CellGroupData],___]:>c,Infinity];chunks=Partition[leafs,UpTo[12]];k=0;
  images=Table[k++;chunkDoc=NotebookPut[Notebook[chunk,StyleDefinitions->LitzPublication`PublicationStylesheet[],Visible->False]];img=Quiet[Rasterize[chunkDoc,"Image",ImageResolution->72]];NotebookClose[chunkDoc];If[ImageQ[img],Export[FileNameJoin[{out,"notebook_previews",item["id"]<>"_final_chunk_"<>ToString[k]<>".png"}],img,"PNG"]];img,{chunk,chunks}];
  renderOK=And@@(ImageQ/@images);img=First[images];scope="All final saved cells rendered in actual front-end NotebookObjects in consecutive batches of at most 12 cells"];
 If[renderOK,Export[FileNameJoin[{out,"notebook_previews",item["id"]<>".png"}],img,"PNG"],AppendTo[failures,"Final render failed: "<>item["id"]]];
 plainTexts=Cases[First[saved],HoldPattern[Cell[t_TextData,"Text",o___]]:>StringJoin[Cases[t/.HoldPattern[StyleBox[str_String,opts___]]:>str,_String,Infinity]],Infinity];
 expectedTexts=Lookup[Select[item["cells"],#["type"]=="text"&],"text"];coverage=And@@(MemberQ[plainTexts,#]&/@expectedTexts);
 If[!coverage,AppendTo[failures,"Narrative coverage failed: "<>item["id"]]];
 row=First[Select[ver["notebooks"],#["id"]==item["id"]&]];
 AssociateTo[row,{"sha256"->FileHash[path,"SHA256","HexString"],"all_cells_rendered"->renderOK,"render_scope"->scope,"saved_reopened"->MatchQ[saved,_Notebook],"panel_widths_pt"->Table[310,{paneCount}],"panel_equal_width"->True,"narrative_paragraph_coverage"->coverage,"panel_container"->"Native PaneBox with exact 310 pt width and ResizeToFit; native Graphics3D remains interactive","native_3D_content_unchanged"->(Map[First,Cases[old,_Graphics3DBox,Infinity]]===Map[First,Cases[saved,_Graphics3DBox,Infinity]]),"layout_previous_sha256"->FileHash[backup,"SHA256","HexString"]}];
 AppendTo[records,row];Print["FINAL LAYOUT ",item["id"]," panels=",paneCount," render=",renderOK];Clear[old,nb,saved,img,images];
 ,{item,req["documents"]}];
];
UsingFrontEnd[TimeConstrained[finalize[],3500,AppendTo[failures,"Final layout protection timeout"]]];
If[Length[records]==Length[req["documents"]],Export[FileNameJoin[{out,"notebook_verification.json"}],Join[ver,<|"notebooks"->records,"failures"->failures|>],"RawJSON"]];
Export[FileNameJoin[{out,"final_layout_verification.json"}],<|"notebooks"->records,"failures"->failures,"physical_solver_calls"->0|>,"RawJSON"];
Exit[If[Length[records]==Length[req["documents"]]&&Length[failures]==0,0,1]];
