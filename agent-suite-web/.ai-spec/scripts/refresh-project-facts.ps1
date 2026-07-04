param(
  [string]$ProjectRoot = "",
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Roots {
  param([string]$ExplicitRoot)

  if ($ExplicitRoot) {
    $project = (Resolve-Path -LiteralPath $ExplicitRoot).Path
    return [PSCustomObject]@{ ProjectRoot = $project; SpecRoot = (Join-Path $project ".ai-spec") }
  }

  $cwd = (Get-Location).Path
  if (Test-Path -LiteralPath (Join-Path $cwd ".ai-spec")) {
    return [PSCustomObject]@{ ProjectRoot = $cwd; SpecRoot = (Join-Path $cwd ".ai-spec") }
  }

  $candidate = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
  if ((Split-Path -Leaf $candidate) -eq ".ai-spec") {
    return [PSCustomObject]@{ ProjectRoot = (Split-Path -Parent $candidate); SpecRoot = $candidate }
  }

  return [PSCustomObject]@{ ProjectRoot = $candidate; SpecRoot = $candidate }
}

function Get-TextHash {
  param([string]$Text)

  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $hash = $sha.ComputeHash($bytes)
    return (($hash | ForEach-Object { $_.ToString("x2") }) -join "")
  }
  finally {
    $sha.Dispose()
  }
}

function Get-JsonObject {
  param([string]$Path)

  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return $null
  }

  return Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json
}

function Get-PackageMaps {
  param($PackageJson)

  $deps = [ordered]@{}
  $scripts = [ordered]@{}

  if ($null -eq $PackageJson) {
    return [PSCustomObject]@{ Dependencies = $deps; Scripts = $scripts }
  }

  foreach ($section in @("dependencies", "devDependencies")) {
    if ($PackageJson.PSObject.Properties.Name -contains $section) {
      foreach ($prop in $PackageJson.$section.PSObject.Properties) {
        $deps[$prop.Name] = [string]$prop.Value
      }
    }
  }

  if ($PackageJson.PSObject.Properties.Name -contains "scripts") {
    foreach ($prop in $PackageJson.scripts.PSObject.Properties) {
      $scripts[$prop.Name] = [string]$prop.Value
    }
  }

  return [PSCustomObject]@{ Dependencies = $deps; Scripts = $scripts }
}

function Find-TechStack {
  param($Dependencies)

  $known = @(
    "next", "react", "vue", "svelte", "vite", "typescript",
    "express", "fastify", "nestjs", "@nestjs/core",
    "drizzle-orm", "prisma", "@prisma/client", "typeorm", "sequelize",
    "mysql2", "pg", "sqlite3", "better-sqlite3", "redis", "ioredis",
    "vitest", "jest", "playwright", "@playwright/test", "cypress",
    "eslint", "prettier", "tailwindcss"
  )

  $found = New-Object System.Collections.Generic.List[string]
  foreach ($name in $known) {
    if ($Dependencies.Contains($name)) {
      $found.Add("$name $($Dependencies[$name])")
    }
  }

  if ($found.Count -eq 0) {
    return @("- No common framework or tool detected from package.json.")
  }

  return $found | ForEach-Object { "- $_" }
}

function Get-ScriptLines {
  param($Scripts)

  if ($Scripts.Count -eq 0) {
    return @("- No package.json scripts detected.")
  }

  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($key in ($Scripts.Keys | Sort-Object)) {
    $lines.Add(("- {0}: {1}" -f $key, $Scripts[$key]))
  }
  return $lines
}

function Get-EnvKeys {
  param([string]$ProjectRoot)

  $files = Get-ChildItem -LiteralPath $ProjectRoot -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\.env(\..*)?\.example$' -or $_.Name -match '^\.env\.example$' } |
    Sort-Object Name

  $keys = New-Object System.Collections.Generic.SortedSet[string]
  foreach ($file in $files) {
    foreach ($line in (Get-Content -LiteralPath $file.FullName -Encoding UTF8 -ErrorAction SilentlyContinue)) {
      if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
        [void]$keys.Add($matches[1])
      }
    }
  }

  if ($keys.Count -eq 0) {
    return @("- No .env*.example keys detected.")
  }

  return $keys | ForEach-Object { "- $_" }
}

function Get-DirectoryTree {
  param([string]$ProjectRoot)

  $ignore = @(".git", ".ai-spec", ".agents", ".codex", "node_modules", ".next", "dist", "build", "coverage", ".turbo", ".cache")
  $ignoreFiles = @("project-facts.md")
  $rootName = Split-Path -Leaf $ProjectRoot
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add("$rootName/")

  $items = Get-ChildItem -LiteralPath $ProjectRoot -Force -ErrorAction SilentlyContinue |
    Where-Object { ($ignore -notcontains $_.Name) -and ($ignoreFiles -notcontains $_.Name) } |
    Sort-Object @{ Expression = { -not $_.PSIsContainer } }, Name |
    Select-Object -First 40

  foreach ($item in $items) {
    $suffix = if ($item.PSIsContainer) { "/" } else { "" }
    $lines.Add("|-- $($item.Name)$suffix")
    if ($item.PSIsContainer) {
      $children = Get-ChildItem -LiteralPath $item.FullName -Force -ErrorAction SilentlyContinue |
        Where-Object { ($ignore -notcontains $_.Name) -and ($ignoreFiles -notcontains $_.Name) } |
        Sort-Object @{ Expression = { -not $_.PSIsContainer } }, Name |
        Select-Object -First 20
      foreach ($child in $children) {
        $childSuffix = if ($child.PSIsContainer) { "/" } else { "" }
        $lines.Add("|   |-- $($child.Name)$childSuffix")
      }
    }
  }

  return $lines
}

