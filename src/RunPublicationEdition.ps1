param(
 [Parameter(Mandatory=$true)][string]$RunId,
 [ValidateSet('report','paper','all')][string]$Edition='all',
 [ValidateSet('zh-CN','en','all')][string]$Language='all',
 [ValidateSet('merged','chapters','all')][string]$Form='all',
 [ValidateSet('single','ieee','all')][string]$Layout='all',
 [ValidateSet('preflight','panels','compose','documents','notebooks','pdf','verify','package','all')][string]$Stage='all',
 [string]$SourceManifest='manuscript/publication.json'
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$pythonPath=if($env:LITZ_PYTHON){$env:LITZ_PYTHON}else{(Get-Command python -ErrorAction Stop).Source}
$env:PYTHONUTF8='1'
& $pythonPath (Join-Path $PSScriptRoot 'RunPublicationBuild.py') --run-id $RunId --edition $Edition --language $Language --form $Form --layout $Layout --stage $Stage --source-manifest $SourceManifest
exit $LASTEXITCODE
