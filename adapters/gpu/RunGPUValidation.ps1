param([string]$RunId, [switch]$NotebookInput)
$ErrorActionPreference = 'Stop'
$gpuProjectRoot = (Get-Item (Join-Path (Join-Path ((Get-Item (Join-Path $PSScriptRoot "../../")).FullName) "src") '../../')).FullName
if (-not $RunId) { $RunId = 'gpu_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') }
if ($RunId -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid run ID.' }
$gpuOutputPath = Join-Path $gpuProjectRoot ('outputs/' + $RunId)
if (Test-Path -LiteralPath $gpuOutputPath) { throw 'Run ID already exists; choose a new ID.' }
$gpuWolframCommand = Get-Command wolframscript -ErrorAction Stop
$gpuPreviousRunId = $env:LITZ_RUN_ID
$gpuQueueMutex=[Threading.Mutex]::new($false,'Local\LitzWolframGPUQueue');$gpuQueueHeld=$false
try {
    while(-not $gpuQueueHeld){try{$gpuQueueHeld=$gpuQueueMutex.WaitOne(1000)}catch [Threading.AbandonedMutexException]{$gpuQueueHeld=$true}}
    $env:LITZ_RUN_ID = $RunId
    $gpuEntryFile = if ($NotebookInput) { 'EvaluateGPUNotebookHeadless.wls' } else { 'RunGPUValidation.wls' }
    $gpuConsoleLines = @(& $gpuWolframCommand.Source -file (Join-Path $PSScriptRoot $gpuEntryFile) 2>&1 | ForEach-Object {
        Write-Host $_
        $_.ToString()
    })
    $gpuExitCode = $LASTEXITCODE
    if (Test-Path -LiteralPath $gpuOutputPath) {
        $gpuConsoleLines | Set-Content -LiteralPath (Join-Path $gpuOutputPath 'run_log.txt') -Encoding utf8
        $gpuSmiCommand = Get-Command nvidia-smi -ErrorAction SilentlyContinue
        if ($gpuSmiCommand) {
            & $gpuSmiCommand.Source --query-gpu=name,driver_version,memory.total,compute_cap --format=csv |
                Set-Content -LiteralPath (Join-Path $gpuOutputPath 'nvidia_gpu.csv') -Encoding utf8
        }
    }
} finally {
    if($gpuQueueHeld){$gpuQueueMutex.ReleaseMutex()};$gpuQueueMutex.Dispose()
    $env:LITZ_RUN_ID = $gpuPreviousRunId
}
exit $gpuExitCode
