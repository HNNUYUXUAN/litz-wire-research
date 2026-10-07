param(
 [ValidateSet('Preflight','Run','Export','Verify')][string]$Action='Preflight',
 [ValidateSet('low32','high64gpu')][string]$Profile='high64gpu',
 [string]$TaskId,
 [string]$RunId,
 [string]$Bundle,
 [string]$Config,
 [string]$ReferenceRuns,
 [string]$SelectionFile,
 [switch]$DocumentHost,
 [string]$AnsysPython,
 [ValidateSet(1,2)][int]$InterfaceRevision=1,
 [ValidateSet(1,4)][int]$KernelAssemblyWorkers=1
)
$ErrorActionPreference='Stop'
$closureRoot=Split-Path -Parent $PSScriptRoot
$closurePython=(Get-Command python).Source
$closureArgs=@((Join-Path $PSScriptRoot 'PreManuscriptClosure.py'),'--action',$Action.ToLowerInvariant(),'--profile',$Profile)
if($TaskId){$closureArgs+=@('--task',$TaskId)}
if($RunId){$closureArgs+=@('--run-id',$RunId)}
if($Bundle){$closureArgs+=@('--bundle',$Bundle)}
if($Config){$closureArgs+=@('--config',$Config)}
if($ReferenceRuns){$closureArgs+=@('--reference-runs',$ReferenceRuns)}
if($SelectionFile){$closureArgs+=@('--selection-file',$SelectionFile)}
if($DocumentHost){$closureArgs+='--document-host'}
if($AnsysPython){$closureArgs+=@('--ansys-python',$AnsysPython)}
$closureArgs+=@('--interface-revision',[string]$InterfaceRevision)
$closureArgs+=@('--kernel-assembly-workers',[string]$KernelAssemblyWorkers)
& $closurePython @closureArgs
exit $LASTEXITCODE
