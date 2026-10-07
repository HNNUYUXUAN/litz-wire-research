Get[FileNameJoin[{stageRoot,"src","PEEC.wl"}]];Needs["CUDALink`"];CUDALink`$DisableWLGPUSDKDownload=True;
stageCheck["physical_GPU_runtime",If[TrueQ[CUDALink`CUDAQ[]],0,1],0,"GPU_PEEC"];
{gpCompile,gpKernel}=AbsoluteTiming[ExternalEvaluate["CUDA",Get[FileNameJoin[{stageRoot,"src","GPUVolumeFarKernel.wl"}]]]];
gpCases={};gpBlocked=None;gpResumeID=None;
If[stageName==="gpu_scale",Get[FileNameJoin[{stageRoot,"src","NotebookView.wl"}]];gpResume=LitzView`OpenStage[stageRoot,"gpu_scale"];If[AssociationQ[gpResume],gpCases=Lookup[gpResume["data"],"cases",{}];gpResumeID=gpResume["run_id"]]];
Do[If[AnyTrue[gpCases,Lookup[#,"cross_divisions",0]==gm&],Print["Retain completed GPU physical case ",gm," from ",gpResumeID];Continue[]];Print["Physical PEEC GPU cross divisions=",gm];
 gpPredictedCount=Count[Flatten[Table[If[((r-.5)/gm-.5)^2+((c-.5)/gm-.5)^2<=.25,1,0],{r,gm},{c,gm}]],1];gpPredictedBytes=96. gpPredictedCount^2;
 gpFreeRAM=Quiet[Check[ToExpression[StringTrim[RunProcess[{"powershell","-NoProfile","-Command","[int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024"},"StandardOutput"]]],0]];
 If[stageName==="gpu_scale"&&gpPredictedBytes>Max[gpFreeRAM-2 1024^3,0],gpBlocked=<|"cross_divisions"->gm,"predicted_filaments"->gpPredictedCount,"predicted_host_bytes"->gpPredictedBytes,"free_RAM_bytes"->gpFreeRAM,"execution_status"->"blocked_environment_resource_budget"|>;Print[gpBlocked];Break[]];gpCPU=LitzPEEC`LongitudinalModel[gm,.16,200000.];gn=gpCPU["filaments"];gw=gpCPU["cell_width_m"];gpPts=gpCPU["centers_m"];
 gpQ=LitzPEEC`Private`quad[4];gpQxy=Flatten[Table[gw/2 {s[[1]],t[[1]]},{s,gpQ},{t,gpQ}],1];gpQw=Flatten[Table[s[[2]] t[[2]]/4,{s,gpQ},{t,gpQ}]];
 gpX=GPUArray[NumericArray[gpPts[[All,1]],"Real64"]];gpY=GPUArray[NumericArray[gpPts[[All,2]],"Real64"]];
 gpQX=GPUArray[NumericArray[gpQxy[[All,1]],"Real64"]];gpQY=GPUArray[NumericArray[gpQxy[[All,2]],"Real64"]];gpQW=GPUArray[NumericArray[gpQw,"Real64"]];
 gpOut=GPUArray[NumericArray[ConstantArray[0.,4099],"Real64"]];gpFlat=ConstantArray[0.,gn^2];gpBatchTimes={};
 {gpAssemblySeconds,gpAssemblyToken}=AbsoluteTiming[Do[gpCount=Min[4099,gn^2-gpStart];{gpBatch,gpPiece}=AbsoluteTiming[gpKernel[gpOut,gpX,gpY,gpQX,gpQY,gpQW,gn,gpStart,gpCount,.16,5. gw];Take[Normal[gpOut],gpCount]];
 gpFlat[[gpStart+1;;gpStart+gpCount]]=gpPiece;AppendTo[gpBatchTimes,gpBatch],{gpStart,0,gn^2-1,4099}];Null];
 gpL=Partition[gpFlat,gn];gpNear=Table[Norm[gpPts[[r]]-gpPts[[c]]]<=5. gw,{r,gn},{c,gn}];
 gpL=MapThread[If[#1,#2,#3]&,{gpNear,gpCPU["partial_inductance_matrix_H"],gpL},2];
 gpError=Norm[Flatten[gpL-gpCPU["partial_inductance_matrix_H"]]]/Norm[Flatten[gpCPU["partial_inductance_matrix_H"]]];
 stageCheck["GPU_volume_L_matrix_"<>ToString[gn],gpError,10.^-10,"GPU_CPU_identical_volume_quadrature_PEEC"];
 gpZ=gpCPU["resistance_matrix_ohm"]+I 2 Pi 200000. gpL;
 gpAug=ArrayFlatten[{{gpZ,-Transpose[{ConstantArray[1.,gn]}]},{{ConstantArray[1.,gn]},{{0.}}}}];gpRHS=Join[ConstantArray[0.+0. I,gn],{20.+0. I}];
 {gpUpload,{gpAZ,gpB}}=AbsoluteTiming[{GPUArray[NumericArray[N[gpAug],"ComplexReal64"]],GPUArray[NumericArray[gpRHS,"ComplexReal64"]]}];
 {gpSolveSeconds,gpSol}=AbsoluteTiming[Normal[LinearSolve[gpAZ,gpB]]];
 gpResidual=Norm[gpAug.gpSol-gpRHS]/Norm[gpRHS];gpCurrentErr=Norm[Most[gpSol]-gpCPU["solution"]["currents"]]/Norm[gpCPU["solution"]["currents"]];
 stageCheck["GPU_physical_PEEC_residual_"<>ToString[gn],gpResidual,10.^-10,"GPU_common_port_PEEC"];
 stageCheck["GPU_physical_PEEC_currents_"<>ToString[gn],gpCurrentErr,10.^-10,"GPU_common_port_PEEC"];
 gpPower=Re[Conjugate[Most[gpSol]].gpCPU["resistance_matrix_ohm"].Most[gpSol]];
 stageCheck["GPU_physical_PEEC_power_"<>ToString[gn],Abs[Re[Last[gpSol] 20.]-gpPower]/gpPower,.001,"GPU_common_port_PEEC"];
 AppendTo[gpCases,<|"cross_divisions"->gm,"filaments"->gn,"length_m"->.16,"actual_area_m2"->gpCPU["area_m2"],"CPU_assembly_seconds"->gpCPU["assembly_seconds"],"GPU_far_assembly_copyback_seconds"->gpAssemblySeconds,"CPU_near_self_reference_reused"->True,
 "GPU_upload_seconds"->gpUpload,"GPU_dense_solve_copyback_seconds"->gpSolveSeconds,"batch_max_seconds"->Max[gpBatchTimes],"batch_target_seconds"->.25,"L_matrix_relative_error"->gpError,"current_relative_error"->gpCurrentErr,"linear_residual"->gpResidual,
 "Rac_ohm_per_axial_m"->gpPower/(400*.16),"Bessel_Rac_relative_error"->gpCPU["Bessel_Rac_relative_error"],"currents"->Most[gpSol]|>];
 stageData=<|"source_model"->"physical_longitudinal_PEEC_CPU_GPU_cross_validation","cases"->gpCases,"compile_seconds"->gpCompile|>;stageSave[];Print[KeyDrop[Last[gpCases],"currents"]],{gm,If[stageName==="gpu_scale",{56,80,112,160},{14,28,40}]}];
If[Length[gpCases]==3,stageCheck["PEEC_spatial_fine_change",Abs[gpCases[[3]]["Rac_ohm_per_axial_m"]/gpCases[[2]]["Rac_ohm_per_axial_m"]-1],.01,"longitudinal_PEEC"];
 stageCheck["PEEC_fine_Bessel_Rac",Last[gpCases]["Bessel_Rac_relative_error"],.01,"longitudinal_PEEC"]];
stageData=Append[stageData,"assumptions"->"Physical finite longitudinal volume PEEC, CPU exact singular self and near tensor quadrature, GPU far terms use identical 4x4 transverse tensor weights and exact axial double integral. All complex currents solved on GPU with common-end voltage and total20A. Matrix and solution CPU comparisons separate from Bessel physical convergence. CPU baseline complete assembly is computed for validation; timings do not falsely count this as eliminated work. Full vector RT0 and finite helices are separate routes." ];
stageFigure["physical_PEEC_CPU_GPU_time",ListLogLogPlot[{({#["filaments"],#["CPU_assembly_seconds"]}&/@gpCases),({#["filaments"],#["GPU_far_assembly_copyback_seconds"]}&/@gpCases)},Joined->True,PlotLegends->{"CPU full reference assembly","GPU far assembly + copyback"},Frame->True,FrameLabel->{"filaments","seconds"},ImageSize->600]];


