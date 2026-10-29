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
End[];EndPackage[];
