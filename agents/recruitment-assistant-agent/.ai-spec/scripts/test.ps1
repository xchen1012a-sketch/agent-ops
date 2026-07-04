param(
  [string]$ProjectRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$check = Join-Path $PSScriptRoot 'check.ps1'
if ($ProjectRoot) {
  & $check -ProjectRoot $ProjectRoot
} else {
  & $check
}
if (-not $?) {
  throw 'Template check failed.'
}

Write-Output 'Template test passed: structure and skill contract checks completed.'
