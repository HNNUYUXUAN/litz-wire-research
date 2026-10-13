param(
 [Parameter(Mandatory=$true)][string]$RunId,
 [ValidateSet('report','paper','all')][string]$Edition='all',
 [ValidateSet('zh-CN','en','all')][string]$Language='all',
 [ValidateSet('merged','chapters','all')][string]$Form='all',
 [ValidateSet('single','ieee','all')][string]$Layout='all',
 [ValidateSet('preflight','panels','compose','documents','notebooks','pdf','verify','package','all')][string]$Stage='all',
 [string]$SourceManifest='manuscript/publication.json'
)
$ErrorActionPreference="Stop"
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'tools/publication/RunPublicationEdition.ps1') @PSBoundParameters
exit $LASTEXITCODE
