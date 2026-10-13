param([string]$RunId='rerun_20261005_summary')
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'adapters/wolfram/SummarizeHighPerformanceRun.ps1') @PSBoundParameters
exit $LASTEXITCODE
