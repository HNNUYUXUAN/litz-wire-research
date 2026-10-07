param([string]$BoundaryRun='nb_boundary_20261004_220927_453')
$ErrorActionPreference='Stop'
$auditRoot=Split-Path -Parent $PSScriptRoot
$auditId='delivery_audit_'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff')
$auditDir=Join-Path $auditRoot ('outputs/'+$auditId)
New-Item -ItemType Directory -Path $auditDir | Out-Null
$auditRoutes=Get-Content -Raw (Join-Path $auditRoot "outputs/$BoundaryRun/route_status.json") | ConvertFrom-Json
$auditRows=[Collections.Generic.List[object]]::new()
$auditRuns=@($auditRoutes.run_id)+@('gpu_20261004_204207_778')
foreach($auditRun in $auditRuns){
 $auditManifest=Get-Content -Raw (Join-Path $auditRoot "outputs/$auditRun/run_manifest.json") | ConvertFrom-Json
 foreach($auditSource in $auditManifest.sources){
  $auditFile=Join-Path $auditRoot ("outputs/$auditRun/source_snapshot/"+$auditSource.path)
  if($auditRun -eq 'gpu_20261004_204207_778'){$auditFile=Join-Path $auditRoot ("outputs/$auditRun/source_snapshot/"+(Split-Path -Leaf $auditSource.path))}
  $auditHash=(Get-FileHash -LiteralPath $auditFile -Algorithm SHA256).Hash.ToLowerInvariant()
  $auditRows.Add([pscustomobject]@{run_id=$auditRun;path=$auditSource.path;matches=($auditHash -eq $auditSource.sha256.ToLowerInvariant())})
 }
}
$auditRows | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $auditDir 'source_hashes.json') -Encoding utf8
$auditPSRows=foreach($auditFile in Get-ChildItem (Join-Path $auditRoot 'src') -Filter '*.ps1'){
 $auditTokens=$null;$auditErrors=$null
 [void][Management.Automation.Language.Parser]::ParseFile($auditFile.FullName,[ref]$auditTokens,[ref]$auditErrors)
 [pscustomobject]@{path=$auditFile.Name;valid=($auditErrors.Count -eq 0);errors=@($auditErrors.Message)}
}
$auditPSRows | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $auditDir 'powershell_syntax.json') -Encoding utf8
$auditWLS=Get-Content -Raw (Join-Path $auditRoot 'outputs/final_implementation_audit_20261004_212411_872/source_syntax.wls')
[IO.File]::WriteAllText((Join-Path $auditDir 'source_syntax.wls'),$auditWLS,[Text.UTF8Encoding]::new($false))
& wolframscript -file (Join-Path $auditDir 'source_syntax.wls') | Set-Content (Join-Path $auditDir 'source_syntax_log.txt') -Encoding utf8
$auditWLExit=$LASTEXITCODE
$auditSummary=@{run_id=$auditId;archived_source_count=$auditRows.Count;hash_mismatches=@($auditRows | Where-Object {-not $_.matches}).Count;powershell_invalid=@($auditPSRows | Where-Object {-not $_.valid}).Count;wolfram_syntax_process_exit=$auditWLExit;boundary_run=$BoundaryRun}
$auditSummary | ConvertTo-Json | Set-Content (Join-Path $auditDir 'summary.json') -Encoding utf8
$auditRegistry=Join-Path $auditRoot 'docs/总控/当前运行索引.json'
$auditRoutes | ConvertTo-Json -Depth 8 | Set-Content $auditRegistry -Encoding utf8
$auditLines=@('# 当前运行索引','','按阶段精确匹配的最新归档；模型验收与CLI退出分别报告。空退出码表示未取得正常退出证据。历史失败和源码快照均保留。','',"边界来源：[$BoundaryRun](../../outputs/$BoundaryRun/route_status.json)",'','| 路线 | 最新运行 | 检查通过/失败 | CLI退出 |','|---|---|---:|---:|')
foreach($auditRoute in $auditRoutes){$auditLines+=('| '+$auditRoute.route+' | ['+$auditRoute.run_id+'](../../outputs/'+$auditRoute.run_id+'/results.json) | '+$auditRoute.passed_checks+'/'+$auditRoute.failed_checks+' | '+$auditRoute.process_exit_code+' |')}
$auditLines+=@('','这些检查数量对应各路线的具体测试，不代表已解决其余物理适用范围。640股细网格、5,024自由度纵向PEEC通过；三维A–φ的电势/规范与完整RT0空间细化尚未通过。结构性能排名、真实端接螺旋场与Ansys实际求解待接续。','',"最终源码核验：[$auditId](../../outputs/$auditId/summary.json)",'','全系列保存输入新内核复跑：[11册报告](../../outputs/delivery_replay_series_20261004_214242_811/series_process_report.json)。GPU册另见[gpu基线验收](../../outputs/gpu_20261004_204207_778/acceptance_report.json)。')
[IO.File]::WriteAllText((Join-Path $auditRoot 'docs/总控/当前运行索引.md'),(($auditLines -join "`n")+"`n"),[Text.UTF8Encoding]::new($false))
$auditSummary | ConvertTo-Json
if($auditSummary.hash_mismatches -or $auditSummary.powershell_invalid -or $auditWLExit){exit 1}
