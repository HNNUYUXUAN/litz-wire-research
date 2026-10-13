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
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'tools/publication/RunPreManuscriptClosure.ps1') @PSBoundParameters
exit $LASTEXITCODE
