param(
    [ValidateSet('all','7','640','curves','native3d')][string]$Case = 'all',
    [string]$RunId,
    [string]$PythonPath,
    [switch]$ShortTest,
    [string]$Config = 'configs/native3d_q1_straight.json',
    [ValidateSet('pilot','suite','preflight')][string]$Mode = 'pilot',
    [ValidateRange(0,2)][int]$MeshIndex = 0,
    [string]$Prerequisite
)
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'adapters/ansys/RunAnsysValidation.ps1') @PSBoundParameters
exit $LASTEXITCODE
