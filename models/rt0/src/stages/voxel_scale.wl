Get[FileNameJoin[{stageRoot,"src","VoxelPEEC.wl"}]];
vxsCases={};
Do[Print["Refine RT0 dimensions=",dims];vxsOne=TimeConstrained[LitzVoxel`FaceFluxModel[dims,.001/dims[[1]],200000.,10,"field"],1800,$Aborted];
 If[!AssociationQ[vxsOne],stageCheck["voxel_refinement_solve",1,0,"RT0_PEEC"];Break[]];AppendTo[vxsCases,vxsOne];
 Scan[stageCheck["refine_"<>ToString[dims[[1]]]<>"_"<>#,vxsOne[#],If[#=="power_residual",.001,10.^-8],"RT0_PEEC"]&,{"linear_residual","continuity_residual","power_residual"}];
 Print[KeyTake[vxsOne,{"cells","face_flux_DOF","loss_W","assembly_seconds"}]];
 stageData=<|"source_model"->"RT0_PEEC_spatial_refinement","cases"->vxsCases|>;stageSave[],{dims,{{2,2,4},{3,3,6},{4,4,8}}}];
If[Length[vxsCases]==3,stageCheck["RT0_spatial_fine_change",Abs[vxsCases[[3]]["loss_W"]/vxsCases[[2]]["loss_W"]-1],.01,"RT0_PEEC"]];
stageData=<|"source_model"->"RT0_PEEC_spatial_refinement","cases"->vxsCases,"assumptions"->"Same 1x1x2 mm cuboid, uniform 1mT RMS Bz, zero net transport. Refine three-component RT0 discretization with fixed physical dimensions. Spatial change must pass separately from quadrature and conservation."|>;
