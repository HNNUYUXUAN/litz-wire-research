If[!DirectoryQ[FileNameJoin[{stageRoot,"notebooks"}]],CreateDirectory[FileNameJoin[{stageRoot,"notebooks"}]]];
pnIndex=Import[FileNameJoin[{stageRoot,"docs","总控","当前运行索引.json"}],"RawJSON"];
pnRows=KeyValueMap[Function[{key,value},<|"route"->key,"run_id"->value["selected_run_id"],
 "status"->Lookup[value,"physical_acceptance_status","see_individual_tests"]|>],pnIndex["routes"]];
pnInput[str_]:=Cell[BoxData[ToBoxes[ToExpression[str,InputForm,HoldForm]]],"Input"];
pnNb=Notebook[{
 Cell["10 当前设备三维攻关与实际证据","Title"],
 Cell["所有运行按明确run_id读取。解析、制造解、几何筛选、数值守恒与真实三维结构精度分别验收。制造解通过不能证明导体端部或绝缘接口正确；几何公平不能证明共端电磁均流。","Text"],
 Cell["有效清单与最新失败","Section"],Cell[BoxData[ToBoxes[Dataset[pnRows]]],"Output"],
 pnInput["litzRoot=DirectoryName[NotebookDirectory[]]; index=Import[FileNameJoin[{litzRoot,\"docs\",\"总控\",\"当前运行索引.json\"}],\"RawJSON\"]; Dataset[index[\"routes\"]]"],
 Cell["固定物理约定","Section"],Cell["SI；exp(jωt)；RMS；σ=5.8×10^7 S/m；200kHz；20A；20℃。股线侧壁绝缘、端部共电势，总流约束自求分流。报告轴向长度下Rdc、Rac、损耗、弧长和铜体积。无热模型和实验验证。","Text"],
 Cell["新内核复跑入口","Section"],
 pnInput["StartProcess[{\"powershell\",\"-NoProfile\",\"-File\",FileNameJoin[{litzRoot,\"src\",\"RunNotebookStage.ps1\"}],\"-Stage\",\"fem3_mms\"}]"],
 pnInput["StartProcess[{\"powershell\",\"-NoProfile\",\"-File\",FileNameJoin[{litzRoot,\"src\",\"RunNotebookStage.ps1\"}],\"-Stage\",\"voxel_operator_tests\"}]"],
 Cell["重型计算应串行启动；具体模型、失败与参数见对应outputs/run_id中的results、test_report、resource_curve与source_snapshot。Python/AEDT入口见src/RunAnsysValidation.ps1。此Notebook保存回读验收不表示图形前端本轮交互求值已通过。","Text"]},StyleDefinitions->"Default.nb"];
pnPath=FileNameJoin[{stageRoot,"notebooks","10_3D_Progress_And_Evidence.nb"}];
Block[{$ContextPath={"System`"},$Context="Global`"},Put[pnNb,pnPath]];
stageCheck["progress_Notebook_readback",If[MatchQ[Get[pnPath],_Notebook],0,1],0,"Notebook_expression_roundtrip"];
stageData=<|"source_model"->"explicit_run_index_Notebook","index_snapshot"->pnIndex,"assumptions"->"Notebook source and cached status only; GUI replay not run."|>;
