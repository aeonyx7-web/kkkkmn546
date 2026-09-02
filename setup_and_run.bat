@echo off
chcp 65001 >nul
title Setup Smart Gas Station System

echo ============================================================
echo  Starting Automated Setup for Smart Gas Station System...
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%setup_environment.ps1

echo [INFO] Project directory: %SCRIPT_DIR%
echo [INFO] Requesting Administrator Privileges...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -Verb RunAs -ArgumentList '-NoExit -NoProfile -ExecutionPolicy Bypass -File \"\"%SCRIPT_PATH%\"\"'"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start PowerShell as Administrator.
    pause
) else (
    echo [OK] Setup window launched. Please follow the instructions in the new window.
    timeout /t 5 >nul
)
