(* Read-only diagnostics of preserved A-phi fields. No PDE or mesh solve. *)
Needs["NDSolve`FEM`"];
cdSourceID="rerun_20261005_fem3_cylinder_report";
cdMMSSourceID="3d_20261005_fem3_mms_distinct";
cdRead[id_,name_]:=Import[FileNameJoin[{stageRoot,"outputs",id,name}],"RawJSON"];
cdWxf[id_]:=Import[FileNameJoin[{stageRoot,"outputs",id,"results.wxf"}],"WXF"];
cdSourcePath=FileNameJoin[{stageRoot,"outputs",cdSourceID,"results.wxf"}];
cdMMSPath=FileNameJoin[{stageRoot,"outputs",cdMMSSourceID,"results.wxf"}];
If[!And@@(FileExistsQ/@{cdSourcePath,cdMMSPath}),Print["Explicit diagnostic source missing; no solve fallback"];$Failed,
 cdSource=cdWxf[cdSourceID];cdMMS=cdWxf[cdMMSSourceID];
 cdParameter=cdRead[cdSourceID,"parameters.json"];
 cdSigma=Lookup[cdParameter,"conductivity_S_per_m",5.8*^7];cdFrequency=Lookup[cdParameter,"frequency_Hz",200000.];
 cdCurrent=Lookup[cdParameter,"current_RMS_A",20.];cdA=.001;cdOmega=2 Pi cdFrequency;
 cdV=cdCurrent LitzPhysics`WireZ[cdA,cdFrequency];
 cdQ=I cdOmega (4 Pi 10.^-7) cdSigma cdA^2;
 cdRI[v_List]:=Flatten[({Re[#],Im[#]}&/@v)];
 cdRI[v_?NumericQ]:={Re[v],Im[v]};
 cdGrad[f_,pt_]:=Table[(Derivative@@UnitVector[3,k])[f]@@pt,{k,3}];
 cdGauge[fs_,pt_]:=Sum[(Derivative@@UnitVector[3,k])[fs[[k]]]@@pt,{k,3}];
 cdJ[fs_,pt_]:=-cdSigma cdV (((#@@pt)&/@Take[fs,3])+cdGrad[fs[[4]],pt]);
 cdEval[fs_,pt_]:=Module[{u,psi,gp,gauge},u=(#@@pt)&/@Take[fs,3];psi=fs[[4]]@@pt;gp=cdGrad[fs[[4]],pt];gauge=cdGauge[fs,pt];
  Join[pt,cdRI[u],cdRI[psi],cdRI[gp],cdRI[gauge],cdRI[cdV/(I cdOmega) u],cdRI[cdA cdV psi],cdRI[-cdSigma cdV(u+gp)],cdRI[cdV gp]]];
 cdH[p_,n_]:=Flatten[Table[{p<>ToString[k]<>"_real",p<>ToString[k]<>"_imag"},{k,n}]];
 cdHeaders=Join[{"node_id_1based","x_dimensionless","y_dimensionless","z_dimensionless"},cdH["u_component_",3],{"psi_real","psi_imag"},cdH["grad_psi_component_",3],{"div_u_real","div_u_imag"},cdH["A_T_m_component_",3],{"phi_V_real","phi_V_imag"},cdH["J_A_per_m2_RMS_component_",3],cdH["grad_phi_V_per_m_component_",3]];
 cdCases={};cdGateChecks={};cdFiniteDifferencePoints={{.137,.219,.417},{-.173,.253,.813},{.227,-.191,1.327},{-.293,-.157,1.731}};
 Do[
  cdFields=cdCase["fields"];cdMesh=cdCase["mesh"];
  cdCoordinates=cdMesh["Coordinates"];cdElements=cdMesh["MeshElements"];
  cdNodes=Length[cdCoordinates];Print["Cached 3D diagnostics nodes=",cdNodes];
  cdElementData=Map[<|"element_type"->ToString[Head[#]],"connectivity_node_ids"->#[[1]],"original_markers"->If[Length[#]>=2,#[[2]],"not_present"]|>&,cdElements];
  cdBoundaries=Quiet[Check[cdMesh["BoundaryElements"],$Failed]];
  cdBoundaryIDs=If[ListQ[cdBoundaries],DeleteDuplicates[Flatten[(#[[1]]&/@cdBoundaries)]],{}];
  cdSampleIDs=DeleteDuplicates[Round[Subdivide[1,cdNodes-1,Min[127,cdNodes-1]]]];
  cdSamples=Quiet[Table[Prepend[cdEval[cdFields,cdCoordinates[[id]]],id],{id,cdSampleIDs}]];
  cdAllNodeValues=Quiet[MapIndexed[Function[{pt,idx},Join[{First[idx]},pt,cdRI[(#@@pt)&/@cdFields]]],cdCoordinates]];
  cdFieldExportOK=MatrixQ[cdSamples,NumericQ];
  stageCheck["diagnostic_numeric_node_export_"<>ToString[cdNodes],If[cdFieldExportOK,0,1],0,"preserved_field_values_and_derivatives_no_solve"];
  If[cdFieldExportOK,Export[FileNameJoin[{stageDir,"field_nodes_"<>ToString[cdNodes]<>".csv"}],Prepend[cdSamples,cdHeaders],"CSV"]];
  Export[FileNameJoin[{stageDir,"all_node_u_psi_"<>ToString[cdNodes]<>".csv"}],Prepend[cdAllNodeValues,Join[{"node_id_1based","x_dimensionless","y_dimensionless","z_dimensionless"},cdH["u_component_",3],{"psi_real","psi_imag"}]],"CSV"];
  Export[FileNameJoin[{stageDir,"mesh_nodes_"<>ToString[cdNodes]<>".csv"}],Prepend[MapIndexed[Join[{First[#2]},#1,cdA #1]&,cdCoordinates],{"node_id_1based","x_dimensionless","y_dimensionless","z_dimensionless","x_m","y_m","z_m"}],"CSV"];
  Do[Export[FileNameJoin[{stageDir,"connectivity_"<>ToString[cdNodes]<>"_"<>ToString[k]<>".csv"}],cdElementData[[k]]["connectivity_node_ids"],"CSV"],{k,Length[cdElementData]}];
  cdProfile=Table[{r,cdJ[cdFields,{r,0.,1.}][[3]],LitzPhysics`WireJ[cdA r,cdA,cdFrequency,cdCurrent]},{r,0.,.95,.95/80}];
  cdJError=Norm[cdProfile[[All,2]]-cdProfile[[All,3]]]/Norm[cdProfile[[All,3]]];
  cdOriginalPoints=Tuples[{Range[-.5,.5,.25],Range[-.5,.5,.25],{.3,1.,1.7}}];
  cdPhiError=Max[(Abs[(cdFields[[4]]@@#)+#[[3]]]&/@cdOriginalPoints)];
  cdGaugeError=Max[(Abs[cdGauge[cdFields,#]]&/@cdOriginalPoints)];
  cdGradientError=Max[(Norm[cdGrad[cdFields[[4]],#]-{0.,0.,-1.}]&/@cdOriginalPoints)];
  cdBoundarySampleIDs=If[Length[cdBoundaryIDs]>0,cdBoundaryIDs[[DeleteDuplicates[Round[Subdivide[1,Length[cdBoundaryIDs],Min[255,Length[cdBoundaryIDs]-1]]]]]],{}];
  cdBoundaryPhi=If[Length[cdBoundarySampleIDs]>0,Max[Abs[(cdFields[[4]]@@cdCoordinates[[#]])+cdCoordinates[[#,3]]]&/@cdBoundarySampleIDs],Missing["BoundaryElementsUnavailable"]];
  cdExpectedU[pt_]:={0.,0.,1.-LitzPhysics`WireJ[cdA Norm[Take[pt,2]],cdA,cdFrequency,cdCurrent]/(cdSigma cdV)};
  cdBoundaryU=If[Length[cdBoundarySampleIDs]>0,Max[Function[id,Norm[((#@@cdCoordinates[[id]])&/@Take[cdFields,3])-cdExpectedU[cdCoordinates[[id]]]]]/@cdBoundarySampleIDs],Missing["BoundaryElementsUnavailable"]];
  cdFDh=10.^-5;
  cdFD=Table[With[{direct=cdGrad[cdFields[[k]],pt],finite=Table[((cdFields[[k]]@@(pt+cdFDh UnitVector[3,ax]))-(cdFields[[k]]@@(pt-cdFDh UnitVector[3,ax])))/(2 cdFDh),{ax,3}]},Join[pt,{k},cdRI[direct],cdRI[finite],{Norm[direct-finite]}]],{pt,cdFiniteDifferencePoints},{k,4}];
  Export[FileNameJoin[{stageDir,"derivative_crosscheck_"<>ToString[cdNodes]<>".csv"}],Prepend[Flatten[cdFD,1],Join[{"x_dimensionless","y_dimensionless","z_dimensionless","field_component"},cdH["interpolant_gradient_",3],cdH["central_difference_gradient_",3],{"absolute_difference_norm"}]],"CSV"];
  cdBoundaryFacets=If[ListQ[cdBoundaries],Join@@(#[[1]]&/@cdBoundaries),{}];
  cdSideFacetSample=If[Length[cdBoundaryFacets]>0,cdBoundaryFacets[[DeleteDuplicates[Round[Subdivide[1,Length[cdBoundaryFacets],Min[127,Length[cdBoundaryFacets]-1]]]]]],{}];
  cdSideFlux=Table[With[{vertices=cdCoordinates[[Take[ids,3]]]},
    If[Max[vertices[[All,3]]]-Min[vertices[[All,3]]]>10.^-10,
     With[{pt=Mean[vertices],normal=Normalize[Cross[vertices[[2]]-vertices[[1]],vertices[[3]]-vertices[[1]]]]},Join[pt,{Abs[cdJ[cdFields,pt].normal]}]],Nothing]],{ids,cdSideFacetSample}];
  cdSideMax=If[Length[cdSideFlux]>0,Max[cdSideFlux[[All,4]]],Missing["SideFacetsUnavailable"]];
  Scan[Function[pair,stageCheck["reproduce_"<>pair[[1]]<>"_"<>ToString[cdNodes],Abs[pair[[2]]-Lookup[cdCase,pair[[3]],Infinity]],10.^-10,"actual_preserved_A_phi_field_reproduction"]],{{"actual_J",cdJError,"radial_relative_error"},{"phi",cdPhiError,"phi_error"},{"gauge",cdGaugeError,"gauge_sample_residual"}}];
  cdGates=Map[<|"id"->#[[1]],"actual"->#[[2]],"tolerance"->#[[3]],"execution_status"->If[#[[2]]<=#[[3]],"passed","failed"],"source_model"->"actual_preserved_A_phi_cylinder_fields"|>&,{{"J_Bessel",cdJError,.01},{"phi",cdPhiError,10.^-8},{"gauge",cdGaugeError,.001}}];
  AppendTo[cdGateChecks,<|"nodes"->cdNodes,"checks"->cdGates|>];
  AppendTo[cdCases,<|"nodes"->cdNodes,"source_run_id"->cdSourceID,"coordinates_dimensionless"->cdCoordinates,"coordinate_scale_m"->cdA,"elements"->cdElementData,"material"->"original homogeneous copper-only cylinder calibration; no invented material marker","boundary_node_ids"->cdBoundaryIDs,"all_node_u_psi_values"->cdAllNodeValues,"derivative_node_sample_ids"->cdSampleIDs,"derivative_node_sample_policy"->"at most 128 equally indexed mesh nodes, explicit IDs retained; not an all-node derivative maximum","boundary_sample_node_ids"->cdBoundarySampleIDs,"side_facet_sample_policy"->"at most 128 equally indexed original boundary facets; sampled sidewall values only","nodal_field_sample_columns"->cdHeaders,"nodal_field_samples"->If[cdFieldExportOK,cdSamples,"not_exportable_numeric_sampling_failed"],"profile"->cdProfile,"actual_J_Bessel_relative_error"->cdJError,"phi_error_dimensionless"->cdPhiError,"gauge_max_abs_dimensionless"->cdGaugeError,"phi_gradient_error_max_norm_dimensionless"->cdGradientError,"boundary_phi_error_dimensionless"->If[NumberQ[cdBoundaryPhi],cdBoundaryPhi,"not_measured_boundary_elements_unavailable"],"boundary_u_error_max_norm_dimensionless"->If[NumberQ[cdBoundaryU],cdBoundaryU,"not_measured_boundary_elements_unavailable"],"derivative_central_difference_h_dimensionless"->cdFDh,"derivative_crosscheck_max_absolute_norm"->Max[Flatten[cdFD,1][[All,-1]]],"sampled_sidewall_normal_J_max_A_per_m2_RMS"->If[NumberQ[cdSideMax],cdSideMax,"not_measured_side_facets_unavailable"],"historical_gates"->cdGates|>];
  stageData=<|"source_model"->"read_only_preserved_3D_A_phi_diagnostics","cases"->cdCases,"historical_gates"->cdGateChecks,"physical_acceptance_status"->"failed_numerical"|>;stageSave[],
  {cdCase,cdSource["data"]["cases"]}];
 cdMMSPoints=Tuples[Range[.13,.87,.185],3];cdMMSChecks={};
 Do[
  cdMFields=cdMCase["fields"];cdMNodes=cdMCase["nodes"];
  cdMValues=Max[Flatten[Table[Abs[(cdMFields[[k]]@@pt)-{0.,0.,pt[[1]]^2+pt[[2]]^2,-pt[[3]]}[[k]]],{pt,cdMMSPoints},{k,4}]]];
  cdMGrad=Max[Flatten[Table[Abs[(Derivative@@UnitVector[3,ax])[cdMFields[[k]]]@@pt-{{0.,0.,0.},{0.,0.,0.},{2 pt[[1]],2 pt[[2]],0.},{0.,0.,-1.}}[[k,ax]]],{pt,cdMMSPoints},{k,4},{ax,3}]]];
  cdMGauge=Max[Abs[cdGauge[cdMFields,#]]&/@cdMMSPoints];
  cdMResidual=Max[Abs[Flatten[Table[Join[Table[-Sum[(Derivative@@(2 UnitVector[3,ax]))[cdMFields[[k]]]@@pt,{ax,3}]+cdQ ((cdMFields[[k]]@@pt)+(Derivative@@UnitVector[3,k])[cdMFields[[4]]]@@pt)-If[k==3,-4+cdQ(pt[[1]]^2+pt[[2]]^2-1),0.],{k,3}],{Sum[(Derivative@@(2 UnitVector[3,ax]))[cdMFields[[4]]]@@pt,{ax,3}]+cdGauge[cdMFields,pt]}],{pt,cdMMSPoints}]]]]/Max[1.,Abs[cdQ]];
  Scan[stageCheck["cached_MMS_"<>ToString[cdMNodes]<>"_"<>#[[1]],#[[2]],#[[3]],"preserved_independent_polynomial_manufactured_solution"]&,{{"values",cdMValues,10.^-8},{"gradients",cdMGrad,10.^-8},{"gauge",cdMGauge,.001},{"strong_PDE",cdMResidual,10.^-8}}];
  AppendTo[cdMMSChecks,<|"nodes"->cdMNodes,"source_run_id"->cdMMSSourceID,"values_error"->cdMValues,"gradient_error"->cdMGrad,"gauge_error"->cdMGauge,"independent_strong_PDE_residual"->cdMResidual,"assembled_matrix_residual_status"->"not_measured_high_level_saved_NDSolve_does_not_expose_assembled_matrix"|>],
  {cdMCase,cdMMS["data"]["cases"]}];
 cdScalarCases=KeyDrop[#,{"coordinates_dimensionless","elements","boundary_node_ids","all_node_u_psi_values","nodal_field_samples","profile"}]&/@cdCases;
 Export[FileNameJoin[{stageDir,"diagnostic_summary.json"}],<|"source_run_id"->cdSourceID,"source_wxf_sha256"->FileHash[cdSourcePath,"SHA256","HexString"],"cases"->cdScalarCases,"MMS"->cdMMSChecks,"physical_acceptance_status"->"failed_numerical","solver_executed"->False|>,"RawJSON"];
 stageData=<|"source_model"->"read_only_preserved_3D_A_phi_diagnostics","source_run_ids"->{cdSourceID,cdMMSSourceID},"source_wxf_hashes"-><|cdSourceID->FileHash[cdSourcePath,"SHA256","HexString"],cdMMSSourceID->FileHash[cdMMSPath,"SHA256","HexString"]|>,"cases"->cdCases,"historical_gates"->cdGateChecks,"manufactured_solution_recheck"->cdMMSChecks,"solver_executed"->False,"diagnostic_execution_status"->"completed_no_solve","physical_acceptance_status"->"failed_numerical","failure_reason"->"preserved_cylinder_phi_and_gauge_thresholds_failed","unavailable_checks"->{"assembled_matrix_residual_not_stored_by_original_high_level_solver","no_new_mesh_or_PDE_solution","no_air_interface_or_finite_terminal_solution","sampled_sidewall_flux_is_not_a_surface_integral_or_power_acceptance"},"scaling"->"Preserved u=j omega A/V and psi=phi/(a V), a=1mm. A=V u/(j omega), phi=a V psi, J=-sigma V(u+grad_dimensionless psi). Actual saved psi derivatives are always used.","revision_evidence_policy"->"Boundary/derivative/gradient diagnostics distinguish implementation faults from approximation errors; no boundary, scaling or phi substitution is applied without a new explicitly queued solve.","assumptions"->"Read-only original three-mesh cylinder calibration fields and existing independent manufactured solution. Sampling, finite differences and source-hash verification only. Original J .01 / phi 1e-8 / gauge .001 gates remain visible and failed. No FEM rerun, no analytic replacement of saved phi, no three-dimensional structure ranking."|>;
];
