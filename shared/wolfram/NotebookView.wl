BeginPackage["LitzView`"];
OpenStage::usage="OpenStage[root,stage] reads an explicitly pinned run; OpenStage[root,stage,runID] reads that exact evidence. No mtime selection.";
StageDashboard::usage="StageDashboard[root,stage] renders cached verified evidence and provenance.";
VoxelCurrentPlot::usage="VoxelCurrentPlot[result,phase] displays RT0 cell-centre instantaneous current directions from archived phasors; arrows use a stated relative scale.";
Begin["`Private`"];
OpenStage[root_String,stage_String,run_String] := Module[{file,meta},
 If[!StringMatchQ[run,RegularExpression["[A-Za-z0-9_-]+"]],Return[Failure["InvalidRunID",<||>]]];
 Get[FileNameJoin[{root,"shared","wolfram","Evidence.wl"}]];
 file=LitzEvidence`ReadPath[root,FileNameJoin[{root,"outputs",run}]];
 If[!And@@(FileExistsQ[FileNameJoin[{file,#}]]&/@{"results.json","results.wxf"}),Return[Failure["PinnedRunMissing",<|"stage"->stage,"run_id"->run|>]]];
 meta=Import[FileNameJoin[{file,"results.json"}],"RawJSON"];
 If[Lookup[meta,"stage",None]=!=stage,Return[Failure["PinnedStageMismatch",<|"stage"->stage,"run_id"->run|>]]];
 Needs["NDSolve`FEM`"];Import[FileNameJoin[{file,"results.wxf"}],"WXF"]];
OpenStage[root_String,stage_String] := Module[{path,index,row,run},
 path=FileNameJoin[{root,"docs","总控","当前运行索引.json"}];
 If[!FileExistsQ[path],Return[Failure["NoExplicitIndex",<|"stage"->stage|>]]];
 index=Import[path,"RawJSON"];
 row=If[AssociationQ[index],Lookup[Lookup[index,"routes",<||>],stage,<||>],FirstCase[index,_Association?(Lookup[#,"route",None]===stage&),<||>]];
 run=Lookup[row,"selected_run_id",Lookup[row,"run_id",None]];
 If[!StringQ[run],Return[Failure["NoPinnedStage",<|"stage"->stage|>]]];OpenStage[root,stage,run]];
StageDashboard[root_String,stage_String] := Module[{r=OpenStage[root,stage],parts},
 If[!AssociationQ[r],Return[r]];
 parts=Join[{Style["运行证据："<>r["run_id"],14,Bold],
 Row[{"source_model: ",r["source_model"],"   execution_status: ",r["execution_status"]}],Dataset[r["checks"]]},
 Values[r["figures"]],{Pane[Dataset[KeyDrop[r["data"],{"cases","geometries","solution"}]],ImageSize->{Automatic,300},Scrollbars->True]}];
 Column[parts]
];
VoxelCurrentPlot[r_Association,phase_?NumericQ] := Module[{local=r["local_face_ids"],curr=r["currents_RMS_A"],h=r["cell_width_m"],centres,j,peak},
 centres=1000 h (r["cells_coordinates"]-.5);
 j=Table[Table[Mean[(If[#==0,0.,Sqrt[2] Re[Exp[I phase] curr[[#]]]]&/@local[[cell,axis]])]/h^2,{axis,3}],{cell,r["cells"]}];peak=Max[Norm/@j];
 Graphics3D[{Opacity[.06],Cuboid[{0,0,0},1000 h r["dimensions"]],Opacity[1],Arrowheads[.035],MapThread[{ColorData["TemperatureMap"][Norm[#2]/Max[peak,10.^-30]],Arrow[{#1,#1+.7 (1000 h) #2/Max[peak,10.^-30]}]}&,{centres,j}]},Axes->True,AxesLabel->{"x (mm)","y (mm)","z (mm)"},BoxRatios->r["dimensions"],ImageSize->{600,500},PlotLabel->Row[{"RT0 cell-centre j(t), phase=",NumberForm[phase,3],"; max |j|=",NumberForm[peak/10.^6,3]," A/mm^2; relative arrow scale"}]]
];
End[];EndPackage[];
