(* Pure presentation helpers; no physical models are imported or evaluated. *)
BeginPackage["LitzArchiveFormatting`"];
ArchiveStageFor::usage="ArchiveStageFor[file,tag] assigns an archive volume from its source filename.";
ArchiveRoutesFor::usage="ArchiveRoutesFor[stage,routes] selects explicit frozen evidence families.";
ArchiveIntro::usage="ArchiveIntro[stage] gives the bounded interpretation in Chinese.";
ArchiveFormulaCells::usage="ArchiveFormulaCells[stage] gives static TraditionalForm formula cells.";
ArchiveScalarRows::usage="ArchiveScalarRows[value,max] extracts bounded scalar rows, never arrays or matrices.";
ArchiveStaticCellCounts::usage="ArchiveStaticCellCounts[notebook] counts active and saved output cells.";
Begin["`Private`"];
ArchiveStageFor[file_String,tag_:"overview"]:=Switch[FileBaseName[file],
 "00_Environment_Check","environment","00_GPU_Runtime_Check","gpu",
 "01_Q1_Analytical","analytic","02_Q1_FEM_2D","fem2",
 "03_Parallel_Strands","circuits","04_Topology_And_Transposition","geometry",
 "05_Equal_Copper_Comparison","copper","06_Computational_Boundary","boundary",
 "07_3D_FEM_Validation","fem3","08_PEEC_Validation","peec",
 "09_Volume_Flux_PEEC","voxel","10_3D_Progress_And_Evidence","progress",
 "11_Research_Report_Master","master","Litz_Notebook_Index","overview",_,tag];