function Get-GitFacts {
  param([string]$ProjectRoot)

  $lines = New-Object System.Collections.Generic.List[string]
  try {
    $inside = (& git -C $ProjectRoot rev-parse --is-inside-work-tree 2>$null)
    if ($inside -ne "true") {
      return @("- No valid Git repository detected.")
    }

    $branch = (& git -C $ProjectRoot branch --show-current 2>$null)
    if (-not $branch) { $branch = "(detached or unknown)" }
    $status = (& git -C $ProjectRoot status --short 2>$null)
    $remotes = (& git -C $ProjectRoot remote -v 2>$null) | Select-Object -First 4

    $lines.Add("- Current branch: $branch")
    if ($status) {
      $lines.Add("- Working tree: has uncommitted changes")
    }
    else {
      $lines.Add("- Working tree: clean")
    }

    if ($remotes) {
      $lines.Add("- Remotes:")
      foreach ($remote in $remotes) {
        $lines.Add("  - $remote")
      }
    }
    else {
      $lines.Add("- Remotes: none")
    }
  }
  catch {
    return @("- Git status check failed: $($_.Exception.Message)")
  }

  return $lines
}

function Get-SourceHash {
  param(
    [string]$ProjectRoot,
    [string[]]$TreeLines
  )

  $sourceNames = @(
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "tsconfig.json",
    ".env.example",
    ".env.local.example"
  )

  $parts = New-Object System.Collections.Generic.List[string]
  foreach ($name in $sourceNames) {
    $path = Join-Path $ProjectRoot $name
    if (Test-Path -LiteralPath $path -PathType Leaf) {
      $parts.Add("FILE:$name")
      $parts.Add((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant())
    }
  }
  $parts.Add("TREE:")
  foreach ($line in $TreeLines) { $parts.Add($line) }

  return (Get-TextHash -Text ($parts -join "`n")).Substring(0, 16)
}

function Get-ManualSection {
  param(
    [string]$ExistingText,
    [string]$RulesRoot
  )

  $default = ""
  $examplePath = Join-Path $RulesRoot "project-facts.example.md"
  $pattern = '(?s)<!-- ai-facts:manual:start -->.*?<!-- ai-facts:manual:end -->'
  if (Test-Path -LiteralPath $examplePath -PathType Leaf) {
    $exampleText = Get-Content -LiteralPath $examplePath -Encoding UTF8 -Raw
    $exampleMatch = [regex]::Match($exampleText, $pattern)
    if ($exampleMatch.Success) {
      $default = $exampleMatch.Value.TrimEnd()
    }
  }

  if (-not $ExistingText) {
    return $default
  }

  $match = [regex]::Match($ExistingText, $pattern)
  if ($match.Success) {
    return $match.Value.TrimEnd()
  }

  return ($default + "`n`n## [manual] Legacy content to review`n`n" + $ExistingText.TrimEnd())
}

$roots = Resolve-Roots -ExplicitRoot $ProjectRoot
$projectRoot = $roots.ProjectRoot
$specRoot = $roots.SpecRoot
$rulesRoot = Join-Path $specRoot ".ai-rules"
$factsPath = Join-Path $rulesRoot "project-facts.md"

if (-not (Test-Path -LiteralPath $rulesRoot -PathType Container)) {
  throw "Cannot find .ai-rules under spec root: $specRoot"
}

$packageJson = Get-JsonObject -Path (Join-Path $projectRoot "package.json")
$packageMaps = Get-PackageMaps -PackageJson $packageJson
$treeLines = Get-DirectoryTree -ProjectRoot $projectRoot
$sourceHash = Get-SourceHash -ProjectRoot $projectRoot -TreeLines $treeLines

$existingText = ""
if (Test-Path -LiteralPath $factsPath -PathType Leaf) {
  $existingText = Get-Content -LiteralPath $factsPath -Encoding UTF8 -Raw
  $oldHash = $null
  if ($existingText -match 'source hash:\s*([A-Za-z0-9._-]+)') {
    $oldHash = $matches[1]
  }
  if ((-not $Force) -and $oldHash -eq $sourceHash) {
    Write-Output "Project facts already fresh: $factsPath"
    exit 0
  }
}

$refreshTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$techLines = Find-TechStack -Dependencies $packageMaps.Dependencies
$scriptLines = Get-ScriptLines -Scripts $packageMaps.Scripts
$envLines = Get-EnvKeys -ProjectRoot $projectRoot
$gitLines = Get-GitFacts -ProjectRoot $projectRoot
$manualSection = Get-ManualSection -ExistingText $existingText -RulesRoot $rulesRoot
$fence = '```'

$autoSection = @"
<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: $sourceHash
- last refresh: $refreshTime
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

$($techLines -join "`n")

## [auto] Scripts

$($scriptLines -join "`n")

## [auto] Directory structure (top 2 levels)

$($fence)text
$($treeLines -join "`n")
$fence

## [auto] Environment keys

$($envLines -join "`n")

## [auto] Git status

$($gitLines -join "`n")
<!-- ai-facts:auto:end -->
"@

$content = @"
# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

$($autoSection.TrimEnd())

$manualSection
"@

Set-Content -LiteralPath $factsPath -Encoding UTF8 -Value $content.TrimEnd()
Write-Output "Project facts refreshed: $factsPath"
