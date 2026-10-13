$HistoryLength=0;$CharacterEncoding="UTF8";
root=Environment["LITZ_PROJECT"];runID=Environment["LITZ_RUN_ID"];model=Environment["LITZ_TUTORIAL_MODEL"];
out=FileNameJoin[{root,"outputs",runID}];p=Import[FileNameJoin[{out,"parameters.json"}],"RawJSON"];
SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->Min[8,$ProcessorCount]];
Get[FileNameJoin[{root,"shared","wolfram","NotebookPhysics.wl"}]];
checks={};fig=Graphics[{}];data=<||>;scope="";
check[name_,value_,tolerance_]:=AppendTo[checks,<|"name"->name,"actual"->N[value],"tolerance"->tolerance,"passed"->TrueQ[NumericQ[value]&&value<=tolerance]|>];
Switch[model,
 "analytic"|"wolfram-analytic",
 Get[FileNameJoin[{root,"models","analytic","src","Q1Analytical.wl"}]];
 inputs=Import[FileNameJoin[{root,"configs","reference_parameters.json"}],"RawJSON"];inputs=Join[inputs,p];
 data=LitzAnalytical`RoundWireSolution[inputs];
 check["current_integral",data["current_integral_relative_error"],10^-8];check["power_integral",data["power_integral_relative_error"],10^-8];check["low_frequency",Abs[data["low_frequency_Rac_Rdc"]-1],10^-8];
 fig=ListLinePlot[data["profile"][[All,{1,4}]],Frame->True,FrameLabel->{"r (m)","|J| (A/m^2 RMS)"},PlotRange->All];scope="Isolated long round wire internal impedance; Q1 calibration diameter 2 mm.",
 "fem2",
 data=LitzPhysics`DiskFEM[p["mesh_h"]];If[!AssociationQ[data],Print[data];Exit[1]];
 check["current_integral",data["independent_current_quadrature_residual"],.001];check["power",data["power_residual"],.001];check["Bessel_comparison",data["Rac_relative_error"],.01];
 fig=ListLinePlot[data["profile"][[All,{1,4}]],Frame->True,FrameLabel->{"r (m)","|J| (A/m^2 RMS)"}];scope="2D isolated circular diffusion; radius 1 mm, 200 kHz, 20 A RMS. Tutorial is one mesh; convergence is a separate campaign.",
 "circuits",
 data=<|"cases"->Map[LitzPhysics`CommonPort[#[[1]],#[[2]],p["current_RMS_A"]]& ,{{{{.01,.002 I},{.002 I,.01}},{0.,0.}},{{{.01,0.},{0.,.02}},{0.,0.}},{{{.01,.002 I},{.002 I,.01}},{.01 I,-.01 I}}}]|>;
 Do[check["current_"<>ToString[i],data["cases"][[i]]["current_residual"],10^-8];check["power_"<>ToString[i],data["cases"][[i]]["power_residual"],10^-8],{i,3}];
 fig=BarChart[Abs[# ["currents"]]&/@data["cases"],Frame->True,ChartLegends->{"equal","unequal R","external EMF"}];scope="Three common-terminal lumped models; independent sources included in power balance.",
 "coax"|"coax640",
 Get[FileNameJoin[{root,"models","common_terminal","src","CoaxFEM.wl"}]];
 data=LitzCoax`SolveCoax[p["strands"],p["diameter_m"],p["mesh_factor"],p["return_factor"],p["outer_factor"],p["minimum_segments"]];If[!AssociationQ[data],Print[data];Exit[1]];
 Scan[check[#,data[#],10^-8]&,{"linear_residual","current_residual","power_residual"}];
 data["bundle_Rdc_ohm_per_m"]=1/(5.8*^7 data["polygonal_bundle_area_m2"]);data["Rac_over_Rdc"]=data["bundle_Rac_ohm_per_m"]/data["bundle_Rdc_ohm_per_m"];
 data["copper_volume_m3_per_axial_m"]=data["polygonal_bundle_area_m2"];data["arc_lengths_m"]=ConstantArray[1.,p["strands"]];data["arc_length_growth_factors"]=ConstantArray[1.,p["strands"]];data["current_max_relative_complex_deviation"]=Max[Abs[data["strand_currents_RMS_A"]-20./p["strands"]]]/(20./p["strands"]);
 fig=ListPlot[Transpose[{Re[data["strand_currents_RMS_A"]],Im[data["strand_currents_RMS_A"]]}],Frame->True,FrameLabel->{"Re I (A RMS)","Im I (A RMS)"},PlotRange->All];scope="Common-voltage 2D straight insulated strands and controlled coaxial return. 200 kHz, 20 A RMS; small tutorial has insufficient copper for final Q2 design.",
 "geometry",
 data=LitzPhysics`Topology[p["kind"],p["strands"],p["length_m"],p["pitch_m"],p["diameter_m"]];
 check["positive_gap",Max[0.,-data["minimum_surface_gap_m"]],10^-12];check["arc_length",Max[0.,p["length_m"]-Min[data["arc_lengths_m"]]],10^-12];
 fig=Graphics3D[{Thickness[.005],MapIndexed[{ColorData[97][First[#2]],Line[#1]}&,data["paths"]]},Axes->True,AxesLabel->{"x (m)","y (m)","z (m)"},BoxRatios->Automatic];scope="Sampled geometry and axial-length copper accounting; geometric checks do not establish electromagnetic performance.",
 "copper",
 area=p["strands"] Pi (p["diameter_m"]/2)^2;diameter=2 Sqrt[area/Pi];data=<|"nominal_copper_area_m2"->area,"Jdc_A_per_mm2"->20/area/10^6,"equal_area_solid_diameter_m"->diameter,"equal_area_solid_Rac_ohm_per_m"->Re[LitzPhysics`WireZ[diameter/2,200000.]]|>;check["minimum_copper_area",Max[0.,5.*^-6-area],10^-12];fig=Graphics[{Circle[{0,0},diameter/2]},Axes->True];scope="Nominal equal-copper analytical reference; actual path lengths remain required for bundle Rdc.",
 "peec",
 Get[FileNameJoin[{root,"models","peec","src","PEEC.wl"}]];
 data=LitzPEEC`LongitudinalModel[p["cross_divisions"],p["length_m"],p["frequency_Hz"],"MutualQuadratureOrder"->p["quadrature_order"],"MemoryBudgetBytes"->24 2^30];If[!AssociationQ[data],Print[data];Exit[1]];
 Scan[check[#,data["solution"][#],10^-8]&,{"linear_residual","current_residual","power_residual"}];check["reciprocity",data["L_reciprocity_relative_residual"],10^-10];fig=ListPlot[Transpose[{Re[data["solution"]["currents"]],Im[data["solution"]["currents"]]}],Frame->True];scope=data["scope"],
 "voxel"|"rt0",
 Get[FileNameJoin[{root,"models","rt0","src","VoxelPEEC.wl"}]];
 data=LitzVoxel`FaceFluxModel[p["dimensions"],p["cell_width_m"],200000.,p["quadrature_order"],p["excitation"]];If[!AssociationQ[data],Print[data];Exit[1]];
 Scan[check[#,data[#],If[#=="power_residual",.001,10^-8]]&,{"linear_residual","continuity_residual","power_residual"}];
 If[p["excitation"]=="field",check["zero_transport",Abs[data["port_current_A"]],10^-8]];
 fig=BarChart[Abs[data["currents_RMS_A"]],Frame->True,FrameLabel->{"RT0 face","|I| (A RMS)"}];scope="Vector RT0 cuboid operator example; imposed field uses 1 mT RMS and zero net transport. External-field loss is not intrinsic transport resistance.",
 "aphi",
 Needs["NDSolve`FEM`"];
 frozen=Import[Environment["LITZ_APHI_SOURCE"],"WXF"];
 sigma=5.8*^7;voltage=20. LitzPhysics`WireZ[.001,200000.];
 grad[fn_,pt_]:=Table[(Derivative@@UnitVector[3,k])[fn]@@pt,{k,3}];
 gauge[fs_,pt_]:=Sum[(Derivative@@UnitVector[3,k])[fs[[k]]]@@pt,{k,3}];
 cases=Table[
  fields=c["fields"];points=Tuples[{Range[-.5,.5,.25],Range[-.5,.5,.25],{.3,1.,1.7}}];
  phiError=Max[Abs[fields[[4]]@@#+#[[3]]]&/@points];gaugeError=Max[Abs[gauge[fields,#]]&/@points];
  profile=Table[{r,-sigma voltage (((#@@{r,0.,1.})&/@Take[fields,3])+grad[fields[[4]],{r,0.,1.}])[[3]],LitzPhysics`WireJ[.001 r,.001,200000.,20.]},{r,0.,.95,.95/80}];
  jError=Norm[profile[[All,2]]-profile[[All,3]]]/Norm[profile[[All,3]]];
  Scan[check["reproduce_"<>ToString[c["nodes"]]<>"_"<>#[[1]],Abs[#[[2]]-c[#[[3]]]],10^-10]& ,{{"J",jError,"radial_relative_error"},{"phi",phiError,"phi_error"},{"gauge",gaugeError,"gauge_sample_residual"}}];
  <|"nodes"->c["nodes"],"J_Bessel_relative_error"->jError,"phi_error"->phiError,"gauge_residual"->gaugeError,"original_gates"-><|"J"->(jError<=.01),"phi"->(phiError<=10^-8),"gauge"->(gaugeError<=.001)|>,"plot_profile"->Table[{r,Abs[-sigma voltage (((#@@{r,0.,1.})&/@Take[fields,3])+grad[fields[[4]],{r,0.,1.}])[[3]]]},{r,0.,.95,.95/(p["sampling_points"]-1)}]|>,{c,frozen["data"]["cases"]}];
 data=<|"cases"->cases,"sampling_points"->p["sampling_points"],"source_file_SHA256"->FileHash[Environment["LITZ_APHI_SOURCE"],"SHA256","HexString"],"solver_executed"->False|>;
 fig=ListLinePlot[Lookup[cases,"plot_profile"],Frame->True,FrameLabel->{"r/a","|Jz| (A/m^2 RMS)"}];scope="Preserved three-dimensional cylinder field derivatives and original J/phi/gauge gates recomputed without a new solve. Original frequency 200 kHz, copper conductivity 58 MS/m and 20 A RMS are fixed.",
 "wolfram",
 data=<|"version"->$Version,"system_id"->$SystemID,"agenttools_version"->PacletObject["Wolfram/AgentTools"]["Version"],"front_end_connected"->($FrontEnd=!=Null)|>;check["arithmetic",Abs[2+2-4],0.];scope="Kernel arithmetic and package inventory; frontend rendering is independently checked.",
 "gpu",
 Needs["CUDALink`"];
 If[!TrueQ[CUDALink`CUDAQ[]],Export[FileNameJoin[{out,"results.json"}],<|"run_id"->runID,"source_model"->"GPU_environment","execution_status"->"blocked","physical_acceptance_status"->"not_run","error"->"CUDALink CUDA environment unavailable"|>,"RawJSON"];Exit[2]];
 n=p["matrix_size"];SeedRandom[12345];a=RandomReal[{-1,1},{n,n}];b=RandomReal[{-1,1},{n,n}];gpu=CUDALink`CUDADot[a,b];cpu=a.b;err=Norm[gpu-cpu,"Frobenius"]/Norm[cpu,"Frobenius"];check["GPU_CPU_multiply",err,10^-10];
 mat=RandomComplex[{-1.-I,1.+I},{n,n}]+n IdentityMatrix[n];known=N[Exp[I Range[n]/n]];rhs=mat.known;
 gpuSolve=Normal[LinearSolve[GPUArray[NumericArray[mat,"ComplexReal64"]],GPUArray[NumericArray[rhs,"ComplexReal64"]]]];
 solveError=Norm[gpuSolve-known]/Norm[known];check["GPU_complex_known_solution",solveError,10^-10];check["GPU_complex_residual",Norm[mat.gpuSolve-rhs]/Norm[rhs],10^-10];
 signal=RandomComplex[{-1.-I,1.+I},p["fft_size"]];fftMem=CUDALink`CUDAMemoryLoad[signal,"ComplexDouble"];fftOut=CUDALink`CUDAFourier[fftMem];fft=CUDALink`CUDAMemoryGet[fftOut];fftError=Norm[fft-Fourier[signal]]/Norm[Fourier[signal]];check["GPU_FFT_CPU",fftError,10^-10];
 inverse=CUDALink`CUDAInverseFourier[fftOut];check["GPU_FFT_roundtrip",Norm[CUDALink`CUDAMemoryGet[inverse]-signal]/Norm[signal],10^-10];
 Scan[CUDALink`CUDAMemoryUnload,{fftMem,fftOut,inverse}];
 data=<|"matrix_size"->n,"multiply_relative_error"->err,"complex_solve_relative_error"->solveError,"fft_size"->p["fft_size"],"fft_relative_error"->fftError,"fft_execution_status"->"completed"|>;fig=ListPlot[Flatten[Take[gpu,Min[4,n]]],Frame->True];scope="Small Real64/ComplexReal64 GPU/CPU multiplication, known complex solution, residual and cuFFT comparison. Synthetic numerical validation only.",
 _,Print["Unknown tutorial model"];Exit[2]
];
clean[x_Association]:=Map[clean,x];clean[x_List]:=clean/@x;
clean[x_Complex]:=<|"real"->N[Re[x]],"imag"->N[Im[x]]|>;
clean[x_?NumericQ]:=If[TrueQ[Abs[x]<Infinity],N[x],ToString[x,InputForm]];
clean[x_String]:=x;clean[True]:=True;clean[False]:=False;clean[Null]:=Null;clean[x_]:=ToString[x,InputForm];
If[!DirectoryQ[FileNameJoin[{out,"figures"}]],CreateDirectory[FileNameJoin[{out,"figures"}]]];
fig=Show[fig,ImageSize->700,BaseStyle->{FontFamily->"Times New Roman",FontSize->12}];
Export[FileNameJoin[{out,"figures","preview.png"}],fig,"PNG",ImageResolution->144];
Export[FileNameJoin[{out,"results.wxf"}],<|"data"->data,"figure"->fig,"checks"->checks,"scope"->scope|>,"WXF"];
summary=KeyDrop[data,{"mesh","field","Z_ohm","resistance_matrix_ohm","partial_inductance_matrix_H","u_nodes_V_per_m"}];
result=<|"run_id"->runID,"source_model"->Lookup[data,"source_model",model],"execution_status"->"completed","physical_acceptance_status"->If[model=="aphi","failed_retained_phi_gauge",If[AllTrue[checks,TrueQ[#["passed"]]&],"passed_test_scope_only","failed"]],"parameters"->p,"scope"->scope,"checks"->checks,"data"->clean[summary],"Wolfram_version"->$Version|>;
If[Export[FileNameJoin[{out,"results.json"}],result,"RawJSON"]===$Failed,Exit[2]];Print["RESEARCH_CASE_COMPLETE ",model];
Exit[If[AllTrue[checks,TrueQ[#["passed"]]&],0,1]];
