#requires -RunAsAdministrator
# Smart Gas Station - Diagnostic & Fix Script
# Usage: Run PowerShell as Administrator, then: .\fix-gasstation.ps1

$ErrorActionPreference = "Stop"
$port = 5000

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[FAIL] $msg" -ForegroundColor Red }

Write-Step "1) فحص عمل API على المنفذ $port"
$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Ok "البورت $port مفتوح ويستمع (PID: $($listener.OwningProcess))"
} else {
    Write-Err "لا توجد خدمة تستمع على البورت $port!"
    Write-Host "  -> تأكد أن الباك إند يعمل (شغّل التطبيق من publish folder)." -ForegroundColor Yellow
}

Write-Step "2) اختبار استجابة الـ API محلياً"
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$port/swagger" -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -eq 200) { Write-Ok "API يستجيب على http://localhost:$port" }
} catch {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$port/" -UseBasicParsing -TimeoutSec 5
        Write-Ok "API يستجيب على الجذر (Status: $($resp.StatusCode))"
    } catch {
        Write-Err "فشل الاتصال بـ http://localhost:$port من نفس الجهاز!"
    }
}

Write-Step "3) فحص الـ Firewall للمنفذ $port"
$rules = Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object {
    $_.DisplayName -match "GasStation|Smart Gas|$port" -or
    $_.DisplayName -match "5000"
}
if ($rules) {
    Write-Ok "تم العثور على قواعد: $($rules.DisplayName -join ', ')"
} else {
    Write-Warn "لا توجد قاعدة Firewall صريحة للمنفذ $port"
    Write-Host "  -> جاري إنشاء قاعدة للسماح..." -ForegroundColor Yellow

    New-NetFirewallRule -DisplayName "Smart Gas Station API ($port)" `
        -Direction Inbound -Protocol TCP -LocalPort $port `
        -Action Allow -Profile Any | Out-Null
    Write-Ok "تم إنشاء قاعدة Firewall للسماح بالمنفذ $port"
}

Write-Step "4) فحص إعداد الفرونت (عنوان الـ API)"
$frontendPaths = @(
    "$PSScriptRoot\..\frontend",
    "$PSScriptRoot\..\smart-gas-frontend",
    "$PSScriptRoot\..\client",
    "$PSScriptRoot\..\..\frontend",
    "$PSScriptRoot\..\..\smart-gas-frontend"
)

$foundConfig = $false
foreach ($p in $frontendPaths) {
    if (Test-Path $p) {
        Get-ChildItem -Path $p -Recurse -Include *.json,*.ts,*.js,*.env* -ErrorAction SilentlyContinue |
            Select-String -Pattern "localhost:5000|127\.0\.0\.1:5000|baseUrl|API_URL" -List |
            ForEach-Object {
                Write-Host "  -> $($_.Path): $($_.Line.Trim())" -ForegroundColor Gray
                $foundConfig = $true
            }
    }
}
if (-not $foundConfig) {
    Write-Warn "لم يتم العثور على إعداد الفرونت تلقائياً. تحقق يدوياً من:"
    Write-Host "     src/environments/environment.ts (Angular)" -ForegroundColor Yellow
    Write-Host "     .env أو src/config.ts (React/Vue)" -ForegroundColor Yellow
    Write-Host "     يجب أن يكون baseUrl = 'http://localhost:5000'" -ForegroundColor Yellow
}

Write-Step "5) ملخص"
Write-Host "  - افتح المتصفح على: http://localhost:$port/swagger (للتأكد من الباك)" -ForegroundColor White
Write-Host "  - افتح F12 في المتصفح وشاهد Network/Console لمعرفة الخطأ الفعلي" -ForegroundColor White
Write-Host "  - إذا ظهر CORS: أضف origin الفرونت في Program.cs داخل builder.Services.AddCors" -ForegroundColor White

Write-Host "`nانتهى الفحص." -ForegroundColor Cyan
