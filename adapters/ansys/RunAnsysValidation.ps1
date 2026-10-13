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
$ErrorActionPreference = 'Stop'
$root = (Get-Item (Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src") '../../')).FullName
if (-not $RunId) { $RunId = 'ansys_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') }
if ($RunId -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid run ID.' }
$out = Join-Path $root ('outputs/' + $RunId)
if (Test-Path -LiteralPath $out) { throw 'Run ID already exists.' }
New-Item -ItemType Directory -Path $out | Out-Null
$venvPython = $PythonPath
if (-not $venvPython) { $venvPython = $env:LITZ_ANSYS_PYTHON }
if (-not $venvPython) {
    $venvPython = (Get-Command python -ErrorAction Stop).Source
}
if (-not (Test-Path -LiteralPath $venvPython)) { throw "PyAEDT Python not found: $venvPython" }
& $venvPython -c 'import ansys.aedt.core'
if($LASTEXITCODE -ne 0){throw 'Install the ansys extra in this Python environment: python -m pip install -e .[ansys]'}
$meta = [ordered]@{
    run_id = $RunId
    case = $Case
    root = $root
    python = $venvPython
    timestamp = (Get-Date -Format o)
    aedt_expected_version = '2025.2'
    short_test = $ShortTest.IsPresent
}
$meta.aedt_executables = @(Get-ChildItem -LiteralPath (Join-Path $env:ProgramFiles 'ANSYS Inc') -Filter 'ansysedt*.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
$meta.git_head = (& git -C $root rev-parse HEAD)
if ($Case -eq 'native3d') {
    $meta.config = $Config
    $meta.mode = $Mode
    $meta.mesh_index = $MeshIndex
    $meta.prerequisite = $Prerequisite
    $meta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'runner_parameters.json') -Encoding UTF8
    $pythonScript = Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src") 'ansys_native3d.py'
    $pythonArgs = @($pythonScript,'--config',$Config,'--out',$out,'--mode',$Mode,'--mesh-index',[string]$MeshIndex,'--prepared-output')
    if ($Prerequisite) { $pythonArgs += @('--prerequisite',$Prerequisite) }
    # Native Python writes its own complete run_log.txt; the launcher stream is separate.
    & $venvPython @pythonArgs 2>&1 | Tee-Object -FilePath (Join-Path $out 'launcher_stdout.txt')
} else {
    $meta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'parameters.json') -Encoding UTF8
    $pythonScript = Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src") 'ansys_validate.py'
    $pythonArgs=@($pythonScript,'--root',$root,'--out',$out,'--case',$Case)
    if($ShortTest){$pythonArgs+='--short-test'}
    & $venvPython @pythonArgs 2>&1 | Tee-Object -FilePath (Join-Path $out 'run_log.txt')
}
$exitCode = $LASTEXITCODE
if (-not (Test-Path -LiteralPath (Join-Path $out 'process_status.json'))) {
    [ordered]@{run_id=$RunId;process_exit_code=$exitCode;finished=(Get-Date -Format o)} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'process_status.json') -Encoding UTF8
}
exit $exitCode
