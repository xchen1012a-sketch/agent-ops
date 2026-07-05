param(
    [ValidateSet("all", "legal", "recruitment", "data")]
    [string]$Agent = "all",

    [switch]$SkipDependencies,
    [switch]$WithLegalRag,
    [switch]$Migrate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$ComposeFile = Join-Path $RepoRoot "agent-suite-ops\docker-compose.yml"
$LocalComposeFile = Join-Path $RepoRoot "agent-suite-ops\docker-compose.local.yml"
$LogDir = Join-Path $RepoRoot "logs\local-agent-runtime"

$AgentDefs = [ordered]@{
    legal = @{
        Path = "agents\legal-consulting-agent"
        Port = 8101
        App = "legal_consulting_agent.main:app"
        ModuleRoot = "legal_consulting_agent"
    }
    recruitment = @{
        Path = "agents\recruitment-assistant-agent"
        Port = 8102
        App = "recruitment_assistant_agent.main:app"
        ModuleRoot = "recruitment_assistant_agent"
    }
    data = @{
        Path = "agents\data-query-agent"
        Port = 8103
        App = "data_query_agent.main:app"
        ModuleRoot = "data_query_agent"
    }
}

function Get-SelectedAgents {
    if ($Agent -eq "all") {
        return @($AgentDefs.Keys)
    }
    return @($Agent)
}

function Wait-Live {
    param(
        [int]$Port,
        [int]$Attempts = 20
    )

    $uri = "http://127.0.0.1:$Port/v1/health/live"
    for ($i = 0; $i -lt $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $uri -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Start-Dependencies {
    $services = New-Object "System.Collections.Generic.List[string]"
    $services.Add("mysql")
    $services.Add("redis")

    if ($WithLegalRag) {
        $services.Add("qdrant")
        $services.Add("bge-embedding")
        $services.Add("bge-reranker")
    }

    Write-Host "Starting local dependencies: $($services -join ', ')"
    $args = @("compose", "-f", $ComposeFile)
    if (Test-Path -LiteralPath $LocalComposeFile) {
        $args += @("-f", $LocalComposeFile)
    }
    $args += @("up", "-d") + @($services)
    & docker @args
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose dependency startup failed"
    }
}

function Start-OneAgent {
    param([string]$Name)

    $def = $AgentDefs[$Name]
    $agentPath = Join-Path $RepoRoot $def.Path
    $pythonPath = Join-Path $agentPath ".venv\Scripts\python.exe"
    $envPath = Join-Path $agentPath ".env"

    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw "$Name venv python is missing: $pythonPath"
    }
    if (-not (Test-Path -LiteralPath $envPath)) {
        throw "$Name .env is missing: $envPath"
    }

    $connections = Get-NetTCPConnection -LocalPort $def.Port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = ($connections | Select-Object -ExpandProperty OwningProcess -Unique) -join ","
        throw "$Name port $($def.Port) is already in use by PID(s): $pids"
    }

    if ($Migrate) {
        Write-Host "Running Alembic migration for $Name"
        Push-Location $agentPath
        try {
            & $pythonPath -m alembic upgrade head
            if ($LASTEXITCODE -ne 0) {
                throw "$Name migration failed"
            }
        } finally {
            Pop-Location
        }
    }

    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"
    $pidFile = Join-Path $LogDir "$Name.pid"
    $helperPath = Join-Path $PSScriptRoot "start-agent-runtime-helper.py"

    & $pythonPath $helperPath `
        --python $pythonPath `
        --workdir $agentPath `
        --app $def.App `
        --host "127.0.0.1" `
        --port ([string]$def.Port) `
        --stdout $stdout `
        --stderr $stderr `
        --pid-file $pidFile
    if ($LASTEXITCODE -ne 0) {
        throw "$Name process startup command failed"
    }

    if (Wait-Live -Port $def.Port) {
        $pidText = ""
        if (Test-Path -LiteralPath $pidFile) {
            $pidText = (Get-Content -LiteralPath $pidFile -Raw).Trim()
        }
        if ($pidText) {
            Write-Host "$Name started on http://127.0.0.1:$($def.Port) with PID $pidText"
        } else {
            Write-Host "$Name started on http://127.0.0.1:$($def.Port)"
        }
        Write-Host "$Name live health passed"
    } else {
        Write-Warning "$Name live health did not pass yet. Check logs: $stdout and $stderr"
    }
}

if (-not $SkipDependencies) {
    Start-Dependencies
}

foreach ($name in Get-SelectedAgents) {
    Start-OneAgent -Name $name
}

Write-Host "Use agent-suite-ops\scripts\smoke-agent-health.ps1 for health checks."
