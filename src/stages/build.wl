Get[FileNameJoin[{stageRoot,"src","NotebookView.wl"}]];
buildIndex=Import[FileNameJoin[{stageRoot,"docs","总控","当前运行索引.json"}],"RawJSON"];
buildEnvPath=FileNameJoin[{stageRoot,"outputs",Lookup[buildIndex,"progress_run_id","missing"],"environment.json"}];
buildEnvironment=If[FileExistsQ[buildEnvPath],Import[buildEnvPath,"RawJSON"],<||>];
buildEnvironmentText="本机实测环境来源："<>Lookup[buildIndex,"progress_run_id","unknown"]<>"。"<>
 "Wolfram "<>ToString[Lookup[buildEnvironment,"WolframVersion","unknown"]]<>"；CPU="<>ToString[Lookup[buildEnvironment,"cpu","unknown"]]<>
 "；系统逻辑处理器="<>ToString[Lookup[buildEnvironment,"logical_processors","unknown"]]<>
 "；主存GiB="<>ToString[Lookup[buildEnvironment,"ram_bytes",0]/1024.^3]<>
 "；GPU="<>ToString[Lookup[buildEnvironment,"gpu","unknown"]]<>"。前端交互状态单独验收；历史硬件不替代本机实测。";
buildInput[code_String] := Block[{$ContextPath={"System`"},$Context="Global`"},Cell[BoxData[ToBoxes[ToExpression[code,InputForm,HoldForm]]/.TagBox[b_,HoldForm,___]:>b],"Input"]];
buildBook[file_,title_,sections_List,stage_] := Module[{r,inputs,cells,nb,path,read,figs},
 r=LitzView`OpenStage[stageRoot,stage];
 inputs={buildInput["$CharacterEncoding = \"UTF8\"; litzRoot = DirectoryName[NotebookDirectory[]]; Get[FileNameJoin[{litzRoot, \"src\", \"NotebookView.wl\"}]]; Get[FileNameJoin[{litzRoot, \"src\", \"NotebookPhysics.wl\"}]]; LitzView`StageDashboard[litzRoot, \""<>stage<>"\"]"]};
 inputs=Join[inputs,Switch[stage,
 "analytic",{buildInput["Table[{f,LitzPhysics`WireZ[.001,f]},{f,{100.,1000.,200000.}}]"]},
 "fem2",{buildInput["KeyTake[LitzPhysics`DiskFEM[.12],{\"nodes\",\"Rac_ohm_per_m\",\"Rac_relative_error\",\"power_residual\"}]"]},
 "circuits",{buildInput["LitzPhysics`CommonPort[{{.02+.01 I,.003 I},{.003 I,.04+.01 I}},{0.,0.},20.]"]},
 "geometry",{buildInput["KeyDrop[LitzPhysics`Topology[\"single\",7,.02,.01,.0001],\"paths\"]"]},
 "peec",{buildInput["Get[FileNameJoin[{litzRoot,\"src\",\"PEEC.wl\"}]]; KeyTake[LitzPEEC`LongitudinalModel[6,.04,200000.],{\"filaments\",\"Rac_ohm_per_axial_m\",\"Bessel_Rac_relative_error\"}]"]},
 _,{}]];
 cells=Join[{Cell[title,"Title"],Cell["全册约定：SI 计算，exp(+jωt)，RMS 相量，铜 σ=5.8×10⁷ S/m、μr=1、20 ℃，主工况 f=200 kHz、总电流20 A。每米指轴向长度。", "Text"]},
 Flatten[Map[{Cell[#[[1]],"Section"],Cell[#[[2]],"Text"]}&,sections]],
 {Cell["执行与证据","Section"],Cell["下方输入读取实际运行缓存，保留来源与验收结果。重型计算从项目终端运行：powershell -File src/RunNotebookStage.ps1 -Stage "<>stage<>"。运行器使用新内核及唯一 run_id；重算不改写本册章节。", "Text"]},inputs];
 If[AssociationQ[r],
  cells=Join[cells,{Cell["以下输出来自 "<>r["run_id"]<>"；source_model="<>r["source_model"]<>"；execution_status="<>r["execution_status"],"Text"],Cell[BoxData[ToBoxes[Dataset[r["checks"]]]],"Output"]}];
  cells=Join[cells,Flatten[KeyValueMap[{Cell[#1,"Subsection"],Cell[BoxData[ToBoxes[#2]],"Output"]}&,r["figures"]]]];
  cells=Append[cells,Cell[Lookup[r["data"],"assumptions","见运行归档。"],"Text"]],
  cells=Append[cells,Cell["当前没有完成运行缓存；输入会如实显示缺口。","Text"]]
 ];
 If[stage=="analytic",cells=Join[cells,{Cell["瞬时电流：可交互解析图","Section"],Cell["θ=ωt，j(r,t)=√2 Re[J(r) exp(jθ)]；滑块只计算轻量 Bessel 解析曲线。","Text"],
 buildInput["Manipulate[Plot[Sqrt[2] Re[LitzPhysics`WireJ[r/1000.,.001,200000.,20.] Exp[I theta]]/10.^6,{r,0,1},Frame->True,FrameLabel->{\"r (mm)\",\"j(t) (A/mm^2)\"},PlotRange->{-35,35}],{theta,0,2 Pi}]"]}]];
 If[stage=="geometry",cells=Join[cells,{Cell["沿轴向追踪物理股线身份","Section"],
 buildInput["geoCache = LitzView`OpenStage[litzRoot,\"geometry\"][\"data\"][\"geometries\"]; Manipulate[With[{g=geoCache[[kind]],idx=Round[1+400 fraction]},Graphics[Table[{ColorData[97][id],Disk[1000 g[\"paths\"][[id,idx,1;;2]],1000 g[\"diameter_m\"] /2],Black,Text[id,1000 g[\"paths\"][[id,idx,1;;2]]]}, {id,Length[g[\"paths\"]]}],Frame->True,FrameLabel->{\"x (mm)\",\"y (mm)\"},PlotRange->{{-1.5,1.5},{-1.5,1.5}},ImageSize->500]],{kind,{1->\"直束\",2->\"单级\",3->\"传统两级\",4->\"跨层候选\"}},{fraction,0,1}]"]}]];
 If[stage=="voxel",cells=Join[cells,{Cell["闭环瞬时方向：缓存相量的轻量交互","Section"],Cell["箭头来自 RT0 体素中心插值；长度按当前峰值归一化，图上注明峰值和显示比例。零输运外场测试独立标注。","Text"],buildInput["voxelCache = Last[LitzView`OpenStage[litzRoot,\"voxel\"][\"data\"][\"cases\"]]; Manipulate[LitzView`VoxelCurrentPlot[voxelCache,phase],{phase,0,2 Pi}]"]}]];
 If[MemberQ[{"fem2","copper"},stage],buildCoax=LitzView`OpenStage[stageRoot,"coax"];
  If[AssociationQ[buildCoax],cells=Join[cells,{Cell["实际同轴回流场解","Section"],Cell["来源："<>buildCoax["run_id"]<>"；大股数为粗网格执行证据。polygonal_bundle_area_m2 是数值网格铜面积，需与名义圆形铜面积的几何误差分开。","Text"],
  Cell[BoxData[ToBoxes[Dataset[KeyTake[#,{"strands","nodes","mesh_factor","return_factor","outer_factor","polygonal_bundle_area_m2","bundle_Rac_ohm_per_m","bundle_loss_W_per_m","return_loss_W_per_m","input_W_per_m","power_residual"}]&/@buildCoax["data"]["cases"]]]],"Output"]}]]];
 If[MemberQ[{"fem2","copper"},stage],buildFine640=LitzView`OpenStage[stageRoot,"coax640"];If[AssociationQ[buildFine640],cells=Join[cells,{Cell["640股：实际铜面积、三档网格和独立边界检查","Section"],Cell[buildFine640["run_id"]<>"；"<>buildFine640["execution_status"]<>"。圆股采用至少64段边界；等实际网格铜面积实心基线与名义圆形铜面积基线分开。","Text"],Cell[BoxData[ToBoxes[Dataset[buildFine640["checks"]]]],"Output"],Cell[BoxData[ToBoxes[Dataset[Join[KeyTake[#,{"nodes","mesh_factor","return_factor","outer_factor","polygonal_bundle_area_m2","bundle_Rac_ohm_per_m","bundle_loss_W_per_m","return_loss_W_per_m","power_residual"}],<|"Rac_Rdc"->#["bundle_Rac_ohm_per_m"] 5.8*^7 #["polygonal_bundle_area_m2"],"complex_current_deviation_relative"->Norm[#["strand_currents_RMS_A"]-20./640]/Norm[#["strand_currents_RMS_A"]]|>]&/@buildFine640["data"]["cases"]]]],"Output"],Cell[BoxData[ToBoxes[Dataset[buildFine640["data"]["equal_actual_area_solid_internal_baseline"]]]],"Output"]},(Cell[BoxData[ToBoxes[#]],"Output"]&/@Values[buildFine640["figures"]])]]];
 If[stage=="peec",buildGPUPhysics=LitzView`OpenStage[stageRoot,"gpu_physics"];
  If[AssociationQ[buildGPUPhysics],cells=Join[cells,{Cell["实际体积分与复端口的 CPU/GPU 对照","Section"],Cell["来源："<>buildGPUPhysics["run_id"]<>"；source_model="<>buildGPUPhysics["source_model"]<>"；execution_status="<>buildGPUPhysics["execution_status"],"Text"],Cell[BoxData[ToBoxes[Dataset[buildGPUPhysics["checks"]]]],"Output"],Cell[BoxData[ToBoxes[Dataset[KeyDrop[#,"currents"]&/@Lookup[buildGPUPhysics["data"],"cases",{}]]]],"Output"]},(Cell[BoxData[ToBoxes[#]],"Output"]&/@Values[buildGPUPhysics["figures"]])]]];
 If[stage=="peec",buildGPUScale=LitzView`OpenStage[stageRoot,"gpu_scale"];If[AssociationQ[buildGPUScale],cells=Join[cells,{Cell["PEEC 规模扩展与实际资源边界","Section"],Cell[buildGPUScale["run_id"]<>"；"<>buildGPUScale["execution_status"]<>"。CPU完整参考副本与显存限制分别记录；恢复案例保留前序来源。","Text"],Cell[BoxData[ToBoxes[Dataset[buildGPUScale["checks"]]]],"Output"],Cell[BoxData[ToBoxes[Dataset[KeyDrop[#,"currents"]&/@Lookup[buildGPUScale["data"],"cases",{}]]]],"Output"]}]]];
 If[stage=="voxel",buildVoxelScale=LitzView`OpenStage[stageRoot,"voxel_boundary"];
  If[AssociationQ[buildVoxelScale],cells=Join[cells,{Cell["空间细化与资源边界","Section"],Cell["来源："<>buildVoxelScale["run_id"]<>"；守恒和积分通过后仍需独立空间收敛。","Text"],Cell[BoxData[ToBoxes[Dataset[KeyTake[#,{"cells","face_flux_DOF","dimensions","loss_W","linear_residual","power_residual","assembly_seconds"}]&/@Lookup[buildVoxelScale["data"],"cases",{}]]]],"Output"]},(Cell[BoxData[ToBoxes[#]],"Output"]&/@Values[buildVoxelScale["figures"]])]]];
 If[stage=="fem3",Do[build3D=LitzView`OpenStage[stageRoot,route];If[AssociationQ[build3D],cells=Join[cells,{Cell["三维路线："<>route,"Subsection"],Cell[build3D["run_id"]<>"；"<>build3D["execution_status"],"Text"],Cell[BoxData[ToBoxes[Dataset[KeyTake[#,{"nodes","cell_volume","radial_relative_error","phi_error","gauge_sample_residual","execution_status","failure"}]&/@Lookup[build3D["data"],"cases",{}]]]],"Output"]}]],{route,{"fem3","fem3_ooc","fem3_iter"}}]];
 If[stage=="fem3",build3DAudit=LitzView`OpenStage[stageRoot,"fem3_audit"];If[AssociationQ[build3DAudit],cells=Join[cells,{Cell["完整 A-phi 电流后处理复核","Section"],Cell["J=-sigma V (u+grad psi)，包含实际求得的phi梯度。上面的历史径向误差使用phi_z=-1代理；物理电流的当前复核以本节为准。来源："<>build3DAudit["run_id"]<>"；原场来源："<>build3DAudit["data"]["source_run_id"],"Text"],Cell[BoxData[ToBoxes[Dataset[build3DAudit["checks"]]]],"Output"],Cell[BoxData[ToBoxes[Dataset[KeyDrop[#,"profile"]&/@build3DAudit["data"]["cases"]]]],"Output"]},(Cell[BoxData[ToBoxes[#]],"Output"]&/@Values[build3DAudit["figures"]])]]];
 cells=Join[cells,{Cell["独立重算与刷新","Section"],Cell["按钮在独立新内核启动本册重算，启动后可继续阅读；完成后重求第一单元刷新缓存。终端命令同上。","Text"],
 buildInput["Button[\"启动独立重算\",StartProcess[{\"powershell\",\"-NoProfile\",\"-File\",FileNameJoin[{litzRoot,\"src\",\"RunNotebookStage.ps1\"}],\"-Stage\",\""<>stage<>"\"}],Method->\"Queued\"]"]}];
 nb=Notebook[cells,StyleDefinitions->"Default.nb",WindowTitle->title,TaggingRules-><|"LitzStage"->stage,"HeadlessEvidence"->True,"FrontendValidation"->"pending"|>];
 path=FileNameJoin[{stageRoot,"notebooks",file}];Block[{$ContextPath={"System`"},$Context="Global`"},Put[nb,path]];read=Get[path];
 stageCheck["readback_"<>stage,If[MatchQ[read,_Notebook],0,1],0,"Notebook_expression_roundtrip"];
 stageCheck["Chinese_title_"<>stage,If[AnyTrue[ToCharacterCode[title],19968<=#<=40959&],0,1],0,"Notebook_UTF8_text"];
 figs=Length[Cases[read,_GraphicsBox|_Graphics3DBox,Infinity]];Print[file," graphics=",figs];
 <|"file"->file,"stage"->stage,"graphics_expressions"->figs,"input_cells"->Length[Cases[read,Cell[_,"Input",___],Infinity]],"source_run"->If[AssociationQ[r],r["run_id"],Null]|>
];
buildDefs={
 {"00_Environment_Check.nb","00 环境、资源与运行入口",{{"已验证环境",buildEnvironmentText},{"资源预算与性能","每次启动测量空闲资源，任务软预算48GiB主存/12GiB显存；主存2GiB、显存512MiB硬预留。资源曲线见各run_id。性能图区分编译、上传、回传与热运行。"},{"执行范围","无前端保存回读与原生交互前端求值分别验收。已有GPU运行链不会在本册自动安装或改配置。"}},"gpu"},
 {"01_Q1_Analytical.nb","01 单圆铜线：推导、复电流与损耗",{{"扩散方程","由 ∇×H=J、∇×E=−jωμH、J=σE 得 ∇⊥²Ez−jωμσEz=0。圆柱对称给 (1/r)d/dr(r dEz/dr)−κ²Ez=0，κ=(1+j)/δ，δ=√(2/ωμσ)。中心有限性排除 K0，Ez=C I0(κr)。"},{"电流归一化与内部阻抗","利用 ∫₀ᵃ r I0(κr)dr=a I1(κa)/κ，Jz=It κ I0(κr)/(2πa I1(κa))；Zint=Ez(a)/It=κ I0(κa)/(2πaσ I1(κa))。Joule损耗为 ∫|J|²/σ dA=|It|² Re Zint。"},{"工况和限制","Q1直径2mm，Jdc约6.366A/mm²，保留为原题校准。内部阻抗不包含外部回流电感。径向复J、相位、损耗密度与频率变化均为解析模型。50位CPU积分与12项回归是独立验收。"}},"analytic"},
 {"02_Q1_FEM_2D.nb","02 二维场解：解析对照与收敛",{{"模型和弱式","圆盘导体上求 −∇²u+jωμσa²u=0，边界u=1；二阶节点FEM。c=It/(σa²∫u dΩ)，Ez=cu，J=σcu。Zint=c/It；功率独立积分 σa²|c|²∫|u|²dΩ。"},{"网格和误差","至少三档网格，比较复径向场、Rac、功率及网格差。归一化电流与独立积分误差分别说明；二维机器精度FEM不冒充任意精度求解。"},{"空气与同轴回流支线","src/CoaxFEM.wl 求 u=jωAz，与源束和铜回流两个端电压梯度耦合；各绝缘股共享源端电压，仅施加总20A，回流−20A。分别保存束损、回流损、输入功率。缓存运行见 outputs/nb_coax_*，需独立网格、回流距离与外域敏感性。"}},"fem2"},
 {"03_Parallel_Strands.nb","03 共端场路：复电流、功率与被动性",{{"增广端口方程","Zi+e=V1，1ᵀi=It；解 [Z −1; 1ᵀ 0][i;V]=[−e;It]，不通过预设I/N证明均流。"},{"三种解释案例","同阻抗均流、不等电阻分流、非均匀独立感应电势。完整保留幅度与相位。损耗为 iᴴ[(Z+Zᴴ)/2]i；含e时功率检查包含 Re(iᴴe)。"},{"适用范围","解释案例矩阵是可核对的电路模型，实际物理矩阵来自独立FEM或PEEC缓存；二者分别标注。"}},"circuits"},
 {"04_Topology_And_Transposition.nb","04 轨迹、身份与 DTM/iDTM 换位",{{"几何定义","直束、单级旋转、八股子束加总束旋转的传统两级结构，以及小幅径向跨层调制候选。保留物理股ID、中心线、节距、相位、实际弧长、最小采样间隙与曲率。动画和间隙检查不替代场解。"},{"DTM方向和 iDTM","P把物理ID映射至截面槽位；Ztotal=ΣΔz PᵀZslotP。iDTM先构造所有层级断点并集，再在共同区间积分，避免权重或置换方向混淆。分段相加模型对同一组带权块的重排不敏感，这一限制也作为验收。"},{"实际铜和长度","Rdc=(ΣσAi/ℓi)⁻¹；铜体积ΣAiℓi。采样曲率和碰撞尚需连续细化验证，不能直接作为制造通过证据。"}},"geometry"},
 {"05_Equal_Copper_Comparison.nb","05 足铜初始化与等铜对照",{{"输入与公平性","640×0.1mm的实际名义铜面积5.026548mm²，等铜实心直径2.529822mm，Jdc约3.979A/mm²。只按相同实际名义铜面积比较，同时报告弧长与铜体积。"},{"计算层级","实心线为Bessel内部阻抗；本册初始束预测为各股孤立内部阻抗乘实际弧长后共端求解，遗漏互耦、邻近与过渡。完整640股同轴场解另见nb_coax运行，未收敛的大规模结果不用于结构排名。"},{"比较条件","绝对Rac、Rac/Rdc、每轴向米损耗、体积和复电流偏差一起报告。传统多级Litz保留强基线；候选优势需大于离散与模型不确定性。"}},"copper"},
 {"06_Computational_Boundary.nb","06 计算边界、资源曲线与失败证据",{{"边界分类","每条路线分别记录通过规模、首次失败或资源阻塞、实际容差与剩余不确定性。当前完成的最大尝试不自动称为设备最大能力。"},{"资源协同","CPU稀疏FEM保持稀疏；GPU CSR复数MVM、混合GMRES和分块远项核逐项CPU对照。线程和显存驻留性能用端到端测量选择；GPU基础通过不替代物理通过。"},{"长算与故障","两小时为进度汇报节点；持续保存检查点、日志与源码哈希，失败先保留原始消息。已有用户进程造成的低空闲量单列资源条件。"}},"boundary"},
 {"07_3D_FEM_Validation.nb","07 三维原生 A–φ FEM 独立验证",{{"耦合方程","μr=1时以Coulomb规范惩罚构成向量Laplacian；解三个A分量与φ，并显式使用 ∇·J=0。无量纲 u=jωA/V、ψ=φ/(aV)：−Δu+q(u+∇ψ)=0，Δψ+∇·u=0。"},{"当前校准边界","三维圆柱的边界A来自平移不变解析解，φ=−Vz。它验证耦合接口、规范与场误差；未知有限长度端场、螺旋空气界面和真实端接需要另外求解。失败误差保留在输出，不以三维网格图声明物理通过。"},{"推进条件","通过小模型的网格、规范、侧壁通量、截面电流与功率后才扩展真实有限长度及螺旋。若节点元路线受到curl/gauge/interface限制，明确记录并交Ansys复核。"}},"fem3"},
 {"08_PEEC_Validation.nb","08 纯 Wolfram PEEC：体积分与共端求解",{{"纵向体细丝","R采用体电阻积分；Lbc=μ0/(4π)∫∫wb(r)·wc(r′)/|r−r′|dVdV′。直体细丝的轴向双积分解析化，横截面自项用差分卷积和Duffy变换，近项使用体积分。无epsilon距离代替奇异自项。"},{"边界与对照","两端共同电位，求各体细丝复电流和总20A。有限长度部分感抗含外部电感，不能直接对比Q1内部X。报告截面离散、实际面积、长度与积分阶数。"},{"完整体素支线","09使用三个方向RT0面通量基函数，完整电阻重叠矩阵和体积分自/互感，保持法向连续、体内闭环和绝缘侧壁；逐项独立验收。"}},"peec"},
 {"09_Volume_Flux_PEEC.nb","09 三维体素面通量：闭环电流验证",{{"完整电流自由度","每体素使用三方向Raviart–Thomas RT0面通量基函数；共享面电流连续，侧壁面自由度剔除，逐体素散度为零。R含对面基函数交叉项，L含完整体积分。"},{"奇异积分","基函数乘积通过差分相关将六维积分化为三维；自项按八卦限与三个主轴共24个Duffy扇区计算，近/远项不使用距离软化。"},{"两个驱动案例","20A共端输运和1mT RMS均匀Bz驱动、零净输运。后者应出现横向体内闭环，外源有功与损耗闭合；不能用P/I²称为内禀电阻。当前矩形小模型是算法验证，圆线、弯线和真实端部交叉验证须另列。"}},"voxel"}
};
buildRecords=Map[buildBook@@#&,buildDefs];
buildIndex=Notebook[Join[{Cell["Litz 线：Wolfram 可视化计算总入口","Title"],Cell["按解析→二维场解→场路→几何换位→足铜比较→能力边界阅读。所有输出对应实际run_id；三维FEM与PEEC分册记录独立的通过、失败与待验证项。","Text"]},
 Map[Function[r,Cell[TextData[{r["file"],"   ",ButtonBox["打开",BaseStyle->"Hyperlink",ButtonData->{r["file"],None}]}],"Text"]],buildRecords],
 {Cell[TextData[{ButtonBox["GPU 基础运行链",BaseStyle->"Hyperlink",ButtonData->{"00_GPU_Runtime_Check.nb",None}]}],"Text"],Cell["运行命令、资源记录和最新证据索引见 docs/Notebook实施与运行.md。交互前端状态与无前端回放各有独立验收。","Text"]}],StyleDefinitions->"Default.nb"];
Block[{$ContextPath={"System`"},$Context="Global`"},Put[buildIndex,FileNameJoin[{stageRoot,"notebooks","Litz_Notebook_Index.nb"}]]];
Export[FileNameJoin[{stageDir,"notebook_manifest.json"}],buildRecords,"RawJSON"];
stageData=<|"source_model"->"Notebook_builder_from_actual_run_evidence","notebooks"->buildRecords,"assumptions"->"Authored Chinese native Wolfram notebooks; actual cached plots embedded with source run IDs. Builder does not evaluate heavy solvers. Headless replay and frontend GUI validation are independent."|>;


