param([string]$RunId, [switch]$NotebookInput)
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'adapters/gpu/RunGPUValidation.ps1') @PSBoundParameters
exit $LASTEXITCODE
