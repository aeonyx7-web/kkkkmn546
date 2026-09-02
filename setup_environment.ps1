# ==============================================================================
# Script: setup_environment.ps1
# Description: تثبيت جميع المتطلبات اللازمة للمشروع تلقائياً على نظام Windows
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

try {
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "    بدء إعداد وتثبيت بيئة تشغيل نظام محطة الوقود الذكية" -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan

    # تحديد مسار المجلد الحالي بدقة
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    if (-not $scriptDir) {
        $scriptDir = (Get-Location).Path
    }
    Set-Location $scriptDir
    Write-Host "[*] مسار المشروع: $scriptDir" -ForegroundColor Gray

    # 1. التحقق من صلاحيات المسؤول
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "[!] يتطلب السكريبت صلاحيات مسؤول (Administrator)." -ForegroundColor Yellow
        Write-Host "[*] جاري طلب الإذن وإعادة التشغيل كمسؤول..." -ForegroundColor Yellow
        $scriptPath = if ($PSCommandPath) { $PSCommandPath } else { Join-Path $scriptDir "setup_environment.ps1" }
        Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoExit -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
        exit
    }

    Write-Host "[✓] يعمل بصلاحيات المسؤول (Administrator)." -ForegroundColor Green

    # 2. التحقق من وجود winget
    Write-Host "`n[*] التحقق من أداة winget..." -ForegroundColor Cyan
    $wingetCmd = Get-Command "winget" -ErrorAction SilentlyContinue
    if (-not $wingetCmd) {
        # محاولة البحث عن مسار winget في AppData المحلي
        $localWinget = "$env:LOCALAPPDATA\Microsoft\WindowsApps\winget.exe"
        if (Test-Path $localWinget) {
            $env:Path = "$env:LOCALAPPDATA\Microsoft\WindowsApps;$env:Path"
            $wingetCmd = Get-Command "winget" -ErrorAction SilentlyContinue
        }
    }

    if (-not $wingetCmd) {
        Write-Host "[X] أداة winget غير مثبتة على هذا الجهاز!" -ForegroundColor Red
        Write-Host "يرجى تثبيت 'App Installer' من متجر Microsoft Store لتفعيل winget." -ForegroundColor Yellow
        Write-Host "الرابط: https://aka.ms/getwinget" -ForegroundColor Yellow
        Write-Host "`nاضغط أي زر للخروج..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
    Write-Host "[✓] أداة winget متوفرة ومستعدة." -ForegroundColor Green

    # دالة لتحديث متغيرات البيئة (PATH)
    function Refresh-EnvironmentVariables {
        Write-Host "[*] تحديث متغيرات المسار (PATH)..." -ForegroundColor Gray
        $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = "$machinePath;$userPath"

        $commonPaths = @(
            "C:\Program Files\dotnet",
            "C:\Program Files\nodejs",
            "C:\Program Files\PostgreSQL\16\bin",
            "C:\Program Files\PostgreSQL\17\bin",
            "C:\Program Files\PostgreSQL\18\bin",
            "$env:LOCALAPPDATA\Programs\Python\Python312",
            "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
        )
        foreach ($p in $commonPaths) {
            if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) {
                $env:Path = "$p;$env:Path"
            }
        }
    }

    # دالة لتثبيت حزمة عبر winget
    function Install-PackageIfMissing {
        param (
            [string]$Name,
            [string]$PackageId,
            [string]$CheckCommand
        )

        Write-Host "`n------------------------------------------------------" -ForegroundColor DarkCyan
        Write-Host "[*] فحص: $Name..." -ForegroundColor Cyan

        $isInstalled = $false
        if ($CheckCommand) {
            try {
                $checkResult = Invoke-Expression $CheckCommand -ErrorAction Stop
                if ($checkResult) { $isInstalled = $true }
            } catch {
                $isInstalled = $false
            }
        }

        if ($isInstalled) {
            Write-Host "[✓] $Name مثبت بالفعل مسبقاً." -ForegroundColor Green
        } else {
            Write-Host "[+] $Name غير مثبت، جاري التحميل والتثبيت التلقائي..." -ForegroundColor Yellow
            & winget install --id $PackageId --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
            Refresh-EnvironmentVariables
            Write-Host "[✓] انتهى إجراء تثبيت $Name." -ForegroundColor Green
        }
    }

    # 3. تثبيت المتطلبات
    Install-PackageIfMissing -Name ".NET 9.0 SDK" -PackageId "Microsoft.DotNet.SDK.9" -CheckCommand "dotnet --version"
    Install-PackageIfMissing -Name "Node.js LTS (مع npm)" -PackageId "OpenJS.NodeJS.LTS" -CheckCommand "node --version"
    Install-PackageIfMissing -Name "Python 3" -PackageId "Python.Python.3.12" -CheckCommand "python --version"
    Install-PackageIfMissing -Name "PostgreSQL" -PackageId "PostgreSQL.PostgreSQL.16" -CheckCommand "Get-Service postgresql*"

    Refresh-EnvironmentVariables

    # 4. فحص وتشغيل خدمة PostgreSQL
    Write-Host "`n------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "[*] فحص وتشغيل خدمة PostgreSQL..." -ForegroundColor Cyan
    $pgService = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($pgService) {
        if ($pgService.Status -ne 'Running') {
            Write-Host "[+] جاري بدء خدمة PostgreSQL ($($pgService.Name))..." -ForegroundColor Yellow
            Start-Service $pgService.Name
            Set-Service -Name $pgService.Name -StartupType Automatic
            Write-Host "[✓] تم تشغيل الخدمة بنجاح." -ForegroundColor Green
        } else {
            Write-Host "[✓] خدمة PostgreSQL تعمل بالفعل ($($pgService.Name))." -ForegroundColor Green
        }
    } else {
        Write-Host "[!] تنبيه: إذا تم تثبيت PostgreSQL للتو، قد تحتاج لإعادة تشغيل الجهاز مرة واحدة لتفعيل الخدمة." -ForegroundColor Yellow
    }

    # 5. بناء وتشغيل المشروع
    Write-Host "`n======================================================" -ForegroundColor Cyan
    Write-Host "    اكتمال تثبيت جميع المتطلبات! جاري بناء المشروع...  " -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan

    Set-Location $scriptDir

    if (Test-Path "$scriptDir\run_project.py") {
        Write-Host "[*] جاري تشغيل سكريبت run_project.py..." -ForegroundColor Cyan
        python "$scriptDir\run_project.py"
    } else {
        Write-Host "[*] تثبيت حزم npm..." -ForegroundColor Cyan
        npm install
        Write-Host "[*] بناء الفرونت إند..." -ForegroundColor Cyan
        npm run build
        Write-Host "[*] بناء الباك إند..." -ForegroundColor Cyan
        Set-Location "$scriptDir\GasStationApi"
        dotnet publish GasStationApi.csproj -c Release -o ./publish /p:CompressWebAssets=false
        Set-Location "$scriptDir\GasStationApi\publish"
        Write-Host "[*] تشغيل الخادم..." -ForegroundColor Green
        dotnet GasStationApi.dll
    }

} catch {
    Write-Host "`n[X] حدث خطأ أثناء تنفيذ السكريبت:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}

Write-Host "`n------------------------------------------------------" -ForegroundColor Gray
Write-Host "اكتمل التنفيذ. اضغط أي زر للإغلاق..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
