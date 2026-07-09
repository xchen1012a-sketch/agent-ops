param(
    [ValidateSet("all", "legal", "recruitment", "data")]
    [string]$Agent = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$LogDir = Join-Path $RepoRoot "logs\local-agent-runtime"

$AgentDefs = [ordered]@{
    legal = @{ Path = "agents\legal-consulting-agent" }
    recruitment = @{ Path = "agents\recruitment-assistant-agent" }
    data = @{ Path = "agents\data-query-agent" }
}

function Get-SelectedAgents {
    if ($Agent -eq "all") {
        return @($AgentDefs.Keys)
    }
    return @($Agent)
}

foreach ($name in Get-SelectedAgents) {
    $pidFile = Join-Path $LogDir "$name.pid"
    if (-not (Test-Path -LiteralPath $pidFile)) {
        Write-Host "$name has no pid file; nothing to stop"
        continue
    }

    $pidText = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    if (-not ($pidText -match "^\d+$")) {
        Write-Warning "$name pid file is invalid: $pidFile"
        continue
    }

    $processId = [int]$pidText
    $processInfo = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if (-not $processInfo) {
        Write-Host "$name process $processId already exited"
        Remove-Item -LiteralPath $pidFile -Force
        continue
    }

    $expectedPython = Join-Path $RepoRoot ($AgentDefs[$name].Path + "\.venv\Scripts\python.exe")
    if ($processInfo.Path -ne $expectedPython) {
        Write-Warning "$name pid $processId does not use expected Python path; refusing to stop it"
        continue
    }

    Stop-Process -Id $processId -Force
    Remove-Item -LiteralPath $pidFile -Force
    Write-Host "$name process $processId stopped"
}
