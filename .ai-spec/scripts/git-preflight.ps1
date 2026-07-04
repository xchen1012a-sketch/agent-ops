param(
  [string]$ProjectRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
  param([string]$ExplicitRoot)

  if ($ExplicitRoot) {
    return (Resolve-Path -LiteralPath $ExplicitRoot).Path
  }

  $cwd = (Get-Location).Path
  if (Test-Path -LiteralPath (Join-Path $cwd ".ai-spec")) {
    return $cwd
  }

  $candidate = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
  if ((Split-Path -Leaf $candidate) -eq ".ai-spec") {
    return (Split-Path -Parent $candidate)
  }

  return $candidate
}

function Add-Unique {
  param(
    [System.Collections.Generic.List[string]]$List,
    [string[]]$Values
  )

  foreach ($value in $Values) {
    if ([string]::IsNullOrWhiteSpace($value)) { continue }
    if (-not $List.Contains($value)) {
      $List.Add($value)
    }
  }
}

function Is-TextCandidate {
  param([string]$Path)

  $binaryExtensions = @(
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf',
    '.zip', '.7z', '.rar', '.gz', '.tar', '.exe', '.dll',
    '.woff', '.woff2', '.ttf', '.otf', '.mp3', '.mp4', '.mov'
  )
  $ext = [IO.Path]::GetExtension($Path).ToLowerInvariant()
  return -not ($binaryExtensions -contains $ext)
}

$projectRoot = Resolve-ProjectRoot -ExplicitRoot $ProjectRoot
$errors = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

$gitRoot = (& git -C $projectRoot rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
  $errors.Add("Not a Git repository: $projectRoot")
} else {
  $gitRoot = (Resolve-Path -LiteralPath $gitRoot).Path
  $resolvedProject = (Resolve-Path -LiteralPath $projectRoot).Path
  if ($resolvedProject -ne $gitRoot) {
    $warnings.Add("Project root differs from Git root: project=$resolvedProject git=$gitRoot")
  }

  $status = & git -C $gitRoot status --short
  if ($status) {
    $warnings.Add("Working tree has changes; review git status before commit.")
  }

  $changed = New-Object System.Collections.Generic.List[string]
  Add-Unique -List $changed -Values (& git -C $gitRoot diff --name-only --cached)
  Add-Unique -List $changed -Values (& git -C $gitRoot diff --name-only)
  Add-Unique -List $changed -Values (& git -C $gitRoot ls-files --others --exclude-standard)

  $generatedPathPattern = '(^|/)(node_modules|vendor|dist|build|coverage|\.next|out|target|bin|obj)(/|$)'
  $envExamplePattern = '\.env(\..*)?\.(example|sample|template|dist)$|\.env\.(example|sample|template|dist)$'
  $sensitivePathPattern = '(^|/)(id_rsa|id_ed25519|id_dsa|id_ecdsa)$|\.(pem|p12|pfx|key)$'
  $secretPatterns = @(
    '-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'AKIA[0-9A-Z]{16}',
    'gh[pousr]_[A-Za-z0-9_]{36,}',
    'sk-[A-Za-z0-9]{20,}',
    '(?im)^\s*[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY|ACCESS_KEY)[A-Z0-9_]*\s*=\s*["'']?(?!\s*$|changeme|example|placeholder|todo|xxx|<|your_|YOUR_|dummy|test)[^#\r\n]{8,}'
  )

  foreach ($relativePath in $changed) {
    $normalized = $relativePath -replace '\\', '/'
    if ($normalized -match $generatedPathPattern) {
      $warnings.Add("Generated/dependency path changed: $relativePath")
    }

    $absolutePath = Join-Path $gitRoot ($relativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
      continue
    }

    $item = Get-Item -LiteralPath $absolutePath
    if ($item.Length -gt 25MB) {
      $errors.Add("Very large changed file: $relativePath ($([math]::Round($item.Length / 1MB, 1)) MB)")
    } elseif ($item.Length -gt 5MB) {
      $warnings.Add("Large changed file: $relativePath ($([math]::Round($item.Length / 1MB, 1)) MB)")
    }

    if ($normalized -match '(^|/)\.env(\.|$)' -and $normalized -notmatch $envExamplePattern) {
      $errors.Add("Real environment file changed: $relativePath")
    }

    if ($normalized -match $sensitivePathPattern) {
      $errors.Add("Sensitive key/certificate path changed: $relativePath")
    }

    if ($item.Length -gt 2MB -or -not (Is-TextCandidate -Path $absolutePath)) {
      continue
    }

    $text = Get-Content -LiteralPath $absolutePath -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
    if ($null -eq $text) { continue }

    foreach ($pattern in $secretPatterns) {
      if ($text -match $pattern) {
        $errors.Add("Possible secret in changed file: $relativePath")
        break
      }
    }
  }
}

if ($errors.Count -gt 0) {
  Write-Output "Git preflight failed: $projectRoot"
  foreach ($errorItem in $errors) { Write-Output "ERROR $errorItem" }
  foreach ($warningItem in $warnings) { Write-Output "WARN $warningItem" }
  exit 1
}

Write-Output "Git preflight passed: $projectRoot"
foreach ($warningItem in $warnings) { Write-Output "WARN $warningItem" }
