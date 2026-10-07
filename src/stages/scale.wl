Get[FileNameJoin[{stageRoot,"src","CoaxFEM.wl"}]];
scCases={};scFailure=None;
Do[scFree=Quiet[Check[ToExpression[StringTrim[RunProcess[{"powershell","-NoProfile","-Command","[int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024"},"StandardOutput"]]],0]];
 scEstimate=180000. n; (* empirical conservative peak envelope after the 2560-strand execution *)
 Print["Scale attempt n=",n," free bytes=",scFree," predicted peak bytes=",scEstimate];
 If[scEstimate>Max[scFree-2 1024^3,0],scFailure=<|"strands"->n,"execution_status"->"blocked_environment_resource_budget","free_RAM_bytes"->scFree,"predicted_working_bytes"->scEstimate,"reserve_bytes"->2 1024^3|>;Print[scFailure];Break[]];
 scOne=TimeConstrained[LitzCoax`SolveCoax[n,.0001,.6],1800,$Aborted];
 If[!AssociationQ[scOne],scFailure=<|"strands"->n,"failure"->scOne|>;Break[]];AppendTo[scCases,scOne];
 Scan[stageCheck["scale_"<>ToString[n]<>"_"<>#,scOne[#],If[#=="power_residual",.001,10.^-8],"2D_coax_FEM"]&,{"linear_residual","current_residual","power_residual"}];
 stageData=<|"source_model"->"2D_coax_FEM_resource_boundary","cases"->scCases,"first_blocked_case"->scFailure|>;stageSave[],{n,{5120,10240,20480,40960}}];
stageData=<|"source_model"->"2D_coax_FEM_resource_boundary","cases"->scCases,"first_blocked_case"->scFailure,"assumptions"->"Incremental strand scaling beyond the completed 2560-strand baseline. Empirical peak allowance 180000 bytes per strand plus system 2 GiB reserve; budget blockers are explicitly environmental and are not measured device maxima. Coarse mesh; conservation validation does not prove mesh convergence. No other user processes terminated."|>;
