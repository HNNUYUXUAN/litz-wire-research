(* Optional RT0 axis-group assembly. Each worker evaluates the original pair
   integral in the original offset/side order and keeps its per-axis memo cache.
   The caller retains the serial FFT application and GMRES solve. *)
Begin["LitzVoxelOperator`Private`"];
voParallelSourceDirectory=DirectoryName[$InputFileName];

kernelWorkerMemoryBytes[dims_List,padding_List,workers_Integer]:=Module[{effective=If[workers>1,Min[3,workers],0]},
 effective (268435456.+1024. (Times@@dims)+128. (Times@@padding))];

assembleAxisGroup[ax_Integer,dims_List,padding_List,h_?NumericQ,order_Integer,deadline_?NumericQ]:=Module[
 {kernels=Association[],offsets=Tuples[Range[1-#, #-1]&/@dims],ker,d,position,start=AbsoluteTime[],one,cross},
 Do[ker=ConstantArray[0.,padding];
  Do[If[AbsoluteTime[]>deadline,Return[Failure["TimeBudget",<|"execution_status"->"not_completed_time_budget",
    "phase"->"parallel_axis_kernel_assembly","axis"->ax,"completed_axis_kernels"->Length[kernels],"elapsed_seconds"->AbsoluteTime[]-start|>]]];
   position=MapThread[If[#1>=0,#1+1,#2+#1+1]&,{d,padding}];
   ker[[Sequence@@position]]=10.^-7 h canonicalPair[-d,ax,side,other,order],{d,offsets}];
  AssociateTo[kernels,key[{ax,side,other}]->packed[fft[packed[ker]]]],{side,2},{other,2}];
 one=10.^-7 h canonicalPair[{0,0,0},ax,1,1,order];
 cross=10.^-7 h canonicalPair[UnitVector[3,ax],ax,2,1,order];
 <|"axis"->ax,"kernel_fft"->kernels,"diagonal_one_H"->one,"diagonal_cross_H"->cross,
   "elapsed_seconds"->AbsoluteTime[]-start,"worker_kernel_id"->$KernelID,"worker_process_id"->$ProcessID,
   "worker_thread_options"->ToString[SystemOptions["ParallelOptions"],InputForm]|>
];

assembleParallelAxisGroups[dims_List,padding_List,h_?NumericQ,order_Integer,workers_Integer,deadline_?NumericQ,progress_]:=Module[
 {effective=Min[3,workers],before=Kernels[],owned={},launch,ids,assignment,groups,result,source=voParallelSourceDirectory,start=AbsoluteTime[]},
 (* A fresh stage owns the kernels it launches. Avoid altering pre-existing
    workers or closing another caller's kernels. *)
 If[before=!={},Return[Failure["ExistingSubkernels",<|"execution_status"->"blocked_existing_subkernels",
   "reason"->"Parallel RT0 assembly requires a clean main kernel with no pre-existing subkernels.","existing_kernel_count"->Length[before]|>]]];
 result=CheckAbort[
  launch=Quiet[Check[LaunchKernels[effective],$Failed]];owned=Complement[Kernels[],before];
  If[Length[owned]!=effective,
   Failure["ParallelKernelLaunch",<|"execution_status"->"blocked_parallel_kernels","requested_workers"->workers,
    "effective_workers"->effective,"launched_owned_workers"->Length[owned]|>],
   ids=With[{v=FileNameJoin[{source,"VoxelPEEC.wl"}],o=FileNameJoin[{source,"VoxelOperator.wl"}]},
    ParallelEvaluate[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->1];Get[v];Get[o];$KernelID,owned]];
   If[!ListQ[ids]||Length[ids]!=effective||!And@@(IntegerQ/@ids),
    Failure["ParallelPackageLoad",<|"execution_status"->"failed_parallel_package_load"|>],
    assignment=Association[Thread[ids->Range[effective]]];
    emit[progress,<|"phase"->"parallel_axis_kernel_assembly","completed_kernels"->0,"required_kernels"->12,
      "requested_workers"->workers,"effective_workers"->effective,"worker_kernel_ids"->ids,"elapsed_seconds"->AbsoluteTime[]-start|>];
    (* Three axis groups provide cache-preserving parallelism. A request of two
       workers executes axes 1/3 together on the first and axis 2 on the second. *)
    groups=With[{a=assignment,ds=dims,pad=padding,width=h,q=order,until=deadline,n=effective},
      ParallelEvaluate[Map[assembleAxisGroup[#,ds,pad,width,q,until]&,Range[Lookup[a,$KernelID],3,n]],owned]];
    groups=Flatten[groups,1];
    If[Length[groups]!=3||!And@@(AssociationQ/@groups),
     Failure["ParallelAxisAssembly",<|"execution_status"->"failed_parallel_axis_assembly",
       "worker_results"->(If[AssociationQ[#],KeyTake[#, {"axis","elapsed_seconds","worker_kernel_id"}],ToString[#,InputForm]]&/@groups)|>],
     <|"axis_groups"->SortBy[groups,#["axis"]&],"requested_workers"->workers,"effective_workers"->effective,
       "launch_and_assembly_seconds"->AbsoluteTime[]-start|>]]],
  If[owned=!={},Quiet[CloseKernels[owned]]];Abort[]];
 If[owned=!={},Quiet[CloseKernels[owned]]];result
];
End[];
