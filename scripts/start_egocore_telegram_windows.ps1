$EnableH1CanonicalShadow = $env:EGO_ENABLE_H1_CANONICAL_SHADOW
$H1CanonicalShadowAllowlist = $env:EGO_H1_CANONICAL_SHADOW_ALLOWLIST
$RepoRootOverride = $env:EGO_REPO_ROOT
$WindowsPythonOverride = $env:EGO_WINDOWS_PYTHON

$repoRoot = if ($RepoRootOverride) {
    $RepoRootOverride
} else {
    Split-Path -Parent $PSScriptRoot
}
$root = Join-Path $repoRoot "EgoCore"
$openEmotion = Join-Path $repoRoot "OpenEmotion"
$stdout = Join-Path $root "logs\egocore_run.log"
$stderr = Join-Path $root "logs\egocore_err.log"
$pythonLauncher = if ($WindowsPythonOverride) { $WindowsPythonOverride } else { "py" }
$pythonArgs = if ($WindowsPythonOverride) { @("-u", "-m", "app.main", "--telegram") } else { @("-3", "-u", "-m", "app.main", "--telegram") }

if (Test-Path $stdout) {
    Remove-Item $stdout -Force
}
if (Test-Path $stderr) {
    Remove-Item $stderr -Force
}

$env:PYTHONPATH = $openEmotion
if ($EnableH1CanonicalShadow) {
    $env:EGO_ENABLE_H1_CANONICAL_SHADOW = $EnableH1CanonicalShadow
}
if ($H1CanonicalShadowAllowlist) {
    $env:EGO_H1_CANONICAL_SHADOW_ALLOWLIST = $H1CanonicalShadowAllowlist
}
$process = Start-Process `
    -FilePath $pythonLauncher `
    -ArgumentList $pythonArgs `
    -WorkingDirectory $root `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

Write-Output $process.Id
