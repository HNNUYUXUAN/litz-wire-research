param([ValidateSet('analytic','fem2','coax','coax640','scale','circuits','geometry','copper','peec','voxel','voxel_scale','voxel_boundary','voxel_operator','voxel_operator_tests','voxel_operator_quadrature','fem3','fem3_mms','fem3_cylinder','fem3_audit','fem3_ooc','fem3_iter','frontend','gpu','gpu_physics','gpu_scale','peec_equivalence','cpu_workers','boundary','build','replay','handoff','delivery_data','progress_notebook','closure_peec','closure_rt0','closure_geometry','closure_fem3_diagnostics','closure_gpu','closure_gpu_recovery','closure_peec_tests','closure_rt0_parallel_tests','closure_frozen_verify','closure_rt0_collect')][string]$Stage='analytic',[string]$RunId,[string]$Notebook)
$ErrorActionPreference='Stop'
if($Stage -eq 'replay' -and $Notebook -eq '00_GPU_Runtime_Check.nb'){
 & (Join-Path $PSScriptRoot 'RunGPUValidation.ps1') -RunId $RunId -NotebookInput
 exit $LASTEXITCODE
}
if(-not('LitzNativeMemory' -as [type])){
 Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class LitzNativeMemory {
 [StructLayout(LayoutKind.Sequential)] private struct State { public uint length,load; public ulong total,available,pageTotal,pageAvailable,virtualTotal,virtualAvailable,extended; }
 [StructLayout(LayoutKind.Sequential)] private struct Stamp { public uint low,high; }
 [DllImport("kernel32.dll",SetLastError=true)] private static extern bool GlobalMemoryStatusEx(ref State state);
 [DllImport("kernel32.dll",SetLastError=true)] private static extern bool GetExitCodeProcess(IntPtr handle,out uint code);
 [DllImport("kernel32.dll",SetLastError=true)] private static extern IntPtr OpenProcess(uint access,bool inherit,int id);
 [DllImport("kernel32.dll",SetLastError=true)] private static extern bool GetProcessTimes(IntPtr handle,out Stamp created,out Stamp exited,out Stamp kernel,out Stamp user);
 [DllImport("kernel32.dll",SetLastError=true)] private static extern bool TerminateProcess(IntPtr handle,uint code);
 [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
 public static long Available(){ State s=new State();s.length=(uint)Marshal.SizeOf(typeof(State));if(!GlobalMemoryStatusEx(ref s))throw new Exception("GlobalMemoryStatusEx failed");return (long)s.available; }
 public static int ExitCode(IntPtr handle){uint code;if(!GetExitCodeProcess(handle,out code))throw new Exception("GetExitCodeProcess failed");if(code==259)throw new Exception("Process is still running");return unchecked((int)code);}
 public static bool StopOwned(int id,long expectedUtcTicks){
  IntPtr handle=OpenProcess(0x1001,false,id);if(handle==IntPtr.Zero)return false;
  try {Stamp c,e,k,u;if(!GetProcessTimes(handle,out c,out e,out k,out u))return false;
   long fileTime=((long)c.high<<32)|c.low;long actual=DateTime.FromFileTimeUtc(fileTime).Ticks;
   // CIM records microseconds. Bind creation and termination to the same OS
   // handle; tolerate only its rounding, never reopen the PID after checking.
   if(Math.Abs(actual-expectedUtcTicks)>100)return false;
   return TerminateProcess(handle,137);
  } finally {CloseHandle(handle);}
 }
}
'@
}
function Stop-LitzOwnedProcess([int]$ownedTargetId,[string]$ownedCreatedUTC){
 if($ownedCreatedUTC){[void][LitzNativeMemory]::StopOwned($ownedTargetId,([datetime]$ownedCreatedUTC).ToUniversalTime().Ticks)}
}
$stageRoot=Split-Path -Parent $PSScriptRoot
if(-not $RunId){$RunId='nb_'+$Stage+'_'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff')}
if($RunId -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid run ID'}
$stageDir=Join-Path $stageRoot ('outputs/'+$RunId)
if(Test-Path -LiteralPath $stageDir){throw 'Run already exists'}
New-Item -ItemType Directory -Path $stageDir | Out-Null
$stageFreeBytes=[LitzNativeMemory]::Available()
$stageReserve=8GB;$stageAllowance=24GB;$stagePreflightReserve=8GB;$stageVRAMReserveMiB=1024
if($env:LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES){$stageReserve=[int64]$env:LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES;$stagePreflightReserve=$stageReserve}
if($env:LITZ_CLOSURE_MAX_WORKING_BYTES){$stageAllowance=[int64]$env:LITZ_CLOSURE_MAX_WORKING_BYTES}
if($env:LITZ_CLOSURE_MIN_FREE_VRAM_MIB){$stageVRAMReserveMiB=[double]$env:LITZ_CLOSURE_MIN_FREE_VRAM_MIB}
$stageBudget=[Math]::Max([int64]0,[Math]::Min([int64]$stageAllowance,[int64]($stageFreeBytes-$stagePreflightReserve)))
@{run_id=$RunId;free_memory_bytes=$stageFreeBytes;working_budget_bytes=$stageBudget;system_reserve_bytes=$stageReserve;requested_profile=$env:LITZ_CLOSURE_PROFILE;timestamp=(Get-Date -Format o)} | ConvertTo-Json | Set-Content (Join-Path $stageDir 'resource_budget.json') -Encoding utf8
$stageOld=@{id=$env:LITZ_RUN_ID;stage=$env:LITZ_STAGE;nb=$env:LITZ_NOTEBOOK;budget=$env:LITZ_RAM_BUDGET}
$stageGpuMutex=$null;$stageGpuHeld=$false
try{
 if($Stage -in @('gpu','gpu_physics','gpu_scale','closure_gpu') -or ($Stage -eq 'replay' -and $Notebook -eq '00_GPU_Runtime_Check.nb')){
  $stageGpuMutex=[Threading.Mutex]::new($false,'Local\LitzWolframGPUQueue')
  @{state='waiting';owner_pid=$PID;timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'gpu_queue.json') -Encoding utf8
  while(-not $stageGpuHeld){try{$stageGpuHeld=$stageGpuMutex.WaitOne(1000)}catch [Threading.AbandonedMutexException]{$stageGpuHeld=$true}}
  @{state='acquired';owner_pid=$PID;timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'gpu_queue.json') -Encoding utf8
  $stageBudget=[Math]::Max([int64]0,[Math]::Min([int64]$stageAllowance,[int64]([LitzNativeMemory]::Available()-$stagePreflightReserve)))
 }
 $env:LITZ_RUN_ID=$RunId;$env:LITZ_STAGE=$Stage;$env:LITZ_NOTEBOOK=$Notebook;$env:LITZ_RAM_BUDGET=[string]$stageBudget
 $stageWS=if($env:LITZ_WOLFRAMSCRIPT){$env:LITZ_WOLFRAMSCRIPT}else{(Get-Command wolframscript).Source}
 $stageProcess=Start-Process -FilePath $stageWS -ArgumentList @('-file',('"'+(Join-Path $PSScriptRoot 'RunNotebookStage.wls')+'"')) -WorkingDirectory $stageRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $stageDir 'run_log.txt') -RedirectStandardError (Join-Path $stageDir 'stderr.txt')
 $stageProcessHandle=$stageProcess.Handle
 $stageRows=[System.Collections.Generic.List[object]]::new()
 $stageOwned=@{};$stageOwnedHistory=[System.Collections.Generic.List[object]]::new();$stageCPUById=@{};$stageClock=[Diagnostics.Stopwatch]::StartNew();[int64]$stagePeak=0
 $stageOwned[$stageProcess.Id]=@{name=$stageProcess.ProcessName;created=$stageProcess.StartTime.ToUniversalTime().ToString('o')}
 $stageOwnedHistory.Add(@{process_id=$stageProcess.Id;name=$stageProcess.ProcessName;created_UTC=$stageOwned[$stageProcess.Id].created})
 $stageLowMemorySamples=0
 while(-not $stageProcess.HasExited){
  $stageMem=0;$stageCpu=0
  $stageEnvironmentFile=Join-Path $stageDir 'environment.json'
  if(Test-Path -LiteralPath $stageEnvironmentFile){try{$stageKernelId=(Get-Content -Raw -LiteralPath $stageEnvironmentFile | ConvertFrom-Json).process_id;$stageKP=Get-Process -Id $stageKernelId -ErrorAction SilentlyContinue;if($stageKP){$stageMem=$stageKP.WorkingSet64;$stageCpu=$stageKP.CPU}}catch{}}
  # Track all descendants, including ExternalEvaluate helpers, from this run's root.
  $stageAll=Get-CimInstance Win32_Process
  $stageByPid=@{};foreach($stageNode in $stageAll){$stageByPid[[int]$stageNode.ProcessId]=$stageNode}
  $stageChanged=$true
  while($stageChanged){
   $stageChanged=$false
   foreach($stageNode in $stageAll){
    $stageParentId=[int]$stageNode.ParentProcessId;$stageChildId=[int]$stageNode.ProcessId
    if(-not $stageOwned.ContainsKey($stageParentId) -or -not $stageByPid.ContainsKey($stageParentId)){continue}
    $stageParentNode=$stageByPid[$stageParentId]
    # A historical ParentPID can be reused by an unrelated launcher. Both live
    # parent creation identity and child birth after that parent are required.
    if([Math]::Abs(($stageParentNode.CreationDate.ToUniversalTime()-([datetime]$stageOwned[$stageParentId].created).ToUniversalTime()).TotalSeconds) -ge .01 -or $stageNode.CreationDate -lt $stageParentNode.CreationDate){continue}
    $stageChildCreated=$stageNode.CreationDate.ToUniversalTime().ToString('o')
    if(-not $stageOwned.ContainsKey($stageChildId) -or $stageOwned[$stageChildId].created -ne $stageChildCreated){
     $stageOwned[$stageChildId]=@{name=$stageNode.Name;created=$stageChildCreated}
     $stageOwnedHistory.Add(@{process_id=$stageChildId;name=$stageNode.Name;created_UTC=$stageChildCreated})
     $stageChanged=$true
    }
   }
  }
  if($stageKernelId -and -not $stageOwned.ContainsKey([int]$stageKernelId)){$stageNode=$stageByPid[[int]$stageKernelId];if($stageNode -and $stageNode.Name -eq 'wolfram.exe' -and $stageNode.CreationDate.ToUniversalTime() -ge $stageProcess.StartTime.ToUniversalTime()){$stageCreated=$stageNode.CreationDate.ToUniversalTime().ToString('o');$stageOwned[[int]$stageKernelId]=@{name=$stageNode.Name;created=$stageCreated};$stageOwnedHistory.Add(@{process_id=[int]$stageKernelId;name=$stageNode.Name;created_UTC=$stageCreated})}}
  $stageMem=0;$stageCpu=0;$stageActive=@()
  foreach($stageOwnedId in @($stageOwned.Keys)){$stageMember=Get-Process -Id $stageOwnedId -ErrorAction SilentlyContinue;if($stageMember -and [Math]::Abs(($stageMember.StartTime.ToUniversalTime()-([datetime]$stageOwned[$stageOwnedId].created).ToUniversalTime()).TotalSeconds) -lt .01){$stageMem+=$stageMember.WorkingSet64;$stageCPUById[([string]$stageOwnedId+'|'+$stageOwned[$stageOwnedId].created)]=$stageMember.CPU;$stageActive+=$stageOwnedId}}
  foreach($stageSeconds in $stageCPUById.Values){$stageCpu+=$stageSeconds}
  $stagePeak=[Math]::Max([int64]$stagePeak,[int64]$stageMem)
  $stageTimedOut=$env:LITZ_CLOSURE_MAX_SECONDS -and $stageClock.Elapsed.TotalSeconds -gt [double]$env:LITZ_CLOSURE_MAX_SECONDS
  if($stageTimedOut){@{reason='one_hour_task_watchdog';elapsed_seconds=$stageClock.Elapsed.TotalSeconds;owned_process_ids=$stageActive;timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'resource_stop.json') -Encoding utf8;foreach($stageOwnedId in ($stageActive|Sort-Object -Descending)){Stop-LitzOwnedProcess $stageOwnedId $stageOwned[$stageOwnedId].created}}
  $stageGPU=''
  if($stageGpuHeld -and (Get-Command nvidia-smi -ErrorAction SilentlyContinue)){$stageGPU=(& nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv,noheader,nounits 2>$null)-join ' '}
  if($stageGpuHeld -and $stageGPU -match '^\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)' -and [double]$Matches[1] -lt $stageVRAMReserveMiB){
   @{reason='display_VRAM_reserve_breached';reserve_MiB=$stageVRAMReserveMiB;gpu_csv=$stageGPU;timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'resource_stop.json') -Encoding utf8
   foreach($stageOwnedId in ($stageActive|Sort-Object -Descending)){Stop-LitzOwnedProcess $stageOwnedId $stageOwned[$stageOwnedId].created}
  }
  $stageCurrentFree=[LitzNativeMemory]::Available()
  if(($stageCurrentFree -lt $stageReserve -or ($env:LITZ_CLOSURE_MAX_WORKING_BYTES -and $stageMem -gt $stageBudget)) -and ($env:LITZ_CLOSURE_MAX_WORKING_BYTES -or $stageMem -gt 512MB)){$stageLowMemorySamples++}else{$stageLowMemorySamples=0}
  if($stageLowMemorySamples -ge 3){
   @{reason='closure_RAM_budget_or_system_reserve_breached';reserve_bytes=$stageReserve;working_budget_bytes=$stageBudget;system_free_bytes=$stageCurrentFree;kernel_working_bytes=$stageMem;timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'resource_stop.json') -Encoding utf8
   foreach($stageOwnedId in ($stageActive|Sort-Object -Descending)){Stop-LitzOwnedProcess $stageOwnedId $stageOwned[$stageOwnedId].created}
  }
  $stageRows.Add([pscustomobject]@{timestamp=(Get-Date -Format o);kernel_working_bytes=$stageMem;cpu_seconds=$stageCpu;system_free_bytes=$stageCurrentFree;gpu_csv=$stageGPU;owned_process_ids=($stageActive -join ',');elapsed_seconds=$stageClock.Elapsed.TotalSeconds})
  $stageRows | Export-Csv -NoTypeInformation -Encoding utf8 -Path (Join-Path $stageDir 'resource_curve.csv')
  if($Stage -eq 'frontend' -and (Test-Path -LiteralPath (Join-Path $stageDir 'results.json'))){
   $stageCompletedFile=Get-Item -LiteralPath (Join-Path $stageDir 'results.json')
   if(([datetime]::Now-$stageCompletedFile.LastWriteTime).TotalSeconds -gt 15 -and $stageKP -and $stageKP.ProcessName -eq 'wolfram'){
    @{reason='completed_frontend_kernel_shutdown_pending';action='Stop only recorded owned kernel after final result archive';kernel_id=$stageKernelId;timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'shutdown_cleanup.json') -Encoding utf8
    if($stageOwned.ContainsKey([int]$stageKernelId)){Stop-LitzOwnedProcess $stageKernelId $stageOwned[[int]$stageKernelId].created}
   }
  }
  Start-Sleep -Seconds 3;$stageProcess.Refresh()
 }
 $stageProcess.WaitForExit();$stageExit=[LitzNativeMemory]::ExitCode($stageProcessHandle)
 @{run_id=$RunId;process_exit_code=$stageExit;finished=(Get-Date -Format o)} | ConvertTo-Json | Set-Content (Join-Path $stageDir 'process_status.json') -Encoding utf8
 $stageOwnedRows=@($stageOwnedHistory)
 $stageGPUUsed=@();foreach($stageRow in $stageRows){if($stageRow.gpu_csv -match '^\s*[\d.]+\s*,\s*([\d.]+)\s*,'){$stageGPUUsed+=[double]$Matches[1]}}
 @{run_id=$RunId;peak_sampled_process_tree_working_bytes=$stagePeak;CPU_seconds=$stageCpu;elapsed_seconds=$stageClock.Elapsed.TotalSeconds;process_exit_code=$stageExit;owned_processes=$stageOwnedRows;GPU_peak_sampled_device_used_MiB=if($stageGPUUsed.Count){($stageGPUUsed|Measure-Object -Maximum).Maximum}else{$null};GPU_sampling_scope='whole device including background display allocation';sampling_interval_seconds=3;ownership_scope='recorded root and descendants; creation-time checked'}|ConvertTo-Json -Depth 6|Set-Content (Join-Path $stageDir 'resource_summary.json') -Encoding utf8
 if(-not(Test-Path -LiteralPath (Join-Path $stageDir 'results.json'))){& $stageWS -file (Join-Path $PSScriptRoot 'RecoverNotebookRun.wls') | Out-Null}
 if(Test-Path -LiteralPath (Join-Path $stageDir 'resource_stop.json')){$stageFinal=Get-Content -Raw (Join-Path $stageDir 'results.json')|ConvertFrom-Json;$stageFinal.execution_status='stopped_resource_or_time_budget';$stageFinal.physical_acceptance_status='not_verified';$stageFinal.failure_reason='resource_stop.json';$stageFinal|ConvertTo-Json -Depth 20|Set-Content (Join-Path $stageDir 'results.json') -Encoding utf8}
 Get-Content -LiteralPath (Join-Path $stageDir 'run_log.txt') -Tail 15
}finally{
 $stageRemaining=@();foreach($stageOwnedId in @($stageOwned.Keys)){$stageMember=Get-Process -Id $stageOwnedId -ErrorAction SilentlyContinue;if($stageMember -and [Math]::Abs(($stageMember.StartTime.ToUniversalTime()-([datetime]$stageOwned[$stageOwnedId].created).ToUniversalTime()).TotalSeconds) -lt .01){$stageRemaining+=$stageOwnedId;Stop-LitzOwnedProcess $stageOwnedId $stageOwned[$stageOwnedId].created}}
 if($stageRemaining.Count){@{reason='owned_helpers_remaining_after_recorded_root_exit';process_ids=$stageRemaining;scope='only creation-time-verified processes owned by this run';timestamp=(Get-Date -Format o)}|ConvertTo-Json|Set-Content (Join-Path $stageDir 'shutdown_cleanup.json') -Encoding utf8}
 if($stageGpuHeld){$stageGpuMutex.ReleaseMutex()};if($stageGpuMutex){$stageGpuMutex.Dispose()};$env:LITZ_RUN_ID=$stageOld.id;$env:LITZ_STAGE=$stageOld.stage;$env:LITZ_NOTEBOOK=$stageOld.nb;$env:LITZ_RAM_BUDGET=$stageOld.budget
}
exit $stageExit





