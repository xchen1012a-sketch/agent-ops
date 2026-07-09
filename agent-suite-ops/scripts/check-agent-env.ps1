param(
    [ValidateSet("all", "legal", "recruitment", "data")]
    [string]$Agent = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path

$AgentDefs = [ordered]@{
    legal = @{
        Path = "agents\legal-consulting-agent"
        Port = 8101
        Modules = @("fastapi", "sqlalchemy", "redis", "httpx", "langgraph", "qdrant_client")
        RequiredEnv = @(
            "JWT_SECRET",
            "DATABASE_URL",
            "DATABASE_MIGRATION_URL",
            "REDIS_URL",
            "AGENT_CONFIG_ENCRYPTION_KEY",
            "EMBEDDING_BASE_URL",
            "RAG_VECTOR_DB_URL",
            "RAG_RERANKER_BASE_URL"
        )
        CompatibilityEnv = @("DEEPSEEK_API_BASE", "DEEPSEEK_API_KEY")
    }
    recruitment = @{
        Path = "agents\recruitment-assistant-agent"
        Port = 8102
        Modules = @("fastapi", "sqlalchemy", "redis", "httpx", "langgraph")
        RequiredEnv = @(
            "JWT_SECRET",
            "DATABASE_URL",
            "DATABASE_MIGRATION_URL",
            "REDIS_URL",
            "AGENT_CONFIG_ENCRYPTION_KEY"
        )
        CompatibilityEnv = @("DEEPSEEK_API_BASE", "DEEPSEEK_API_KEY")
    }
    data = @{
        Path = "agents\data-query-agent"
        Port = 8103
        Modules = @("fastapi", "sqlalchemy", "redis", "httpx", "langgraph", "sqlglot")
        RequiredEnv = @(
            "JWT_SECRET",
            "DATABASE_URL",
            "DATABASE_MIGRATION_URL",
            "SHOP_DB_READ_URL",
            "REDIS_URL",
            "AGENT_CONFIG_ENCRYPTION_KEY"
        )
        CompatibilityEnv = @("DEEPSEEK_API_BASE", "DEEPSEEK_API_KEY")
    }
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Get-SelectedAgents {
    if ($Agent -eq "all") {
        return @($AgentDefs.Keys)
    }
    return @($Agent)
}

function Get-EnvKeys {
    param([string]$EnvPath)

    $keys = New-Object "System.Collections.Generic.HashSet[string]"
    if (-not (Test-Path -LiteralPath $EnvPath)) {
        return $keys
    }

    foreach ($line in Get-Content -LiteralPath $EnvPath) {
        if ($line -match "^\s*([A-Z0-9_]+)\s*=") {
            [void]$keys.Add($Matches[1])
        }
    }
    return $keys
}

function Test-PythonModules {
    param(
        [string]$PythonPath,
        [string[]]$Modules
    )

    $code = "import importlib.util, sys; missing=[m for m in sys.argv[1:] if importlib.util.find_spec(m) is None]; print('missing modules: ' + ','.join(missing) if missing else 'python modules ok'); sys.exit(1 if missing else 0)"
    $args = @("-c", $code) + $Modules
    & $PythonPath @args
    return $LASTEXITCODE -eq 0
}

$issues = New-Object "System.Collections.Generic.List[string]"

Write-Host "Checking local agent runtime environment under $RepoRoot"

if (Get-Command docker -ErrorAction SilentlyContinue) {
    & docker --version
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "docker command is available"
    } else {
        $issues.Add("docker command failed")
    }
} else {
    $issues.Add("docker command is not available")
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    & docker compose version
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "docker compose is available"
    } else {
        $issues.Add("docker compose failed")
    }
}

foreach ($name in Get-SelectedAgents) {
    $def = $AgentDefs[$name]
    $agentPath = Join-Path $RepoRoot $def.Path
    $pythonPath = Join-Path $agentPath ".venv\Scripts\python.exe"
    $envPath = Join-Path $agentPath ".env"

    Write-Host ""
    Write-Host "[$name]"

    if (Test-Path -LiteralPath $agentPath) {
        Write-Ok "agent directory exists: $agentPath"
    } else {
        $issues.Add("$name agent directory is missing")
        continue
    }

    if (Test-Path -LiteralPath $pythonPath) {
        & $pythonPath --version
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "venv python exists"
        } else {
            $issues.Add("$name python cannot run")
        }
    } else {
        $issues.Add("$name venv python is missing: $pythonPath")
    }

    if (Test-Path -LiteralPath $pythonPath) {
        if (Test-PythonModules -PythonPath $pythonPath -Modules $def.Modules) {
            Write-Ok "core python modules are present"
        } else {
            $issues.Add("$name is missing one or more python modules")
        }
    }

    if (Test-Path -LiteralPath $envPath) {
        Write-Ok ".env exists"
        $envKeys = Get-EnvKeys -EnvPath $envPath
        foreach ($requiredKey in $def.RequiredEnv) {
            if (-not $envKeys.Contains($requiredKey)) {
                $issues.Add("$name .env is missing key $requiredKey")
            }
        }
        foreach ($compatibilityKey in $def.CompatibilityEnv) {
            if (-not $envKeys.Contains($compatibilityKey)) {
                Write-Warn "$name .env is missing current-code compatibility key $compatibilityKey"
            }
        }
    } else {
        $issues.Add("$name .env is missing: $envPath")
    }

    $connections = Get-NetTCPConnection -LocalPort $def.Port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = ($connections | Select-Object -ExpandProperty OwningProcess -Unique) -join ","
        Write-Warn "port $($def.Port) is already in use by PID(s): $pids"
    } else {
        Write-Ok "port $($def.Port) is free"
    }
}

Write-Host ""
if ($issues.Count -gt 0) {
    Write-Fail "Environment check found $($issues.Count) issue(s):"
    foreach ($issue in $issues) {
        Write-Host "- $issue"
    }
    exit 1
}

Write-Ok "Environment check passed"
