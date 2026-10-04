param([switch]$Acceptance,[switch]$ReuseLocalToken)

$ErrorActionPreference = 'Stop'
$taskGrowthRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskGrowthRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Growth Python environment is missing; see companion/README.md.'
}
$taskArguments = @('-m', 'companion.launcher')
if ($Acceptance) { $taskArguments += '--acceptance' }
if ($ReuseLocalToken) { $taskArguments += '--reuse-local-token' }
Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskGrowthRoot -WindowStyle Hidden
