(* The root runner dispatches this stage after adding its name to the allowed
   stages. Heavy physical runs are deliberately sequential. Default is pilot;
   LITZ_VOXEL_OPERATOR_MODE=equivalence adds 1024 cells, =scale additionally
   attempts 3456/8192 only after all three independent equivalence cases pass. *)
Get[FileNameJoin[{stageRoot,"src","VoxelPEEC.wl"}]];
Get[FileNameJoin[{stageRoot,"src","VoxelOperator.wl"}]];
voMode=Environment["LITZ_VOXEL_OPERATOR_MODE"];
If[!MemberQ[{"pilot","equivalence","scale"},voMode],voMode="pilot"];
voCases={};voStopped=None;voProgress=None;
voSpecs=If[voMode=="pilot",{{2,2,8},{4,4,8}},{{2,2,8},{4,4,8},{8,8,16}}];
voRecordProgress[event_]:=(voProgress=event;stageData=<|"source_model"->"RT0_matrix_free_operator_validation","mode"->voMode,"cases"->voCases,"progress"->event,"first_stop"->voStopped|>;stageSave[];Print[event]);
Do[Print["Matrix-free independent equivalence dimensions=",voDims];
 voH=.001/voDims[[1]];
 voOp=LitzVoxelOperator`CreateOperator[voDims,voH,200000.,10,"field","TimeBudgetSeconds"->600.,"ProgressFunction"->voRecordProgress];
 If[!AssociationQ[voOp],voStopped=<|"dimensions"->voDims,"failure"->ToString[voOp,InputForm],"phase"->"operator_assembly"|>;Break[]];
 voNew=LitzVoxelOperator`SolveOperator[voOp,"Tolerance"->10.^-11,"TimeBudgetSeconds"->600.,"CheckpointFunction"->voRecordProgress];
 If[!TrueQ[voNew["converged"]],voStopped=<|"dimensions"->voDims,"failure"->voNew["stop_reason"],"phase"->"GMRES"|>;AppendTo[voCases,<|"operator"->LitzVoxelOperator`OperatorMetadata[voOp],"solution"->voNew,"equivalence_status"->"not_run"|>];Break[]];
 (* Original assembly/LeastSquares is an independent reference, not another
    materialization of the new convolution operator. Keep it only at pilot
    sizes. Budget the old implementation before its quadratic allocation. *)
 voRefEstimate=4000. voOp["cells"]^2;
 voBudget=Quiet[Check[ToExpression[Environment["LITZ_RAM_BUDGET"]],0.]];
 If[!NumericQ[voBudget]||voRefEstimate>.7 voBudget,voStopped=<|"dimensions"->voDims,"phase"->"independent_dense_reference","execution_status"->"blocked_environment_resource_budget","estimated_working_bytes"->voRefEstimate,"working_budget_bytes"->voBudget|>;Break[]];
 voOld=TimeConstrained[LitzVoxel`FaceFluxModel[voDims,voH,200000.,10,"field"],600.,$Aborted];
 If[!AssociationQ[voOld],voStopped=<|"dimensions"->voDims,"phase"->"independent_dense_reference","failure"->ToString[voOld,InputForm]|>;Break[]];
 voVectors={N[Sin[Range[voOp["face_flux_DOF"]]/17.]+I Cos[Range[voOp["face_flux_DOF"]]/23.]],UnitVector[voOp["face_flux_DOF"],1],UnitVector[voOp["face_flux_DOF"],voOp["face_flux_DOF"]]};
 voMatError=Max[Norm[LitzVoxelOperator`ApplyInductance[voOp,#]-voOld["L_H"].#]/Max[Norm[voOld["L_H"].#],$MinMachineNumber]&/@voVectors];
 voCurrentError=Norm[voNew["currents_RMS_A"]-voOld["currents_RMS_A"]]/Norm[voOld["currents_RMS_A"]];
 voLossError=Abs[voNew["loss_W"]/voOld["loss_W"]-1];voBefore=Length[stageChecks];
 stageCheck["RT0_FFT_matvec_"<>ToString[voOp["cells"]],voMatError,10.^-10,"original_RT0_pair_matrix_vs_zero_padded_FFT"];
 stageCheck["RT0_GMRES_currents_"<>ToString[voOp["cells"]],voCurrentError,10.^-8,"independent_dense_LeastSquares_reference"];
 stageCheck["RT0_GMRES_loss_"<>ToString[voOp["cells"]],voLossError,10.^-6,"independent_dense_LeastSquares_reference"];
 Scan[stageCheck["RT0_FFT_"<>ToString[voOp["cells"]]<>"_"<>#,voNew[#],If[#=="power_residual",.001,10.^-8],"matrix_free_RT0"]&,{"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","power_residual"}];
 voPassed=!AnyTrue[Drop[stageChecks,voBefore],#["execution_status"]=="failed"&];
 AppendTo[voCases,<|"operator"->LitzVoxelOperator`OperatorMetadata[voOp],"solution"->voNew,"matvec_relative_error"->voMatError,"current_relative_error"->voCurrentError,"loss_relative_error"->voLossError,"independent_reference_source_model"->voOld["source_model"],"equivalence_status"->If[voPassed,"passed","failed"]|>];
 Clear[voOld,voVectors];voRecordProgress[<|"phase"->"independent_equivalence","cells"->voOp["cells"],"execution_status"->If[voPassed,"passed","failed"]|>];
 If[!voPassed,voStopped=<|"dimensions"->voDims,"phase"->"independent_equivalence","execution_status"->"failed_numerical"|>;Break[]],{voDims,voSpecs}];
If[voMode=="scale"&&voStopped===None&&Length[voCases]==3&&And@@(#["equivalence_status"]=="passed"&/@voCases),
 Do[voDims={voN,voN,2 voN};Print["Matrix-free spatial refinement dimensions=",voDims];
  voOp=LitzVoxelOperator`CreateOperator[voDims,.001/voN,200000.,10,"field","TimeBudgetSeconds"->1800.,"ProgressFunction"->voRecordProgress];
  If[!AssociationQ[voOp],voStopped=<|"dimensions"->voDims,"phase"->"operator_assembly","failure"->ToString[voOp,InputForm]|>;Break[]];
  voNew=LitzVoxelOperator`SolveOperator[voOp,"Tolerance"->10.^-11,"TimeBudgetSeconds"->1800.,"CheckpointFunction"->voRecordProgress];
  AppendTo[voCases,<|"operator"->LitzVoxelOperator`OperatorMetadata[voOp],"solution"->voNew,"equivalence_status"->"not_run_at_this_size","algorithm_equivalence_source"->"32/128/1024-cell independent original matrices in this run"|>];
  If[!TrueQ[voNew["converged"]],voStopped=<|"dimensions"->voDims,"phase"->"GMRES","execution_status"->"failed_numerical","failure"->voNew["stop_reason"]|>;Break[]];
  Scan[stageCheck["RT0_FFT_"<>ToString[voOp["cells"]]<>"_"<>#,voNew[#],If[#=="power_residual",.001,10.^-8],"matrix_free_RT0"]&,{"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","power_residual"}];
  voRecordProgress[<|"phase"->"spatial_refinement","cells"->voOp["cells"],"loss_W"->voNew["loss_W"],"execution_status"->voNew["execution_status"]|>],{voN,{12,16}}]];
voSpatial=Select[voCases,#["operator"]["dimensions"][[3]]==2 #["operator"]["dimensions"][[1]]&&TrueQ[#["solution"]["converged"]]&];
If[Length[voSpatial]>=2,voChange=Abs[Last[voSpatial]["solution"]["loss_W"]/voSpatial[[-2]]["solution"]["loss_W"]-1];
 stageCheck["RT0_FFT_last_spatial_change",voChange,.01,"same_1x1x2_mm_cuboid_external_field_spatial_refinement"]];
If[voStopped=!=None,Export[FileNameJoin[{stageDir,"operator_stop.json"}],voStopped,"RawJSON"];stageCheck["RT0_operator_route_completed",1,0,"operator_stop_preserved"]];
stageData=<|"source_model"->"RT0_matrix_free_operator_validation","mode"->voMode,"cases"->voCases,"first_stop"->voStopped,"progress"->voProgress,
 "assumptions"->"CPU FP64 exact zero-padded Toeplitz matvec using original RT0 pair quadrature and Duffy self integral; sparse overlap R/B, common end port and diagonal-complex/sparse-Schur-preconditioned GMRES. Internal true-residual target tightened to 1e-11 to satisfy independent current-equivalence acceptance at 1e-8; acceptance thresholds unchanged. 32-cell algebra pilot has 1x1x4mm dimensions; spatial series starts at 128 cells and remains 1x1x2mm. Uniform 1mT RMS Bz, zero net transport; imposed-field loss is not intrinsic P/I^2 resistance. Larger scale starts only after independent 32/128/1024-cell equivalence passes. Quadrature-order sensitivity, masked curved geometry/staircase convergence, FEM physical cross-validation and topology ranking are not implied."|>;
stageSave[];
