(* Physical-size layout of archived Graphics, with exact primitive identity checks. *)
$HistoryLength=0;$CharacterEncoding="UTF8";
Quiet[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8]];
Quiet[SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->8]];
root=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
Get[FileNameJoin[{root,"src","PublicationStyles.wl"}]];
requestPath=Last[$ScriptCommandLine];request=Import[requestPath,"RawJSON"];
out=request["output_directory"];records={};failures={};
label[s_]:=LitzPublication`PublicationText[s,9.5];
exportPanel[spec_]:=Module[{source,g,base,layout,pad,frame,sz,canvas,labels,new,legend,bar,range,fn,ticks,colors,path,assets={},r,ext,kind,primitives,diagnostic},
 If[FileHash[spec["source_expression"],"SHA256","HexString"] =!= spec["source_expression_sha256"],AppendTo[failures,"Source identity: "<>spec["id"]];Return[]];
 source=Get[spec["source_expression"]];base=source[[1]];layout=spec["layout"];
 pad=layout["padding_pt"];frame=layout["frame_pt"];sz=layout["plot_image_pt"];canvas=layout["canvas_pt"];kind=spec["layout_kind"];
 labels=(FrameLabel/.Options[base,FrameLabel])/.Rule[FontSize,_]:>Rule[FontSize,9.5];
 new=Show[base,ImageSize->sz,ImagePadding->pad,AspectRatio->frame[[2]]/frame[[1]],
   FrameLabel->labels,BaseStyle->{FontFamily->"Times New Roman",FontSize->9.5},
   FrameTicksStyle->Directive[FontFamily->"Times New Roman",FontSize->9],Background->White];
 diagnostic=<|"numeric_graphics_preserved"->SameQ[base[[1]],new[[1]]],
  "source_primitives_sha256"->Hash[base[[1]],"SHA256","HexString"],"output_primitives_sha256"->Hash[new[[1]],"SHA256","HexString"],
  "source_plot_range"->(PlotRange/.Options[base,PlotRange]),"output_plot_range"->(PlotRange/.Options[new,PlotRange])|>;
 primitives={Inset[new,{0,0},{Left,Bottom},sz]};
 If[kind==="curve",
   legend=source[[2,1]]/.Rule[FontSize,_]:>Rule[FontSize,9];
   legend=legend/.Rule[LegendMarkerSize,_]:>Rule[LegendMarkerSize,{16,9}];
   legend=Framed[legend,Background->None,FrameStyle->None,FrameMargins->3];
   AppendTo[primitives,If[spec["legend_anchor"]==="right",Inset[legend,{238,178},{Right,Top}],Inset[legend,{238,48},{Right,Bottom}]]],
   bar=First@Cases[source,_BarLegend,Infinity];
   fn=bar[[1,1]];range=bar[[1,2]];
   AssociateTo[diagnostic,{"color_range"->range,"color_function_sha256"->Hash[fn,"SHA256","HexString"],"color_endpoint_rgb"->(List@@ColorConvert[fn[#],"RGB"]&/@range)}];
   ticks=Select[Range[0,100,10],range[[1]]<=#<=range[[2]]&];
   colors=ImageResize[Image[Table[{List@@ColorConvert[fn[range[[1]]+(range[[2]]-range[[1]]) t],"RGB"]},{t,1,0,-1/2048}],ColorSpace->"RGB"],{128,2304}];
   AppendTo[primitives,Inset[colors,{208,40},{Left,Bottom},{8,144}]];AppendTo[primitives,{EdgeForm[Directive[GrayLevel[.4],AbsoluteThickness[.4]]],FaceForm[None],Rectangle[{208,40},{216,184}]}];
   Do[With[{y=40+144 (v-range[[1]])/(range[[2]]-range[[1]])},AppendTo[primitives,{Black,AbsoluteThickness[.4],Line[{{216,y},{219,y}}],Text[Style[ToString[v],FontFamily->"Times New Roman",FontSize->9],{221,y},{Left,Center}]}]],{v,ticks}];
   AppendTo[primitives,Text[label["|Jz|"],{230,20}]];
   AppendTo[primitives,Text[label["(A/mm\:00b2)"],{230,7}]]
 ];
 g=Graphics[primitives,PlotRange->{{0,canvas[[1]]},{0,canvas[[2]]}},PlotRangePadding->None,ImagePadding->0,
   ImageSize->canvas,AspectRatio->canvas[[2]]/canvas[[1]],Background->White];
 path=FileNameJoin[{out,"panels",spec["language"],spec["id"]}];
 If[!DirectoryQ[DirectoryName[path]],CreateDirectory[DirectoryName[path],CreateIntermediateDirectories->True]];
 Put[g,path<>".wl"];
 Do[r=Check[If[ext==="png",Export[path<>".png",Rasterize[g,"Image",RasterSize->{2100,1650}],"PNG",ImageResolution->600],Export[path<>"."<>ext,g,ToUpperCase[ext],ImageResolution->600]],$Failed];
 If[StringQ[r]&&FileExistsQ[r],AppendTo[assets,<|"format"->ext,"path"->r,"sha256"->FileHash[r,"SHA256","HexString"],"bytes"->FileByteCount[r]|>],AppendTo[failures,spec["id"]<>" "<>ext<>" export"]],{ext,{"pdf","svg","png"}}];
 AppendTo[records,Join[KeyDrop[spec,{"assets","native_expression"}],diagnostic,<|"assets"->assets,"native_expression"->path<>".wl","width_mm"->88.9,"height_mm"->69.85,"requested_font_size_pt"->9.5,"execution_status"->"completed","solver_executed"->False,"layout_sha256"->Hash[layout,"SHA256","HexString"]|>]];
 Print["PANEL ",spec["language"]," ",spec["id"]," primitives=",diagnostic["numeric_graphics_preserved"]]
];
UsingFrontEnd[Scan[exportPanel,request["panels"]]];
Export[FileNameJoin[{out,"panel_manifest.json"}],<|"schema_version"->1,"run_id"->request["run_id"],"panels"->records,"failures"->failures,"WolframVersion"->$Version,"physical_solver_executed"->False,"CPU_thread_cap"->8,"render_request_sha256"->FileHash[requestPath,"SHA256","HexString"]|>,"RawJSON"];
Exit[If[Length[failures]==0,0,1]];
