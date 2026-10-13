gpuBuildRoot = NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
gpuBuildID = Environment["LITZ_GPU_VERIFIED_RUN_ID"];
If[!StringQ[gpuBuildID] || !StringMatchQ[gpuBuildID, RegularExpression["[A-Za-z0-9_-]+"]], Exit[2]];
gpuBuildSummary = Import[FileNameJoin[{gpuBuildRoot, "outputs", gpuBuildID, "results.json"}], "RawJSON"];
gpuBuildReport = Import[FileNameJoin[{gpuBuildRoot, "outputs", gpuBuildID, "test_report.json"}], "RawJSON"];
If[gpuBuildSummary["execution_status"] =!= "passed", Exit[1]];
gpuBuildCode = "Get[FileNameJoin[{DirectoryName[NotebookDirectory[]], \"src\", \"RunGPUValidation.wls\"}]]";
gpuBuildBoxes = ToBoxes[ToExpression[gpuBuildCode, InputForm, HoldForm]] /. TagBox[boxes_, HoldForm, ___] :> boxes;
gpuBuildFile = FileNameJoin[{gpuBuildRoot, "notebooks", "00_GPU_Runtime_Check.nb"}];
gpuBuildNotebook = Notebook[{
  Cell["00 Wolfram NVIDIA GPU 运行链验证", "Title"],
  Cell["本机：Wolfram 15.0.1、RTX 4060 Laptop GPU（计算能力8.9，约8 GiB）、NVIDIA驱动610.88、WolframGPUSDK 15.0.3（CUDA 12.8.1）。SDK已获用户授权从Wolfram官方源安装。", "Text"],
  Cell["模型与输入：本Notebook只验收GPU运行环境和合成数值任务。固定随机种子20261004，512阶双精度矩阵乘法，128阶复数双精度线性方程已知解，4096点复数FFT，以及4099点双精度自定义核函数。没有电磁场、热模型或Litz结构排名。", "Text"],
  Cell["公式与验收：误差=||GPU结果−CPU/已知解||₂/max(||参考||₂,最小机器正数)，容差10^-10；自定义核函数y=2x+1，容差10^-12，并检查末尾非整块元素。线性解另外验证Ax=b。FFT与CPU采用相同归一化和符号。", "Text"],
  Cell["以下输出来自新进程实际运行。输入会创建新的outputs/run_id，保存版本、参数、日志、每项误差、测试、用时和源码哈希。不自动安装组件。已有run_id拒绝覆盖。", "Text"],
  Cell[BoxData[gpuBuildBoxes], "Input"],
  Cell[BoxData[ToBoxes[gpuBuildSummary]], "Output"],
  Cell[BoxData[ToBoxes[gpuBuildReport]], "Output"],
  Cell["适用范围与限制：双精度矩阵使用GPUArray或CUDALink；FFT使用已验证的CUDALink CUDAFourier/CUDAInverseFourier路径。本机GPUArray复数Fourier触发CUDAArrays_Fourier.dll访问冲突，失败证据在outputs/20261004_gpu_validation_01。自定义核函数使用Wolfram Language编译到CUDA。壁钟用时包含Normal同步/回传，小任务GPU未必更快。交互前端求值另行核验；保存与无前端执行不等同前端验证。", "Text"],
  Cell["运行证据：outputs/" <> gpuBuildID <> "/results.json、test_report.json、acceptance_report.json。操作说明：docs/Wolfram_GPU运行链.md。", "Text"]
}, StyleDefinitions -> "Default.nb"];
Put[gpuBuildNotebook, gpuBuildFile];
If[!MatchQ[Get[gpuBuildFile], _Notebook], Exit[1]];
Print["GPU notebook saved and read back: notebooks/00_GPU_Runtime_Check.nb"];
