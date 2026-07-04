param(
  [string]$ProjectRoot = ""
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

$roots = Resolve-Roots -ExplicitRoot $ProjectRoot
$projectRoot = $roots.ProjectRoot
$specRoot = $roots.SpecRoot

$errors = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Require-File {
  param([string]$RelativePath)
  $path = Join-Path $specRoot $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    $errors.Add("Missing file: $RelativePath")
  }
}

function Require-Dir {
  param([string]$RelativePath)
  $path = Join-Path $specRoot $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Container)) {
    $errors.Add("Missing directory: $RelativePath")
  }
}

$requiredFiles = @(
  'README.md',
  'CLAUDE.md',
  'AGENTS.md',
  '.ai-rules\README.md',
  '.ai-rules\redlines.md',
  '.ai-rules\task-routing.md',
  '.ai-rules\context-loading.md',
  '.ai-rules\documentation-policy.md',
  '.ai-rules\git-workflow.md',
  '.ai-rules\modularity-output.md',
  '.ai-rules\skill-contract.md',
  '.ai-rules\project-facts.example.md',
  'docs\rules\business-rules.example.md',
  'docs\plans\README.md',
  'docs\plans\project-plan.example.md',
  'docs\plans\current.example.md',
  'docs\plans\bugfix-review-plan.example.md',
  'skills\README.md',
  'scripts\create-entry.ps1',
  'scripts\git-preflight.ps1',
  'scripts\git-preflight.sh',
  'scripts\refresh-project-facts.ps1',
  'scripts\refresh-project-facts.sh',
  'scripts\check.sh',
  'scripts\create-entry.cmd',
  'scripts\create-entry.sh'
)

$requiredDirs = @('skills', '.ai-rules', 'docs', 'docs\rules', 'scripts')

foreach ($dir in $requiredDirs) { Require-Dir $dir }
foreach ($file in $requiredFiles) { Require-File $file }

$skillsRoot = Join-Path $specRoot 'skills'
if (Test-Path -LiteralPath $skillsRoot -PathType Container) {
  $skillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory | Sort-Object Name
  if ($skillDirs.Count -eq 0) {
    $errors.Add('No skill directories found under skills/.')
  }

  foreach ($dir in $skillDirs) {
    $skillPath = Join-Path $dir.FullName 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillPath -PathType Leaf)) {
      $errors.Add("Missing SKILL.md: skills\$($dir.Name)")
      continue
    }

    $text = Get-Content -LiteralPath $skillPath -Encoding UTF8 -Raw
    if ($text -notmatch '(?s)^---\s*.*name:\s*.+?description:\s*.+?---') {
      $errors.Add("Invalid frontmatter: skills\$($dir.Name)\SKILL.md")
    }
    foreach ($section in @('## 目标','## 适用场景','## 不适用场景','## 最小上下文','## 工作流','## 停止条件','## 强制执行规则')) {
      if ($text -notmatch [regex]::Escape($section)) {
        $errors.Add("Missing section ${section}: skills\$($dir.Name)\SKILL.md")
      }
    }
    if ($text -notmatch '验证') {
      $errors.Add("Missing verification guidance: skills\$($dir.Name)\SKILL.md")
    }
  }
}

if ((Split-Path -Leaf $specRoot) -eq '.ai-spec') {
  foreach ($entry in @('CLAUDE.md', 'AGENTS.md')) {
    $entryPath = Join-Path $projectRoot $entry
    if (-not (Test-Path -LiteralPath $entryPath -PathType Leaf)) {
      $warnings.Add("Project root entry missing: $entry. Run .ai-spec\scripts\create-entry.ps1")
    }
  }
}

$scriptFiles = Get-ChildItem -LiteralPath (Join-Path $specRoot 'scripts') -Filter '*.ps1' -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'check.ps1' }
$p1 = 'TO' + 'DO:'
$p2 = 'Fill project' + '-specific'
$p3 = 'Template ' + '.*'
$p3 = $p3 + ' script'
$placeholderPatterns = @($p1, $p2, $p3)
$placeholderMatches = $scriptFiles | Select-String -Pattern $placeholderPatterns -ErrorAction SilentlyContinue
if ($placeholderMatches) {
  foreach ($match in $placeholderMatches) {
    $warnings.Add("Placeholder text remains: $($match.Path):$($match.LineNumber)")
  }
}

$sizeBudgets = @(
  [PSCustomObject]@{ Label = 'README.md'; Path = Join-Path $specRoot 'README.md'; MaxLines = 180 },
  [PSCustomObject]@{ Label = '.ai-rules/*.md'; Path = Join-Path $specRoot '.ai-rules'; MaxLines = 160 },
  [PSCustomObject]@{ Label = 'skills/*/SKILL.md'; Path = Join-Path $specRoot 'skills'; MaxLines = 120 }
)

foreach ($budget in $sizeBudgets) {
  if (-not (Test-Path -LiteralPath $budget.Path)) { continue }

  $files = @()
  if ($budget.Label -eq '.ai-rules/*.md') {
    $files = Get-ChildItem -LiteralPath $budget.Path -Filter '*.md' -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -ne 'project-facts.md' }
  } elseif ($budget.Label -eq 'skills/*/SKILL.md') {
    $files = Get-ChildItem -LiteralPath $budget.Path -Directory -ErrorAction SilentlyContinue |
      ForEach-Object {
        $skillFile = Join-Path $_.FullName 'SKILL.md'
        if (Test-Path -LiteralPath $skillFile -PathType Leaf) { Get-Item -LiteralPath $skillFile }
      }
  } else {
    $files = @(Get-Item -LiteralPath $budget.Path -ErrorAction SilentlyContinue)
  }

  foreach ($file in $files) {
    $lineCount = (Get-Content -LiteralPath $file.FullName -Encoding UTF8 | Measure-Object -Line).Lines
    if ($lineCount -gt $budget.MaxLines) {
      $relative = $file.FullName -replace ('^' + [regex]::Escape($specRoot) + '[\\/]*'), ''
      $warnings.Add("Size budget exceeded: $relative has $lineCount lines, budget $($budget.MaxLines). Consider splitting or slimming.")
    }
  }
}

if ($errors.Count -gt 0) {
  Write-Output 'Template check failed:'
  foreach ($e in $errors) { Write-Output "ERROR $e" }
  if ($warnings.Count -gt 0) {
    foreach ($w in $warnings) { Write-Output "WARN $w" }
  }
  exit 1
}

Write-Output "Template check passed: $specRoot"
if ($warnings.Count -gt 0) {
  foreach ($w in $warnings) { Write-Output "WARN $w" }
}




