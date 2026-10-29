Needs["NDSolve`FEM`"];
If[!ListQ[mmHValues],mmHValues={.04,.015,.0035}];
If[!NumericQ[fcSolveTimeout],fcSolveTimeout=120];
If[!NumericQ[mmTolerance],mmTolerance=10.^-8];
If[!NumericQ[mmGaugeTolerance],mmGaugeTolerance=10.^-3];
mmCases={}; mmQ=I 2 Pi 200000. (4 Pi 10.^-7) 5.8*^7 .001^2;
mmPoints=Tuples[Range[.13,.87,.185],3];
Do[
 {mmMeshTime,mmMesh}=AbsoluteTiming[ToElementMesh[Cuboid[{0.,0.,0.},{1.,1.,1.}],"MaxCellMeasure"->mmH,"MeshOrder"->2]];
 mmNodes=Length[mmMesh["Coordinates"]];
 If[mmNodes>2000,AppendTo[mmCases,<|"execution_status"->"blocked_environment_resource_budget","nodes"->mmNodes,"failure_reason"->"manufactured_case_node_budget"|>];Break[]];
 {mmTime,mmSol}=AbsoluteTiming[TimeConstrained[NDSolveValue[{
 -Laplacian[mx[x,y,z],{x,y,z}]+mmQ (mx[x,y,z]+D[mp[x,y,z],x])==0,
 -Laplacian[my[x,y,z],{x,y,z}]+mmQ (my[x,y,z]+D[mp[x,y,z],y])==0,
 -Laplacian[mz[x,y,z],{x,y,z}]+mmQ (mz[x,y,z]+D[mp[x,y,z],z])==-4+mmQ (x^2+y^2-1),
 Laplacian[mp[x,y,z],{x,y,z}]+Div[{mx[x,y,z],my[x,y,z],mz[x,y,z]},{x,y,z}]==0,
 DirichletCondition[mx[x,y,z]==0,True],DirichletCondition[my[x,y,z]==0,True],
 DirichletCondition[mz[x,y,z]==x^2+y^2,True],DirichletCondition[mp[x,y,z]==-z,True]},
 {mx,my,mz,mp},Element[{x,y,z},mmMesh],Method->{"PDEDiscretization"->{"FiniteElement"}}],fcSolveTimeout,$Aborted]];
 If[!MatchQ[mmSol,{_InterpolatingFunction,_InterpolatingFunction,_InterpolatingFunction,_InterpolatingFunction}],
 AppendTo[mmCases,<|"execution_status"->"failed","failure_reason"->"solver_or_time_budget","nodes"->mmNodes,"failure"->ToString[mmSol,InputForm]|>];Break[]];
 mmValues=Max[Flatten[Table[Abs[(mmSol[[k]]@@pt)-{0.,0.,pt[[1]]^2+pt[[2]]^2,-pt[[3]]}[[k]]],{pt,mmPoints},{k,4}]]];
 mmGradients=Max[Flatten[Table[Abs[(Derivative@@UnitVector[3,ax])[mmSol[[k]]]@@pt-{{0.,0.,0.},{0.,0.,0.},{2 pt[[1]],2 pt[[2]],0.},{0.,0.,-1.}}[[k,ax]]],{pt,mmPoints},{k,4},{ax,3}]]];
 mmPhi=Max[Abs[(mmSol[[4]]@@#)+#[[3]]]&/@mmPoints];
 mmGauge=Max[Function[pt,Abs[Sum[(Derivative@@UnitVector[3,k])[mmSol[[k]]]@@pt,{k,3}]]]/@mmPoints];
 mmResidual=Max[Abs[Flatten[Table[With[{v=mmSol,xx=pt[[1]],yy=pt[[2]],zz=pt[[3]]},
 Join[Table[-Sum[(Derivative@@(2 UnitVector[3,ax]))[v[[k]]][xx,yy,zz],{ax,3}]+mmQ (v[[k]][xx,yy,zz]+(Derivative@@UnitVector[3,k])[v[[4]]][xx,yy,zz])-If[k==3,-4+mmQ(xx^2+yy^2-1),0.],{k,3}],
 {Sum[(Derivative@@(2 UnitVector[3,ax]))[v[[4]]][xx,yy,zz],{ax,3}]+Sum[(Derivative@@UnitVector[3,k])[v[[k]]][xx,yy,zz],{k,3}]}]],{pt,mmPoints}]]]]/Max[1.,Abs[mmQ]];
 Scan[stageCheck["MMS_"<>ToString[mmNodes]<>"_"<>#[[1]],#[[2]],#[[3]],"3D_P2_polynomial_manufactured_solution"]&,
 {{"values",mmValues,mmTolerance},{"gradients",mmGradients,mmTolerance},{"phi",mmPhi,mmTolerance},{"gauge",mmGauge,mmGaugeTolerance},{"independent_strong_PDE_residual",mmResidual,mmTolerance}}];
 AppendTo[mmCases,<|"nodes"->mmNodes,"cell_volume"->mmH,"mesh_seconds"->mmMeshTime,"solve_seconds"->mmTime,
 "field_error"->mmValues,"gradient_error"->mmGradients,"phi_error"->mmPhi,"gauge_sample_residual"->mmGauge,
 "independent_strong_PDE_residual"->mmResidual,"fields"->mmSol,"mesh"->mmMesh|>];
 stageData=<|"source_model"->"3D_P2_polynomial_manufactured_solution","cases"->mmCases|>;stageSave[];
 Print["MMS nodes=",mmNodes," values=",mmValues," gradients=",mmGradients," PDE=",mmResidual],
 {mmH,mmHValues}];
 stageCheck["MMS_three_meshes",Max[0,3-Count[mmCases,_?(KeyExistsQ[#,"field_error"]&)]],0,"manufactured_mesh_count"];
 stageCheck["MMS_three_distinct_meshes",Max[0,3-Length[DeleteDuplicates[Lookup[mmCases,"nodes"]]]],0,"manufactured_mesh_count"];
 stageData=<|"source_model"->"3D_P2_polynomial_manufactured_solution","cases"->mmCases,
 "physical_acceptance_status"->If[AnyTrue[stageChecks,#["execution_status"]==="failed"&],"failed_numerical","passed"],
 "assembled_algebraic_residual_status"->"not_measured_NDSolve_high_level_does_not_expose_matrix",
 "assumptions"->"Four coupled complex PDEs on dimensionless unit cube. P2 exact polynomial Atilde={0,0,x^2+y^2}, phi=-z; exact Dirichlet on all faces. Independently sampled physical derivatives and strong PDE residual; no claimed assembled matrix residual. Operator calibration, not conductor air interfaces, finite ends, insulation or topology performance."|>;
 Export[FileNameJoin[{stageDir,"mms_summary.json"}],KeyDrop[#, {"fields","mesh"}]&/@mmCases,"RawJSON"];
