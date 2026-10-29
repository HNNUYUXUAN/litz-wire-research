param([string]$BoundaryRun='nb_boundary_20261004_220927_453')
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'adapters/wolfram/AuditNotebookDelivery.ps1') @PSBoundParameters
exit $LASTEXITCODE
