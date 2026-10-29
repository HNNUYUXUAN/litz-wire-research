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
End[];EndPackage[];
