BeginPackage["LitzPEEC`"];
LongitudinalModel::usage="LongitudinalModel[m,length,frequency,options] finite-volume rectangular filaments approximating a round wire; insulated longitudinal basis. Options expose mutual/self quadrature, resource preflight and compatible pairwise or lattice-offset assembly.";
SelfIntegral::usage="SelfIntegral[width,height,length] singular transverse self integral using difference convolution and Duffy mapping.";
Begin["`Private`"];
Options[SelfIntegral]={"SelfAccuracyGoal"->10,"SelfPrecisionGoal"->8,"SelfWorkingPrecision"->MachinePrecision};
Options[LongitudinalModel]={"MutualQuadratureOrder"->4,"SelfAccuracyGoal"->10,"SelfPrecisionGoal"->8,
 "SelfWorkingPrecision"->MachinePrecision,"TotalCurrentRMSA"->20.,"MemoryBudgetBytes"->Infinity,
 "ComputeInductanceEigenvalue"->True,"MutualKernelMethod"->"Pairwise","ProgressFunction"->None};
lk[d_?NumericQ,len_?NumericQ]:=2 (len ArcSinh[len/d]-Sqrt[len^2+d^2]+d);
SelfIntegral[wx_?NumericQ,wy_?NumericQ,len_?NumericQ,OptionsPattern[]] := 4 NIntegrate[u (1-u) (1-u t) (lk[u Sqrt[wx^2+wy^2 t^2],len]+lk[u Sqrt[wy^2+wx^2 t^2],len]),{u,0,1},{t,0,1},WorkingPrecision->OptionValue["SelfWorkingPrecision"],AccuracyGoal->OptionValue["SelfAccuracyGoal"],PrecisionGoal->OptionValue["SelfPrecisionGoal"],Method->{"GlobalAdaptive","SymbolicProcessing"->0}];
quad[n_Integer] := Module[{j,e,v},j=Table[If[Abs[r-s]==1,Min[r,s]/Sqrt[4. Min[r,s]^2-1.],0.],{r,n},{s,n}];{e,v}=Eigensystem[j];SortBy[Transpose[{e,2. v[[All,1]]^2}],First]];
(* With e=0, solve Z*x=1, V=It/sum(x), i=V*x. This is algebraically
   identical to the augmented common-end equations without a second full matrix.
   R is diagonal and positive; Joule power uses R directly. *)
zeroSourcePort[z_,r_,it_] := Module[{x,c,v,p,n=Length[z]},x=LinearSolve[z,ConstantArray[1.+0.I,Length[z]]];v=it/Total[x];c=v x;p=Re[Conjugate[c].r.c];
 <|"currents"->c,"voltage"->v,"impedance"->v/it,"loss_W"->p,"external_source_absorbed_W"->0.,"input_W"->Re[v Conjugate[it]],
 "linear_residual"->Norm[Join[z.c-v,{Total[c]-it}]]/Max[Abs[it],$MinMachineNumber],"current_residual"->Abs[Total[c]-it]/Abs[it],"common_voltage_residual"->Norm[z.c-v]/Max[Norm[z.c],$MinMachineNumber],"power_residual"->Abs[Re[v Conjugate[it]]-p]/Max[p,$MinMachineNumber],"minimum_dissipation_eigenvalue"->Min[Normal[Diagonal[r]]]|>];
