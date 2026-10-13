(* Matrix-free RT0 PEEC.  This package reuses the independently archived
   LitzVoxel`Private`pair quadrature; no point-kernel or distance softening. *)
BeginPackage["LitzVoxelOperator`"];
CreateOperator::usage="CreateOperator[dims,h,f,order,excitation,options] constructs exact zero-padded RT0 convolution kernels, sparse R/B and a common end port. ActiveCells/ConductorLabels optionally mask insulated conductors.";
ApplyInductance::usage="ApplyInductance[operator,v] applies the RT0 inductance without a dense matrix.";
ApplyImpedance::usage="ApplyImpedance[operator,v] applies R+j omega L.";
SolveOperator::usage="SolveOperator[operator,options] solves scaled continuity/common-end equations with sparse Schur-preconditioned restarted GMRES and measured true residuals.";
DenseReference::usage="DenseReference[operator] materializes only small reference systems; returns Failure above the explicit reference DOF limit.";
OperatorMetadata::usage="OperatorMetadata[operator] returns geometry, budget and execution metadata without FFT arrays or solver factors.";
Begin["`Private`"];
Get[FileNameJoin[{DirectoryName[$InputFileName],"VoxelOperatorParallel.wl"}]];
Options[CreateOperator]={"ActiveCells"->Automatic,"ConductorLabels"->Automatic,"MemoryBudgetBytes"->Automatic,"TimeBudgetSeconds"->600.,"ProgressFunction"->None,"KernelAssemblyWorkers"->1};
Options[SolveOperator]={"Restart"->40,"MaxIterations"->800,"Tolerance"->10.^-8,"TotalCurrentRMSA"->Automatic,"TimeBudgetSeconds"->600.,"CheckpointFunction"->None};
Options[DenseReference]={"MaximumDOF"->600};
key[x_]:=ToString[x,InputForm];
environmentBudget[]:=Module[{s=Environment["LITZ_RAM_BUDGET"]},If[StringQ[s]&&StringMatchQ[s,DigitCharacter..],ToExpression[s],Infinity]];
emit[fun_,event_]:=If[fun=!=None,fun[event]];
packed[x_]:=Developer`ToPackedArray[N[x]];
fft[x_]:=Fourier[x,FourierParameters->{1,-1}];
ifft[x_]:=InverseFourier[x,FourierParameters->{1,-1}];
(* Reflection removes redundant quadrature evaluations while retaining the
   same volume integral. Non-axis reflections leave each RT0 shape unchanged. *)
canonicalPair[d_,ax_,i_,j_,order_]:=Module[{dd=Abs[d],ii=i,jj=j},
 If[d[[ax]]<0,ii=3-i;jj=3-j];
 If[ii==2&&jj==2,ii=1;jj=1];
 LitzVoxel`Private`pair[dd,ax,ii,jj,order]];

CreateOperator[dims_List,h_?NumericQ,f_?NumericQ,order_Integer,excitation_String,OptionsPattern[]]:=Module[
 {cells,labels,labelMap,index,faces,faceIndex,local,nc,nf,grid,scatter,r,b,port,e,c,edges,components,
  budget,padding,np,estimate,progress=OptionValue["ProgressFunction"],start=AbsoluteTime[],time=OptionValue["TimeBudgetSeconds"],
  kernelFFT,ker,offsets,d,position,diagL,unit,one,elapsed,sourceRows,sourceLabels,
  workers=OptionValue["KernelAssemblyWorkers"],effectiveWorkers,workerEstimate,parallelResult,axisTerms,workerMetadata={}},
 If[Length[dims]!=3||!And@@(IntegerQ[#]&&#>0&/@dims)||h<=0||f<0||order<2||!MemberQ[{"transport","field"},excitation]||!IntegerQ[workers]||workers<1,
  Return[Failure["InvalidParameters",<|"dimensions"->dims,"h"->h,"f"->f,"order"->order,"excitation"->excitation|>]]];
 If[Length[DownValues[LitzVoxel`Private`pair]]==0,Return[Failure["ReferenceKernelNotLoaded",<|"required_package"->"src/VoxelPEEC.wl"|>]]];
 cells=If[OptionValue["ActiveCells"]===Automatic,Tuples[Range/@dims],OptionValue["ActiveCells"]];
 If[!ListQ[cells]||cells=={}||!And@@(MatchQ[#,{_Integer,_Integer,_Integer}]&&And@@Thread[1<=#]&&And@@Thread[#<=dims]&/@cells)||Length[DeleteDuplicates[cells]]!=Length[cells],
  Return[Failure["InvalidActiveCells",<||>]]];
 labels=If[OptionValue["ConductorLabels"]===Automatic,ConstantArray[1,Length[cells]],OptionValue["ConductorLabels"]];
 If[!ListQ[labels]||Length[labels]!=Length[cells]||!And@@(IntegerQ[#]&&#>0&/@labels),Return[Failure["InvalidConductorLabels",<||>]]];
 (* Preserve caller cell/label order; the regular box case matches FaceFluxModel. *)
 nc=Length[cells];index=Association[MapIndexed[key[#1]->First[#2]&,cells]];
 labelMap=Association[MapThread[key[#1]->#2&,{cells,labels}]];
 faces=Flatten[Table[If[Lookup[index,key[k+UnitVector[3,ax]],0]>0&&Lookup[labelMap,key[k+UnitVector[3,ax]],0]==Lookup[labelMap,key[k]],{{ax,k}},{}],{k,cells},{ax,3}],2];
 faces=Join[faces,({3,ReplacePart[#,3->0]}&/@Select[cells,#[[3]]==1&]),({3,#}&/@Select[cells,#[[3]]==dims[[3]]&])];
 faces=DeleteDuplicates[faces];nf=Length[faces];
 If[nf==0,Return[Failure["NoFluxFaces",<||>]]];
 faceIndex=Association[MapIndexed[key[#1]->First[#2]&,faces]];
 local=Table[Table[Lookup[faceIndex,key[{ax,ReplacePart[k,ax->k[[ax]]-1+side]}],0],{ax,3},{side,0,1}],{k,cells}];
 edges=Table[If[Lookup[index,key[k+UnitVector[3,ax]],0]>0&&Lookup[labelMap,key[k+UnitVector[3,ax]],0]==Lookup[labelMap,key[k]],UndirectedEdge[Lookup[index,key[k]],Lookup[index,key[k+UnitVector[3,ax]]]],Nothing],{k,cells},{ax,3}];
 components=ConnectedComponents[Graph[Range[nc],Flatten[edges]]];
 If[AnyTrue[components,!AnyTrue[cells[[#]],#[[3]]==1&]||!AnyTrue[cells[[#]],#[[3]]==dims[[3]]&]&],
  Return[Failure["UnportedComponent",<|"reason"->"Every connected conductor component must reach both common end planes; closed internal domains need a separate gauge/port formulation."|>]]];
 padding=2^Ceiling[Log[2,2 dims]];np=Times@@padding;
 budget=If[OptionValue["MemoryBudgetBytes"]===Automatic,environmentBudget[],OptionValue["MemoryBudgetBytes"]];
 (* Includes twelve cached complex kernels, FFT scratch, Arnoldi vectors,
    sparse factors and WL quadrature memoization. It is an estimate, not a
    measured hardware limit. Runtime runner retains its own reserve guard. *)
 effectiveWorkers=If[workers==1,1,Min[3,workers]];
 workerEstimate=kernelWorkerMemoryBytes[dims,padding,workers];
 estimate=1280. np+32768. nc+1024. nf+workerEstimate;
 If[NumericQ[budget]&&estimate>.7 budget,Return[Failure["ResourceBudget",<|"execution_status"->"blocked_environment_resource_budget","estimated_working_bytes"->estimate,"working_budget_bytes"->budget,"soft_fraction"->.7,"measured_allocation"->False|>]]];
 grid=packed[(#[[1]]-1) padding[[2]] padding[[3]]+(#[[2]]-1) padding[[3]]+#[[3]]&/@cells];
 (* Indices must remain integers, unlike numerical field arrays. *)
 grid=Round[grid];
 scatter=Table[With[{ids=local[[All,ax,side]],rows=Range[nc]},With[{keep=Flatten[Position[ids,_?(#>0&)]]},SparseArray[Thread[Transpose[{rows[[keep]],ids[[keep]]}]->1.],{nc,nf}]]],{ax,3},{side,2}];
 r=Total[Table[(Transpose[scatter[[ax,1]]].scatter[[ax,1]]+Transpose[scatter[[ax,2]]].scatter[[ax,2]])/(3. 5.8*^7 h)
  +(Transpose[scatter[[ax,1]]].scatter[[ax,2]]+Transpose[scatter[[ax,2]]].scatter[[ax,1]])/(6. 5.8*^7 h),{ax,3}]];
 b=Total[Table[-scatter[[ax,1]]+scatter[[ax,2]],{ax,3}]];
 port=packed[If[#[[1]]==3&&#[[2,3]]==0,1.,0.]&/@faces];
 e=ConstantArray[0.+0. I,nf];
 If[excitation=="field",e=packed[Table[With[{ax=faces[[i,1]],k=faces[[i,2]]},If[ax==1,I 2 Pi f (-.001 (k[[2]]-.5) h/2) h,If[ax==2,I 2 Pi f (.001 (k[[1]]-.5) h/2) h,0.]]],{i,nf}]]];
 c=Join[b,SparseArray[{port}]];
 kernelFFT=Association[];offsets=Tuples[Range[1-#, #-1]&/@dims];
 If[workers==1,Do[ker=ConstantArray[0.,padding];
  Do[If[AbsoluteTime[]-start>time,Return[Failure["TimeBudget",<|"execution_status"->"not_completed_time_budget","phase"->"kernel_assembly","completed_kernels"->Length[kernelFFT],"elapsed_seconds"->AbsoluteTime[]-start|>]]];
   position=MapThread[If[#1>=0,#1+1,#2+#1+1]&,{d,padding}];
   ker[[Sequence@@position]]=10.^-7 h canonicalPair[-d,ax,side,other,order],{d,offsets}];
  AssociateTo[kernelFFT,key[{ax,side,other}]->packed[fft[packed[ker]]]];
  emit[progress,<|"phase"->"kernel_assembly","completed_kernels"->Length[kernelFFT],"required_kernels"->12,"elapsed_seconds"->AbsoluteTime[]-start|>],
  {ax,3},{side,2},{other,2}];
  axisTerms=Table[{10.^-7 h canonicalPair[{0,0,0},ax,1,1,order],10.^-7 h canonicalPair[UnitVector[3,ax],ax,2,1,order]},{ax,3}],
  parallelResult=assembleParallelAxisGroups[dims,padding,h,order,workers,start+time,progress];
  If[!AssociationQ[parallelResult],Return[parallelResult]];
  kernelFFT=Join@@Lookup[parallelResult["axis_groups"],"kernel_fft"];
  axisTerms=({#["diagonal_one_H"],#["diagonal_cross_H"]}&/@parallelResult["axis_groups"]);
  workerMetadata=KeyDrop[#,{"kernel_fft","diagonal_one_H","diagonal_cross_H"}]&/@parallelResult["axis_groups"];
  emit[progress,<|"phase"->"kernel_assembly","completed_kernels"->12,"required_kernels"->12,
    "requested_workers"->workers,"effective_workers"->effectiveWorkers,"axis_worker_metadata"->workerMetadata,"elapsed_seconds"->AbsoluteTime[]-start|>];
  Clear[parallelResult]];
 diagL=packed[Table[With[{ax=face[[1]],k=face[[2]]},one=axisTerms[[ax,1]];
  If[ax==3&&(k[[3]]==0||k[[3]]==dims[[3]]),one,2 one+2 axisTerms[[ax,2]]]],{face,faces}]];
 sourceRows=Flatten[Position[port,1.]];
 sourceLabels=Table[Lookup[labelMap,key[ReplacePart[faces[[i,2]],3->1]]],{i,sourceRows}];
 elapsed=AbsoluteTime[]-start;
 <|"source_model"->"3D_RT0_exact_Toeplitz_matrix_free_PEEC","execution_status"->"constructed","dimensions"->dims,"cell_width_m"->h,"frequency_Hz"->f,"quadrature_order"->order,
  "excitation"->excitation,"cells"->nc,"face_flux_DOF"->nf,"cells_coordinates"->cells,"conductor_labels"->labels,"faces"->faces,"local_face_ids"->local,
  "padding"->padding,"padded_grid_ids"->grid,"scatter"->scatter,"R_ohm"->r,"B"->b,"C"->c,"port"->port,"external_voltage_RMS_V"->e,"L_diagonal_H"->diagL,"kernel_fft"->kernelFFT,
  "source_face_rows"->sourceRows,"source_face_labels"->sourceLabels,"assembly_seconds"->elapsed,"estimated_working_bytes"->estimate,"working_budget_bytes"->budget,
  "estimated_worker_bytes"->workerEstimate,"kernel_assembly_workers_requested"->workers,"kernel_assembly_workers_effective"->effectiveWorkers,
  "kernel_assembly_method"->If[workers==1,"serial_original_offset_order","parallel_axis_groups_original_offset_order"],"axis_worker_metadata"->workerMetadata,
  "FFT_parameters"->{1,-1},"scope"->"Full three-component RT0 on a regular Cartesian grid, optional labelled active-cell mask. Insulating lateral/mask faces omitted. Every connected conductor component reaches both end planes. All bottom end faces share one port potential; top end faces share the grounded potential. Original finite-volume convolution quadrature and Duffy self integral retained. No capacitance/radiation. Geometry staircase error and spatial convergence require separate tests."|>
];

OperatorMetadata[op_Association]:=KeyDrop[op,{"scatter","R_ohm","B","C","port","external_voltage_RMS_V","L_diagonal_H","kernel_fft","padded_grid_ids"}];

ApplyInductance[op_Association,v_List]:=Module[{out=ConstantArray[0.+0. I,op["face_flux_DOF"]],pad=op["padding"],np,ids=op["padded_grid_ids"],a,b,fv,field},
 If[Length[v]!=op["face_flux_DOF"],Return[Failure["VectorDimensions",<||>]]];np=Times@@pad;
 Do[fv=Table[a=ConstantArray[0.+0. I,np];a[[ids]]=op["scatter"][[ax,other]].v;fft[ArrayReshape[packed[a],pad]],{other,2}];
  Do[field=ifft[op["kernel_fft"][key[{ax,side,1}]] fv[[1]]+op["kernel_fft"][key[{ax,side,2}]] fv[[2]]];
   out+=Transpose[op["scatter"][[ax,side]]].Flatten[field][[ids]],{side,2}],{ax,3}];packed[out]];
ApplyImpedance[op_Association,v_List]:=op["R_ohm"].v+I 2 Pi op["frequency_Hz"] ApplyInductance[op,v];

DenseReference[op_Association,OptionsPattern[]]:=Module[{nf=op["face_flux_DOF"],nc=op["cells"],l,z,c=Normal[op["C"]],sys},
 If[nf+nc+1>OptionValue["MaximumDOF"],Return[Failure["DenseReferenceBudget",<|"total_DOF"->nf+nc+1,"limit"->OptionValue["MaximumDOF"]|>]]];
 l=Transpose[Table[ApplyInductance[op,UnitVector[nf,j]],{j,nf}]];
 z=Normal[op["R_ohm"]]+I 2 Pi op["frequency_Hz"] l;
 sys=ArrayFlatten[{{z,-Transpose[c]},{c,ConstantArray[0.,{nc+1,nc+1}]}}];
 <|"L_H"->l,"Z_ohm"->z,"system"->sys,"R_ohm"->Normal[op["R_ohm"]],"source_model"->"materialized_small_RT0_Toeplitz_reference"|>];

SolveOperator[op_Association,OptionsPattern[]]:=Module[
 {nf=op["face_flux_DOF"],nc=op["cells"],c=op["C"],r=op["R_ohm"],e=op["external_voltage_RMS_V"],it,
  zscale,iscale=1.,d,dinv,schur,schurSolve,apply,precondition,rhs,x,res,preResidual,v,h,beta,w,coeff,trial,j,k,count=0,cycle=0,restart=OptionValue["Restart"],
  max=OptionValue["MaxIterations"],tol=OptionValue["Tolerance"],start=AbsoluteTime[],time=OptionValue["TimeBudgetSeconds"],checkpoint=OptionValue["CheckpointFunction"],
  history={},stop="max_iterations",curr,phi,vport,joule,pin,voltageResidual,currentResidual,sourceCurrents,labels,scaleRHS,success=False,breakdown=False},
 If[!IntegerQ[restart]||restart<1||!IntegerQ[max]||max<1||tol<=0,Return[Failure["InvalidSolverOptions",<||>]]];
 it=If[OptionValue["TotalCurrentRMSA"]===Automatic,If[op["excitation"]=="transport",20.,0.],OptionValue["TotalCurrentRMSA"]];
 d=packed[Normal[Diagonal[r]]+I 2 Pi op["frequency_Hz"] op["L_diagonal_H"]];
 zscale=Max[Abs[d]];If[!NumericQ[zscale]||zscale<=0,Return[Failure["InvalidImpedanceScale",<||>]]];d=d/zscale;
 dinv=SparseArray[Band[{1,1}]->(1./d),{nf,nf}];schur=c.dinv.Transpose[c];
 schurSolve=Quiet[Check[LinearSolve[schur],$Failed]];
 If[Head[schurSolve]=!=LinearSolveFunction,Return[Failure["PreconditionerFactorization",<|"execution_status"->"failed_numerical","phase"->"sparse_Schur_factorization"|>]]];
 apply[y_]:=Join[ApplyImpedance[op,Take[y,nf]]/zscale-Transpose[c].Drop[y,nf],c.Take[y,nf]];
 precondition[y_]:=Module[{a=Take[y,nf],bb=Drop[y,nf],q,t},q=dinv.a;t=schurSolve[bb-c.q];Join[q+dinv.Transpose[c].t,t]];
 rhs=packed[Join[-e/(zscale iscale),ConstantArray[0.,nc],{it/iscale}]];
 scaleRHS=Max[Norm[rhs],$MinMachineNumber];x=ConstantArray[0.+0. I,nf+nc+1];res=rhs-apply[x];
 If[Norm[res]/scaleRHS<=tol,success=True;stop="converged"];
 While[!success&&count<max&&AbsoluteTime[]-start<time,
  cycle++;beta=Norm[precondition[res]];If[!NumericQ[beta]||beta==0.,stop="preconditioner_breakdown";Break[]];
  v={precondition[res]/beta};h=ConstantArray[0.+0. I,{restart+1,restart}];trial=x;breakdown=False;
  Do[w=precondition[apply[v[[j]]]];
   (* Twice modified Gram-Schmidt controls loss of orthogonality. *)
   Do[Do[coeff=Conjugate[v[[k]]].w;h[[k,j]]+=coeff;w-=coeff v[[k]],{k,j}],{2}];
   h[[j+1,j]]=Norm[w];If[Abs[h[[j+1,j]]]>10.^-14,AppendTo[v,w/h[[j+1,j]]],breakdown=True];
   coeff=LeastSquares[h[[1;;j+1,1;;j]],Join[{beta},ConstantArray[0.+0. I,j]]];
   trial=x+Total[MapThread[Times,{coeff,v[[1;;j]]}]];res=rhs-apply[trial];count++;
   AppendTo[history,<|"iteration"->count,"restart_cycle"->cycle,"true_relative_residual"->Norm[res]/scaleRHS,"elapsed_seconds"->AbsoluteTime[]-start|>];
   If[Norm[res]/scaleRHS<=tol,success=True;stop="converged";Break[]];
   If[AbsoluteTime[]-start>=time,stop="time_budget";Break[]];
   If[breakdown,stop="Arnoldi_breakdown";Break[]];If[count>=max,Break[]],{j,Min[restart,max-count]}];
  x=trial;emit[checkpoint,<|"phase"->"GMRES","iteration"->count,"true_relative_residual"->Norm[res]/scaleRHS,"elapsed_seconds"->AbsoluteTime[]-start,"execution_status"->If[success,"converged","running"]|>];
  If[breakdown&&!success,Break[]]];
 If[!success&&AbsoluteTime[]-start>=time,stop="time_budget"];
 curr=packed[iscale Take[x,nf]];phi=packed[zscale iscale Take[x,{nf+1,nf+nc}]];vport=zscale iscale Last[x];
 joule=Re[Conjugate[curr].r.curr];pin=Re[vport Conjugate[it]-Conjugate[curr].e];
 voltageResidual=Norm[ApplyImpedance[op,curr]-Transpose[c].(zscale iscale Drop[x,nf])+e]/Max[Norm[e],Norm[ApplyImpedance[op,curr]],Abs[vport],$MinMachineNumber];
 currentResidual=Norm[c.curr-Join[ConstantArray[0.,nc],{it}]]/Max[Norm[curr],Abs[it],$MinMachineNumber];
 labels=DeleteDuplicates[op["source_face_labels"]];
 sourceCurrents=Association[Table[ToString[label]->Total[Pick[curr[[op["source_face_rows"]]],op["source_face_labels"],label]],{label,labels}]];
 <|"source_model"->op["source_model"],"execution_status"->If[success,"executed","failed_numerical"],"stop_reason"->stop,"converged"->success,
  "iterations"->count,"restart"->restart,"max_iterations"->max,"linear_residual"->Norm[rhs-apply[x]]/scaleRHS,"voltage_equation_residual"->voltageResidual,"constraint_residual"->currentResidual,
  "continuity_residual"->Norm[op["B"].curr]/Max[Norm[curr],$MinMachineNumber],"port_current_A"->op["port"].curr,"port_current_relative_residual"->Abs[op["port"].curr-it]/Max[Abs[it],Norm[curr],$MinMachineNumber],
  "currents_RMS_A"->curr,"cell_potentials_V"->phi,"port_voltage_V"->vport,"source_conductor_currents_RMS_A"->sourceCurrents,
  "loss_W"->joule,"input_W"->pin,"power_residual"->Abs[pin-joule]/Max[Abs[joule],$MinMachineNumber],"transverse_current_norm_A"->Norm[Pick[curr,op["faces"][[All,1]],_?(#!=3&)]],
  "side_wall_flux_A"->0.,"side_wall_flux_status"->"structurally_zero_by_omitted_insulating_faces","elapsed_seconds"->AbsoluteTime[]-start,"history"->history,
  "preconditioner"->"diag(R+j omega L) with sparse C D^-1 C^T Schur factorization","Schur_DOF"->nc+1,"Schur_nonzeros"->Length[schur["NonzeroValues"]],"impedance_scale_ohm"->zscale,"current_scale_A"->iscale|>
];
End[];EndPackage[];
