BeginPackage["LitzVoxel`"];
FaceFluxModel::usage="FaceFluxModel[dimensions,cellWidth,frequency,quadratureOrder,excitation] full vector RT0 face-flux Galerkin volume PEEC on a cuboid.";
Begin["`Private`"];
qrule[n_] := qrule[n]=Module[{j,e,v},j=Table[If[Abs[r-s]==1,Min[r,s]/Sqrt[4. Min[r,s]^2-1.],0.],{r,n},{s,n}];{e,v}=Eigensystem[j];SortBy[Transpose[{e,2. v[[All,1]]^2}],First]];
cubeRule[n_] := cubeRule[n]=Module[{q=({(#[[1]]+1)/2,#[[2]]/2}&/@qrule[n]),pts,ws},
 ws=Flatten[Table[r[[2]] t[[2]] u[[2]],{r,q},{t,q},{u,q}]];
 Table[{Flatten[Table[sgn {r[[1]],t[[1]],u[[1]]},{r,q},{t,q},{u,q}],2],ws},{sgn,Tuples[{-1.,1.},3]}]];
corr[s_,i_,j_] := Module[{a=If[i==1,1.,0.],b=If[i==1,-1.,1.],c=If[j==1,1.,0.],d=If[j==1,-1.,1.],lo=Max[0.,-s],hi=Min[1.,1.-s]},
 a (c+d s) (hi-lo)+(b (c+d s)+a d) (hi^2-lo^2)/2+b d (hi^3-lo^3)/3];
(* Difference convolution reduces the exact six-dimensional volume integral to three
   dimensions. Self term uses 24 Duffy sectors; no epsilon softening of 1/r. *)
pair[offset_List,axis_Integer,i_Integer,j_Integer,order_Integer] := pair[offset,axis,i,j,order] = Module[{q=qrule[order],qp,qw,dd,other,self,ans,rule,points,weights,fn},
 other=DeleteCases[Range[3],axis];
 fn=If[ValueQ[pairFunction],pairFunction,pairFunction=Compile[{{pts,_Real,2},{weights,_Real,1},{off,_Real,1},{ax,_Integer},{ii,_Integer},{jj,_Integer}},Module[{total=0.,k=1,s=0.,lo=0.,hi=0.,a=0.,b=0.,c=0.,d=0.,cc=0.,rr=0.,p=0,q=0},
 a=If[ii==1,1.,0.];b=If[ii==1,-1.,1.];c=If[jj==1,1.,0.];d=If[jj==1,-1.,1.];p=If[ax==1,2,1];q=If[ax==3,2,3];
 For[k=1,k<=Length[weights],k++,s=pts[[k,ax]];lo=Max[0.,-s];hi=Min[1.,1.-s];cc=a (c+d s) (hi-lo)+(b (c+d s)+a d) (hi^2-lo^2)/2+b d (hi^3-lo^3)/3;
 rr=Sqrt[(off[[1]]+pts[[k,1]])^2+(off[[2]]+pts[[k,2]])^2+(off[[3]]+pts[[k,3]])^2];
 total+=weights[[k]] cc (1-Abs[pts[[k,p]]]) (1-Abs[pts[[k,q]]])/rr];total],RuntimeOptions->"Speed"]];
 If[Norm[offset]==0,
  rule=({(#[[1]]+1)/2,#[[2]]/2}&/@q);
  ans=Total[Flatten[Table[
   (* Non-sector components are r*t and r*u; assign explicitly to avoid duplication. *)
   points=Flatten[Table[With[{o=DeleteCases[Range[3],sector]},ReplacePart[ConstantArray[0.,3],{sector->sgn[[sector]] r[[1]],o[[1]]->sgn[[o[[1]]]] r[[1]] t[[1]],o[[2]]->sgn[[o[[2]]]] r[[1]] u[[1]]}]],{r,rule},{t,rule},{u,rule}],2];
   weights=Flatten[Table[r[[2]] t[[2]] u[[2]] r[[1]]^2,{r,rule},{t,rule},{u,rule}]];
   fn[points,weights,N[offset],axis,i,j],{sector,3},{sgn,Tuples[{-1.,1.},3]}]]],
  (* Cached sign-split quadrature nodes avoid rebuilding identical rule arrays. *)
  ans=Total[fn[#[[1]],#[[2]],N[offset],axis,i,j]&/@cubeRule[order]]];ans];
FaceFluxModel[dims_List,h_?NumericQ,f_?NumericQ,order_Integer,excitation_String] := Module[{cells,faces,faceIndex,nf,nc,local,inc,rr,ll,ri,li,entries,assemble,b,r,l,z,port,rhs,sys,s,curr,phi,pin,power,e,amp,co,offset,fun,idx,sign,center,vol,continuity,solver,gauge,known,kt,tm,reciprocity},
 cells=Tuples[Range/@dims];nc=Length[cells];
 faces=Join[Flatten[Table[If[k[[ax]]<dims[[ax]],{{ax,k}},{}],{k,cells},{ax,3}],2],Flatten[Table[{3,{i,j,0}},{i,dims[[1]]},{j,dims[[2]]}],1],Flatten[Table[{3,{i,j,dims[[3]]}},{i,dims[[1]]},{j,dims[[2]]}],1]];
 faces=DeleteDuplicates[faces];nf=Length[faces];faceIndex=Association[MapIndexed[ToString[#1,InputForm]->First[#2]&,faces]];
 local=Table[Table[With[{key=ToString[{ax,ReplacePart[k,ax->k[[ax]]-1+side]},InputForm]},Lookup[faceIndex,key,0]],{ax,3},{side,0,1}],{k,cells}];
 inc=Flatten[Table[Table[If[local[[ci,ax,side]]>0,{ci,local[[ci,ax,side]]}->If[side==1,-1.,1.],Nothing],{ax,3},{side,2}],{ci,nc}]];
 b=SparseArray[inc,{nc,nf}];
 assemble[rules_] := SparseArray[Map[First[#[[All,1]]]->Total[#[[All,2]]]& ,GatherBy[({First[#],Last[#]}&/@rules),First]],{nf,nf}];
 ri=Reap[Do[Do[If[local[[ci,ax,i]]>0&&local[[ci,ax,j]]>0,Sow[{local[[ci,ax,i]],local[[ci,ax,j]]}->If[i==j,1/3.,1/6.]/(5.8*^7 h)]],{ax,3},{i,2},{j,2}],{ci,nc}]][[2,1]];
 r=assemble[ri];
 {tm,li}=AbsoluteTiming[Reap[Do[offset=cells[[cj]]-cells[[ci]];
  Do[If[local[[ci,ax,i]]>0&&local[[cj,ax,j]]>0,Sow[{local[[ci,ax,i]],local[[cj,ax,j]]}->(10.^-7 h pair[offset,ax,i,j,order])]],{ax,3},{i,2},{j,2}],{ci,nc},{cj,nc}]][[2,1]]];
 l=Normal[assemble[li]];reciprocity=Norm[Flatten[l-Transpose[l]]]/Norm[Flatten[l]];l=(l+Transpose[l])/2;z=Normal[r]+I 2 Pi f l;
 port=Table[If[faces[[i,1]]==3&&faces[[i,2,3]]==0,1.,0.],{i,nf}];
 e=ConstantArray[0.+0. I,nf];
 If[excitation=="field",(* Uniform Bz=1 mT RMS, A=(-By/2,Bx/2,0); exact volume average RT0 dot A. *)
  e=Table[With[{ax=faces[[i,1]],k=faces[[i,2]]},If[ax==1,I 2 Pi f (-.001 (k[[2]]-.5) h/2) h,If[ax==2,I 2 Pi f (.001 (k[[1]]-.5) h/2) h,0.]]],{i,nf}]];
 (* One redundant continuity equation is removed only for a completely closed model;
    open equal-potential end faces fix the internal potential reference. *)
 sys=ArrayFlatten[{{z,-Transpose[Normal[b]],-Transpose[{port}]},{Normal[b],ConstantArray[0.,{nc,nc}],ConstantArray[0.,{nc,1}]},{{port},ConstantArray[0.,{1,nc}],{{0.}}}}];
 rhs=Join[-e,ConstantArray[0.,nc],{If[excitation=="transport",20.,0.]}];s=LeastSquares[sys,rhs];curr=Take[s,nf];phi=Take[s,{nf+1,nf+nc}];
 power=Re[Conjugate[curr].r.curr];pin=Re[Last[s] Conjugate[Last[rhs]]-Conjugate[curr].e];
 <|"source_model"->"3D_RT0_volume_face_flux_PEEC","dimensions"->dims,"cell_width_m"->h,"quadrature_order"->order,"excitation"->excitation,"cells"->nc,"face_flux_DOF"->nf,
 "faces"->faces,"local_face_ids"->local,"cells_coordinates"->cells,"R_ohm"->Normal[r],"L_H"->l,"currents_RMS_A"->curr,"cell_potentials_V"->phi,"port_voltage_V"->Last[s],
 "assembly_seconds"->tm,"linear_residual"->Norm[sys.s-rhs]/Max[Norm[rhs],$MinMachineNumber],"continuity_residual"->Norm[b.curr]/Max[Norm[curr],$MinMachineNumber],
 "port_current_A"->port.curr,"loss_W"->power,"input_W"->pin,"power_residual"->Abs[pin-power]/Max[power,$MinMachineNumber],
 "reciprocity_before_symmetrization"->reciprocity,"minimum_R_eigenvalue"->Min[Eigenvalues[Normal[r]]],"minimum_L_eigenvalue"->Min[Eigenvalues[l]],"transverse_current_norm_A"->Norm[Pick[curr,faces[[All,1]],_?(#!=3&)]],
 "side_wall_flux_A"->0.,"scope"->"Full three-component Raviart-Thomas RT0 cuboid flux basis; normal continuity enforced cellwise; side faces excluded (insulating); common end potentials. Transverse closed-loop currents retained. No capacitance or radiation; imposed field energy accounted separately."|>
];
End[];EndPackage[];
