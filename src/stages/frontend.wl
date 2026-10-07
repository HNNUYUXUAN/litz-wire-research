feCopy=FileNameJoin[{stageDir,"frontend_Q1_replay.nb"}];
feSource=FileNameJoin[{stageRoot,"notebooks","01_Q1_Analytical.nb"}];feNB=Get[feSource];
feNB=feNB/.Cell[BoxData[b_],"Input",opts___]:>With[{held=ToExpression[b,StandardForm,HoldForm]/.HoldPattern[NotebookDirectory[]]->DirectoryName[feSource]},Block[{$ContextPath={"System`"},$Context="Global`"},Cell[BoxData[ToBoxes[held]/.TagBox[bx_,HoldForm,___]:>bx],"Input",opts]]];
Block[{$ContextPath={"System`"},$Context="Global`"},Put[feNB,feCopy]];
Print["Attempt actual FrontEnd open, NotebookEvaluate and save on an isolated output copy."];
{feTime,feValue}=AbsoluteTiming[TimeConstrained[UsingFrontEnd[feObject=NotebookOpen[feCopy,Visible->False];feEval=NotebookEvaluate[feObject,InsertResults->True];NotebookSave[feObject];NotebookClose[feObject];<|"opened"->True,"evaluated"->True,"saved"->True|>],60,$Aborted]];
stageCheck["frontend_open_evaluate_save",If[AssociationQ[feValue],0,1],0,"actual_Wolfram_FrontEnd"];
If[AssociationQ[feValue],feSaved=Get[feCopy];feMessageCells=Length[Cases[feSaved,Cell[_,"Message",___],Infinity]];
 stageCheck["frontend_evaluated_no_error_cells",feMessageCells,0,"actual_Wolfram_FrontEnd"];
 stageCheck["frontend_evaluated_graphics",If[Length[Cases[feSaved,_GraphicsBox,Infinity]]>=4,0,1],0,"actual_Wolfram_FrontEnd"];
 stageCheck["frontend_chinese_title",If[MemberQ[Cases[feSaved,Cell[t_String,"Title",___]:>t,Infinity],"01 单圆铜线：推导、复电流与损耗"],0,1],0,"actual_Wolfram_FrontEnd"]];
stageData=<|"source_model"->"actual_Wolfram_FrontEnd","elapsed_seconds"->feTime,"result"->feValue,"assumptions"->"Open an output-directory copy of authored Q1 notebook, sequential FrontEnd evaluation with InsertResults->True, save and close. Does not modify original notebook or user installation. Timeout is preserved as frontend failure; headless and GPU successes are independent."|>;
Get[FileNameJoin[{stageRoot,"src","NotebookView.wl"}]];
Do[feVisual=LitzView`OpenStage[stageRoot,visualStage];If[AssociationQ[feVisual],fePreferred=Switch[visualStage,"analytic","complex_J","fem2","radial_comparison","geometry","geometry_multilevel","voxel","closed_loop_3D_current"];feGraphics={Lookup[feVisual["figures"],fePreferred]};If[Length[feGraphics]>0,fePNG=FileNameJoin[{stageDir,visualStage<>"_native_preview.png"}];UsingFrontEnd[Export[fePNG,Rasterize[First[feGraphics],"Image",ImageResolution->120],"PNG"]];stageCheck["native_preview_"<>visualStage,If[FileExistsQ[fePNG],0,1],0,"actual_FrontEnd_graphics_rasterization"]]],{visualStage,{"analytic","fem2","geometry","voxel"}}];


