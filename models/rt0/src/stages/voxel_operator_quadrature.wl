(* Fixed 128-cell quadrature sensitivity, followed by an unequal-area
   labelled AC common-port example. No curved/round-wire or FEM claim. *)
Get[FileNameJoin[{stageRoot,"src","VoxelPEEC.wl"}]];
Get[FileNameJoin[{stageRoot,"src","VoxelOperator.wl"}]];
qopCases={};qopStops={};qopProgress=Null;qopDimensions={4,4,8};qopH=.00025;
qopParameters=<|"field_case_dimensions"->qopDimensions,"cell_width_m"->qopH,"frequency_Hz"->200000,
 "uniform_field_RMS_T"->.001,"field_case_net_transport_A"->0,"quadrature_orders"->{10,14,18},
 "GMRES_true_residual_target"->10.^-11,"case_time_budget_seconds"->600,
 "masked_AC_dimensions"->{3,2,6},"masked_AC_cell_width_m"->.0005,"masked_AC_total_current_RMS_A"->20,
 "masked_AC_cross_section_area_ratio"->{1,2},"phasor"->"exp(+j omega t)","conductivity_S_per_m"->5.8*^7|>;
Export[FileNameJoin[{stageDir,"operator_quadrature_parameters.json"}],qopParameters,"RawJSON"];
qopCheckpoint[event_]:=(qopProgress=event;
 stageData=<|"source_model"->"RT0_FFT_quadrature_and_labelled_AC_port_validation","parameters"->qopParameters,"cases"->qopCases,"stops"->qopStops,"progress"->event|>;
 stageSave[];Print[event]);
