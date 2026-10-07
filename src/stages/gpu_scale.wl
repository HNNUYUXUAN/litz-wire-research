Get[FileNameJoin[{stageRoot,"src","stages","gpu_physics.wl"}]];
stageData["resumed_completed_cases_from"]=gpResumeID;stageData["first_blocked_case"]=gpBlocked;
If[Length[gpCases]>=2,stageCheck["GPU_scale_spatial_change",Abs[Last[gpCases]["Rac_ohm_per_axial_m"]/gpCases[[-2]]["Rac_ohm_per_axial_m"]-1],.01,"longitudinal_PEEC"];stageCheck["GPU_scale_Bessel_Rac",Last[gpCases]["Bessel_Rac_relative_error"],.01,"longitudinal_PEEC"]];
