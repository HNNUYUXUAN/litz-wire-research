param([string]$RunId='rerun_20261005_summary')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$out=Join-Path $root ('outputs/'+$RunId)
if(Test-Path -LiteralPath $out){throw 'Summary run already exists'}
New-Item -ItemType Directory -Path $out | Out-Null
$rows=@()
$dirs=Get-ChildItem (Join-Path $root 'outputs') -Directory | Where-Object {$_.Name -match '^(full_20261005_|rerun_20261005_(analytic|gpu)$|ansys_20261005_)'} | Sort-Object Name
foreach($dir in $dirs){
 $resultPath=Join-Path $dir.FullName 'results.json'
 $r=if(Test-Path $resultPath){Get-Content -Raw $resultPath | ConvertFrom-Json}else{$null}
 $reportPath=Join-Path $dir.FullName 'test_report.json'
 $report=if(Test-Path $reportPath){Get-Content -Raw $reportPath | ConvertFrom-Json}else{$null}
 $processPath=Join-Path $dir.FullName 'process_status.json'
 $process=if(Test-Path $processPath){Get-Content -Raw $processPath | ConvertFrom-Json}else{$null}
 $resourcePath=Join-Path $dir.FullName 'resource_stop.json'
 $stop=if(Test-Path $resourcePath){Get-Content -Raw $resourcePath | ConvertFrom-Json}else{$null}
 $failed=@($report.tests | Where-Object {$_.execution_status -eq 'failed'}).Count
 $passed=@($report.tests | Where-Object {$_.execution_status -eq 'passed'}).Count
 $status='not_run'
 if($stop -or $r.execution_status -eq 'blocked_environment_resource_budget'){$status='blocked_environment_resource_budget'}
 elseif($failed -gt 0 -or $r.execution_status -match '^failed'){$status='failed_numerical'}
 elseif($r.execution_status -in @('passed','executed','constructed')){$status='passed'}
 if($dir.Name -eq 'full_20261005_fem3_ooc'){$status='blocked_environment_resource_budget'}
 if($dir.Name -eq 'full_20261005_replay_00_GPU_Runtime_Check'){$status='blocked_environment_resource_budget'}
 $rows += [pscustomobject]@{run_id=$dir.Name;stage=$r.stage;status=$status;raw_execution_status=$r.execution_status;passed_checks=$passed;failed_checks=$failed;process_exit_code=$process.process_exit_code;elapsed_seconds=$r.elapsed_seconds;source_model=$r.source_model;resource_stop=$stop;evidence=('outputs/'+$dir.Name+'/results.json')}
}
$summary=[ordered]@{run_id=$RunId;timestamp=(Get-Date -Format o);source_head=(& git -C $root rev-parse HEAD);runs=$rows;scope_note='passed applies to the checks of each model only. Coarse scale execution, Notebook replay and CAD handoff are not finite-end 3D physical convergence.'}
$summary | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $out 'summary.json') -Encoding utf8
$lines=@('# 2026-10-05 高性能设备复跑验收','','源提交 e600cafead7645fd7be9cc8edd59af7b9ce47618；保留历史目录与本机解析短测。','# 结论','','640 股二维 FEM：网格变化 0.0119%，回流距离变化 0.000495%，外域变化 0.000270%，通过本模型门槛。','9856 filaments GPU/CPU 矩阵、复电流、功率对照通过；20108 filaments 触发 2 GiB RAM 预留。','3456 体素完成（约 43.5 分钟），残差/功率/互易性通过，空间变化 3.8487% > 1%，failed_numerical。更细网格按致密存储平方增长，当前主存没有安全预算。','三维 A–φ 前两档完成，电势与规范不通过；第三档直接分解触发内存保护，OOC 报内存不足，Krylov 100 次未收敛。','Ansys Student 7/640 股共同电压赋值被拒绝；7 股 crosslayer/24 股 multilevel STL 导入明确被 Student 禁止。均流、曲线有限端场、Ansys 网格与功率验收未完成。','Notebook 回放通过表示保存输入执行成功，不证明其中失败路线已收敛。GPU 册通用入口目录冲突已留证，专用入口通过。','handoff 2664 检查通过，但 CLI 返回 1，生命周期不一致保留。','没有热模型，不作热合格或完整真实 Litz 结构排名。','','| 运行 | 分类 | 检查通过/失败 | CLI |','|---|---|---:|---:|')
foreach($row in $rows){$lines += ('| ['+$row.run_id+'](../'+$row.run_id+'/results.json) | '+$row.status+' | '+$row.passed_checks+'/'+$row.failed_checks+' | '+$row.process_exit_code+' |')}
$lines | Set-Content (Join-Path $out '验收报告.md') -Encoding utf8
$index=Join-Path $root 'docs/总控/当前运行索引.md'
$old=Get-Content -Raw $index
('# 当前运行索引 — 2026-10-05 高性能设备复跑'+"`n`n"+'最新结果：[验收报告](../../outputs/'+$RunId+'/验收报告.md)；[机器可读运行分类](../../outputs/'+$RunId+'/summary.json)。分类以本次检查与资源停止证据为准，历史表保留在下方。'+"`n`n"+$old) | Set-Content $index -Encoding utf8
