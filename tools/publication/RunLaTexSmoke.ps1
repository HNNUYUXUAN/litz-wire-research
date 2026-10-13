param(
 [string]$RunId=('latex_smoke_'+(Get-Date -Format 'yyyyMMdd_HHmmss')),
 [ValidateSet('manual','latexmk')][string]$Driver='latexmk',
 [string]$Python
)
$ErrorActionPreference='Stop'
if(-not $Python){
 $latexBundledPython=(Get-Command python -ErrorAction Stop).Source
 if(Test-Path -LiteralPath $latexBundledPython){$Python=$latexBundledPython}
 else{$Python=(Get-Command python -ErrorAction Stop).Source}
}
& $Python -X utf8 -B (Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src") 'BuildLaTexSmoke.py') --run-id $RunId --driver $Driver
exit $LASTEXITCODE
