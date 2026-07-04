param(
  [string]$ProjectRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$check = Join-Path $PSScriptRoot 'check.ps1'
$entry = Join-Path $PSScriptRoot 'create-entry.ps1'

if ($ProjectRoot) {
  & $check -ProjectRoot $ProjectRoot
  if (-not $?) {
    throw 'Template check failed.'
  }
  & $entry -ProjectRoot $ProjectRoot -DryRun
} else {
  & $check
  if (-not $?) {
    throw 'Template check failed.'
  }

  $tmpBase = Join-Path ([IO.Path]::GetTempPath()) 'agent-lite-rules-smoke'
  $tmpProject = Join-Path $tmpBase ([guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path (Join-Path $tmpProject '.ai-spec') | Out-Null
  try {
    & $entry -ProjectRoot $tmpProject -DryRun
  } finally {
    $resolvedTmp = Resolve-Path -LiteralPath $tmpProject -ErrorAction SilentlyContinue
    $resolvedBase = Resolve-Path -LiteralPath $tmpBase -ErrorAction SilentlyContinue
    if ($resolvedTmp -and $resolvedBase -and $resolvedTmp.Path.StartsWith($resolvedBase.Path)) {
      Remove-Item -LiteralPath $resolvedTmp.Path -Recurse -Force
    }
  }
}

Write-Output 'Template smoke passed: check and create-entry dry run completed.'