ArchiveRoutesFor[stage_String,routes_List]:=Module[{base,prefixes},
 If[MemberQ[{"overview","master"},stage],Return[routes]];
 {base,prefixes}=Switch[stage,
  "environment",{{"gpu","cpu_workers","frontend"},{"closure_gpu_","closure_peec_small_tests","closure_voxel_operator_tests","closure_closure_rt0_parallel_tests"}},
  "analytic",{{"analytic"},{"closure_analytic"}},
  "fem2",{{"fem2","coax","coax640","ansys_port"},{"closure_ansys_2d_"}},
  "circuits",{{"circuits","coax","coax640","ansys_port"},{"closure_ansys_2d_"}},
  "geometry",{{"geometry","handoff","ansys_import"},{"closure_geometry","closure_ansys_native_"}},
  "copper",{{"copper","coax640","scale"},{"closure_geometry","closure_ansys_2d_"}},
  "peec",{{"peec","peec_equivalence","gpu_physics"},{"closure_peec_","closure_gpu_m","closure_frozen_physics_collect"}},
  "voxel",{{"voxel","voxel_scale","voxel_boundary","voxel_operator_tests","voxel_operator_quadrature"},{"closure_rt0_","closure_voxel_operator_tests","closure_closure_rt0_parallel_tests","closure_frozen_physics_collect"}},
  "fem3",{{"fem3","fem3_audit","fem3_ooc","fem3_iter","fem3_cylinder","fem3_mms"},{"closure_fem3_","closure_ansys_native_"}},
  "gpu",{{"gpu","gpu_physics","gpu_scale","peec_equivalence"},{"closure_gpu_","closure_frozen_physics_collect"}},
  "progress",{{"fem3","fem3_audit","fem3_ooc","fem3_iter","fem3_cylinder","fem3_mms","voxel","voxel_scale","voxel_boundary","progress_notebook","delivery_data"},{"closure_rt0_","closure_fem3_","closure_ansys_","closure_geometry","closure_frozen_physics_collect"}},
  "boundary",{{"boundary","cpu_workers","gpu_scale","scale","fem3_audit","fem3_ooc","fem3_iter"},{"closure_peec_","closure_rt0_","closure_gpu_","closure_ansys_","closure_fem3_"}},
  _,{{stage},{}}];
 Select[routes,Function[r,MemberQ[base,r]||AnyTrue[prefixes,StringStartsQ[r,#]&]]]];
ArchiveIntro[stage_]:=Switch[stage,
 "environment","阅读环境按当前设备实测记录。成稿重绘仅使用 CPU，线程上限 8；设备安装 GPU 与本次文稿是否调用 GPU 分开记录。历史环境验收只说明对应运行链的测试范围。",
 "analytic","Q1 保留直径 2 mm、200 kHz、20 A RMS 的孤立长圆铜线内部阻抗校准。它的铜面积约 3.142 mm²，直流电流密度约 6.366 A/mm²；不能作为 Q2 足铜设计。",
 "fem2","二维平移截面场解与解析值、回流及外域敏感性分别记录。旧七股和 640 股对照保留；本轮 Ansys 二维两电压基解的网格身份不一致，未获得有效的最终 20 A 档。",
 "circuits","各股沿途绝缘、端部并联。共同端电压及总电流约束决定复电流；均流仅是独立的理想参考。外加感应电势进入完整功率平衡。",
 "geometry","本轮几何检查限定为采样轨迹、铜量与合成分区一致性。弧长增长必须计入直流电阻和铜体积；采样几何通过不能推出真实换位结构性能排名。",
 "copper","Q2 名义铜截面至少 5 mm²，并使用实际铜量作等铜对照。传统多级 Litz 保留为强基线；候选损耗差需大于相关数值不确定性才支持排名。",
 "peec","本轮 11 个纵向 PEEC 档覆盖 1,264/5,024 根体积丝、长度、互项积分阶数及自项精度。结论限定为直线有限长度纵向模型。GPU 两档仅验证同模型 CPU/GPU 等价；它们不证明实际换位结构更优。",
 "voxel","本轮 RT0 方体为 1×1×2 mm、200 kHz、均匀外加 Bz=1 mT RMS、净输运电流 0 A。n=16→20→24 的连续两档损耗变化门槛 1%，最细 q=14→18 验证门槛 0.1%。专项参数优先于 generic parameters.json 的 20 A 模板。",
 "fem3","三维 A–φ 诊断、制造解与物理算例分开呈现。规范、共同端电势、残差、功率和侧壁通量必须同时通过；已有失败与有限停止记录保留，不能写为完成独立三维场解验证。",
 "gpu","读取历史冻结的 CPU/GPU 等价和 9,856 档恢复证据。本次归档构建不调用 CUDA、GPU 阵列或场求解；硬件时间仅属于原运行环境。",
 "progress","本册集中读取三维模型、RT0 空间与积分验证、结构几何及 Ansys 有限失败证据。完成的数值范围与未完成的真实结构性能问题分别标注。",
 "boundary","资源曲线的进程归属与模型峰值范围需匹配。RT0 q18 原资源总峰包含独立 reader 等进程，精确的纯物理全程峰值未知；保留原曲线和排除说明。",
 _,"本册按冻结索引汇集成稿证据。物理模型通过、缓存完整性通过、序列化通过及界面显示通过属于不同验收范围。全部原始历史与源码快照仍保留，文稿表图从冻结数据生成。"];
formula[expr_]:=Block[{$ContextPath=Prepend[$ContextPath,"LitzArchiveFormatting`Private`"]},Cell[BoxData[ToBoxes[expr/.{delta->\[Delta],kappa->\[Kappa],sigma->\[Sigma],omega->\[Omega],mu->\[Mu],ell->\[ScriptL],phi->\[CurlyPhi],epsilon->\[Epsilon]},TraditionalForm]],"DisplayFormula",Evaluatable->False]];
ArchiveFormulaCells[stage_]:=Switch[stage,
 "analytic",{formula[HoldForm[delta==Sqrt[2/(omega mu sigma)]]],formula[HoldForm[kappa==(1+I)/delta]],formula[HoldForm[Subscript[Z,int]==kappa BesselI[0,kappa a]/(2 Pi a sigma BesselI[1,kappa a])]],formula[HoldForm[Subscript[R,dc]==1/(sigma Pi a^2)]],formula[HoldForm[Subscript[P,J]==Subscript[\[ScriptCapitalI],RMS]^2 Re[Subscript[Z,int]]]]},
 "circuits"|"fem2",{formula[HoldForm[Z i-V one==-e]],formula[HoldForm[Sum[Subscript[i,k],{k,1,n}]==Subscript[\[ScriptCapitalI],total]]],formula[HoldForm[P==Re[Conjugate[i].(Z.i)]]]},
 "geometry"|"copper",{formula[HoldForm[Subscript[R,dc]==(Sum[sigma Subscript[A,k]/Subscript[ell,k],{k,1,n}])^-1]],formula[HoldForm[Subscript[V,Cu]==Sum[Subscript[A,k] Subscript[ell,k],{k,1,n}]]],formula[HoldForm[Subscript[g,k]==Subscript[ell,k]/Subscript[L,axial]]]},
 "peec",{formula[HoldForm[Z==R+I omega L]],formula[HoldForm[Subscript[R,k]==ell/(sigma Subscript[A,k])]],formula[HoldForm[Subscript[R,ac]==Subscript[P,J]/(Subscript[\[ScriptCapitalI],total]^2 Subscript[L,axial])]],formula[HoldForm[epsilon==Abs[Subscript[x,fine]-Subscript[x,coarse]]/Abs[Subscript[x,coarse]]]]},
 "voxel",{formula[HoldForm[D.q==0]],formula[HoldForm[Subscript[\[ScriptCapitalI],net]==0]],formula[HoldForm[Subscript[P,J]==Sum[(Abs[Subscript[q,minus]]^2+Abs[Subscript[q,plus]]^2+Re[Conjugate[Subscript[q,minus]] Subscript[q,plus]])/(3 sigma h),{cell,1,N},{axis,1,3}]]],formula[HoldForm[Subscript[r,true]==Norm[A.x-b,2]/Norm[b,2]]]},
 "fem3",{formula[HoldForm[J==-sigma (I omega A+Grad[phi])]],formula[HoldForm[Div[J]==0]],formula[HoldForm[Curl[(1/mu) Curl[A]]==J]]},
 "gpu",{formula[HoldForm[Subscript[epsilon,i]==Norm[Subscript[i,GPU]-Subscript[i,CPU],2]/Norm[Subscript[i,CPU],2]]]},
 _,{formula[HoldForm[Subscript[P,J]==Integrate[Abs[J]^2/sigma,V]]],formula[HoldForm[Subscript[R,dc]==(Sum[sigma Subscript[A,k]/Subscript[ell,k],{k,1,n}])^-1]]}];
smallScalarQ[x_]:=StringQ[x]||NumberQ[x]||MemberQ[{True,False,Null},x];
ArchiveScalarRows[value_,limit_Integer:12]:=Module[{rows={},walk,skip},
 skip={"source_manifest","source_files","retained_original_binary_files","source_snapshot","configuration","model_assumptions","parameters","geometries","geometry","mesh","fields","field","solution","currents_RMS_A_ReIm","cell_fields","residual_history","R_ohm","L_H","Z_ohm","resistance_matrix_ohm","partial_inductance_matrix_H","profile","checks","test_report"};
 walk[x_,path_,depth_]:=Which[Length[rows]>=limit,Null,
  smallScalarQ[x],If[path=!=""&&(!StringQ[x]||StringLength[x]<=180),AppendTo[rows,{path,x}]],
  AssociationQ[x]&&Lookup[x,"representation",None]=!="numeric_csv"&&depth<4,KeyValueMap[If[!MemberQ[skip,ToString[#1]],walk[#2,If[path==="",ToString[#1],path<>"/"<>ToString[#1]],depth+1]]&,x],
  ListQ[x]&&Length[x]<=4&&AllTrue[x,smallScalarQ],AppendTo[rows,{path,x}],
  ListQ[x]&&Length[x]<=4&&AllTrue[x,AssociationQ]&&depth<3,MapIndexed[walk[#1,path<>"/"<>ToString[First[#2]],depth+1]&,x],True,Null];
 walk[value,"",0];Take[rows,UpTo[limit]]];
ArchiveStaticCellCounts[notebook_]:=<|"input_cell_count"->Count[notebook,Cell[_,"Input",___],Infinity],"output_cell_count"->Count[notebook,Cell[_,"Output",___],Infinity],"formula_cell_count"->Count[notebook,Cell[_,"DisplayFormula",___],Infinity],"dynamic_box_count"->Count[notebook,_DynamicBox|_DynamicModuleBox,Infinity],"button_box_count"->Count[notebook,_ButtonBox,Infinity]|>;
End[];EndPackage[];
