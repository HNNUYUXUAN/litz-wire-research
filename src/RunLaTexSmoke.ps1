param(
 [string]$RunId=('latex_smoke_'+(Get-Date -Format 'yyyyMMdd_HHmmss')),
 [ValidateSet('manual','latexmk')][string]$Driver='latexmk',
 [string]$Python
)
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'tools/publication/RunLaTexSmoke.ps1') @PSBoundParameters
exit $LASTEXITCODE