LongitudinalModel[m_Integer,len_?NumericQ,f_?NumericQ,OptionsPattern[]] := Module[{a=.001,w,centers,area,n,q,qp,qw,lmat,rmat,z,sol,t,kernel,sv,ref,dxs,dys,
 order=OptionValue["MutualQuadratureOrder"],ag=OptionValue["SelfAccuracyGoal"],pg=OptionValue["SelfPrecisionGoal"],
 wp=OptionValue["SelfWorkingPrecision"],it=OptionValue["TotalCurrentRMSA"],budget=OptionValue["MemoryBudgetBytes"],
 method=OptionValue["MutualKernelMethod"],progress=OptionValue["ProgressFunction"],estimate,selfTime,solveTime,eigenTime,eigenMin,
 start=AbsoluteTime[],lattice,lookup,offsets,values,emit,reciprocity,sampledEnergy,vectors},
 If[m<2||len<=0||f<0||!IntegerQ[order]||order<2||!NumericQ[it]||it==0||!NumericQ[ag]||!NumericQ[pg]||ag<0||pg<0||
   !MemberQ[{"Pairwise","GridOffsets"},method]||!(TrueQ[budget===Infinity]||TrueQ[NumericQ[budget]&&budget>0]),
   Return[Failure["InvalidPEECOptions",<|"cross_divisions"->m,"length_m"->len,"frequency_Hz"->f|>]]];
 emit[event_]:=If[progress=!=None,progress[event]];
 w=2 a/m;centers=Select[Flatten[Table[{x,y},{x,-a+w/2,a-w/2,w},{y,-a+w/2,a-w/2,w}],1],Norm[#]<=a&];
 n=Length[centers];area=w^2;estimate=128. n^2+32768. n;
 If[NumericQ[budget]&&estimate>.7 budget,Return[Failure["ResourceBudget",<|"execution_status"->"blocked_environment_resource_budget",
  "filaments"->n,"estimated_working_bytes"->estimate,"working_budget_bytes"->budget,"measured_allocation"->False|>]]];
 emit[<|"phase"->"preflight","filaments"->n,"estimated_working_bytes"->estimate,"working_budget_bytes"->If[budget===Infinity,Null,budget]|>];
 q=quad[order];qp=Flatten[Table[w/2 {s[[1]],t[[1]]},{s,q},{t,q}],1];qw=Flatten[Table[s[[2]] t[[2]]/4,{s,q},{t,q}]];
 (* A_i^-1 integral over each cross section and exact double integration along z.
    Self uses autocorrelation plus Duffy map; mutual uses tensor Gauss, no epsilon-distance substitute. *)
 kernel=Compile[{{dx,_Real},{dy,_Real},{ll,_Real},{pts,_Real,2},{weights,_Real,1}},Module[{total=0.,d=0.,i=1,j=1},
 If[dx!=0.||dy!=0.,For[i=1,i<=Length[weights],i++,For[j=1,j<=Length[weights],j++,d=Sqrt[(dx+pts[[i,1]]-pts[[j,1]])^2+(dy+pts[[i,2]]-pts[[j,2]])^2];total+=weights[[i]] weights[[j]] 2 (ll Log[ll/d+Sqrt[1+(ll/d)^2]]-Sqrt[ll^2+d^2]+d)]]];total],RuntimeOptions->"Speed",RuntimeAttributes->{Listable},Parallelization->True];
 {selfTime,sv}=AbsoluteTiming[SelfIntegral[w,w,len,"SelfAccuracyGoal"->ag,"SelfPrecisionGoal"->pg,"SelfWorkingPrecision"->wp]];
 If[!NumericQ[sv]||!TrueQ[sv>0],Return[Failure["SelfIntegralFailed",<|"value"->ToString[sv,InputForm]|>]]];
 emit[<|"phase"->"self_integral","elapsed_seconds"->selfTime,"self_integral_m"->sv|>];
 {t,lmat}=AbsoluteTiming[
  If[method=="Pairwise",
   dxs=Flatten[Outer[Subtract,centers[[All,1]],centers[[All,1]]]];dys=Flatten[Outer[Subtract,centers[[All,2]],centers[[All,2]]]];
   lmat=10.^-7 Partition[kernel[dxs,dys,len,qp,qw],n],
   (* Uniform square lattice: exact same tensor-volume kernel depends only on
      integer displacement. Reuse translation/reflection symmetry; no point
      kernel, softened distance, near/far approximation or new physics. *)
   lattice=Round[(centers+ a)/w-.5];offsets=Tuples[Range[0,m-1],2];
   values=kernel[N[w offsets[[All,1]]],N[w offsets[[All,2]]],N[len],qp,qw];
   lookup=Partition[values,m];lookup[[1,1]]=sv;
   lmat=Developer`ToPackedArray[10.^-7 Table[With[{d=Abs[lattice[[i]]-lattice[[j]]]+1},lookup[[d[[1]],d[[2]]]]],{i,n},{j,n}]]];
  Do[lmat[[i,i]]=10.^-7 N[sv],{i,n}];lmat];
 emit[<|"phase"->"mutual_assembly","elapsed_seconds"->t,"filaments"->n,"kernel_method"->method,"mutual_quadrature_order"->order|>];
 Clear[dxs,dys];rmat=SparseArray[Band[{1,1}]->len/(5.8*^7 area),{n,n}];z=rmat+I 2 Pi f lmat;
 {solveTime,sol}=AbsoluteTiming[zeroSourcePort[z,rmat,it]];ref=Re[LitzPhysics`WireZ[Sqrt[n area/Pi],f]];
 emit[<|"phase"->"common_port_solve","elapsed_seconds"->solveTime,"linear_residual"->sol["linear_residual"]|>];
 reciprocity=Norm[lmat-Transpose[lmat],"Frobenius"]/Max[Norm[lmat,"Frobenius"],$MinMachineNumber];
 vectors={N[Sin[Range[n]/17.]+I Cos[Range[n]/23.]],ConstantArray[1.+0.I,n],sol["currents"]};
 sampledEnergy=Min[Re[Conjugate[#].lmat.#]/Max[Norm[#]^2,$MinMachineNumber]&/@vectors];
 {eigenTime,eigenMin}=If[TrueQ[OptionValue["ComputeInductanceEigenvalue"]],AbsoluteTiming[Min[Eigenvalues[lmat]]],{0.,Null}];
 <|"source_model"->"finite_length_longitudinal_volume_filament_PEEC","cross_divisions"->m,"filaments"->n,"length_m"->len,"area_m2"->n area,"cell_width_m"->w,
 "centers_m"->centers,"resistance_matrix_ohm"->rmat,"partial_inductance_matrix_H"->lmat,"Z_ohm"->z,"solution"->sol,"assembly_seconds"->t,
 "self_integral_seconds"->selfTime,"solve_seconds"->solveTime,"eigenvalue_seconds"->eigenTime,"elapsed_seconds"->(AbsoluteTime[]-start),
 "Rac_ohm_per_axial_m"->sol["loss_W"]/(Abs[it]^2 len),"Bessel_equal_area_Rac_ohm_per_m"->ref,
 "Bessel_Rac_relative_error"->Abs[sol["loss_W"]/(Abs[it]^2 len ref)-1],"minimum_L_eigenvalue_H"->eigenMin,
 "inductance_passivity_status"->If[eigenMin===Null,"sampled_quadratic_forms_only","full_eigenvalue_measured"],
 "minimum_sampled_L_quadratic_form_H"->sampledEnergy,"L_reciprocity_relative_residual"->reciprocity,
 "mutual_quadrature_order"->order,"self_accuracy_goal"->ag,"self_precision_goal"->pg,"self_working_precision"->ToString[wp,InputForm],
 "mutual_kernel_method"->method,"estimated_working_bytes"->estimate,"working_budget_bytes"->If[budget===Infinity,Null,budget],
 "scope"->"Longitudinal, uniform-in-z volume basis; transverse eddy loops and end redistribution omitted. Finite-length partial X includes external inductance; compare Rac only with long-wire Bessel, record length and polygonal area sensitivity."|>
];
End[];EndPackage[];