Do[qopStart=AbsoluteTime[];Print["Fixed 128-cell quadrature order=",qopOrder];
 qopPair=TimeConstrained[
  qopOp=LitzVoxelOperator`CreateOperator[qopDimensions,qopH,200000.,qopOrder,"field","TimeBudgetSeconds"->600.,"ProgressFunction"->qopCheckpoint];
  If[AssociationQ[qopOp],qopSol=LitzVoxelOperator`SolveOperator[qopOp,"Tolerance"->10.^-11,
    "TimeBudgetSeconds"->Max[.001,600.-(AbsoluteTime[]-qopStart)],"CheckpointFunction"->qopCheckpoint];{qopOp,qopSol},qopOp],600.,$Aborted];
 If[!MatchQ[qopPair,{_Association,_Association}],
  AppendTo[qopStops,<|"case_kind"->"fixed_128_cell_field","quadrature_order"->qopOrder,"failure"->ToString[qopPair,InputForm],"elapsed_seconds"->AbsoluteTime[]-qopStart|>];Break[]];
 {qopOp,qopSol}=qopPair;
 AppendTo[qopCases,<|"case_kind"->"fixed_128_cell_field","operator"->LitzVoxelOperator`OperatorMetadata[qopOp],"solution"->qopSol,
  "case_elapsed_seconds"->AbsoluteTime[]-qopStart|>];
 Scan[stageCheck["RT0_quadrature_"<>ToString[qopOrder]<>"_"<>#,qopSol[#],If[#=="power_residual",.001,10.^-8],"fixed_128_cell_RT0_FFT_quadrature"]&,
  {"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","power_residual"}];
 stageCheck["RT0_quadrature_"<>ToString[qopOrder]<>"_zero_net_transport",Abs[qopSol["port_current_A"]],10.^-8,"external_field_closed_loops"];
 qopCheckpoint[<|"phase"->"quadrature_case_completed","quadrature_order"->qopOrder,"loss_W"->qopSol["loss_W"],"iterations"->qopSol["iterations"],"execution_status"->qopSol["execution_status"]|>];
 If[!TrueQ[qopSol["converged"]],AppendTo[qopStops,<|"case_kind"->"fixed_128_cell_field","quadrature_order"->qopOrder,"failure"->qopSol["stop_reason"]|>];Break[]],
 {qopOrder,{10,14,18}}];
qopFieldCases=Select[qopCases,#["case_kind"]=="fixed_128_cell_field"&];
stageCheck["all_three_RT0_quadrature_orders_completed",Abs[Length[qopFieldCases]-3],0,"required_10_14_18_orders"];
qopLossChange=Null;qopCurrentChange=Null;
If[Length[qopFieldCases]==3&&And@@(TrueQ[#["solution"]["converged"]]&/@qopFieldCases),
 qopLossChange=Abs[qopFieldCases[[3]]["solution"]["loss_W"]/qopFieldCases[[2]]["solution"]["loss_W"]-1];
 qopCurrentChange=Norm[qopFieldCases[[3]]["solution"]["currents_RMS_A"]-qopFieldCases[[2]]["solution"]["currents_RMS_A"]]/Norm[qopFieldCases[[3]]["solution"]["currents_RMS_A"]];
 stageCheck["RT0_14_to_18_loss_change",qopLossChange,.001,"same_geometry_same_FFT_basis_quadrature_sensitivity"];
 stageCheck["RT0_14_to_18_complex_current_change",qopCurrentChange,.001,"same_geometry_same_FFT_basis_quadrature_sensitivity"]];

(* Two separated labelled rectangular conductors, cross-sectional areas h^2
   and 2h^2, both length 6h. End voltage is shared and only total20A is fixed. *)
qopMask=Join[Table[{1,1,z},{z,6}],Flatten[Table[{3,y,z},{y,2},{z,6}],1]];
qopLabels=Join[ConstantArray[1,6],ConstantArray[2,12]];
qopStart=AbsoluteTime[];Print["Unequal labelled AC conductors, shared end voltage and total20A"];
qopACPair=TimeConstrained[
 qopACOp=LitzVoxelOperator`CreateOperator[{3,2,6},.0005,200000.,14,"transport","ActiveCells"->qopMask,"ConductorLabels"->qopLabels,
  "TimeBudgetSeconds"->600.,"ProgressFunction"->qopCheckpoint];
 If[AssociationQ[qopACOp],qopACSol=LitzVoxelOperator`SolveOperator[qopACOp,"TotalCurrentRMSA"->20.,"Tolerance"->10.^-11,
  "TimeBudgetSeconds"->Max[.001,600.-(AbsoluteTime[]-qopStart)],"CheckpointFunction"->qopCheckpoint];{qopACOp,qopACSol},qopACOp],600.,$Aborted];
qopACData=Null;
If[MatchQ[qopACPair,{_Association,_Association}],
 {qopACOp,qopACSol}=qopACPair;
 AppendTo[qopCases,<|"case_kind"->"unequal_labelled_AC_common_port","operator"->LitzVoxelOperator`OperatorMetadata[qopACOp],"solution"->qopACSol,
  "nominal_copper_area_m2"->3 .0005^2,"axial_length_m"->6 .0005,"DC_closed_form_R_ohm"->1/(5.8*^7 .0005),
  "case_elapsed_seconds"->AbsoluteTime[]-qopStart|>];
 Scan[stageCheck["unequal_labelled_AC_"<>#,qopACSol[#],If[#=="power_residual",.001,10.^-8],"labelled_RT0_AC_common_port"]&,
  {"linear_residual","voltage_equation_residual","constraint_residual","continuity_residual","port_current_relative_residual","power_residual"}];
 qopStrandCurrents=Values[qopACSol["source_conductor_currents_RMS_A"]];
 stageCheck["two_labelled_AC_source_currents_reported",Abs[Length[qopStrandCurrents]-2],0,"physical_strand_labels"];
 stageCheck["labelled_AC_source_currents_sum_to20A",Abs[Total[qopStrandCurrents]-20.]/20.,10.^-8,"common_terminal_total_current"];
 stageCheck["unequal_labelled_AC_currents_not_forced_to10A",If[Norm[qopStrandCurrents-10.]>10.^-6,0,1],0,"unequal_areas_common_voltage_autonomous_current_division"];
 qopACData=<|"execution_status"->qopACSol["execution_status"],"converged"->qopACSol["converged"],"stop_reason"->qopACSol["stop_reason"],
  "currents_RMS_A_ReIm"->Map[{Re[#],Im[#]}&,qopACSol["source_conductor_currents_RMS_A"]],
  "voltage_RMS_V_ReIm"->{Re[qopACSol["port_voltage_V"]],Im[qopACSol["port_voltage_V"]]},"loss_W"->qopACSol["loss_W"],
  "power_residual"->qopACSol["power_residual"],"linear_residual"->qopACSol["linear_residual"]|>;
 If[!TrueQ[qopACSol["converged"]],AppendTo[qopStops,<|"case_kind"->"unequal_labelled_AC_common_port","failure"->qopACSol["stop_reason"]|>]],
 AppendTo[qopStops,<|"case_kind"->"unequal_labelled_AC_common_port","failure"->ToString[qopACPair,InputForm],"elapsed_seconds"->AbsoluteTime[]-qopStart|>];
 stageCheck["unequal_labelled_AC_case_completed",1,0,"AC_operator_and_solve_execution"]];
qopSummary=<|"run_id"->stageID,"source_model"->"RT0_FFT_quadrature_and_labelled_AC_port_validation",
 "execution_status"->If[qopStops!={}||AnyTrue[stageChecks,#["execution_status"]=="failed"&],"failed_numerical","passed"],
 "parameters"->qopParameters,"field_cases"->Map[<|"quadrature_order"->#["operator"]["quadrature_order"],"loss_W"->#["solution"]["loss_W"],
   "linear_residual"->#["solution"]["linear_residual"],"iterations"->#["solution"]["iterations"],"converged"->#["solution"]["converged"],
   "case_elapsed_seconds"->#["case_elapsed_seconds"]|>&,qopFieldCases],
 "loss_change_14_to_18"->qopLossChange,"complex_current_change_14_to_18"->qopCurrentChange,"unequal_labelled_AC"->qopACData,"stops"->qopStops|>;
Export[FileNameJoin[{stageDir,"operator_quadrature_summary.json"}],qopSummary,"RawJSON"];
stageData=<|"source_model"->"RT0_FFT_quadrature_and_labelled_AC_port_validation","parameters"->qopParameters,"cases"->qopCases,"summary"->qopSummary,"stops"->qopStops,
 "assumptions"->"Fixed 128-cell 1x1x2mm cuboid in independent uniform 1mT RMS Bz, zero net transport; quadrature orders10/14/18 using original volume pair integral and 24-sector Duffy self with full mutual kernels. Loss/current change14to18 target0.1% is separate from spatial convergence. Additional18-cell transport model has two separated labelled rectangular conductors of cross-sectional areas1:2, common bottom-end voltage and grounded top ends, total20A RMS; no per-label current imposed. AC partial inductance references omitted remote return, so this is an interface/energy test and not a complete real cable circuit. Nominal copper area0.75mm2 is below the5mm2 final design requirement. Curved voxelization, round-wire staircase geometry, explicit return sensitivity, end-field validation, independent FEM comparison and topology ranking remain unverified."|>;
stageSave[];
