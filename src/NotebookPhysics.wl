BeginPackage["LitzPhysics`"];
WireZ::usage="WireZ[radius,frequency] internal round-wire impedance per axial metre.";
WireJ::usage="WireJ[r,radius,frequency,current] RMS phasor current density.";
CommonPort::usage="CommonPort[Z,e,total] solves common-end currents and voltage.";
DiskFEM::usage="DiskFEM[h] independent 2D complex diffusion FEM in a circular conductor.";
Topology::usage="Topology[kind,n,length,pitch,diameter] sampled labelled strand trajectories.";
StrandCenters::usage="StrandCenters[n,diameter] labelled close-packed straight-strand cross-section centres in metres.";
DTM::usage="DTM[blocks,permutations,weights] slot-to-physical impedance integration.";
IDTM::usage="IDTM[breakpoints,matrixFunction,permutationFunction] integrates union intervals.";
Begin["`Private`"];
sigma=5.8*^7; mu=4. Pi 10.^-7;
WireZ[a_?NumericQ,f_?NumericQ] := If[f==0,1/(sigma Pi a^2),With[{k=Sqrt[I 2 Pi f mu sigma]},k BesselI[0,k a]/(2 Pi a sigma BesselI[1,k a])]];
WireJ[r_?NumericQ,a_?NumericQ,f_?NumericQ,it_?NumericQ] := If[f==0,it/(Pi a^2),With[{k=Sqrt[I 2 Pi f mu sigma]},it k BesselI[0,k r]/(2 Pi a BesselI[1,k a])]];
StrandCenters[n_Integer,d_?NumericQ] := If[n==1,{{0.,0.}},If[n==7,Join[{{0.,0.}},Table[1.2 d {Cos[t],Sin[t]},{t,0,5 Pi/3,Pi/3}]],Take[SortBy[Flatten[Table[1.15 d {i+j/2.,Sqrt[3.] j/2.},{i,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]},{j,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]}],1],Norm],n]]];
CommonPort[z_?MatrixQ,e_List,it_?NumericQ] := Module[{n=Length[e],a,b,s,c,v,h,p,ext},
 a=ArrayFlatten[{{z,-Transpose[{ConstantArray[1.,n]}]},{ {ConstantArray[1.,n]},{{0.}} }}];
 b=Join[-e,{it}]; s=LinearSolve[a,b]; c=Most[s]; v=Last[s]; h=(z+ConjugateTranspose[z])/2;
 p=Re[Conjugate[c].h.c]; ext=Re[Conjugate[c].e];
 <|"currents"->c,"voltage"->v,"linear_residual"->Norm[a.s-b]/Max[Norm[b],$MinMachineNumber],
 "current_residual"->Abs[Total[c]-it]/Max[Abs[it],$MinMachineNumber],
 "common_voltage_residual"->Norm[z.c+e-v]/Max[Norm[z.c]+Norm[e],$MinMachineNumber],
 "loss_W"->p,"external_source_absorbed_W"->ext,"input_W"->Re[v Conjugate[it]],
 "power_residual"->Abs[Re[v Conjugate[it]]-p-ext]/Max[p,Abs[ext],$MinMachineNumber],
 "minimum_dissipation_eigenvalue"->Min[Re[Eigenvalues[N[h]]]],"impedance"->v/it|>
];
DiskFEM[h_?NumericQ] := Module[{mesh,u,sol,x,y,k2,int,pow,scale,j,z,p,rad,tm,integ,points,qrule,shape,deriv,tri,coords,nodal,gaussCurrent,quadKernel},
 Needs["NDSolve`FEM`"];
 k2=I 2 Pi 200000. mu sigma (0.001)^2;
 {tm,mesh}=AbsoluteTiming[NDSolve`FEM`ToElementMesh[Disk[{0.,0.},1.],"MaxCellMeasure"->h^2/2,"MeshOrder"->2]];
 {p,sol}=AbsoluteTiming[NDSolveValue[{-Laplacian[u[x,y],{x,y}]+k2 u[x,y]==0,DirichletCondition[u[x,y]==1,True]},u,Element[{x,y},mesh],Method->{"PDEDiscretization"->{"FiniteElement"}}]];
 If[Head[sol]=!=InterpolatingFunction,Return[Failure["FEMSolution",<|"h"->h|>]]];
 integ[fn_] := NIntegrate[fn[x,y],Element[{x,y},mesh],Method->{Automatic,"SymbolicProcessing"->0},AccuracyGoal->12,PrecisionGoal->10,MaxRecursion->15];
 int=integ[Function[{xx,yy},sol[xx,yy]]]; scale=20./(sigma 10.^-6 int);
 pow=sigma 10.^-6 Abs[scale]^2 integ[Function[{xx,yy},Abs[sol[xx,yy]]^2]];
 qrule=Join[{{1/3.,1/3.,1/3.,.225}},
  Append[#,.132394152788506]&/@DeleteDuplicates[Permutations[{.059715871789770,.470142064105115,.470142064105115}]],
  Append[#,.125939180544827]&/@DeleteDuplicates[Permutations[{.797426985353087,.101286507323456,.101286507323456}]]];
 shape=({#[[1]] (2 #[[1]]-1),#[[2]] (2 #[[2]]-1),#[[3]] (2 #[[3]]-1),4 #[[1]] #[[2]],4 #[[2]] #[[3]],4 #[[3]] #[[1]]}&/@qrule);
 deriv=({{1-4 #[[1]],1-4 #[[1]]},{4 #[[2]]-1,0.},{0.,4 #[[3]]-1},{4 (#[[1]]-#[[2]]),-4 #[[2]]},{4 #[[3]],4 #[[2]]},{-4 #[[3]],4 (#[[1]]-#[[3]])}}&/@qrule);
 coords=mesh["Coordinates"];nodal=sol["ValuesOnGrid"];tri=Join@@(#[[1]]&/@mesh["MeshElements"]);
 gaussCurrent=Total[Table[With[{xy=coords[[id]],uv=nodal[[id]]},.5 Total[MapThread[#1[[4]] Abs[Det[Transpose[#3].xy]] (sol@@(#2.xy))&,{qrule,shape,deriv}]]],{id,tri}]];
 z=scale/20.;
 points=Table[{r/1000.,Re[sigma scale sol[r,0.]],Im[sigma scale sol[r,0.]],Abs[sigma scale sol[r,0.]]},{r,0.,0.999,0.999/100}];
 <|"source_model"->"2D_circular_conductor_diffusion_FEM","h_normalized"->h,"nodes"->Length[mesh["Coordinates"]],
 "mesh_seconds"->tm,"solve_seconds"->p,"Rac_ohm_per_m"->Re[z],"Xinternal_ohm_per_m"->Im[z],
 "loss_W_per_m"->Re[pow],"Rac_relative_error"->Abs[Re[z]/Re[WireZ[0.001,200000.]]-1],
 "power_residual"->Abs[Re[pow]-400 Re[z]]/(400 Re[z]),
 "current_residual"->Abs[sigma 10.^-6 scale int-20.]/20.,
 "independent_current_quadrature_residual"->Abs[sigma 10.^-6 scale gaussCurrent-20.]/20.,
 "profile"->points,"field"->sol,"mesh"->mesh,"scale_V_per_m"->scale|>
];
Topology[kind_String,n_Integer,len_?NumericQ,pitch_?NumericQ,d_?NumericQ] := Module[{base,fun,zs,paths,lens,gap,curv,closed,t,rot,group,inner,center,groupCenters,pts,nearest},
 base=StrandCenters[n,d];
 groupCenters=Take[SortBy[Flatten[Table[{i+j/2.,Sqrt[3.] j/2.},{i,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]},{j,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]}],1],Norm],Ceiling[n/8]];
 rot[t_]:={{Cos[t],-Sin[t]},{Sin[t],Cos[t]}};
 fun[id_,z_]:=Switch[kind,"straight",base[[id]],"single",rot[2 Pi z/pitch].base[[id]],
 "multilevel",rot[2 Pi z/pitch].(If[n==7,base[[id]],With[{g=Quotient[id-1,8],k=Mod[id-1,8]},
  4.5 d groupCenters[[g+1]]+1.4 d rot[2 Pi z/(pitch/4)].{Cos[2 Pi k/8],Sin[2 Pi k/8]}]]),
 "crosslayer",rot[2 Pi z/pitch].(base[[id]]+0.04 d Sin[4 Pi z/pitch+2 Pi id/n] Normalize[base[[id]]+{0.00001,0.00002}])];
 zs=Subdivide[0.,len,400]; paths=Table[Append[fun[id,#],#]&/@zs,{id,n}];
 lens=Total[Norm/@Differences[#]]&/@paths;
 gap=If[n==1,Infinity,Min[Table[pts=Table[fun[i,z],{i,n}];nearest=Nearest[pts,pts,2];Min[MapThread[Norm[#1-#2[[2]]]&,{pts,nearest}]]-d,{z,Subdivide[0.,len,80]}]]];
 curv=Min[Flatten[Map[Function[path,With[{v=Differences[path],acc=Differences[Differences[path]]},Table[If[Norm[Cross[v[[k]],acc[[k]]]]>10.^-30,Norm[v[[k]]]^3/Norm[Cross[v[[k]],acc[[k]]]],10.^30],{k,Length[acc]}]]],paths]]];
 closed=Max[Norm[Most[Last[#]]-Most[First[#]]]&/@paths];
 <|"source_model"->"sampled_geometric_trajectories","kind"->kind,"strand_ids"->Range[n],"nominal_copper_area_m2"->n Pi (d/2)^2,
 "axial_length_m"->len,"pitch_m"->pitch,"diameter_m"->d,"paths"->paths,"arc_lengths_m"->lens,
 "Rdc_ohm"->1/Total[sigma Pi (d/2)^2/lens],"copper_volume_m3"->Total[Pi (d/2)^2 lens],
 "minimum_surface_gap_m"->gap,"minimum_curvature_radius_m"->curv,"periodic_position_error_m"->closed|>
];
DTM[blocks_List,perms_List,weights_List] := Total[MapThread[Function[{z,p,w},w Transpose[p].z.p],{blocks,perms,weights}]];
IDTM[breaks_List,zfun_,pfun_] := Module[{b=Sort[DeleteDuplicates[Flatten[breaks]]],mid,w},
 mid=(Most[b]+Rest[b])/2; w=Differences[b];DTM[zfun/@mid,pfun/@mid,w]];
End[];EndPackage[];


