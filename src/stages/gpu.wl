Needs["CUDALink`"];
CUDALink`$DisableWLGPUSDKDownload=True;
stageCheck["CUDA_runtime",If[TrueQ[CUDALink`CUDAQ[]],0,1],0,"GPU_runtime"];
gpuCases={};gpuTimings={};
{gpuCompile,csrKernel}=AbsoluteTiming[ExternalEvaluate["CUDA",Get[FileNameJoin[{stageRoot,"src","GPUCSRKernel.wl"}]]]];
Print["CSR CUDA compiled seconds=",gpuCompile];
Do[
 gpuA=SparseArray[{Band[{1,1}]->(4.+.2 I),Band[{1,2}]->(-1.+.1 I),Band[{2,1}]->(-1.+.1 I)},{gpuN,gpuN}];
 gpuRP=gpuA["RowPointers"];gpuCI=Flatten[gpuA["ColumnIndices"]]-1;gpuValues=gpuA["NonzeroValues"];
 gRP=GPUArray[NumericArray[gpuRP,"Integer64"]];gCI=GPUArray[NumericArray[gpuCI,"Integer64"]];
 gAR=GPUArray[NumericArray[Re[gpuValues],"Real64"]];gAI=GPUArray[NumericArray[Im[gpuValues],"Real64"]];
 gpuX=N[Sin[Range[gpuN]/17.]+I Cos[Range[gpuN]/23.]];
 gXR=GPUArray[NumericArray[Re[gpuX],"Real64"]];gXI=GPUArray[NumericArray[Im[gpuX],"Real64"]];
 gYR=GPUArray[NumericArray[ConstantArray[0.,gpuN],"Real64"]];gYI=GPUArray[NumericArray[ConstantArray[0.,gpuN],"Real64"]];
 {gpuMVSeconds,gpuY}=AbsoluteTiming[csrKernel[gRP,gCI,gAR,gAI,gXR,gXI,gYR,gYI,gpuN];Normal[gYR]+I Normal[gYI]];
 gpuErr=Norm[gpuY-gpuA.gpuX]/Norm[gpuA.gpuX];stageCheck["CSR_complex_FP64_"<>ToString[gpuN],gpuErr,10.^-10,"custom_GPU_CSR"];
 AppendTo[gpuCases,<|"rows"->gpuN,"nnz"->Length[gpuValues],"relative_error"->gpuErr,"warm_matvec_and_copyback_seconds"->gpuMVSeconds|>];
 Print[Last[gpuCases]];stageData=<|"source_model"->"GPU_algorithm_prototypes","CSR_cases"->gpuCases|>;stageSave[],{gpuN,{129,4099,65537}}];
(* Restart-free Arnoldi for a diagonally dominant complex reference. Matrix remains sparse.
   This first validated prototype keeps Arnoldi on CPU and executes all matvecs on GPU. *)
gpuN=65537;gpuB=gpuA.gpuX;gpuBeta=Norm[gpuB];gpuV={gpuB/gpuBeta};gpuH=ConstantArray[0.+0. I,{41,40}];gpuGMRESHistory={};
gpuMV[v_]:=Module[{vr=GPUArray[NumericArray[Re[v],"Real64"]],vi=GPUArray[NumericArray[Im[v],"Real64"]]},csrKernel[gRP,gCI,gAR,gAI,vr,vi,gYR,gYI,gpuN];Normal[gYR]+I Normal[gYI]];
{gpuGMRESSeconds,gpuApprox}=AbsoluteTiming[
 Do[gpuW=gpuMV[gpuV[[j]]];
  Do[gpuH[[k,j]]=Conjugate[gpuV[[k]]].gpuW;gpuW-=gpuH[[k,j]] gpuV[[k]],{k,j}];
  gpuH[[j+1,j]]=Norm[gpuW];
  If[Abs[gpuH[[j+1,j]]]>10.^-14,AppendTo[gpuV,gpuW/gpuH[[j+1,j]]]];
  gpuCoef=LeastSquares[gpuH[[1;;j+1,1;;j]],Join[{gpuBeta},ConstantArray[0.,j]]];
  gpuApprox=Total[MapThread[Times,{gpuCoef,gpuV[[1;;j]]}]];
  gpuRes=Norm[gpuA.gpuApprox-gpuB]/Norm[gpuB];AppendTo[gpuGMRESHistory,{j,gpuRes}];If[gpuRes<10.^-10,Break[]],{j,40}];gpuApprox];
