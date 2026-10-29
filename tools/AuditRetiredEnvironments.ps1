param([string]$Output='outputs/integration_20261028_01/old-environment-audit.json')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$prefixes=@(
    (Join-Path $repo '.venv'),
    'C:\Users\admin\Documents\Codex\2026-10-04\du-2\work\pyaedt-mcp-venv'
)
$roots=@($repo,'C:\Workspaces\repos\litz-wire-modeling','C:\Workspaces\repos\litz-wire-modeling-src',
         'C:\Workspaces\repos\veriharness','C:\workspace\qits','C:\workspace\tanwei',
         'C:\Workspaces\projects\cluetide-botchain','C:\Workspaces\projects\gitee-maintenance')
$paths=@('C:\Users\admin\.codex\config.toml')
foreach($root in $roots){
    foreach($name in @('litz.config.json','.codex/config.toml','.mcp.json','.vscode/settings.json')){
        $paths+=Join-Path $root $name
    }
}
$configRecords=@()
foreach($path in $paths){
    if(Test-Path -LiteralPath $path -PathType Leaf){
        $content=[IO.File]::ReadAllText($path).Replace('\\','/').Replace('\','/').ToLowerInvariant()
        $matches=@($prefixes | Where-Object {$content.Contains($_.Replace('\','/').ToLowerInvariant())})
        $configRecords+=@{path=$path;old_prefix_matches=$matches}
    }
}
$processes=@(Get-CimInstance Win32_Process | Where-Object {
    $exe=$_.ExecutablePath
    $exe -and @($prefixes | Where-Object {$exe.StartsWith($_+'\',[StringComparison]::OrdinalIgnoreCase)}).Count -gt 0
} | Select-Object ProcessId,CreationDate,ExecutablePath)
$record=@{checked_at=[DateTimeOffset]::UtcNow.ToString('o');prefixes=$prefixes;configurations=$configRecords;
          active_processes=$processes;scope='Saved project runtime configurations, global Codex MCP configuration and current executable paths';
          status='reviewed';decision='Retire project-only prefixes after inspecting reference owners; preserve a prefix with another active owner'}
$destination=[IO.Path]::GetFullPath((Join-Path $repo $Output))
if(-not $destination.StartsWith((Join-Path $repo 'outputs')+[IO.Path]::DirectorySeparatorChar)){throw 'Output boundary failed'}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $destination -Encoding utf8
$configRecords | Where-Object {$_.old_prefix_matches.Count -gt 0} | ConvertTo-Json -Depth 5
Write-Output ('Active matching processes: '+$processes.Count)
