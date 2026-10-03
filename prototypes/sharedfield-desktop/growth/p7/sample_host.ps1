param([int]$Samples = 12, [int]$IntervalSeconds = 2)
$ErrorActionPreference = 'Stop'
$sampleRoot = Join-Path $PSScriptRoot '..\runs\p7\host'
New-Item -ItemType Directory -Path $sampleRoot -Force | Out-Null
$samplePath = Join-Path $sampleRoot ((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '.jsonl')
$processorCount = [Environment]::ProcessorCount
$previousCpu = @{}
$previousTime = $null
for ($sampleIndex = 0; $sampleIndex -lt $Samples; $sampleIndex++) {
    $sampleTime = [DateTimeOffset]::UtcNow
    # Only named P7 components; other Python/Node workloads are intentionally not attributed.
    $processes = @(Get-Process airi,java -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -eq 'airi' -or $_.MainWindowTitle -like 'Minecraft 1.21.1*'
    })
    $processRows = @($processes | ForEach-Object {
        $cpuValue = $_.CPU
        $cpuPercent = $null
        if ($null -ne $previousTime -and $previousCpu.ContainsKey($_.Id)) {
            $elapsed = ($sampleTime - $previousTime).TotalSeconds
            $cpuPercent = 100 * ($cpuValue - $previousCpu[$_.Id]) / $elapsed / $processorCount
        }
        $previousCpu[$_.Id] = $cpuValue
        [ordered]@{pid=$_.Id; name=$_.ProcessName; cpu_seconds=$cpuValue; cpu_percent_of_all_logical_processors=$cpuPercent;
            working_set_bytes=$_.WorkingSet64; private_bytes=$_.PrivateMemorySize64}
    })
    $connections = @(Get-NetTCPConnection -State Established,Listen -ErrorAction SilentlyContinue | Where-Object {
        $_.OwningProcess -in $processes.Id
    } | Select-Object OwningProcess,State,LocalAddress,LocalPort,RemoteAddress,RemotePort)
    $gpu = & nvidia-smi --query-gpu=name,temperature.gpu,clocks.current.graphics,memory.used,memory.total,utilization.gpu,power.draw --format=csv,noheader,nounits
    $record = [ordered]@{utc=$sampleTime.ToString('o'); logical_processors=$processorCount;
        scope='partial: AIRI and Minecraft client; no claim of complete body plus local voice coexistence';
        processes=$processRows; tcp=$connections; gpu_csv_name_C_MHz_usedMiB_totalMiB_percent_W=@($gpu)}
    $record | ConvertTo-Json -Depth 6 -Compress | Add-Content -LiteralPath $samplePath -Encoding utf8
    $previousTime = $sampleTime
    if ($sampleIndex -lt ($Samples - 1)) { Start-Sleep -Seconds $IntervalSeconds }
}
Write-Output $samplePath
