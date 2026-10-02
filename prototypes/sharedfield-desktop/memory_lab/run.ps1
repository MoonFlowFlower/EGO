param(
    [ValidateSet('setup','start','test','smoke','development','memory','growth','report','stop','campaign')]
    [string]$Command = 'test',
    [ValidateSet('baseline','memos','hindsight')][string]$Arm = 'baseline',
    [string]$Run = 'comparison-02',
    [string]$Batch = 'batch-01',
    [string]$Campaign = 'reliability-01',
    [ValidateSet('deepseek','qwen37','qwen35','gemini')][string]$Profile = 'deepseek'
)
$ErrorActionPreference = 'Stop'
$labRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $labRoot
Set-Location -LiteralPath $projectRoot
$labPython = Join-Path $labRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $labPython)) {
    & uv venv --python 3.11.15 (Join-Path $labRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create isolated Python environment' }
}
switch ($Command) {
    'setup' { & $labPython -B -m memory_lab.manage setup }
    'start' { & $labPython -B -m memory_lab.manage start --batch $Batch --profile $Profile --campaign $Campaign }
    'campaign' { & $labPython -B -m memory_lab.campaign --id $Campaign }
    'stop' { & $labPython -B -m memory_lab.manage stop }
    'test' { & $labPython -B -m unittest discover -s memory_lab/tests -v }
    'smoke' { & $labPython -B -m memory_lab.smoke $Arm --id (Get-Date -Format 'yyyyMMdd-HHmmss') }
    'development' { & $labPython -B -m memory_lab.runner --split development --run $Run }
    'memory' { & $labPython -B -m memory_lab.runner --split heldout --run $Run }
    'growth' { & $labPython -B -m memory_lab.growth --arm $Arm --memory-run $Run }
    'report' { & $labPython -B -m memory_lab.report memory --run $Run }
}
if ($LASTEXITCODE -ne 0) { throw "memory_lab $Command failed; inspect evidence before retrying paid work" }
