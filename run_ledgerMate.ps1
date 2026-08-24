<#
.SYNOPSIS
LedgerMate Windows development launcher with lifecycle guard.
#>
param(
    [switch]$Stop,
    [switch]$Restart,
    [string]$Url = "http://127.0.0.1:8000"
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Get-UrlStatus([string]$u) {
    try {
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3
        return $r.StatusCode
    } catch {
        return $null
    }
}

function Find-LedgerMatePid {
    $listen = netstat -ano | Select-String ":8000\s+.*LISTENING"
    if (-not $listen) { return $null }
    foreach ($line in $listen) {
        $parts = $line.ToString().Trim() -split '\s+'
        if ($parts.Count -ge 5) {
            $pid = $parts[-1]
            $cmd = tasklist /FI "PID eq $pid" /FO CSV /NH 2>$null | ConvertFrom-Csv -ErrorAction SilentlyContinue
            if ($cmd -and $cmd.ImageName -match "python") {
                $wmic = wmic process where "ProcessId=$pid" get CommandLine /format:list 2>$null
                if ($wmic -match "ledgermate") { return [int]$pid }
            }
        }
    }
    return $null
}

if ($Stop) {
    $pid = Find-LedgerMatePid
    if ($pid) {
        Write-Host "[LedgerMate] Stopping PID $pid ..."
        Stop-Process -Id $pid -Force
        Start-Sleep -Seconds 2
        Write-Host "[LedgerMate] Stopped."
    } else {
        Write-Host "[LedgerMate] No running LedgerMate found on port 8000."
    }
    exit 0
}

if ($Restart) {
    & $PSCommandPath -Stop
    & $PSCommandPath
    exit 0
}

$health = Get-UrlStatus "$Url/api/health"
if ($health -eq 200) {
    Write-Host "[LedgerMate] Already running at $Url"
    Start-Process $Url
    exit 0
}

$pid = Find-LedgerMatePid
if ($pid) {
    Write-Host "[LedgerMate] Stale LedgerMate detected (PID $pid). Stopping..."
    Stop-Process -Id $pid -Force
    Start-Sleep -Seconds 2
}

Write-Host "[LedgerMate] Starting server..."
$proc = Start-Process -FilePath "python" -ArgumentList "src\ledgermate\api.py" -PassThru -NoNewWindow
Start-Sleep -Seconds 3
$health2 = Get-UrlStatus "$Url/api/health"
if ($health2 -eq 200) {
    Write-Host "[LedgerMate] Started successfully at $Url (PID $($proc.Id))"
    Start-Process $Url
} else {
    Write-Host "[LedgerMate] Failed to confirm health at $Url"
    exit 1
}
