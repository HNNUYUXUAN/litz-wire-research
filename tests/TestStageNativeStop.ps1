param([string]$RunId='closure_20261005_native_stop_fixture_01',[string]$PythonPath)
$ErrorActionPreference='Stop'
$fixtureRoot=Split-Path -Parent $PSScriptRoot
if(-not $PythonPath){$PythonPath=(Get-Command python -ErrorAction Stop).Source}
$fixtureDir=Join-Path (Join-Path $fixtureRoot 'outputs') $RunId
if(Test-Path -LiteralPath $fixtureDir){throw "Fixture run already exists: $fixtureDir"}
[void](New-Item -ItemType Directory -Path (Join-Path $fixtureDir 'source_snapshot') -Force)
$fixtureResults=[System.Collections.Generic.List[object]]::new()
$fixtureChildren=[System.Collections.Generic.List[object]]::new()
$fixtureChildEvidence=[System.Collections.Generic.List[object]]::new()
$fixtureSources=[System.Collections.Generic.List[object]]::new()
$fixtureFailed=$false
$fixtureCompileStatus='not_run'
function Get-FixtureSHA([byte[]]$Bytes){
 $algorithm=[Security.Cryptography.SHA256]::Create()
 try{return ([BitConverter]::ToString($algorithm.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$algorithm.Dispose()}
}
foreach($fixtureRelative in @('src/RunNotebookStage.ps1','tests/TestStageNativeStop.ps1')){
 $fixturePath=Join-Path $fixtureRoot $fixtureRelative
 $fixtureBytes=[IO.File]::ReadAllBytes($fixturePath)
 $fixtureSHA=Get-FixtureSHA $fixtureBytes
 $fixtureSnapshot=Join-Path (Join-Path $fixtureDir 'source_snapshot') ([IO.Path]::GetFileName($fixtureRelative))
 [IO.File]::WriteAllBytes($fixtureSnapshot,$fixtureBytes)
 $fixtureSources.Add(@{path=$fixtureRelative;sha256=$fixtureSHA;frozen_path=('source_snapshot/'+[IO.Path]::GetFileName($fixtureRelative))})
 if($fixtureRelative -eq 'src/RunNotebookStage.ps1'){$fixtureStageSource=[Text.Encoding]::UTF8.GetString($fixtureBytes)}
}
@{run_id=$RunId;PythonPath=$PythonPath;sleep_command='import time; time.sleep(120)';maximum_children=3;wrong_creation_offset_seconds=1;accepted_CIM_rounding_microseconds=10;wait_after_stop_milliseconds=5000;solver_started=$false;Wolfram_started=$false;Ansys_started=$false;timestamp_UTC=[datetime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $fixtureDir 'parameters.json') -Encoding utf8
function Get-SourceSegment([string]$Start,[string]$End){
 $startIndex=$fixtureStageSource.IndexOf($Start,[StringComparison]::Ordinal)
 if($startIndex -lt 0){throw "Missing start anchor: $Start"}
 $endIndex=$fixtureStageSource.IndexOf($End,$startIndex,[StringComparison]::Ordinal)
 if($endIndex -lt 0){throw "Missing end anchor: $End"}
 return [scriptblock]::Create($fixtureStageSource.Substring($startIndex,$endIndex-$startIndex))
}
function Add-Check([string]$Name,[bool]$Passed,$Evidence){$fixtureResults.Add(@{name=$Name;passed=$Passed;evidence=$Evidence})}
function Start-FixtureChild([string]$Label){
 $child=Start-Process -FilePath $PythonPath -ArgumentList @('-c','"import time; time.sleep(120)"') -WorkingDirectory $fixtureRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $fixtureDir ($Label+'_stdout.txt')) -RedirectStandardError (Join-Path $fixtureDir ($Label+'_stderr.txt'))
 $originalHandle=$child.Handle
 $nativeCreated=$child.StartTime.ToUniversalTime()
 $cim=Get-CimInstance Win32_Process -Filter ("ProcessId = "+$child.Id)
 if(-not $cim){throw "Owned child not visible in CIM: $($child.Id)"}
 $evidence=@{label=$Label;process_id=$child.Id;native_StartTime_UTC=$nativeCreated.ToString('o');CIM_created_UTC=$cim.CreationDate.ToUniversalTime().ToString('o');original_handle_retained=$true;actual_exit_code=$null;started_command=@($PythonPath,'-c','import time; time.sleep(120)')}
 $record=@{process=$child;handle=$originalHandle;created=$nativeCreated;CIM_created=$cim.CreationDate.ToUniversalTime();evidence=$evidence}
 $fixtureChildren.Add($record)
 $fixtureChildEvidence.Add($evidence)
 return $record
}
try{
 # Compile only the frozen source's actual native helper and its PS wrapper.
 $fixtureHelper=Get-SourceSegment "if(-not('LitzNativeMemory' -as [type])){" '$stageRoot=Split-Path'
 . $fixtureHelper
 $fixtureCompileStatus='passed'
 Add-Check 'actual_source_native_helper_compiles' $true @{type='LitzNativeMemory';source_sha256=$fixtureSources[0].sha256}
 $fixtureFinally=Get-SourceSegment ' $stageRemaining=@();foreach' ' if($stageRemaining.Count)'

 $first=Start-FixtureChild 'direct_contract'
 $wrongResult=[LitzNativeMemory]::StopOwned($first.process.Id,$first.CIM_created.AddSeconds(1).Ticks)
 $first.process.Refresh()
 Add-Check 'wrong_creation_refused_and_child_alive' (-not $wrongResult -and -not $first.process.HasExited) @{StopOwned_return=$wrongResult;process_id=$first.process.Id;HasExited=$first.process.HasExited;wrong_created_UTC=$first.CIM_created.AddSeconds(1).ToString('o')}
 $correctResult=[LitzNativeMemory]::StopOwned($first.process.Id,$first.CIM_created.Ticks)
 $didExit=$first.process.WaitForExit(5000)
 $firstExit=if($didExit){[LitzNativeMemory]::ExitCode($first.handle)}else{$null}
 $first.evidence.actual_exit_code=$firstExit
 Add-Check 'correct_CIM_creation_accepted' $correctResult @{StopOwned_return=$correctResult;expected_created_UTC=$first.CIM_created.ToString('o');process_id=$first.process.Id}
 Add-Check 'actual_exit137_from_original_retained_handle' ($didExit -and $firstExit -eq 137) @{WaitForExit=$didExit;actual_exit_code=$firstExit;exit_origin='GetExitCodeProcess on original retained Start-Process Handle'}

 $second=Start-FixtureChild 'finally_matching'
 $third=Start-FixtureChild 'finally_wrong_identity'
 $stageOwned=@{}
 $stageOwned[$second.process.Id]=@{created=$second.CIM_created.ToString('o');name='python.exe'}
 $stageOwned[$third.process.Id]=@{created=$third.CIM_created.AddSeconds(1).ToString('o');name='python.exe'}
 . $fixtureFinally
 $secondDidExit=$second.process.WaitForExit(5000)
 $secondExit=if($secondDidExit){[LitzNativeMemory]::ExitCode($second.handle)}else{$null}
 $second.evidence.actual_exit_code=$secondExit
 $third.process.Refresh()
 Add-Check 'actual_finally_matching_identity_exit137' ($secondDidExit -and $secondExit -eq 137 -and $stageRemaining.Count -eq 1 -and $stageRemaining[0] -eq $second.process.Id) @{recorded_remaining=@($stageRemaining);actual_exit_code=$secondExit;exit_origin='GetExitCodeProcess on original retained Start-Process Handle'}
 Add-Check 'actual_finally_wrong_identity_child_survives' (-not $third.process.HasExited) @{process_id=$third.process.Id;HasExited=$third.process.HasExited;recorded_wrong_created_UTC=$stageOwned[$third.process.Id].created}
}catch{
 $fixtureFailed=$true
 $fixtureError=$_.Exception.ToString()
 $fixtureError|Set-Content -LiteralPath (Join-Path $fixtureDir 'fixture_error.txt') -Encoding utf8
 Add-Check 'fixture_exception' $false @{error=$fixtureError;compile_status=$fixtureCompileStatus}
}finally{
 # Only these fixture-created children, their saved creation identity and original
 # retained process handles are used. No PID-only or broad-name cleanup occurs.
 foreach($record in $fixtureChildren){
  try{
   $record.process.Refresh()
   $cleanupStop=$null
   if(-not $record.process.HasExited){$cleanupStop=[LitzNativeMemory]::StopOwned($record.process.Id,$record.created.Ticks)}
   $recordDidExit=$record.process.WaitForExit(5000)
   $recordExit=if($recordDidExit){[LitzNativeMemory]::ExitCode($record.handle)}else{$null}
   $record.evidence.actual_exit_code=$recordExit
   $record.evidence.cleanup_StopOwned_return=$cleanupStop
   $record.evidence.finally_cleanup_exit_origin='GetExitCodeProcess on original retained Start-Process Handle'
   Add-Check ('owned_fixture_cleanup:'+ $record.evidence.label) ($recordDidExit -and $recordExit -eq 137) @{process_id=$record.process.Id;actual_exit_code=$recordExit;cleanup_StopOwned_return=$cleanupStop}
  }catch{
   $fixtureFailed=$true
   Add-Check ('owned_fixture_cleanup:'+ $record.evidence.label) $false @{process_id=$record.process.Id;error=$_.Exception.ToString()}
  }
  $record.process.Dispose()
 }
}
foreach($fixtureSource in $fixtureSources){
 $currentSHA=(Get-FileHash -LiteralPath (Join-Path $fixtureRoot $fixtureSource.path) -Algorithm SHA256).Hash.ToLowerInvariant()
 Add-Check ('source_unchanged_during_fixture:'+ $fixtureSource.path) ($currentSHA -eq $fixtureSource.sha256) @{sha256=$currentSHA;frozen_sha256=$fixtureSource.sha256}
}
$failedChecks=@($fixtureResults|Where-Object {-not $_.passed})
$fixtureReport=@{run_id=$RunId;source_model='native_same_handle_process_termination_contract';execution_status=if($fixtureFailed -or $failedChecks.Count){'failed'}else{'passed'};physical_acceptance_status='not_applicable';solver_started=$false;Wolfram_started=$false;Ansys_started=$false;compile_status=$fixtureCompileStatus;source_files=@($fixtureSources);parameters_file='parameters.json';checks=@($fixtureResults);check_count=$fixtureResults.Count;failed_check_count=$failedChecks.Count;owned_fixture_processes=@($fixtureChildEvidence);scope='Only three self-owned Python sleep subprocesses; actual frozen native StopOwned and actual source finally segment; actual child exit codes read via original retained handles';timestamp_UTC=[datetime]::UtcNow.ToString('o')}
$fixtureReport|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $fixtureDir 'test_report.json') -Encoding utf8
Write-Output ("$RunId checks="+$fixtureResults.Count+" failed="+$failedChecks.Count+" compile="+$fixtureCompileStatus)
if($fixtureFailed -or $failedChecks.Count){exit 1}
exit 0