stageCheck["GPU_CSR_GMRES_true_residual",gpuRes,10.^-8,"hybrid_GPU_CSR_GMRES"];
stageCheck["GPU_CSR_GMRES_known_solution",Norm[gpuApprox-gpuX]/Norm[gpuX],10.^-8,"hybrid_GPU_CSR_GMRES"];
Print["GMRES iterations=",Length[gpuGMRESHistory]," seconds=",gpuGMRESSeconds];
{farCompile,farKernel}=AbsoluteTiming[ExternalEvaluate["CUDA",Get[FileNameJoin[{stageRoot,"src","GPUFarKernel.wl"}]]]];
farN=257;farXY=Table[{.002 Cos[k],.002 Sin[k]},{k,N[Range[farN]*2 Pi/farN]}];
farGX=GPUArray[NumericArray[farXY[[All,1]],"Real64"]];farGY=GPUArray[NumericArray[farXY[[All,2]],"Real64"]];
farOut=GPUArray[NumericArray[ConstantArray[0.,8191],"Real64"]];farCPU=Flatten[Table[If[r==c,0.,With[{d=Norm[farXY[[r]]-farXY[[c]]],l=.02},2.*^-7 (l ArcSinh[l/d]-Sqrt[l^2+d^2]+d)]],{r,farN},{c,farN}]];
farGPU={};farBatchTimes={};
Do[farCount=Min[8191,farN^2-farStart];{farSeconds,farChunk}=AbsoluteTiming[farKernel[farOut,farGX,farGY,farN,farStart,farCount,.02];Take[Normal[farOut],farCount]];farGPU=Join[farGPU,farChunk];AppendTo[farBatchTimes,farSeconds],{farStart,0,farN^2-1,8191}];
stageCheck["PEEC_far_axial_integral_kernel",Norm[farGPU-farCPU]/Norm[farCPU],10.^-10,"GPU_far_centre_quadrature"];
(* Real64 dense workload: use modest host memory and compare warm repeated end-to-end operations. *)
BlockRandom[SeedRandom[20261004];Do[
 bmA=RandomReal[{-1,1},{bn,bn}];bmB=RandomReal[{-1,1},{bn,bn}];
 Do[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->bt];{bCPU,bCPUResult}=AbsoluteTiming[bmA.bmB];
 AppendTo[gpuTimings,<|"kind"->"CPU_dense_dot","n"->bn,"MKL_threads"->bt,"seconds"->bCPU|>],{bt,{1,8,16}}];
 {bUpload,{bmGA,bmGB}}=AbsoluteTiming[{GPUArray[NumericArray[bmA,"Real64"]],GPUArray[NumericArray[bmB,"Real64"]]}];
 Do[{bGPU,bGPUResult}=AbsoluteTiming[Normal[bmGA.bmGB]];AppendTo[gpuTimings,<|"kind"->"GPU_dense_dot_copyback","n"->bn,"repeat"->rep,"upload_seconds"->bUpload,"seconds"->bGPU|>],{rep,3}];
 stageCheck["dense_dot_"<>ToString[bn],Norm[Flatten[bGPUResult-bCPUResult]]/Norm[Flatten[bCPUResult]],10.^-10,"GPU_dense_dot"],{bn,{256,512,1024,2048}}]];
SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8];
stageData=<|"source_model"->"GPU_algorithm_prototypes","CSR_compile_seconds"->gpuCompile,"CSR_cases"->gpuCases,
 "GMRES"-><|"rows"->gpuN,"iterations"->Length[gpuGMRESHistory],"elapsed_seconds"->gpuGMRESSeconds,"true_residual"->gpuRes,"history"->gpuGMRESHistory,"scope"->"CPU Arnoldi and least-squares, GPU CSR matvec; vectors uploaded per matvec. Fully resident Krylov is a subsequent optimization."|>,
 "far_kernel"-><|"compile_seconds"->farCompile,"n"->farN,"batch_entries"->8191,"batch_seconds"->farBatchTimes,"relative_error"->Norm[farGPU-farCPU]/Norm[farCPU]|>,
 "dense_benchmarks"->gpuTimings,"assumptions"->"Existing official GPU runtime. FP64 WL-to-CUDA CSR complex matvec and exact axial filament centre kernel, odd dimensions and batch tails. This far centre quadrature only integrates axial coordinates; near/self replaced by CPU volume integrals in physical PEEC. Hybrid GMRES validated on synthetic complex diagonally dominant sparse matrix, not yet an accepted FEM solver. Timings include upload/copyback where labelled; compile reported separately. Thread setting is local to this disposable kernel."|>;
stageFigure["GMRES_convergence",ListLogPlot[gpuGMRESHistory,Joined->True,Frame->True,FrameLabel->{"iteration","true relative residual"},ImageSize->600]];
stageFigure["dense_CPU_GPU",ListLogLogPlot[Table[With[{rows=Select[gpuTimings,If[k=="GPU",#["kind"]=="GPU_dense_dot_copyback"&&#["repeat"]==3,#["kind"]=="CPU_dense_dot"&&#["MKL_threads"]==k]&]},({#["n"],#["seconds"]}&/@rows)],{k,{1,8,16,"GPU"}}],Joined->True,PlotLegends->{"CPU 1","CPU 8","CPU 16","GPU warm + copyback"},Frame->True,FrameLabel->{"matrix order","seconds"},ImageSize->600]];
