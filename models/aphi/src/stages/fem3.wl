Needs["NDSolve`FEM`"];
f3Solver=Switch[stageName,"fem3_ooc",{Automatic,Method->{"Pardiso","OOC"->True}},"fem3_iter",{Automatic,Method->{"Krylov",Method->"BiCGSTAB",Tolerance->10.^-10,"Preconditioner"->"ILU0","MaxIterations"->100}},_,Automatic];
If[stageName==="fem3_ooc",SetEnvironment["MKL_PARDISO_OOC_PATH"->stageDir];SetEnvironment["MKL_PARDISO_OOC_FILE_NAME"->"litz_3d_factor"];SetEnvironment["MKL_PARDISO_OOC_MAX_CORE_SIZE"->"1024"]];
If[stageName==="fem3_ooc",SetDirectory[stageDir]];
f3Cases={};f3Omega=2 Pi 200000.;f3Mu=4 Pi 10.^-7;f3Sigma=5.8*^7;f3a=.001;f3V=LitzPhysics`WireZ[f3a,200000.] 20.;
(* Dimensionless Atilde = j omega A / V and phitilde = phi / (a V).
   Coulomb gauge penalty gives vector Laplacian; continuity is explicitly coupled. *)
f3q=I f3Omega f3Mu f3Sigma f3a^2;
f3Exact[x_?NumericQ,y_?NumericQ]:=1-LitzPhysics`WireJ[f3a Sqrt[x*x+y*y],f3a,200000.,20.]/(f3Sigma f3V);
Do[Print["3D A-phi calibration cell volume=",f3h];
 {f3MeshTime,f3Mesh}=AbsoluteTiming[NDSolve`FEM`ToElementMesh[Cylinder[{{0.,0.,0.},{0.,0.,2.}},1.],"MaxCellMeasure"->f3h,"MeshOrder"->2]];
 f3Nodes=Length[f3Mesh["Coordinates"]];
 f3Budget=Quiet[Check[ToExpression[Environment["LITZ_RAM_BUDGET"]],0]];
 f3Predicted=If[stageName==="fem3",95000.,12000.] f3Nodes;
 If[NumberQ[f3Budget]&&f3Predicted>f3Budget,
  AppendTo[f3Cases,<|"cell_volume"->f3h,"nodes"->f3Nodes,"execution_status"->"blocked_environment_resource_budget","predicted_working_bytes"->f3Predicted,"available_budget_bytes"->f3Budget|>];Print[Last[f3Cases]];Break[]];
 f3BC[x_,y_]=1-(Sqrt[I f3Omega f3Mu f3Sigma] BesselI[0,Sqrt[I f3Omega f3Mu f3Sigma] f3a Sqrt[x^2+y^2]]/(2 Pi f3a BesselI[1,Sqrt[I f3Omega f3Mu f3Sigma] f3a])) 20./(f3Sigma f3V);
 {f3SolveTime,f3Sol}=AbsoluteTiming[TimeConstrained[NDSolveValue[{
 -Laplacian[ax[x,y,z],{x,y,z}]+f3q (ax[x,y,z]+D[ph[x,y,z],x])==0,
 -Laplacian[ay[x,y,z],{x,y,z}]+f3q (ay[x,y,z]+D[ph[x,y,z],y])==0,
 -Laplacian[az[x,y,z],{x,y,z}]+f3q (az[x,y,z]+D[ph[x,y,z],z])==0,
 Laplacian[ph[x,y,z],{x,y,z}]+Div[{ax[x,y,z],ay[x,y,z],az[x,y,z]},{x,y,z}]==0,
 DirichletCondition[ax[x,y,z]==0,True],DirichletCondition[ay[x,y,z]==0,True],DirichletCondition[az[x,y,z]==f3BC[x,y],True],DirichletCondition[ph[x,y,z]==-z,True]},
 {ax,ay,az,ph},Element[{x,y,z},f3Mesh],Method->{"PDEDiscretization"->{"FiniteElement","PDESolveOptions"->{"LinearSolver"->f3Solver}}}],1800,$Aborted]];
 If[!MatchQ[f3Sol,{_InterpolatingFunction,_InterpolatingFunction,_InterpolatingFunction,_InterpolatingFunction}],
 AppendTo[f3Cases,<|"cell_volume"->f3h,"execution_status"->"failed","failure"->ToString[f3Sol,InputForm]|>];Break[]];
 f3Rad=Table[{r,-f3Sigma f3V (f3Sol[[3]][r,0.,1.]+Derivative[0,0,1][f3Sol[[4]]][r,0.,1.]),LitzPhysics`WireJ[f3a r,f3a,200000.,20.]},{r,0.,.999,.999/80}];
 f3Err=Norm[f3Rad[[All,2]]-f3Rad[[All,3]]]/Norm[f3Rad[[All,3]]];
 f3PhiErr=Max[Table[Abs[f3Sol[[4]][.2,.1,z]+z],{z,0.,2.,.1}]];
 f3Gauge=Max[Abs[Table[Derivative[1,0,0][f3Sol[[1]]][r,0.,1.]+Derivative[0,1,0][f3Sol[[2]]][r,0.,1.]+Derivative[0,0,1][f3Sol[[3]]][r,0.,1.],{r,0.,.9,.1}]]];
 f3Nonconvergence=stageName==="fem3_iter"&&AnyTrue[$MessageList,StringContainsQ[ToString[#,InputForm],"krymit"]&];
 If[f3Nonconvergence,stageCheck["Krylov_calibration_convergence",1,0,"native_Krylov_iteration_diagnostic"]];
 AppendTo[f3Cases,<|"source_model"->"3D_A_phi_translation_invariant_calibration","cell_volume"->f3h,"nodes"->Length[f3Mesh["Coordinates"]],"mesh_seconds"->f3MeshTime,"solve_seconds"->f3SolveTime,"radial_relative_error"->f3Err,"phi_error"->f3PhiErr,"gauge_sample_residual"->f3Gauge,"profile"->f3Rad,"fields"->f3Sol,"mesh"->f3Mesh|>];
 stageData=<|"source_model"->"3D_A_phi_calibration","cases"->f3Cases|>;stageSave[];Print[KeyTake[Last[f3Cases],{"nodes","radial_relative_error","gauge_sample_residual"}]];If[f3Nonconvergence,Break[]],{f3h,{.00075,.00025,.00008}}];
f3Solved=Select[f3Cases,KeyExistsQ[#,"radial_relative_error"]&];
If[Length[f3Solved]>0,stageCheck["A_phi_3D_Bessel_J",Last[f3Solved]["radial_relative_error"],.01,"3D_A_phi_calibration"];
 stageCheck["A_phi_common_potential",Last[f3Solved]["phi_error"],10.^-8,"3D_A_phi_calibration"];
 stageCheck["A_phi_sampled_gauge",Last[f3Solved]["gauge_sample_residual"],10.^-3,"3D_A_phi_calibration"];
 stageCheck["three_completed_3D_meshes",Max[0,3-Length[f3Solved]],0,"3D_A_phi_calibration"];
 stageFigure["3D_mesh",Last[f3Solved]["mesh"]["Wireframe"]];
 stageFigure["3D_radial_comparison",ListLinePlot[{({1000 f3a #[[1]],Abs[#[[2]]]/10.^6}&/@Last[f3Solved]["profile"]),({1000 f3a #[[1]],Abs[#[[3]]]/10.^6}&/@Last[f3Solved]["profile"])},PlotLegends->{"3D A-phi FEM","Bessel"},Frame->True,FrameLabel->{"r (mm)","Abs J (A/mm^2)"},ImageSize->600]]];
stageData=<|"source_model"->"3D_A_phi_translation_invariant_calibration","cases"->f3Cases,"assumptions"->"Actual four coupled complex nodal PDEs on a 3D cylinder. mu_r=1; Coulomb gauge penalty vector Laplacian, continuity Laplace(phi)+Div(Atilde)=0. Axial length 2 mm in calibration domain. Prescribed analytic A on lateral and end surfaces and phi=-Vz calibrate a translation-invariant wire. This validates operator/interface and gauge; it does not solve unknown finite-length end fields, air-conductor interfaces, or physical terminations. Finite helical extension requires controlled curl/gauge/interface and insulation boundary conditions and independent comparison."|>;
