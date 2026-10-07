Get[FileNameJoin[{stageRoot,"src","PEEC.wl"}]];eqRows={};
Do[eqNew=LitzPEEC`LongitudinalModel[m,.04,200000.];eqReference=LitzPhysics`CommonPort[eqNew["Z_ohm"],ConstantArray[0.,eqNew["filaments"]],20.];
 stageCheck["port_equivalent_currents_"<>ToString[m],Norm[eqNew["solution"]["currents"]-eqReference["currents"]]/Norm[eqReference["currents"]],10.^-10,"sparse_R_and_reduced_zero_source_port_vs_augmented"];
 stageCheck["port_equivalent_power_"<>ToString[m],Abs[eqNew["solution"]["loss_W"]/eqReference["loss_W"]-1],10.^-10,"independent_Joule_vs_Hermitian_impedance"];
 stageCheck["reduced_port_residual_"<>ToString[m],eqNew["solution"]["linear_residual"],10.^-8,"same_full_impedance_matrix"];
 AppendTo[eqRows,<|"cross_divisions"->m,"filaments"->eqNew["filaments"],"R_head"->ToString[Head[eqNew["resistance_matrix_ohm"]]],"current_relative_error"->Norm[eqNew["solution"]["currents"]-eqReference["currents"]]/Norm[eqReference["currents"]]|>],{m,{6,14}}];
stageData=<|"source_model"->"PEEC_memory_optimization_equivalence","cases"->eqRows,"assumptions"->"Sparse diagonal resistor and early release of pair-coordinate arrays; e=0 common-end solve Zx=1 and normalization is independently compared to the original augmented solve on exactly the same physical matrix. No change to volume quadrature, current convention or physics."|>;
