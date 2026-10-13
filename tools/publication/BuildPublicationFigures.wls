$HistoryLength=0;$CharacterEncoding="UTF8";
Quiet[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8]];
Quiet[SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->8]];
pubRoot=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
Get[FileNameJoin[{pubRoot,"src","PublicationStyles.wl"}]];
Get[FileNameJoin[{pubRoot,"src","PublicationLineArt.wl"}]];
pubArgs=Rest[$ScriptCommandLine];
If[Length[pubArgs]<1,Print["A JSON render request is required."];Exit[2]];
pubRequest=Import[Last[pubArgs],"RawJSON"];
pubOutput=pubRequest["output_directory"];
pubFailures={};pubRecords={};
pubSizedFigure[g_,width_]:=Module[{w},w=First[ImageDimensions[Rasterize[g,"Image",ImageResolution->72]]];Magnify[g,N[width/w]]];
pubSpecimenNotebooks[]:=Module[{lang,t,base,figures,sized,widths,cells,nb,path,doc,img,restored,rotated,rotationPath,rotationDoc,rotationRead,rotationBoxes,rotationImage,rotationOK,rows={}},
 Do[
  t=pubRequest["notebook_texts"][lang];base=FileNameJoin[{pubOutput,"panels",lang}];
  figures=Get[FileNameJoin[{base,#<>".wl"}]]&/@{"q1_magnitude","q1_cross_section","multilevel_detail"};
  sized=pubSizedFigure[#,310]&/@figures;
  widths=First[ImageDimensions[Rasterize[#,"Image",ImageResolution->72]]]&/@sized;
  If[!And@@(#==310&/@widths),AppendTo[pubFailures,"Unequal Notebook figure widths: "<>lang]];
  cells={Cell[LitzPublication`PublicationTextData[t["title"],24],"Title"],Cell[LitzPublication`PublicationTextData[t["subtitle"],11],"Subtitle"],
   Cell[LitzPublication`PublicationTextData[t["section"],16],"Section"],Cell[LitzPublication`PublicationTextData[t["paragraph"],12],"Text"],
   LitzPublication`PublicationFormula[HoldForm[Subscript[R,dc]==(Sum[\[Sigma] Subscript[A,k]/Subscript[\[ScriptL],k],{k,1,n}])^-1]],
   Cell[BoxData[ToBoxes[Grid[{{sized[[1]],sized[[2]]}},Spacings->{2,1}],StandardForm]],"Output"],
   Cell[LitzPublication`PublicationTextData[t["caption_2d"],10],"Caption"],
   Cell[BoxData[ToBoxes[sized[[3]],StandardForm]],"Output"],
   Cell[LitzPublication`PublicationTextData[t["caption_3d"],10],"Caption"]};
  nb=Notebook[cells,StyleDefinitions->LitzPublication`PublicationStylesheet[],WindowSize->{1040,1080},DefaultNewCellStyle->"Text",TaggingRules-><|"PhysicalSolverExecuted"->False,"GPUComputeUsed"->False,"SpecimenRunID"->pubRequest["run_id"],"Native3DRotation"->True|>];
  path=FileNameJoin[{pubOutput,"specimen_"<>lang<>".nb"}];Put[nb,path];doc=NotebookOpen[path,Visible->False];NotebookSave[doc];
  img=Quiet[Check[Rasterize[doc,"Image",ImageResolution->120],$Failed]];
  If[ImageQ[img],Export[FileNameJoin[{pubOutput,"specimen_"<>lang<>".png"}],img,"PNG"],AppendTo[pubFailures,"Specimen Notebook rasterization failed: "<>lang]];
  restored=NotebookGet[doc];NotebookClose[doc];
  rotated=restored/.b_Graphics3DBox:>Apply[Graphics3DBox,Append[DeleteCases[List@@b,HoldPattern[ViewPoint->_]],ViewPoint->{-2.5,-2.,1.4}]];
  rotationPath=FileNameJoin[{pubOutput,"specimen_"<>lang<>"_rotated_roundtrip.nb"}];Put[rotated,rotationPath];
  rotationDoc=NotebookOpen[rotationPath,Visible->False];NotebookSave[rotationDoc];NotebookClose[rotationDoc];
  rotationDoc=NotebookOpen[rotationPath,Visible->False];rotationRead=NotebookGet[rotationDoc];
  rotationImage=Quiet[Check[Rasterize[rotationDoc,"Image",ImageResolution->120],$Failed]];
  If[ImageQ[rotationImage],Export[FileNameJoin[{pubOutput,"specimen_"<>lang<>"_rotated_roundtrip.png"}],rotationImage,"PNG"]];
  NotebookClose[rotationDoc];rotationBoxes=Cases[rotationRead,_Graphics3DBox,Infinity];
  rotationOK=Length[rotationBoxes]==1&&ImageQ[rotationImage]&&Cases[First[rotationBoxes],(ViewPoint->v_):>v,{1}]=={{-2.5,-2.,1.4}}&&FreeQ[First[rotationBoxes],_Apply|_DeleteCases|_Sequence]&&First[First[rotationBoxes]]===First[First[Cases[restored,_Graphics3DBox,Infinity]]];
  If[!rotationOK,AppendTo[pubFailures,"Native 3D viewpoint roundtrip failed: "<>lang]];
  AppendTo[rows,<|"language"->lang,"notebook"->path,"sha256"->FileHash[path,"SHA256","HexString"],"actual_NotebookObject_rendered"->ImageQ[img],"whole_notebook_render_scope"->"All cells of the complete small specimen NotebookObject", "native_3D_box_count"->Count[restored,_Graphics3DBox,Infinity],"input_count"->Count[restored,Cell[_,"Input",___],Infinity],"dynamic_count"->Count[restored,_DynamicBox|_DynamicModuleBox,Infinity],"figure_widths_at_72_dpi"->widths,"equal_figure_width_pt"->310,"viewpoint_changed_saved_reopened"->rotationOK,"rotation_roundtrip_copy"->rotationPath|>],
 {lang,pubRequest["languages"]}];
 Export[FileNameJoin[{pubOutput,"specimen_notebooks.json"}],<|"notebooks"->rows,"failures"->pubFailures,"physical_solver_executed"->False|>,"RawJSON"];
];
If[TrueQ[Lookup[pubRequest,"notebooks_only",False]],UsingFrontEnd[pubSpecimenNotebooks[]];Exit[If[Length[pubFailures]==0,0,1]]];
pubRGB[s_String]:=RGBColor@@(FromDigits[#,16]/255.&/@StringPartition[StringDrop[s,1],2]);
pubLabel[s_]:=LitzPublication`PublicationText[s,10];
pubBar[fn_,lo_,hi_,label_]:=With[{color=fn,lower=lo,upper=hi},BarLegend[{(color[Clip[(#-lower)/Max[upper-lower,10.^-30],{0,1}]]&),{lower,upper}},LegendLabel->LitzPublication`PublicationText[label,12.5],LabelStyle->{FontFamily->"Times New Roman",FontSize->12},LegendMarkerSize->{9,120}]];
pubPlot[raw_]:=Module[{spec,series,styles,g,leg,pts,kind=raw["kind"],opts,rows,fn,lo,hi,paths,radius,colors,values,body,image,ranges,center,span,primitives,vectors,vscale,nodes,columns,centers,reference,plotRange,ys,scaling},
 spec=If[KeyExistsQ[raw,"data_file"],Join[Import[raw["data_file"],"RawJSON"],raw],raw];
 If[KeyExistsQ[spec,"value_key"],AssociateTo[spec,"values"->spec[spec["value_key"]]]];
 opts=LitzPublication`PublicationPlotOptions[];
 Switch[kind,
 "mesh_outline",
  Graphics[{Directive[pubRGB["#265B8F"],AbsoluteThickness[.35]],GraphicsComplex[spec["points_mm"],Line[Append[#,First[#]]&/@spec["triangles"]]]},Frame->True,Axes->False,AspectRatio->1,FrameLabel->{pubLabel[spec["x_label"]],pubLabel[spec["y_label"]]},Evaluate[Sequence@@DeleteCases[opts,Frame->_|Axes->_]]],
 "strand_section",
  Graphics[Flatten[MapIndexed[{If[First[#2]==1,pubRGB["#265B8F"],pubRGB["#B87333"]],Disk[#1,spec["radius_mm"]],Inset[LitzPublication`PublicationText[ToString[First[#2]],9,If[First[#2]==1,White,Black]],#1]}&,spec["points_mm"]],1],Frame->True,Axes->False,AspectRatio->1,PlotRangePadding->Scaled[.15],FrameLabel->{pubLabel[spec["x_label"]],pubLabel[spec["y_label"]]},Evaluate[Sequence@@DeleteCases[opts,Frame->_|Axes->_|PlotRangePadding->_]]],
 "curve",
  series=spec["series"];styles=(Directive[pubRGB[Lookup[#,"color","#265B8F"]],AbsoluteThickness[1.25]]&/@series);
  pts=Lookup[series,"points"];
  reference=Lookup[spec,"reference_lines",{}];scaling=Lookup[spec,"scaling",None]/.Null->None;plotRange=All;
  If[Length[reference]>0,ys=Flatten[pts,1][[All,2]];
   plotRange={All,{If[ListQ[scaling]&&MemberQ[{"Log","Log10","Log2"},Last[scaling]],Min[Join[ys,reference]]/1.6,Min[0,Min[Join[ys,reference]]]],Max[Join[ys,reference]]*1.16}}];
  g=ListLinePlot[pts,PlotHighlighting->None,Joined->Lookup[spec,"joined",True],PlotStyle->styles,PlotRange->plotRange,AspectRatio->.8,GridLines->{None,reference},GridLinesStyle->Directive[GrayLevel[.75],Dashed],
   FrameLabel->{pubLabel[spec["x_label"]],pubLabel[spec["y_label"]]},ImagePadding->{{66,14},{37,12}},Evaluate[Sequence@@DeleteCases[opts,ImagePadding->_]],ScalingFunctions->scaling];
  If[Length[series]>1,g=Legended[g,Placed[LineLegend[styles,(LitzPublication`PublicationText[#["label"],9]&/@series),LegendLayout->"Column",LabelStyle->{FontFamily->"Times New Roman",FontSize->9}],Above]]];g,
 "density",
  rows=spec["points"];{lo,hi}=Lookup[spec,{"minimum","maximum"}];
  fn=If[Lookup[spec,"cyclic",False],LitzPublication`PublicationPhaseColor,LitzPublication`PublicationMagnitudeColor];
  g=With[{color=fn,lower=lo,upper=hi},ListDensityPlot[rows,InterpolationOrder->1,ColorFunction->(color[Clip[(#-lower)/(upper-lower),{0,1}]]&),ColorFunctionScaling->False,
   PlotRange->All,FrameLabel->{LitzPublication`PublicationText[spec["x_label"],12.5],LitzPublication`PublicationText[spec["y_label"],12.5]},AspectRatio->1,Mesh->None,
   BaseStyle->{FontFamily->"Times New Roman",FontSize->12.5},Evaluate[Sequence@@DeleteCases[opts,BaseStyle->_]]]];
  Legended[g,Placed[pubBar[fn,lo,hi,spec["color_label"]],Right]],
 "mesh_field"|"cell_field",
  pts=spec["points_mm"];values=spec["values"];{lo,hi}=Lookup[spec,{"minimum","maximum"},{Min[values],Max[values]}];
  fn=If[Lookup[spec,"cyclic",False],LitzPublication`PublicationPhaseColor,LitzPublication`PublicationMagnitudeColor];
  colors=fn[Clip[(#-lo)/Max[hi-lo,10.^-30],{0,1}]]&/@values;
  primitives=If[kind==="mesh_field",GraphicsComplex[pts,MapThread[{#2,EdgeForm[None],Polygon[#1]}&,{spec["triangles"],colors}]],
   MapThread[{#2,EdgeForm[None],Rectangle[#1-spec["cell_width_mm"]/2,#1+spec["cell_width_mm"]/2]}&,{pts,colors}]];
  ranges=Lookup[spec,"ranges_mm",Transpose[{Min/@Transpose[pts],Max/@Transpose[pts]}]];
  If[kind==="cell_field",ranges=ranges+{{-1,1},{-1,1}} spec["cell_width_mm"]/2];
  body=Graphics[primitives,PlotRange->ranges,ImagePadding->0,PlotRangePadding->0,ImageSize->252,Background->White];
  image=Rasterize[body,"Image",RasterSize->{2100,Automatic}];center=Mean/@ranges;span=Subtract@@Reverse[#]&/@ranges;
  g=Graphics[{Inset[image,center,Center,span]},PlotRange->ranges,Frame->True,Axes->False,AspectRatio->1,
   FrameLabel->{LitzPublication`PublicationText[spec["x_label"],12.5],LitzPublication`PublicationText[spec["y_label"],12.5]},
   BaseStyle->{FontFamily->"Times New Roman",FontSize->12.5},Evaluate[Sequence@@DeleteCases[opts,BaseStyle->_|Frame->_|Axes->_]]];
  Legended[g,Placed[pubBar[fn,lo,hi,spec["color_label"]],Right]],
 "field3d",
  pts=spec["points_mm"];values=spec["values"];{lo,hi}=Lookup[spec,{"minimum","maximum"},{Min[values],Max[values]}];
  fn=LitzPublication`PublicationMagnitudeColor;colors=fn[Clip[(#-lo)/Max[hi-lo,10.^-30],{0,1}]]&/@values;
  primitives=MapThread[{#2,PointSize[.012],Point[#1]}&,{pts,colors}];
  If[KeyExistsQ[spec,"vectors_real_phase0"],vectors=spec["vectors_real_phase0"];vscale=.12/Max[Norm/@vectors];
   primitives=MapThread[{#3,AbsoluteThickness[.7],Arrowheads[.015],Arrow[{#1,#1+vscale #2}]}&,{pts,vectors,colors}]];
  If[KeyExistsQ[spec,"geometry_dimensions_mm"],PrependTo[primitives,{FaceForm[Opacity[0]],EdgeForm[Directive[GrayLevel[.6],AbsoluteThickness[.5]]],Cuboid[{0,0,0},spec["geometry_dimensions_mm"]]}]];
  g=Graphics3D[primitives,Background->White,Lighting->{{"Ambient",White}},Axes->True,Boxed->True,
   AxesLabel->(LitzPublication`PublicationText[#,12.5]&/@{"x (mm)","y (mm)","z (mm)"}),
   BaseStyle->{FontFamily->"Times New Roman",FontSize->12.5},BoxStyle->Directive[GrayLevel[.55],AbsoluteThickness[.5]],
   ViewProjection->"Orthographic",ViewPoint->{2.2,-3.2,1.8},ViewVertical->{0,0,1},SphericalRegion->True,ImageSize->252,ImagePadding->{{50,30},{40,40}},PlotRange->All];
  Legended[g,Placed[pubBar[fn,lo,hi,spec["color_label"]],Right]],
 "schematic", pubLineArt[spec],
 "geometry",
  paths=spec["paths_mm"];radius=spec["radius_mm"];
  colors=Table[If[MemberQ[Lookup[spec,"highlight_ids",{}],i],pubRGB["#265B8F"],pubRGB["#B87333"]],{i,Length[paths]}];
  Graphics3D[MapThread[{#2,Specularity[White,18],Tube[#1,radius]}&,{paths,colors}],
   Background->White,Boxed->False,Axes->False,Lighting->{{"Ambient",GrayLevel[.52]},{"Directional",White,ImageScaled[{2,0,2}]},{"Directional",GrayLevel[.4],ImageScaled[{-2,1,1}]}},
   ViewPoint->{2.2,-3.2,1.8},ViewVertical->{0,0,1},ViewProjection->"Orthographic",ImageSize->252,
   PlotRange->All,SphericalRegion->True,BaseStyle->{FontFamily->"Times New Roman",FontSize->10}],
 _,AppendTo[pubFailures,"Unsupported kind: "<>kind];$Failed]
];
pubExport[spec_]:=Module[{g,path,assets={},start=AbsoluteTime[],r,ext,scene},
 path=FileNameJoin[{pubOutput,"panels",spec["language"],spec["id"]}];
 If[!DirectoryQ[DirectoryName[path]],CreateDirectory[DirectoryName[path],CreateIntermediateDirectories->True]];
 g=pubPlot[spec];If[g===$Failed,Return[]];
 Put[g,path<>".wl"];
 Do[
  r=Quiet[Check[If[ext==="png",Export[path<>".png",Rasterize[g,"Image",RasterSize->{2100,Automatic}],"PNG",ImageResolution->600],Export[path<>"."<>ext,g,ToUpperCase[ext],ImageResolution->600]],$Failed]];
  If[StringQ[r]&&FileExistsQ[r],AppendTo[assets,<|"format"->ext,"path"->r,"sha256"->FileHash[r,"SHA256","HexString"],"bytes"->FileByteCount[r]|>],AppendTo[pubFailures,spec["id"]<>" "<>ext<>" export failed"]],
 {ext,{"pdf","svg","png"}}];
 If[MemberQ[{"geometry","field3d"},spec["kind"]],Export[path<>".wxf",g,"WXF"]];
 AppendTo[pubRecords,<|"id"->spec["id"],"language"->spec["language"],"kind"->spec["kind"],"assets"->assets,"native_expression"->path<>".wl","width_mm"->88.9,"requested_font_size_pt"->10,"raster_dpi"->600,
  "elapsed_seconds"->(AbsoluteTime[]-start),"data_sha256"->spec["data_sha256"],"source_model"->spec["source_model"],"source_run_id"->spec["source_run_id"],"caption"->spec["caption"],"source_physical_acceptance_status"->Lookup[spec,"source_physical_acceptance_status","see frozen source scope"],"execution_status"->"export_attempt_completed; see asset count and failures","solver_executed"->False|>];
 Print["PANEL ",spec["language"]," ",spec["id"]," exports=",Length[assets]];
 Clear[g]
];
pubResult=TimeConstrained[UsingFrontEnd[
 pubFonts=$FontFamilies;
 (* Auxiliary-front-end kernels may return an empty $FontFamilies. That is not
    evidence of missing fonts. Actual exported font resources are checked by
    the Python verifier, and the actual NotebookObject is visually rendered. *)
 If[!And@@(FileExistsQ/@(FileNameJoin[{Environment["WINDIR"],"Fonts",#}]&/@{"simsun.ttc","times.ttf"})),AppendTo[pubFailures,"Requested Windows font files missing"]];
 If[Length[pubFailures]==0,Scan[pubExport,pubRequest["panels"]]];
 CreateDirectory[FileNameJoin[{pubOutput,"annotations"}],CreateIntermediateDirectories->True];
 Do[With[{label=Graphics[{Text[Style["("<>letter<>")",FontFamily->"Times New Roman",FontSize->10],{15,7.5}]},PlotRange->{{0,30},{0,15}},ImagePadding->0,ImageSize->{30,15},Background->White]},
  Export[FileNameJoin[{pubOutput,"annotations",letter<>".pdf"}],label,"PDF"];Export[FileNameJoin[{pubOutput,"annotations",letter<>".svg"}],label,"SVG"]],{letter,{"a","b","c","d"}}];
 True
],1800,$Failed];
If[pubResult===$Failed,AppendTo[pubFailures,"Native frontend/export timeout"]];
Export[FileNameJoin[{pubOutput,"panel_manifest.json"}],<|"schema_version"->1,"run_id"->pubRequest["run_id"],"panels"->pubRecords,"failures"->pubFailures,"WolframVersion"->$Version,"font_enumeration_status"->If[ListQ[pubFonts]&&Length[pubFonts]>0,"available","unavailable_in_auxiliary_frontend; verify actual exported fonts"],"CPU_thread_cap"->8,"physical_solver_executed"->False,"GPU_compute_used"->False,"render_request_sha256"->FileHash[Last[pubArgs],"SHA256","HexString"]|>,"RawJSON"];
Exit[If[Length[pubFailures]==0,0,1]];
