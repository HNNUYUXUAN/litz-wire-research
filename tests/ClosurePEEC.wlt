(* Small independent pairwise-versus-offset regression must pass before the
   new cached assembly is used for a high-resolution closure run. *)
closureTestRoot=If[ValueQ[stageRoot],stageRoot,DirectoryName[DirectoryName[$InputFileName]]];
Get[FileNameJoin[{closureTestRoot,"src","NotebookPhysics.wl"}]];
Get[FileNameJoin[{closureTestRoot,"src","PEEC.wl"}]];
closureLegacy=LitzPEEC`LongitudinalModel[6,.04,200000.];
closureOffsets=LitzPEEC`LongitudinalModel[6,.04,200000.,"MutualKernelMethod"->"GridOffsets"];
VerificationTest[And@@(AssociationQ/@{closureLegacy,closureOffsets}),True,TestID->"PEEC-legacy-and-offset-models-executed"]
VerificationTest[{closureLegacy["mutual_quadrature_order"],closureLegacy["self_accuracy_goal"],closureLegacy["self_precision_goal"],closureLegacy["mutual_kernel_method"]},
 {4,10,8,"Pairwise"},TestID->"PEEC-default-quadrature-and-assembly-compatibility"]
VerificationTest[{closureLegacy["filaments"],closureLegacy["centers_m"],closureLegacy["area_m2"]},
 {closureOffsets["filaments"],closureOffsets["centers_m"],closureOffsets["area_m2"]},TestID->"PEEC-offset-cache-preserves-filament-geometry"]
VerificationTest[Norm[closureLegacy["partial_inductance_matrix_H"]-closureOffsets["partial_inductance_matrix_H"],"Frobenius"]/
 Norm[closureLegacy["partial_inductance_matrix_H"],"Frobenius"]<10.^-12,True,TestID->"PEEC-offset-cache-versus-independent-pairwise-volume-matrix"]
VerificationTest[Norm[closureLegacy["solution"]["currents"]-closureOffsets["solution"]["currents"]]/Norm[closureLegacy["solution"]["currents"]]<10.^-10,
 True,TestID->"PEEC-offset-cache-complex-current-equivalence"]
VerificationTest[Abs[closureOffsets["solution"]["loss_W"]/closureLegacy["solution"]["loss_W"]-1]<10.^-10,
 True,TestID->"PEEC-offset-cache-Joule-loss-equivalence"]
closureAugmented=LitzPhysics`CommonPort[closureOffsets["Z_ohm"],ConstantArray[0.,closureOffsets["filaments"]],20.];
VerificationTest[Norm[closureAugmented["currents"]-closureOffsets["solution"]["currents"]]/Norm[closureAugmented["currents"]]<10.^-10,
 True,TestID->"PEEC-independent-augmented-common-port-equivalence"]
VerificationTest[And@@(closureOffsets["solution"][#]<10.^-8&/@{"linear_residual","current_residual","common_voltage_residual","power_residual"}),
 True,TestID->"PEEC-offset-port-current-voltage-power-residuals"]
closureQ6=LitzPEEC`LongitudinalModel[4,.04,200000.,"MutualKernelMethod"->"GridOffsets","MutualQuadratureOrder"->6,
 "SelfAccuracyGoal"->12,"SelfPrecisionGoal"->10,"ComputeInductanceEigenvalue"->False];
VerificationTest[{closureQ6["mutual_quadrature_order"],closureQ6["self_accuracy_goal"],closureQ6["self_precision_goal"],closureQ6["minimum_L_eigenvalue_H"],closureQ6["inductance_passivity_status"]},
 {6,12,10,Null,"sampled_quadratic_forms_only"},TestID->"PEEC-explicit-quadrature-options-and-passivity-scope"]
VerificationTest[closureQ6["L_reciprocity_relative_residual"]<10.^-12,True,TestID->"PEEC-high-order-volume-integral-reciprocity"]
VerificationTest[MatchQ[LitzPEEC`LongitudinalModel[6,.04,200000.,"MemoryBudgetBytes"->1.],Failure["ResourceBudget",_Association]],
 True,TestID->"PEEC-memory-preflight-before-dense-allocation"]
VerificationTest[MatchQ[LitzPEEC`LongitudinalModel[4,.04,200000.,"MutualQuadratureOrder"->1],Failure["InvalidPEECOptions",_Association]],
 True,TestID->"PEEC-invalid-quadrature-order-rejected"]
closureDC=LitzPEEC`LongitudinalModel[4,.16,0.,"MutualKernelMethod"->"GridOffsets","ComputeInductanceEigenvalue"->False];
VerificationTest[Abs[closureDC["Rac_ohm_per_axial_m"]/(1/(5.8*^7 closureDC["area_m2"]))-1]<10.^-12,
 True,TestID->"PEEC-finite-length-DC-equal-area-closed-form"]
VerificationTest[And@@(SyntaxQ[Import[FileNameJoin[{closureTestRoot,"src","stages",#}],"Text"]]&/@{"closure_peec.wl","closure_rt0.wl"}),
 True,TestID->"PEEC-and-RT0-closure-stage-syntax"]
