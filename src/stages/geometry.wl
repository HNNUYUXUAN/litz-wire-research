geoCases=Table[LitzPhysics`Topology[kind,If[kind=="multilevel",24,7],.02,.01,.0001],{kind,{"straight","single","multilevel","crosslayer"}}];
Do[stageCheck["gap_"<>g["kind"],Max[0.,-g["minimum_surface_gap_m"]],10.^-12,"sampled_geometry"];
 stageCheck["periodic_position_"<>g["kind"],g["periodic_position_error_m"],10.^-10,"sampled_geometry"];
 stageFigure["geometry_"<>g["kind"],Graphics3D[MapIndexed[{ColorData[97][First[#2]],Line[1000 #1]}&,g["paths"]],Axes->True,AxesLabel->{"x (mm)","y (mm)","z (mm)"},BoxRatios->{1,1,2},ImageSize->{600,500},PlotLabel->"Display aspect adjusted; coordinates in mm"]],{g,geoCases}];
dtN=7;dtZ=DiagonalMatrix[N[Range[dtN]] .001]+I .0001 Table[1./(1+Abs[i-j]),{i,dtN},{j,dtN}];
dtP=Table[IdentityMatrix[dtN][[RotateLeft[Range[dtN],k]]],{k,0,dtN-1}];
dtAverage=LitzPhysics`DTM[ConstantArray[dtZ,dtN],dtP,ConstantArray[1./dtN,dtN]];
dtSol=LitzPhysics`CommonPort[dtAverage,ConstantArray[0.,dtN],20.];
dtFunc[z_?NumericQ]:=dtZ;
dtPerm[z_?NumericQ]:=dtP[[Min[Floor[z dtN]+1,dtN]]];
idtAverage=LitzPhysics`IDTM[{N[Range[0,dtN]/dtN],{0.,.17,.41,1.}},dtFunc,dtPerm];
stageCheck["DTM_iDTM_union_agreement",Norm[dtAverage-idtAverage]/Norm[dtAverage],10.^-12,"additive_permutation_model"];
stageCheck["balanced_row_sums",Norm[dtAverage.ConstantArray[1.,dtN]-Mean[dtAverage.ConstantArray[1.,dtN]]]/Norm[dtAverage],10.^-12,"additive_permutation_model"];
stageCheck["DTM_complex_current_balance",Norm[dtSol["currents"]-20./dtN]/20.,10.^-10,"additive_permutation_model"];
stageCheck["DTM_order_invariance",Norm[dtAverage-LitzPhysics`DTM[ConstantArray[dtZ,dtN],Reverse[dtP],ConstantArray[1./dtN,dtN]]],10.^-12,"additive_permutation_model"];
stageData=<|"source_model"->"sampled_geometry_and_additive_DTM","geometries"->geoCases,"DTM"-><|"slot_impedance_ohm_per_m"->dtZ,"permutations_slot_from_physical"->dtP,"weights_m"->ConstantArray[1./dtN,dtN],"Z_ohm"->dtAverage,"solution"->dtSol,"iDTM"->idtAverage|>,
 "assumptions"->"Geometry is a sampled centreline model, round copper plus specified nominal clearance. multilevel: eight strands per subbundle, counter/relative pitch p/4 and whole-bundle pitch p; this is an explicit traditional two-level baseline, not an optimized industrial construction. crosslayer is a small radial modulation candidate. Gap and curvature checks are sampled and need refined continuous collision checks before manufacturing. DTM matrices here are explanatory synthetic reciprocal passive impedances; P maps physical IDs to slots, Ztotal=sum dz P^T Z P. iDTM integrates the union of all supplied breakpoints. This additive model cannot resolve transitions or nonlocal coupling."|>;
Export[FileNameJoin[{stageDir,"strand_geometry.wxf"}],geoCases,"WXF"];

