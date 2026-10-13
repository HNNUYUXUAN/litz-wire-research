Get[FileNameJoin[{stageRoot,"src","PEEC.wl"}]];
Needs["CUDALink`"];
CUDALink`$DisableWLGPUSDKDownload=True;
cgCase=Environment["LITZ_CLOSURE_CASE_ID"];
cgM=Switch[cgCase,"gpu_m40",40,"gpu_m80",80,_,0];
cgBudget=Quiet[Check[ToExpression[Environment["LITZ_RAM_BUDGET"]],0]];
cgN=Count[Flatten[Table[If[((r-.5)/cgM-.5)^2+((c-.5)/cgM-.5)^2<=.25,1,0],{r,cgM},{c,cgM}]],1];
cgPrediction=192 cgN^2+1024^3;
Export[FileNameJoin[{stageDir,"parameters.json"}],<|"case_id"->cgCase,"cross_divisions"->cgM,"length_m"->.16,"frequency_Hz"->200000.,"total_current_RMS_A"->20.,"mutual_quadrature_order"->4,"self_accuracy_goal"->10,"self_precision_goal"->8,"CPU_method"->"GridOffsets independently regressed against Pairwise","GPU_method"->"same q4 tensor far integral; CPU singular self/near reused","predicted_working_bytes"->cgPrediction,"memory_budget_bytes"->cgBudget,"maximum_seconds"->3600,"phasor"->"exp(+j omega t)","units"->"SI","scope"->"single straight round-wire longitudinal PEEC CPU/GPU equivalence"|>,"RawJSON"];
cgRun[]:=Module[{},
 If[cgM==0||!TrueQ[CUDALink`CUDAQ[]]||cgPrediction>cgBudget,
  stageData=<|"source_model"->"longitudinal_PEEC_GPU_closure","physical_acceptance_status"->"not_run","failure_reason"->"invalid_case_GPU_or_resource_preflight"|>;Return[$Failed]];
 stageCheck["physical_GPU_runtime",0,0,"GPU_PEEC"];
 {cgCompile,cgKernel}=AbsoluteTiming[ExternalEvaluate["CUDA",Get[FileNameJoin[{stageRoot,"src","GPUVolumeFarKernel.wl"}]]]];
 cgCPU=LitzPEEC`LongitudinalModel[cgM,.16,200000.,"MutualKernelMethod"->"GridOffsets","ComputeInductanceEigenvalue"->False,"MemoryBudgetBytes"->cgBudget];
 If[!AssociationQ[cgCPU],stageData=<|"failure_reason"->ToString[cgCPU,InputForm]|>;Return[$Failed]];
 cgW=cgCPU["cell_width_m"];cgPts=cgCPU["centers_m"];
 cgQ=LitzPEEC`Private`quad[4];
 cgQxy=Flatten[Table[cgW/2 {s[[1]],t[[1]]},{s,cgQ},{t,cgQ}],1];
 cgQw=Flatten[Table[s[[2]] t[[2]]/4,{s,cgQ},{t,cgQ}]];
 cgX=GPUArray[NumericArray[cgPts[[All,1]],"Real64"]];cgY=GPUArray[NumericArray[cgPts[[All,2]],"Real64"]];
 cgQX=GPUArray[NumericArray[cgQxy[[All,1]],"Real64"]];cgQY=GPUArray[NumericArray[cgQxy[[All,2]],"Real64"]];cgQW=GPUArray[NumericArray[cgQw,"Real64"]];
 cgOut=GPUArray[NumericArray[ConstantArray[0.,4099],"Real64"]];cgFlat=ConstantArray[0.,cgN^2];cgBatchTimes={};
 {cgAssemblySeconds,cgToken}=AbsoluteTiming[Do[
  cgCount=Min[4099,cgN^2-cgStart];
  {cgBatch,cgPiece}=AbsoluteTiming[cgKernel[cgOut,cgX,cgY,cgQX,cgQY,cgQW,cgN,cgStart,cgCount,.16,5. cgW];Take[Normal[cgOut],cgCount]];
  cgFlat[[cgStart+1;;cgStart+cgCount]]=cgPiece;AppendTo[cgBatchTimes,cgBatch],{cgStart,0,cgN^2-1,4099}];Null];
 cgL=Partition[cgFlat,cgN];cgFlat=.;
 cgNear=Table[Norm[cgPts[[r]]-cgPts[[c]]]<=5. cgW,{r,cgN},{c,cgN}];
 cgL=MapThread[If[#1,#2,#3]&,{cgNear,cgCPU["partial_inductance_matrix_H"],cgL},2];cgNear=.;
 cgMatrixError=Norm[Flatten[cgL-cgCPU["partial_inductance_matrix_H"]]]/Norm[Flatten[cgCPU["partial_inductance_matrix_H"]]];
 stageCheck["CPU_GPU_identical_volume_L_matrix",cgMatrixError,10.^-10,"same_q4_longitudinal_PEEC"];
 cgZ=cgCPU["resistance_matrix_ohm"]+I 2 Pi 200000. cgL;
 cgAug=ArrayFlatten[{{cgZ,-Transpose[{ConstantArray[1.,cgN]}]},{{ConstantArray[1.,cgN]},{{0.}}}}];cgRHS=Join[ConstantArray[0.+0. I,cgN],{20.+0. I}];
 {cgUpload,{cgAZ,cgB}}=AbsoluteTiming[{GPUArray[NumericArray[N[cgAug],"ComplexReal64"]],GPUArray[NumericArray[cgRHS,"ComplexReal64"]]}];
 {cgSolve,cgSol}=AbsoluteTiming[Normal[LinearSolve[cgAZ,cgB]]];
 cgCurrents=Most[cgSol];cgVoltage=Last[cgSol];
 cgResidual=Norm[cgAug.cgSol-cgRHS]/Norm[cgRHS];
 cgCurrentError=Norm[cgCurrents-cgCPU["solution"]["currents"]]/Norm[cgCPU["solution"]["currents"]];
 cgPower=Re[Conjugate[cgCurrents].cgCPU["resistance_matrix_ohm"].cgCurrents];
 cgPowerResidual=Abs[Re[cgVoltage Conjugate[20.]]-cgPower]/cgPower;
 stageCheck["CPU_GPU_complex_currents",cgCurrentError,10.^-10,"same_matrix_common_port"];
 stageCheck["GPU_true_linear_residual",cgResidual,10.^-10,"common_port"];
 stageCheck["GPU_total_current",Abs[Total[cgCurrents]-20.]/20.,10.^-8,"common_port"];
 stageCheck["GPU_independent_Joule_power",cgPowerResidual,.001,"common_port"];
 cgRows=Table[{k,cgPts[[k,1]],cgPts[[k,2]],Re[cgCurrents[[k]]],Im[cgCurrents[[k]]],Abs[cgCurrents[[k]]],Arg[cgCurrents[[k]]],Re[cgCPU["solution"]["currents"][[k]]],Im[cgCPU["solution"]["currents"][[k]]]},{k,cgN}];
 Export[FileNameJoin[{stageDir,"currents.csv"}],Prepend[cgRows,{"filament_id","x_m","y_m","GPU_current_real_RMS_A","GPU_current_imag_RMS_A","GPU_current_abs_RMS_A","GPU_current_phase_rad","CPU_current_real_RMS_A","CPU_current_imag_RMS_A"}],"CSV"];
 cgSummary=<|"run_id"->stageID,"source_model"->"physical_longitudinal_PEEC_CPU_GPU_cross_validation","case_id"->cgCase,"cross_divisions"->cgM,"filaments"->cgN,"length_m"->.16,"actual_area_m2"->cgCPU["area_m2"],"copper_volume_m3"->cgCPU["area_m2"] .16,"Rdc_ohm"->.16/(5.8*^7 cgCPU["area_m2"]),"Rac_ohm_per_axial_m"->cgPower/(400 .16),"loss_W"->cgPower,"voltage_real_RMS_V"->Re[cgVoltage],"voltage_imag_RMS_V"->Im[cgVoltage],"CPU_assembly_seconds"->cgCPU["assembly_seconds"],"GPU_far_assembly_copyback_seconds"->cgAssemblySeconds,"GPU_upload_seconds"->cgUpload,"GPU_dense_solve_copyback_seconds"->cgSolve,"compile_seconds"->cgCompile,"batch_max_seconds"->Max[cgBatchTimes],"L_matrix_relative_error"->cgMatrixError,"current_relative_error"->cgCurrentError,"linear_residual"->cgResidual,"power_residual"->cgPowerResidual,"Bessel_Rac_relative_error"->cgCPU["Bessel_Rac_relative_error"],"execution_status"->"executed","physical_acceptance_status"->If[AnyTrue[stageChecks,#["execution_status"]==="failed"&],"failed_CPU_GPU_equivalence","passed_CPU_GPU_equivalence_only"],"passivity_scope"->"sampled_forms_only_full_eigenvalue_not_computed","units"->"SI RMS","currents_Re_Im_A"->({Re[#],Im[#]}&/@cgCurrents)|>;
 Export[FileNameJoin[{stageDir,"gpu_case.json"}],cgSummary,"RawJSON"];
 Export[FileNameJoin[{stageDir,"CPU_model.wxf"}],cgCPU,"WXF"];
 Export[FileNameJoin[{stageDir,"GPU_solution.wxf"}],<|"partial_inductance_matrix_H"->cgL,"currents_RMS_A"->cgCurrents,"voltage_RMS_V"->cgVoltage|>,"WXF"];
 stageData=Join[cgSummary,<|"cases"->{cgSummary},"assumptions"->"Finite straight longitudinal volume PEEC CPU/GPU equivalence at identical q4 quadrature. CPU singular self and near terms are reused; GPU evaluates far integrals and solves the full augmented common-voltage total-current system. This is not transverse circulation or true Litz end redistribution. Full CPU assembly is performed for validation and remains included in timings. Original 9856/20108 historical evidence is separate."|>];stageSave[];
 Clear[cgX,cgY,cgQX,cgQY,cgQW,cgOut,cgAZ,cgB,cgAug,cgZ,cgCPU,cgL];
 Null
];
cgOutcome=TimeConstrained[cgRun[],3600,$Aborted];
If[cgOutcome===$Aborted,stageData=<|"source_model"->"longitudinal_PEEC_GPU_closure","physical_acceptance_status"->"not_verified","failure_reason"->"one_hour_case_budget"|>];
cgOutcome
