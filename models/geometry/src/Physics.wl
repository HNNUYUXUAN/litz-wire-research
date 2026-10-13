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
StrandCenters[n_Integer,d_?NumericQ] := If[n==1,{{0.,0.}},If[n==7,Join[{{0.,0.}},Table[1.2 d {Cos[t],Sin[t]},{t,0,5 Pi/3,Pi/3}]],Take[SortBy[Flatten[Table[1.15 d {i+j/2.,Sqrt[3.] j/2.},{i,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]},{j,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]}],1],Norm],n]]];
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
