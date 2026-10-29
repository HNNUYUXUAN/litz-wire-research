(* Calibrate the same coupled A-phi equations with axial mesh consistency. *)
Needs["NDSolve`FEM`"];
fcCases={}; fcV=LitzPhysics`WireZ[.001,200000.] 20.;fcQ=I 2 Pi 200000. (4 Pi 10.^-7) 5.8*^7 .001^2;
fcBC[x_,y_]=1-(Sqrt[I 2 Pi 200000. (4 Pi 10.^-7) 5.8*^7] BesselI[0,Sqrt[I 2 Pi 200000. (4 Pi 10.^-7) 5.8*^7] .001 Sqrt[x^2+y^2]]/(2 Pi .001 BesselI[1,Sqrt[I 2 Pi 200000. (4 Pi 10.^-7) 5.8*^7] .001]))20./(5.8*^7 fcV);
If[!ListQ[fcHValues],fcHValues={.35,.22,.14}];
If[!NumericQ[fcSolveTimeout],fcSolveTimeout=600];
If[!ListQ[fcTolerances],fcTolerances={.01,10.^-8,.001}];
Do[
 fcBoundaryN=Ceiling[2 Pi/fcH];
 fcBoundaryXY=Table[{Cos[2 Pi k/fcBoundaryN],Sin[2 Pi k/fcBoundaryN]},{k,0,fcBoundaryN-1}];
 fcBoundary=ToBoundaryMesh["Coordinates"->fcBoundaryXY,"BoundaryElements"->{LineElement[Partition[Range[fcBoundaryN],2,1,{1,1}]]}];
 fcCross=ToElementMesh[fcBoundary,"MaxCellMeasure"->fcH^2/2,"MeshOrder"->1];
 fcXY=fcCross["Coordinates"];fcTriangles=Sort/@Join@@(#[[1]]&/@fcCross["MeshElements"]);
 fcN=Length[fcXY];fcZ=Subdivide[0.,2.,4];fcCoords=Flatten[Table[Append[xy,z],{z,fcZ},{xy,fcXY}],1];
 fcTets=Flatten[Table[With[{a=tri[[1]]+layer fcN,b=tri[[2]]+layer fcN,c=tri[[3]]+layer fcN},
 {{a,b,c,c+fcN},{a,b,b+fcN,c+fcN},{a,a+fcN,b+fcN,c+fcN}}],{layer,0,3},{tri,fcTriangles}],2];
 fcMesh=ToElementMesh["Coordinates"->fcCoords,"MeshElements"->{TetrahedronElement[fcTets]}];
 fcMesh=MeshOrderAlteration[fcMesh,2];
 fcNodes=Length[fcMesh["Coordinates"]];
 Print["Extruded cylinder nodes=",fcNodes," order=",fcMesh["MeshOrder"]];
 If[!IntegerQ[fcNodes]||fcNodes>10000,stageCheck["cylinder_node_budget",1,0,"resource_preflight"];Break[]];
 fcTrace[x_,y_]=fcBC[x,y];
 If[fcBoundaryMode==="discrete_2D",
  fcCrossP2=MeshOrderAlteration[fcCross,2];
  fcDiscrete=TimeConstrained[NDSolveValue[{-Laplacian[az[x,y],{x,y}]+fcQ(az[x,y]-1)==0,
    DirichletCondition[az[x,y]==fcBC[x,y],True]},az,Element[{x,y},fcCrossP2],
    Method->{"PDEDiscretization"->{"FiniteElement"}}],fcSolveTimeout,$Aborted];
  If[!MatchQ[fcDiscrete,_InterpolatingFunction],stageCheck["discrete_trace_solve",1,0,"2D_control"];Break[]];
  fcTrace[x_,y_]:=fcDiscrete[x,y]];
 {fcTime,fcSol}=AbsoluteTiming[TimeConstrained[NDSolveValue[{
 -Laplacian[cx[x,y,z],{x,y,z}]+fcQ(cx[x,y,z]+D[cp[x,y,z],x])==0,
 -Laplacian[cy[x,y,z],{x,y,z}]+fcQ(cy[x,y,z]+D[cp[x,y,z],y])==0,
 -Laplacian[cz[x,y,z],{x,y,z}]+fcQ(cz[x,y,z]+D[cp[x,y,z],z])==0,
 Laplacian[cp[x,y,z],{x,y,z}]+Div[{cx[x,y,z],cy[x,y,z],cz[x,y,z]},{x,y,z}]==0,
 DirichletCondition[cx[x,y,z]==0,True],DirichletCondition[cy[x,y,z]==0,True],
 DirichletCondition[cz[x,y,z]==fcTrace[x,y],True],DirichletCondition[cp[x,y,z]==-z,True]},
 {cx,cy,cz,cp},Element[{x,y,z},fcMesh],Method->{"PDEDiscretization"->{"FiniteElement"}}],fcSolveTimeout,$Aborted]];
 If[!MatchQ[fcSol,{_InterpolatingFunction,_InterpolatingFunction,_InterpolatingFunction,_InterpolatingFunction}],
 stageCheck["cylinder_solver_completed",1,0,"execution_failure"];
 AppendTo[fcCases,<|"nodes"->fcNodes,"execution_status"->"failed","failure"->ToString[fcSol,InputForm]|>];Break[]];
 fcProfile=Table[{r,-5.8*^7 fcV(fcSol[[3]][r,0.,1.]+Derivative[0,0,1][fcSol[[4]]][r,0.,1.]),LitzPhysics`WireJ[.001 r,.001,200000.,20.]},{r,0.,.95,.95/80}];
 fcErr=Norm[fcProfile[[All,2]]-fcProfile[[All,3]]]/Norm[fcProfile[[All,3]]];
 fcPts=Tuples[{Range[-.5,.5,.25],Range[-.5,.5,.25],{.3,1.,1.7}}];
 fcPhi=Max[Function[pt,Abs[(fcSol[[4]]@@pt)+pt[[3]]]]/@fcPts];
 fcGauge=Max[Function[pt,Abs[Sum[(Derivative@@UnitVector[3,k])[fcSol[[k]]]@@pt,{k,3}]]]/@fcPts];
 Scan[stageCheck["cylinder_"<>ToString[fcNodes]<>"_"<>#[[1]],#[[2]],#[[3]],"3D_extruded_polygonal_A_phi_calibration"]&,
 {{"actual_J_Bessel",fcErr,fcTolerances[[1]]},{"phi",fcPhi,fcTolerances[[2]]},{"gauge",fcGauge,fcTolerances[[3]]}}];
 AppendTo[fcCases,<|"nodes"->fcNodes,"cross_section_target_h"->fcH,"mesh_order"->fcMesh["MeshOrder"],"solve_seconds"->fcTime,
 "radial_relative_error"->fcErr,"phi_error"->fcPhi,"gauge_sample_residual"->fcGauge,"profile"->fcProfile,"fields"->fcSol,"mesh"->fcMesh|>];
 If[fcBoundaryMode==="discrete_2D",Export[FileNameJoin[{stageDir,"discrete_cross_"<>ToString[fcNodes]<>".wxf"}],<|"mesh"->fcCrossP2,"field"->fcDiscrete|>,"WXF"]];
 stageData=<|"source_model"->"3D_extruded_polygonal_A_phi_calibration","cases"->fcCases|>;stageSave[],{fcH,fcHValues}];
 stageCheck["cylinder_requested_meshes",Max[0,Length[fcHValues]-Length[fcCases]],0,"3D_calibration_mesh_count"];
 stageData=<|"source_model"->"3D_extruded_polygonal_A_phi_calibration","cases"->fcCases,
 "physical_acceptance_status"->If[AnyTrue[stageChecks,#["execution_status"]==="failed"&],"failed_numerical","passed"],
 "failure_reason"->If[AnyTrue[stageChecks,#["execution_status"]==="failed"&],"calibration_error_threshold",Null],
 "assumptions"->"Axially consistent tetrahedral extrusion of a linear polygonal disk, upgraded to P2 without projecting polygon sides. Same original four complex PDEs and full analytical Dirichlet A/phi. Actual computed phi gradient included in J. Geometry error and phi/gauge thresholds retained. Axial length 2mm operator calibration; no finite-end, return, air interface, insulated topology or full 1m claim."|>;
 Export[FileNameJoin[{stageDir,"cylinder_summary.json"}],KeyDrop[#, {"fields","mesh","profile"}]&/@fcCases,"RawJSON"];
