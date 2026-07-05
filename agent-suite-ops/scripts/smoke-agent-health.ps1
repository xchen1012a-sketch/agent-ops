param(
    [ValidateSet("all", "legal", "recruitment", "data")]
    [string]$Agent = "all",

    [switch]$RequireReady
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AgentDefs = [ordered]@{
    legal = @{ Port = 8101 }
    recruitment = @{ Port = 8102 }
    data = @{ Port = 8103 }
}

function Get-SelectedAgents {
    if ($Agent -eq "all") {
        return @($AgentDefs.Keys)
    }
    return @($Agent)
}

function Invoke-Health {
    param([string]$Uri)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 5
        return @{
            Ok = $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
            StatusCode = $response.StatusCode
            Body = $response.Content
        }
    } catch {
        $statusCode = 0
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        return @{
            Ok = $false
            StatusCode = $statusCode
            Body = $_.Exception.Message
        }
    }
}

$failed = $false

foreach ($name in Get-SelectedAgents) {
    $port = $AgentDefs[$name].Port
    $liveUri = "http://127.0.0.1:$port/v1/health/live"
    $readyUri = "http://127.0.0.1:$port/v1/health/ready"

    Write-Host ""
    Write-Host "[$name]"

    $live = Invoke-Health -Uri $liveUri
    Write-Host "live  $($live.StatusCode) $liveUri"
    if (-not $live.Ok) {
        $failed = $true
    }

    $ready = Invoke-Health -Uri $readyUri
    Write-Host "ready $($ready.StatusCode) $readyUri"
    if ($RequireReady -and -not $ready.Ok) {
        $failed = $true
    }
}

if ($failed) {
    exit 1
}
