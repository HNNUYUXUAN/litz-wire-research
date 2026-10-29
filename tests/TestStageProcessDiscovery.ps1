param([string]$RunId='closure_20261005_process_discovery_fixture_01')
$ErrorActionPreference='Stop'
$fixtureRoot=Split-Path -Parent $PSScriptRoot
$fixtureDir=Join-Path (Join-Path $fixtureRoot 'outputs') $RunId
if(Test-Path -LiteralPath $fixtureDir){throw "Fixture run already exists: $fixtureDir"}
[void](New-Item -ItemType Directory -Path (Join-Path $fixtureDir 'source_snapshot') -Force)
$fixtureResults=[System.Collections.Generic.List[object]]::new()
$fixtureSources=[System.Collections.Generic.List[object]]::new()
function Get-FixtureSHA([byte[]]$Bytes){
 $algorithm=[Security.Cryptography.SHA256]::Create()
 try{return ([BitConverter]::ToString($algorithm.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$algorithm.Dispose()}
}
foreach($fixtureRelative in @('src/RunNotebookStage.ps1','src/PreManuscriptClosure.py','tests/TestStageProcessDiscovery.ps1')){
 $fixturePath=Join-Path $fixtureRoot $fixtureRelative
 $fixtureBytes=[IO.File]::ReadAllBytes($fixturePath)
 $fixtureSHA=Get-FixtureSHA $fixtureBytes
 $fixtureSnapshot=Join-Path (Join-Path $fixtureDir 'source_snapshot') ([IO.Path]::GetFileName($fixtureRelative))
 [IO.File]::WriteAllBytes($fixtureSnapshot,$fixtureBytes)
 $fixtureSources.Add(@{path=$fixtureRelative;sha256=$fixtureSHA;frozen_path=('source_snapshot/'+[IO.Path]::GetFileName($fixtureRelative))})
 if($fixtureRelative -eq 'src/RunNotebookStage.ps1'){$fixtureStageSource=[Text.Encoding]::UTF8.GetString($fixtureBytes)}
}
function Get-SourceSegment([string]$Start,[string]$End){
 $startIndex=$fixtureStageSource.IndexOf($Start,[StringComparison]::Ordinal)
 if($startIndex -lt 0){throw "Missing start anchor: $Start"}
 $endIndex=$fixtureStageSource.IndexOf($End,$startIndex,[StringComparison]::Ordinal)
 if($endIndex -lt 0){throw "Missing end anchor: $End"}
 return [scriptblock]::Create($fixtureStageSource.Substring($startIndex,$endIndex-$startIndex))
}
$fixtureDiscovery=Get-SourceSegment '$stageByPid=@{};foreach' '  if($stageKernelId -and'
$fixtureCPU=Get-SourceSegment '  $stageMem=0;$stageCpu=0;$stageActive=@()' '  $stagePeak=[Math]::Max'
$fixtureFinally=Get-SourceSegment ' $stageRemaining=@();foreach' ' if($stageRemaining.Count)'
function New-FakeCim([int]$Id,[int]$Parent,[string]$Created){
 return [pscustomobject]@{ProcessId=$Id;ParentProcessId=$Parent;Name=('fixture_'+$Id+'.exe');CreationDate=[datetime]$Created}
}
function New-Owned([string]$Created){return @{name='fixture.exe';created=([datetime]$Created).ToUniversalTime().ToString('o')}}
function Add-Check([string]$Name,[bool]$Passed,$Evidence){
 $fixtureResults.Add(@{name=$Name;passed=$Passed;evidence=$Evidence})
}
function Get-Process{
 [CmdletBinding()]param([int]$Id)
 if($fixtureLive.ContainsKey($Id)){return $fixtureLive[$Id]}
 return $null
}
function Stop-Process{
 [CmdletBinding()]param([int]$Id)
 $fixtureStopped.Add($Id)
}
function New-FakeLive([int]$Id,[string]$Created,[int64]$Memory,[double]$CPU){
 return [pscustomobject]@{Id=$Id;StartTime=[datetime]$Created;WorkingSet64=$Memory;CPU=$CPU;ProcessName=('fixture_'+$Id)}
}
$fixtureT0='2026-10-05T01:00:00Z'
$fixtureT1='2026-10-05T01:00:01Z'
$fixtureT2='2026-10-05T01:00:02Z'
$fixtureT3='2026-10-05T01:00:03Z'
$fixtureT4='2026-10-05T01:00:04Z'

# Every executable segment below is extracted from the frozen production source.
$stageOwned=@{100=(New-Owned $fixtureT0)}
$stageOwnedHistory=[System.Collections.Generic.List[object]]::new()
$stageAll=@((New-FakeCim 300 200 $fixtureT2),(New-FakeCim 200 100 $fixtureT1),(New-FakeCim 100 1 $fixtureT0))
. $fixtureDiscovery
Add-Check 'unordered_live_descendants_discovered' ($stageOwned.ContainsKey(200) -and $stageOwned.ContainsKey(300)) @{owned_ids=@($stageOwned.Keys);history_count=$stageOwnedHistory.Count}
. $fixtureDiscovery
Add-Check 'same_identity_history_not_duplicated' ($stageOwnedHistory.Count -eq 2) @{history_count=$stageOwnedHistory.Count}

$stageOwned=@{100=(New-Owned $fixtureT0)}
$stageOwnedHistory=[System.Collections.Generic.List[object]]::new()
$stageAll=@((New-FakeCim 200 100 $fixtureT1))
. $fixtureDiscovery
Add-Check 'absent_historical_parent_excluded' (-not $stageOwned.ContainsKey(200)) @{owned_ids=@($stageOwned.Keys)}

$stageOwned=@{100=(New-Owned $fixtureT0)}
$stageOwnedHistory=[System.Collections.Generic.List[object]]::new()
$stageAll=@((New-FakeCim 100 1 $fixtureT2),(New-FakeCim 200 100 $fixtureT3))
. $fixtureDiscovery
Add-Check 'reused_live_parent_identity_excluded' (-not $stageOwned.ContainsKey(200)) @{owned_parent_created=$stageOwned[100].created;live_parent_created=$fixtureT2}

$stageOwned=@{100=(New-Owned $fixtureT2)}
$stageOwnedHistory=[System.Collections.Generic.List[object]]::new()
$stageAll=@((New-FakeCim 100 1 $fixtureT2),(New-FakeCim 200 100 $fixtureT1))
. $fixtureDiscovery
Add-Check 'child_born_before_current_parent_excluded' (-not $stageOwned.ContainsKey(200)) @{parent_created=$fixtureT2;child_created=$fixtureT1}

$stageOwned=@{100=(New-Owned $fixtureT0);200=(New-Owned $fixtureT1)}
$stageOwnedHistory=[System.Collections.Generic.List[object]]::new()
$stageOwnedHistory.Add(@{process_id=200;created_UTC=$stageOwned[200].created;name='fixture_old.exe'})
$stageAll=@((New-FakeCim 100 1 $fixtureT0),(New-FakeCim 200 100 $fixtureT3),(New-FakeCim 300 200 $fixtureT4))
. $fixtureDiscovery
Add-Check 'valid_descendant_pid_reuse_replaces_current_identity' ($stageOwned[200].created -eq ([datetime]$fixtureT3).ToUniversalTime().ToString('o') -and $stageOwned.ContainsKey(300)) @{current_created=$stageOwned[200].created;owned_ids=@($stageOwned.Keys)}
Add-Check 'pid_reuse_historical_identity_retained' (@($stageOwnedHistory|Where-Object process_id -eq 200).Count -eq 2) @{history=@($stageOwnedHistory)}

$stageOwned=@{100=(New-Owned $fixtureT0);200=(New-Owned $fixtureT1)}
$stageCPUById=@{}
$fixtureLive=@{100=(New-FakeLive 100 $fixtureT0 100 2);200=(New-FakeLive 200 $fixtureT1 200 5)}
. $fixtureCPU
Add-Check 'cpu_live_creation_matching_first_sample' ($stageMem -eq 300 -and $stageCpu -eq 7) @{memory=$stageMem;cpu=$stageCpu;keys=@($stageCPUById.Keys)}
$stageOwned[200]=New-Owned $fixtureT3
$fixtureLive[200]=New-FakeLive 200 $fixtureT3 300 11
. $fixtureCPU
Add-Check 'cpu_pid_and_creation_key_retains_two_lifetimes' ($stageMem -eq 400 -and $stageCpu -eq 18 -and $stageCPUById.Count -eq 3) @{memory=$stageMem;cpu=$stageCpu;keys=@($stageCPUById.Keys)}
$fixtureLive[200]=New-FakeLive 200 $fixtureT4 9999 9999
. $fixtureCPU
Add-Check 'reused_unowned_live_pid_excluded_from_current_sample' ($stageMem -eq 100 -and $stageCpu -eq 18 -and $stageActive.Count -eq 1 -and $stageActive[0] -eq 100) @{memory=$stageMem;cpu=$stageCpu;active=@($stageActive)}

$stageOwned=@{100=(New-Owned $fixtureT0);200=(New-Owned $fixtureT1);300=(New-Owned $fixtureT2)}
$fixtureLive=@{100=(New-FakeLive 100 $fixtureT0 100 2);200=(New-FakeLive 200 $fixtureT4 9999 9999)}
$fixtureStopped=[System.Collections.Generic.List[int]]::new()
. $fixtureFinally
Add-Check 'finally_stops_only_live_matching_owned_creation' ($fixtureStopped.Count -eq 1 -and $fixtureStopped[0] -eq 100 -and $stageRemaining.Count -eq 1 -and $stageRemaining[0] -eq 100) @{stopped=@($fixtureStopped);recorded_remaining=@($stageRemaining)}

foreach($fixtureSource in $fixtureSources){
 $currentSHA=(Get-FileHash -LiteralPath (Join-Path $fixtureRoot $fixtureSource.path) -Algorithm SHA256).Hash.ToLowerInvariant()
 Add-Check ('source_unchanged_during_fixture:'+ $fixtureSource.path) ($currentSHA -eq $fixtureSource.sha256) @{sha256=$currentSHA;frozen_sha256=$fixtureSource.sha256}
}
$fixtureFailed=@($fixtureResults|Where-Object {-not $_.passed})
$fixtureReport=@{run_id=$RunId;source_model='pure_PowerShell_fake_CIM_process_tree_contract';execution_status=if($fixtureFailed.Count){'failed'}else{'passed'};physical_acceptance_status='not_applicable';solver_started=$false;Wolfram_started=$false;Ansys_started=$false;process_commands_started=@();source_files=@($fixtureSources);checks=@($fixtureResults);check_count=$fixtureResults.Count;failed_check_count=$fixtureFailed.Count;scope='Exact discovery, CPU aggregation and finally segments extracted from source; Get-Process and Stop-Process mocked; no real process discovery, start or termination';timestamp_UTC=[datetime]::UtcNow.ToString('o')}
$fixtureReport|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $fixtureDir 'test_report.json') -Encoding utf8
@{run_id=$RunId;process_exit_code=if($fixtureFailed.Count){1}else{0};exit_origin='actual fixture outcome';finished_UTC=[datetime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $fixtureDir 'process_status.json') -Encoding utf8
Write-Output ("$RunId checks="+$fixtureResults.Count+" failed="+$fixtureFailed.Count)
if($fixtureFailed.Count){exit 1}
exit 0
