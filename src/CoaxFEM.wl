BeginPackage["LitzCoax`"];
SolveCoax::usage="SolveCoax[n,diameter,meshFactor,returnFactor,outerFactor] linear triangular Az/common voltage FEM, concentric copper return shell.";
Begin["`Private`"];
SolveCoax[n_Integer,d_?NumericQ,mf_?NumericQ,rf_:2.,of_:1.5,minSegments_Integer:24] := Module[
 {sc=.001,centers,rad,br,ri,ro,out,coords={},edges={},marks={},addCircle,nseg,bmesh,mesh,regions,xy,tri,mark,nt,nn,area,gx,gy,e,bx,by,k,m,c,ac,ids,bound,free,sys,rhs,s,u,v,j,strandI,loss,returnLoss,pin,tt,port,blocks,mm,cm,am,pp,budget,estimate},
 Needs["NDSolve`FEM`"];
 centers=LitzPhysics`StrandCenters[n,d]/sc;
 rad=d/(2 sc);br=Max[Norm/@centers]+rad;ri=rf br;ro=ri+Max[4 rad,.3];out=of ro;
 nseg=Max[minSegments,Ceiling[2 Pi/mf]];
 addCircle[center_,r_,marker_,segments_] := Module[{start=Length[coords],p},p=Table[center+r {Cos[t],Sin[t]},{t,0.,2 Pi-2 Pi/segments,2 Pi/segments}];coords=Join[coords,p];edges=Join[edges,Table[start+{i,Mod[i,segments]+1},{i,segments}]];marks=Join[marks,ConstantArray[marker,segments]]];
 Do[addCircle[centers[[i]],rad,i,nseg],{i,n}];
 addCircle[{0.,0.},ri,n+1,Max[96,Ceiling[2 Pi ri/(mf rad)]]];addCircle[{0.,0.},ro,n+2,Max[96,Ceiling[2 Pi ro/(mf rad)]]];addCircle[{0.,0.},out,n+3,96];
 bmesh=NDSolve`FEM`ToBoundaryMesh["Coordinates"->coords,"BoundaryElements"->{NDSolve`FEM`LineElement[edges,marks]}];
 regions=Join[Table[{centers[[i]],i,(mf rad)^2/2},{i,n}],{{{(ri+ro)/2,0.},n+1,(mf rad)^2/2},{{br+(.15 (ri-br)),0.},0,Max[(mf rad)^2/2,.01]},{{(ro+out)/2,0.},0,.2}}];
 {tt,mesh}=AbsoluteTiming[NDSolve`FEM`ToElementMesh[bmesh,"RegionHoles"->None,"RegionMarker"->regions,"MeshOrder"->1]];
 If[Head[mesh]=!=NDSolve`FEM`ElementMesh,Return[Failure["CoaxMesh",<|"n"->n|>]]];
 xy=mesh["Coordinates"];tri=Join@@(#[[1]]&/@mesh["MeshElements"]);mark=Join@@(#[[2]]&/@mesh["MeshElements"]);nt=Length[tri];nn=Length[xy];
 budget=Quiet[Check[ToExpression[Environment["LITZ_RAM_BUDGET"]],10.^9]];estimate=400. nn+300. nt;
 If[NumberQ[budget]&&estimate>Max[budget,10.^8],Return[Failure["ResourceBudget",<|"nodes"->nn,"triangles"->nt,"estimated_assembly_bytes"->estimate,"available_budget_bytes"->budget|>]]];
 blocks=Table[With[{p=xy[[id]]},With[{det=Det[{p[[2]]-p[[1]],p[[3]]-p[[1]]}]},
 {Abs[det]/2,{p[[2,2]]-p[[3,2]],p[[3,2]]-p[[1,2]],p[[1,2]]-p[[2,2]]}/det,{p[[3,1]]-p[[2,1]],p[[1,1]]-p[[3,1]],p[[2,1]]-p[[1,1]]}/det}]],{id,tri}];
 area=blocks[[All,1]];gx=blocks[[All,2]];gy=blocks[[All,3]];
 ids=Flatten[Table[Thread[{ConstantArray[t,3],tri[[t]]}],{t,nt}],1];
 e=SparseArray[Thread[ids->1.],{nt,nn}];bx=SparseArray[Thread[ids->Flatten[gx]],{nt,nn}];by=SparseArray[Thread[ids->Flatten[gy]],{nt,nn}];
 k=Transpose[bx].SparseArray[Band[{1,1}]->area,{nt,nt}].bx+Transpose[by].SparseArray[Band[{1,1}]->area,{nt,nt}].by;
 (* Explicit mapped markers, air is zero. *)
 ac=MapThread[If[1<=#2<=n+1,#1,0.]&,{area,mark}];
 m=(Transpose[e].SparseArray[Band[{1,1}]->(ac/12),{nt,nt}].e+SparseArray[Band[{1,1}]->(Transpose[e].ac/12),{nn,nn}]);
 c=SparseArray[Transpose[{Transpose[e].MapThread[If[1<=#2<=n,#1/3,0.]&,{area,mark}],Transpose[e].MapThread[If[#2==n+1,#1/3,0.]&,{area,mark}]}]];
 am=Normal[Total/@Transpose[c]];
 bound=Pick[Range[nn],(Norm[#]>=out (1-10.^-8)&/@xy)];free=Complement[Range[nn],bound];
 sys=Join[Join[k[[free,free]]/(I 2 Pi 200000. 4 Pi 10.^-7 5.8*^7 sc^2)+m[[free,free]],-c[[free]],2],Join[-Transpose[c[[free]]],SparseArray[Band[{1,1}]->am,{2,2}],2]];
 rhs=Join[ConstantArray[0.,Length[free]],{20.,-20.}/(5.8*^7 sc^2)];
 Print["COAX n=",n," nodes=",nn," triangles=",nt," system bytes=",ByteCount[sys]];
 {port,s}=AbsoluteTiming[LinearSolve[sys,rhs]];u=ConstantArray[0.+0. I,nn];u[[free]]=Most[Most[s]];v=Take[s,-2];
 loss=0.;returnLoss=0.;strandI=ConstantArray[0.+0. I,n];
 Do[If[1<=mark[[t]]<=n+1,pp=If[mark[[t]]<=n,1,2];j=v[[pp]]-u[[tri[[t]]]];
 mm=area[[t]]/12 {{2.,1.,1.},{1.,2.,1.},{1.,1.,2.}};
 If[pp==1,strandI[[mark[[t]]]]+=5.8*^7 sc^2 area[[t]] Mean[j];loss+=5.8*^7 sc^2 Re[Conjugate[j].mm.j],returnLoss+=5.8*^7 sc^2 Re[Conjugate[j].mm.j]]],{t,nt}];
 pin=Re[20. (v[[1]]-v[[2]])];
 <|"source_model"->"2D_linear_triangle_Az_common_voltage_coax_FEM","strands"->n,"diameter_m"->d,"mesh_factor"->mf,"circle_segments"->nseg,"return_factor"->rf,"outer_factor"->of,
 "nodes"->nn,"triangles"->nt,"system_nonzeros"->Length[sys["NonzeroValues"]],"matrix_bytes"->ByteCount[sys],"mesh_seconds"->tt,"solve_seconds"->port,
 "source_voltage_V_per_m"->v[[1]],"return_voltage_V_per_m"->v[[2]],"strand_currents_RMS_A"->strandI,
 "bundle_loss_W_per_m"->loss,"return_loss_W_per_m"->returnLoss,"input_W_per_m"->pin,"bundle_Rac_ohm_per_m"->loss/400.,
 "matrix_head"->ToString[Head[sys]],"linear_residual"->Norm[sys.s-rhs]/Norm[rhs],"current_residual"->Abs[Total[strandI]-20.]/20.,"power_residual"->Abs[pin-loss-returnLoss]/Max[pin,$MinMachineNumber],
 "polygonal_bundle_area_m2"->sc^2 am[[1]],"return_inner_radius_m"->sc ri,"return_outer_radius_m"->sc ro,"outer_radius_m"->sc out,
 "mesh"->mesh,"u_nodes_V_per_m"->u,"element_markers"->mark,"triangles_node_ids"->tri|>
];
End[];EndPackage[];

