ggSample[kind_String,n_Integer,len_,pitch_,d_,count_Integer]:=Module[{base,fun,rot,groups,zs,paths,lens,gap,curv,pts,near},
 base=LitzPhysics`StrandCenters[n,d];
 groups=Take[SortBy[Flatten[Table[{i+j/2.,Sqrt[3.] j/2.},{i,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]},{j,-Ceiling[Sqrt[n]],Ceiling[Sqrt[n]]}],1],Norm],Ceiling[n/8]];
 rot[t_]:={{Cos[t],-Sin[t]},{Sin[t],Cos[t]}};
 fun[id_,z_]:=Switch[kind,"straight",base[[id]],"single",rot[2 Pi z/pitch].base[[id]],"multilevel",rot[2 Pi z/pitch].(If[n==7,base[[id]],With[{g=Quotient[id-1,8],k=Mod[id-1,8]},4.5 d groups[[g+1]]+1.4 d rot[2 Pi z/(pitch/4)].{Cos[2 Pi k/8],Sin[2 Pi k/8]}]]),"crosslayer",rot[2 Pi z/pitch].(base[[id]]+.04 d Sin[4 Pi z/pitch+2 Pi id/n] Normalize[base[[id]]+{.00001,.00002}])];
 zs=Subdivide[0.,len,count];paths=Table[Append[fun[id,#],#]&/@zs,{id,n}];lens=Total[Norm/@Differences[#]]&/@paths;
 gap=Min[Table[pts=Table[fun[i,z],{i,n}];near=Nearest[pts,pts,2];Min[MapThread[Norm[#1-#2[[2]]]&,{pts,near}]]-d,{z,Subdivide[0.,len,count/5]}]];
 curv=Min[Flatten[Map[Function[path,With[{v=Differences[path],acc=Differences[Differences[path]]},Table[If[Norm[Cross[v[[k]],acc[[k]]]]>10.^-30,Norm[v[[k]]]^3/Norm[Cross[v[[k]],acc[[k]]]],10.^30],{k,Length[acc]}]]],paths]]];
 <|"source_model"->"sampled_geometric_trajectories","kind"->kind,"strand_ids"->Range[n],"axial_sample_segments"->count,"gap_sample_segments"->count/5,"nominal_copper_area_m2"->n Pi (d/2)^2,"axial_length_m"->len,"pitch_m"->pitch,"diameter_m"->d,"paths"->paths,"arc_lengths_m"->lens,"arc_growth_ratio"->lens/len,"Rdc_ohm"->1/Total[5.8*^7 Pi (d/2)^2/lens],"copper_volume_m3"->Total[Pi (d/2)^2 lens],"minimum_surface_gap_m"->gap,"minimum_curvature_radius_m"->curv,"periodic_position_error_m"->Max[Norm[Most[Last[#]]-Most[First[#]]]&/@paths]|>
];
ggCases={};ggComparisons={};
Do[
 ggSet=Table[ggSample[kind,If[kind=="multilevel",24,7],.02,.01,.0001,c],{c,{400,800,1600}}];
 ggBase=LitzPhysics`Topology[kind,If[kind=="multilevel",24,7],.02,.01,.0001];
 stageCheck["default_geometry_compatibility_"<>kind,Norm[Flatten[ggSet[[1]]["paths"]-ggBase["paths"]]],10.^-12,"sampled_geometry"];
 Do[
  ggA=ggSet[[i-1]];ggB=ggSet[[i]];
  ggDelta=<|"kind"->kind,"coarse_segments"->ggA["axial_sample_segments"],"fine_segments"->ggB["axial_sample_segments"],"maximum_arc_length_relative_change"->Max[Abs[ggB["arc_lengths_m"]/ggA["arc_lengths_m"]-1]],"Rdc_relative_change"->Abs[ggB["Rdc_ohm"]/ggA["Rdc_ohm"]-1],"copper_volume_relative_change"->Abs[ggB["copper_volume_m3"]/ggA["copper_volume_m3"]-1],"gap_absolute_change_m"->Abs[ggB["minimum_surface_gap_m"]-ggA["minimum_surface_gap_m"]],"curvature_radius_relative_change"->Abs[ggB["minimum_curvature_radius_m"]/ggA["minimum_curvature_radius_m"]-1]|>;
  AppendTo[ggComparisons,ggDelta];stageCheck["arc_sampling_"<>kind<>"_"<>ToString[i],ggDelta["maximum_arc_length_relative_change"],.01,"sampled_geometry"];
  stageCheck["curvature_sampling_"<>kind<>"_"<>ToString[i],ggDelta["curvature_radius_relative_change"],.01,"sampled_geometry"],{i,2,3}];
 Do[stageCheck["gap_"<>kind<>"_"<>ToString[g["axial_sample_segments"]],Max[0.,-g["minimum_surface_gap_m"]],10.^-12,"sampled_geometry"];
  stageCheck["period_"<>kind<>"_"<>ToString[g["axial_sample_segments"]],g["periodic_position_error_m"],10.^-10,"sampled_geometry"],{g,ggSet}];
 ggLast=Last[ggSet];ggRows=Flatten[Table[MapIndexed[Join[{id,First[#2]},#1]&,ggLast["paths"][[id]]],{id,Length[ggLast["strand_ids"]]}],1];
 Export[FileNameJoin[{stageDir,"geometry_"<>kind<>".csv"}],Prepend[ggRows,{"strand_id","sample_id","x_m","y_m","z_m"}],"CSV"];
 ggCases=Join[ggCases,ggSet],{kind,{"straight","single","multilevel","crosslayer"}}];
ggK=7;ggZ=DiagonalMatrix[N[Range[ggK]] .001]+I .0001 Table[1./(1+Abs[i-j]),{i,ggK},{j,ggK}];
ggP=Table[IdentityMatrix[ggK][[RotateLeft[Range[ggK],k]]],{k,0,ggK-1}];
ggFunc[z_?NumericQ]:=ggZ;ggPerm[z_?NumericQ]:=ggP[[Min[Floor[z ggK]+1,ggK]]];
ggDTM={};
Do[ggBlocks=ConstantArray[ggZ,ggK mult];ggPerms=Flatten[Table[ConstantArray[p,mult],{p,ggP}],1];ggWeights=ConstantArray[1./(ggK mult),ggK mult];
 ggTotal=LitzPhysics`DTM[ggBlocks,ggPerms,ggWeights];
 ggIDTM=LitzPhysics`IDTM[{N[Range[0,ggK mult]/(ggK mult)],{0.,.17,.41,1.}},ggFunc,ggPerm];
 ggSol=LitzPhysics`CommonPort[ggTotal,ConstantArray[0.,ggK],20.];
 stageCheck["DTM_iDTM_"<>ToString[ggK mult],Norm[ggTotal-ggIDTM]/Norm[ggTotal],10.^-8,"synthetic_additive_DTM"];
 stageCheck["DTM_current_"<>ToString[ggK mult],ggSol["current_residual"],10.^-8,"synthetic_additive_DTM"];
 stageCheck["DTM_voltage_"<>ToString[ggK mult],ggSol["common_voltage_residual"],10.^-8,"synthetic_additive_DTM"];
 stageCheck["DTM_power_"<>ToString[ggK mult],ggSol["power_residual"],.001,"synthetic_additive_DTM"];
 AppendTo[ggDTM,<|"segments"->ggK mult,"weights_m"->ggWeights,"physical_to_slot_permutations"->ggPerms,"Z_ohm"->ggTotal,"iDTM_Z_ohm"->ggIDTM,"solution"->ggSol|>],{mult,{1,2,4}}];
Do[stageCheck["DTM_K_2K_4K_Z_"<>ToString[i],Norm[ggDTM[[i]]["Z_ohm"]-ggDTM[[i-1]]["Z_ohm"]]/Norm[ggDTM[[i]]["Z_ohm"]],.01,"synthetic_additive_DTM"];stageCheck["DTM_K_2K_4K_currents_"<>ToString[i],Norm[ggDTM[[i]]["solution"]["currents"]-ggDTM[[i-1]]["solution"]["currents"]]/20.,.01,"synthetic_additive_DTM"],{i,2,3}];
Export[FileNameJoin[{stageDir,"geometry_data.json"}],<|"run_id"->stageID,"source_model"->"sampled_geometry_sensitivity","units"->"SI","geometries"->(KeyDrop[#,"paths"]&/@ggCases),"comparisons"->ggComparisons,"trajectory_files"->("geometry_"<>#<>".csv"&/@{"straight","single","multilevel","crosslayer"})|>,"RawJSON"];
Export[FileNameJoin[{stageDir,"DTM_data.json"}],<|"run_id"->stageID,"source_model"->"synthetic_additive_permutation_model","scope"->"partition invariance of the existing piecewise-constant explanatory model; no real end-region or nonlocal field ranking","cases"->Map[Function[c,Join[KeyDrop[c,{"Z_ohm","iDTM_Z_ohm","solution"}],<|"Z_real_ohm"->Re[c["Z_ohm"]],"Z_imag_ohm"->Im[c["Z_ohm"]],"currents_Re_Im_RMS_A"->({Re[#],Im[#]}&/@c["solution"]["currents"]),"voltage_Re_Im_RMS_V"->{Re[c["solution"]["voltage"]],Im[c["solution"]["voltage"]]},"loss_W"->c["solution"]["loss_W"]|>]],ggDTM]|>,"RawJSON"];
stageData=<|"source_model"->"sampled_geometry_and_existing_additive_DTM_sensitivity","geometries"->ggCases,"sampling_comparisons"->ggComparisons,"DTM_cases"->ggDTM,"physical_acceptance_status"->If[AnyTrue[stageChecks,#["execution_status"]==="failed"&],"failed_sampling_checks","passed_sampled_geometry_and_synthetic_partition_scope"],"assumptions"->"Same labelled geometric formula as archived manuscript geometry: straight/single/crosslayer 7 strands, traditional multilevel 24 strands, length .02m, pitch .01m, diameter .1mm. Samples 400/800/1600 and gap samples80/160/320. Sampled gap/curvature do not establish continuous manufacturability. K7/14/28 split the existing synthetic piecewise-constant DTM and preserve physical strand IDs; this is partition invariance, not a solved true transposition structure or ranking."|>;
stageSave[];
