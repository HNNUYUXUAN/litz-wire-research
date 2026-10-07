cuArea=640 Pi (.0001/2)^2;cuRadius=Sqrt[cuArea/Pi];
cuSolidZ=LitzPhysics`WireZ[cuRadius,200000.];cuStrandZ=LitzPhysics`WireZ[.00005,200000.];
cuGeos=Table[LitzPhysics`Topology[k,640,.01,.01,.0001],{k,{"straight","single","multilevel","crosslayer"}}];
cuRows=Table[With[{l=g["arc_lengths_m"]},With[{z=cuStrandZ l},With[{s=LitzPhysics`CommonPort[DiagonalMatrix[z],ConstantArray[0.,640],20.]},
 <|"kind"->g["kind"],"source_model"->"uncoupled_internal_impedance_reduced_prediction","nominal_copper_area_m2"->cuArea,"axial_length_m"->.01,
 "Rdc_ohm_per_axial_m"->g["Rdc_ohm"]/.01,"Rac_ohm_per_axial_m"->Re[s["impedance"]]/.01,"Rac_Rdc"->Re[s["impedance"]]/g["Rdc_ohm"],
 "loss_W_per_axial_m"->s["loss_W"]/.01,"copper_volume_m3_per_axial_m"->g["copper_volume_m3"]/.01,"mean_arc_length_growth"->Mean[l]/.01,
 "complex_current_deviation_relative"->Norm[s["currents"]-20./640]/Norm[s["currents"]],"minimum_gap_m"->g["minimum_surface_gap_m"]|>]]],{g,cuGeos}];
stageCheck["minimum_nominal_area",Max[0.,5.*^-6-cuArea],10.^-15,"geometry_area"];
stageCheck["total_dc_current_density_limit",Max[0.,20./cuArea/10.^6-4.],10.^-12,"geometry_area"];
stageData=<|"source_model"->"equal_copper_analytical_and_uncoupled_reduced_prediction","area_m2"->cuArea,"solid_diameter_m"->2 cuRadius,
 "solid"-><|"source_model"->"Bessel_internal_impedance","Rdc_ohm_per_m"->1/(5.8*^7 cuArea),"Rac_ohm_per_m"->Re[cuSolidZ],"Xinternal_ohm_per_m"->Im[cuSolidZ],"loss_W_per_m"->400 Re[cuSolidZ]|>,"bundle_predictions"->cuRows,
 "assumptions"->"640 x 0.1 mm is an initialization, area 5.026548 mm^2. Solid uses the same actual nominal copper area. Bundle figures only sum isolated strand internal impedances along actual arc lengths and solve ideal common-end parallel currents; mutual coupling/proximity/transition losses omitted. Values are a reduced prediction, unsuitable for final topology ranking. Per metre is axial; volume and lengths included. Full-field 640-strand route is separate."|>;
stageFigure["arc_length_cost",BarChart[Lookup[cuRows,"mean_arc_length_growth"],ChartLabels->Lookup[cuRows,"kind"],Frame->True,FrameLabel->{"geometry","arc length / axial length"},ImageSize->600]];
stageFigure["internal_loss_prediction",BarChart[Join[{400 Re[cuSolidZ]},Lookup[cuRows,"loss_W_per_axial_m"]],ChartLabels->Join[{"equal-copper solid"},Lookup[cuRows,"kind"]],Frame->True,FrameLabel->{"model","W / axial m"},ImageSize->650]];
