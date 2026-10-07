bdStages={"analytic","fem2","coax","coax640","scale","circuits","geometry","copper","fem3","fem3_audit","fem3_ooc","fem3_iter","peec","voxel","voxel_scale","voxel_boundary","gpu","gpu_physics","gpu_scale","peec_equivalence","cpu_workers","frontend","handoff"};
Get[FileNameJoin[{stageRoot,"src","NotebookView.wl"}]];
bdProcessExit[id_]:=Module[{f=FileNameJoin[{stageRoot,"outputs",id,"process_status.json"}],a},If[!FileExistsQ[f],Return[Null]];a=Quiet[Check[ImportString[StringReplace[Import[f,"Text"],FromCharacterCode[65279]->""],"RawJSON"],$Failed]];If[AssociationQ[a],Lookup[a,"process_exit_code",Null],Null]];
bdRuns=Association[Map[Function[name,name->LitzView`OpenStage[stageRoot,name]],bdStages]];
bdSummary=Map[Function[name,With[{r=bdRuns[name]},If[AssociationQ[r],
 <|"route"->name,"run_id"->r["run_id"],"execution_status"->r["execution_status"],"source_model"->r["source_model"],"process_exit_code"->bdProcessExit[r["run_id"]],"passed_checks"->Count[Lookup[r["checks"],"execution_status"],"passed"],"failed_checks"->Count[Lookup[r["checks"],"execution_status"],"failed"],
 "remaining_uncertainty"->Switch[name,"coax","Large-strand attempts require separate mesh/return/outer convergence; infinite axial model.","fem3","Native nodal A-phi gauge/field convergence unresolved; prescribed analytical boundaries, no real finite ends.","peec","Longitudinal basis lacks transverse end loops; length/area/near quadrature sensitivity required.","voxel","Full vector closed-loop cuboid test passed only at recorded resolution; round/bent/strand geometry and independent 3D field comparison remain.","gpu","Synthetic CSR/GMRES and centre far kernel verified; physical longitudinal PEEC GPU integration is separately verified; fully resident Krylov and FEM iterative physics calibration remain unresolved.","geometry","Sampled collision/curvature; additive synthetic DTM omits nonlocal transitions.","copper","Uncoupled analytical strand prediction omits proximity; no final topology ranking.",_,"See source assumptions and tolerance report."]|>,<|"route"->name,"execution_status"->"not_run"|>]]],bdStages];
bdCoax=If[AssociationQ[bdRuns["coax"]],bdRuns["coax"]["data"],<||>];
bdScales=If[KeyExistsQ[bdCoax,"cases"],Map[KeyTake[#,{"strands","nodes","triangles","matrix_bytes","mesh_seconds","solve_seconds","bundle_Rac_ohm_per_m","power_residual"}]&,bdCoax["cases"]],{}];
stageData=<|"source_model"->"audited_execution_boundary","routes"->bdSummary,"coax_scale_attempts"->bdScales,"coax_first_blocked_case"->Lookup[bdCoax,"first_blocked_case",None],
 "device_maximum_claim"->False,"assumptions"->"This audit records the largest completed attempted cases and real validation failures; no last tested size is presented as the hardware maximum. Reserve-based rejection is an environment resource condition, not an absolute algorithmic limit. Native A-phi calibration failure is a model/numerical validation boundary. Full 3D structure performance is unresolved; no winning topology asserted."|>;
Export[FileNameJoin[{stageDir,"route_status.json"}],bdSummary,"RawJSON"];
Export[FileNameJoin[{stageDir,"coax_scale_attempts.json"}],bdScales,"RawJSON"];
If[Length[bdScales]>0,stageFigure["FEM_scale_memory",ListLogLogPlot[({#["nodes"],#["matrix_bytes"]/2.^20}&/@bdScales),Frame->True,FrameLabel->{"FEM nodes","sparse system (MiB)"},PlotMarkers->Automatic,ImageSize->600]]];
stageFigure["checks_by_route",BarChart[({Lookup[#,"passed_checks",0],Lookup[#,"failed_checks",0]}&/@bdSummary),ChartLabels->Lookup[bdSummary,"route"],ChartLegends->{"passed checks","failed checks"},ImageSize->800]];
bdResource=LitzView`OpenStage[stageRoot,"scale"];
If[AssociationQ[bdResource],bdResourceDir=FileNameJoin[{stageRoot,"outputs",bdResource["run_id"]}];bdCurve=Rest[Import[FileNameJoin[{bdResourceDir,"resource_curve.csv"}],"CSV"]];
 If[Length[bdCurve]>0,stageFigure["actual_kernel_memory",ListLinePlot[MapIndexed[{First[#2],ToExpression[ToString[#1[[2]]]]/2.^30}&,bdCurve],Frame->True,FrameLabel->{"resource sample","kernel working set (GiB)"},ImageSize->600]]]];




