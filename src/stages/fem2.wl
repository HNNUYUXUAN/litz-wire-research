femCases={};
Do[Print["DISK FEM h=",h];
 femOne=TimeConstrained[LitzPhysics`DiskFEM[h],600,$Aborted];
 If[!AssociationQ[femOne],AppendTo[femCases,<|"h"->h,"execution_status"->"failed","failure"->ToString[femOne,InputForm]|>];stageCheck["FEM_solution_"<>ToString[h],1,0,"2D_FEM"];Break[]];
 AppendTo[femCases,femOne];stageData=<|"source_model"->"2D_diffusion_FEM","cases"->femCases|>;stageSave[];
 Print[KeyTake[femOne,{"nodes","Rac_relative_error","power_residual","solve_seconds"}]],{h,{0.24,0.12,0.06}}];
If[Length[femCases]==3&&AllTrue[femCases,KeyExistsQ[#,"Rac_relative_error"]&],
 stageCheck["FEM_analytic_Rac",Last[femCases]["Rac_relative_error"],.01,"2D_FEM"];
 stageCheck["FEM_fine_grid_change",Abs[Last[femCases]["Rac_ohm_per_m"]/femCases[[-2]]["Rac_ohm_per_m"]-1],.01,"2D_FEM"];
 stageCheck["FEM_independent_power",Last[femCases]["power_residual"],.001,"2D_FEM"];
 stageCheck["FEM_current",Last[femCases]["current_residual"],10.^-8,"2D_FEM"];
 stageCheck["FEM_independent_current_quadrature",Last[femCases]["independent_current_quadrature_residual"],10.^-8,"manual_Dunavant_physical_IF_vs_NIntegrate"];
 femProfile=Last[femCases]["profile"];
 femRef=Table[{r,Re[LitzPhysics`WireJ[r,.001,200000.,20.]],Im[LitzPhysics`WireJ[r,.001,200000.,20.]]},{r,femProfile[[All,1]]}];
 stageFigure["radial_comparison",ListLinePlot[{(#*{1000,10.^-6}&/@femProfile[[All,{1,2}]]),(#*{1000,10.^-6}&/@femRef[[All,{1,2}]]),(#*{1000,10.^-6}&/@femProfile[[All,{1,3}]]),(#*{1000,10.^-6}&/@femRef[[All,{1,3}]])},PlotLegends->{"FEM Re J","Bessel Re J","FEM Im J","Bessel Im J"},Frame->True,FrameLabel->{"r (mm)","J (A/mm^2)"},ImageSize->600]];
 stageFigure["convergence",ListLogLogPlot[Table[{c["nodes"],c["Rac_relative_error"]},{c,femCases}],Joined->True,Frame->True,FrameLabel->{"nodes","relative Rac error"},ImageSize->600]];
 stageFigure["mesh",Last[femCases]["mesh"]["Wireframe"]];
 stageData=<|"source_model"->"2D_diffusion_FEM","cases"->femCases,"assumptions"->"Circular conductor-only complex diffusion PDE, quadratic nodal FEM, normalized unit boundary Ez. Coordinates scaled by radius; physical integrals retain a^2. Internal impedance; no air/return in this calibration. Independently integrate squared field over the actual mesh. Machine precision FEM."|>;
 Export[FileNameJoin[{stageDir,"convergence.csv"}],Prepend[Table[Lookup[c,{"h_normalized","nodes","Rac_ohm_per_m","Rac_relative_error","power_residual","solve_seconds"}],{c,femCases}],{"h/a","nodes","Rac_ohm_per_m","Rac_error","power_error","solve_s"}],"CSV"];
];


