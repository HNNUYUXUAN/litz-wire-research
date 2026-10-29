cpuConfigurations={{1,8},{2,4},{4,2},{8,1}};cpuRows={};
cpuJob[index_] := BlockRandom[SeedRandom[20261004+index];Module[{a=RandomReal[{-1,1},{768,768}],b=RandomReal[{-1,1},{768,768}],c,t},
 {t,c}=AbsoluteTiming[a.b];<|"job"->index,"dot_seconds"->t,"checksum"->Total[c[[1]]],"process_id"->$ProcessID,"thread_options"->ToString[SystemOptions["ParallelOptions"],InputForm]|>]];
Do[cpuWorkers=conf[[1]];cpuThreads=conf[[2]];
 cpuFree=Quiet[Check[ToExpression[StringTrim[RunProcess[{"powershell","-NoProfile","-Command","[int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024"},"StandardOutput"]]],0]];
 If[cpuWorkers>1&&cpuWorkers*220000000.>Max[cpuFree-2 1024^3,0],AppendTo[cpuRows,<|"workers"->cpuWorkers,"MKL_threads_per_worker"->cpuThreads,"execution_status"->"blocked_environment_resource_budget","free_RAM_bytes"->cpuFree|>];Continue[]];
 If[cpuWorkers==1,SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->cpuThreads];{cpuSeconds,cpuValues}=AbsoluteTiming[Table[cpuJob[k],{k,16}]],
  {cpuLaunchSeconds,cpuKernels}=AbsoluteTiming[LaunchKernels[cpuWorkers]];
  If[Length[cpuKernels]!=cpuWorkers,CloseKernels[];AppendTo[cpuRows,<|"workers"->cpuWorkers,"execution_status"->"failed_launch"|>];Continue[]];
  With[{ct=cpuThreads},ParallelEvaluate[SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->ct]]];
  DistributeDefinitions[cpuJob];{cpuSeconds,cpuValues}=AbsoluteTiming[ParallelTable[cpuJob[k],{k,16},Method->"FinestGrained"]];CloseKernels[]];
 If[cpuWorkers==1,cpuReference=Lookup[cpuValues,"checksum"]];
 cpuError=Norm[Lookup[cpuValues,"checksum"]-cpuReference]/Norm[cpuReference];stageCheck["CPU_worker_consistency_"<>ToString[cpuWorkers],cpuError,10.^-10,"independent_CPU_workload"];
 AppendTo[cpuRows,<|"workers"->cpuWorkers,"MKL_threads_per_worker"->cpuThreads,"jobs"->16,"matrix_order"->768,"execution_status"->"executed","wall_seconds_excluding_worker_launch"->cpuSeconds,"worker_launch_seconds"->If[cpuWorkers==1,0,cpuLaunchSeconds],"jobs_per_second"->16/cpuSeconds,"reference_error"->cpuError,"actual_worker_thread_options"->DeleteDuplicates[Lookup[cpuValues,"thread_options"]]|>];
 stageData=<|"source_model"->"CPU_worker_throughput_benchmark","configurations"->cpuRows|>;stageSave[];Print[Last[cpuRows]],{conf,cpuConfigurations}];
SetSystemOptions["ParallelOptions"->"MKLThreadNumber"->8];
stageData=<|"source_model"->"CPU_worker_throughput_benchmark","configurations"->cpuRows,"assumptions"->"16 reproducible independent Real64 768-square dense products, seed fixed per job. Compare 1x8,2x4,4x2,8x1 under measured system memory and 2GiB reserve. Each job includes allocation and random data, wall timings include scheduling/transfers, worker launch recorded separately. Do not generalize winner to FEM factorization or all workloads."|>;
stageFigure["CPU_worker_throughput",BarChart[Lookup[Select[cpuRows,KeyExistsQ[#,"jobs_per_second"]&],"jobs_per_second"],ChartLabels->({ToString[#["workers"]]<>"x"<>ToString[#["MKL_threads_per_worker"]]}&/@Select[cpuRows,KeyExistsQ[#,"jobs_per_second"]&]),Frame->True,FrameLabel->{"kernels x MKL threads","independent jobs / second"},ImageSize->600]];
