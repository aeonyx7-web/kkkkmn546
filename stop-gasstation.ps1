# Stop the running GasStation API and free the locked DLL
# Run PowerShell as Administrator

Write-Host "=== Stopping .NET Host (PID 7300) and any GasStationApi process ===" -ForegroundColor Cyan

# 1) Kill the specific PID from the error
$pid7300 = Get-Process -Id 7300 -ErrorAction SilentlyContinue
if ($pid7300) {
    Write-Host "Killing PID 7300: $($pid7300.ProcessName)" -ForegroundColor Yellow
    Stop-Process -Id 7300 -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "PID 7300 not running." -ForegroundColor Green
}

# 2) Kill any other GasStationApi / dotnet process holding the publish folder
Get-Process -Name "GasStationApi", "dotnet" -ErrorAction SilentlyContinue | ForEach-Object {
    $path = ""
    try { $path = $_.Path } catch {}
    if ($path -match "GasStationApi" -or $_.ProcessName -eq "GasStationApi") {
        Write-Host "Killing $($_.ProcessName) (PID $($_.Id)) - $path" -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

# 3) Also kill anything listening on port 5000 to be safe
$conns = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    if ($p) {
        Write-Host "Killing $($p.ProcessName) (PID $($p.Id)) - holds port 5000" -ForegroundColor Yellow
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2

# 4) Verify port 5000 is free
$still = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
if ($still) {
    Write-Host "[FAIL] Port 5000 is STILL in use by PID $($still.OwningProcess)" -ForegroundColor Red
} else {
    Write-Host "[OK] Port 5000 is now free." -ForegroundColor Green
}

Write-Host "`nNow you can re-run the publish script and the API will start fresh." -ForegroundColor Cyan
Write-Host "Press any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
