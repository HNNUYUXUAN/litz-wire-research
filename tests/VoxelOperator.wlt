voTestRoot=SelectFirst[{If[ValueQ[stageRoot],stageRoot,""],Environment["LITZ_PROJECT"],DirectoryName[DirectoryName[$InputFileName]],Directory[]},StringQ[#]&&FileExistsQ[FileNameJoin[{#,"configs","reference_parameters.json"}]]&];
If[MissingQ[voTestRoot],Print["Set LITZ_PROJECT to the research checkout."];Abort[]];
Get[FileNameJoin[{voTestRoot,"src","VoxelPEEC.wl"}]];
Get[FileNameJoin[{voTestRoot,"src","VoxelOperator.wl"}]];
voTestOld=LitzVoxel`FaceFluxModel[{2,2,3},.0005,200000.,6,"transport"];
voTestOp=LitzVoxelOperator`CreateOperator[{2,2,3},.0005,200000.,6,"transport"];
voTestVector=N[Sin[Range[voTestOp["face_flux_DOF"]]/3.]+I Cos[Range[voTestOp["face_flux_DOF"]]/5.]];
voTestNew=LitzVoxelOperator`SolveOperator[voTestOp,"TimeBudgetSeconds"->120.];
VerificationTest[voTestOp["faces"],voTestOld["faces"],TestID->"RT0-global-face-order-identical"]
VerificationTest[voTestOp["local_face_ids"],voTestOld["local_face_ids"],TestID->"RT0-local-basis-mapping-identical"]
VerificationTest[Norm[Flatten[Normal[voTestOp["R_ohm"]]-voTestOld["R_ohm"]]]/Norm[Flatten[voTestOld["R_ohm"]]]<10.^-12,True,TestID->"RT0-overlap-resistance-matrix-identical"]
VerificationTest[Norm[LitzVoxelOperator`ApplyInductance[voTestOp,voTestVector]-voTestOld["L_H"].voTestVector]/Norm[voTestOld["L_H"].voTestVector]<10.^-10,True,TestID->"Toeplitz-complex-matvec-versus-independent-original-assembly"]
VerificationTest[And@@Table[Norm[LitzVoxelOperator`ApplyInductance[voTestOp,UnitVector[voTestOp["face_flux_DOF"],j]]-voTestOld["L_H"][[All,j]]]/Norm[voTestOld["L_H"][[All,j]]]<10.^-10,{j,{1,voTestOp["face_flux_DOF"]}}],True,TestID->"Toeplitz-end-impulses-do-not-wrap"]
VerificationTest[TrueQ[voTestNew["converged"]]&&voTestNew["linear_residual"]<10.^-8,True,TestID->"GMRES-measured-true-residual"]
VerificationTest[Norm[voTestNew["currents_RMS_A"]-voTestOld["currents_RMS_A"]]/Norm[voTestOld["currents_RMS_A"]]<10.^-8,True,TestID->"GMRES-complex-currents-versus-original-dense-saddle-solve"]
VerificationTest[Abs[voTestNew["loss_W"]/voTestOld["loss_W"]-1]<10.^-6,True,TestID->"GMRES-Joule-loss-versus-original-dense-saddle-solve"]
VerificationTest[voTestNew["power_residual"]<.001&&voTestNew["continuity_residual"]<10.^-8,True,TestID->"RT0-physical-power-and-continuity"]
voTestMask=Join[Table[{1,1,z},{z,3}],Flatten[Table[{3,y,z},{y,2},{z,3}],1]];
voTestMaskOp=LitzVoxelOperator`CreateOperator[{3,2,3},.0005,0.,4,"transport","ActiveCells"->voTestMask,"ConductorLabels"->Join[ConstantArray[1,3],ConstantArray[2,6]]];
voTestMaskSol=LitzVoxelOperator`SolveOperator[voTestMaskOp,"TimeBudgetSeconds"->120.];
VerificationTest[Sort[Values[voTestMaskSol["source_conductor_currents_RMS_A"]]]//Chop,{20./3,40./3},SameTest->(Norm[#1-#2]<10.^-8&),TestID->"Unequal-masked-conductors-share-port-without-forced-equal-currents"]
VerificationTest[Abs[voTestMaskSol["loss_W"]/(400./(5.8*^7 .0005))-1]<10.^-8,True,TestID->"Masked-unequal-conductor-DC-independent-closed-form"]
VerificationTest[MatchQ[LitzVoxelOperator`CreateOperator[{3,3,3},.0005,200000.,4,"transport","ActiveCells"->{{2,2,2}}],Failure["NoFluxFaces"|"UnportedComponent",_Association]],True,TestID->"Unported-mask-is-rejected-before-solve"]
VerificationTest[MatchQ[LitzVoxelOperator`CreateOperator[{2,2,3},.0005,200000.,4,"transport","MemoryBudgetBytes"->1.],Failure["ResourceBudget",_Association]],True,TestID->"Predicted-budget-rejection-precedes-kernel-allocation"]
