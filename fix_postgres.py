"""
Diagnose & repair PostgreSQL 18 (postgresql-x64-18) service that starts then stops.
Run PowerShell as Administrator, then:  python fix_postgres.py
"""

import os
import sys
import time
import subprocess
import re


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_ps(cmd: str) -> tuple[int, str]:
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        capture_output=True, text=True
    )
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def hr(t):
    print(f"\n=== {t} ===")


def step_pg_dir():
    hr("1) Locate PostgreSQL install")
    code, out = run_ps(
        "Get-ChildItem 'C:\\Program Files\\PostgreSQL','C:\\Program Files (x86)\\PostgreSQL' "
        "-Directory -ErrorAction SilentlyContinue | Select-Object FullName | ConvertTo-Json"
    )
    print(out.strip() or "  Not found in default paths.")


def step_event_log():
    hr("2) Read recent PostgreSQL errors from Windows Event Log")
    code, out = run_ps(
        "Get-EventLog -LogName Application -Source 'PostgreSQL' -Newest 8 -ErrorAction SilentlyContinue "
        "| Select-Object TimeGenerated, EntryType, Message | Format-List | Out-String"
    )
    print(out.strip() or "  No PostgreSQL events found.")


def step_listening_5432():
    hr("3) Check port 5432")
    code, out = run_ps(
        "Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue "
        "| Select-Object LocalAddress, LocalPort, OwningProcess, @{n='Proc';e={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} "
        "| Format-Table -AutoSize | Out-String"
    )
    print(out.strip() or "  No process is listening on 5432.")


def step_stop_and_start():
    hr("4) Restart the postgresql-x64-18 service")
    print("Stopping service...")
    code, out = run_ps("Stop-Service -Name 'postgresql-x64-18' -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; $true")
    print("Starting service...")
    code, out = run_ps(
        "Start-Service -Name 'postgresql-x64-18' -ErrorAction SilentlyContinue; "
        "Start-Sleep -Seconds 3; "
        "(Get-Service -Name 'postgresql-x64-18' -ErrorAction SilentlyContinue) | "
        "Select-Object Status, StartType | Format-List | Out-String"
    )
    print(out.strip() or "  Service not found.")


def step_check_data_dir():
    hr("5) Inspect PostgreSQL data directory")
    code, out = run_ps(
        "Get-ChildItem 'C:\\Program Files\\PostgreSQL\\18\\data' -ErrorAction SilentlyContinue "
        "| Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize | Out-String"
    )
    print(out.strip() or "  Default data dir not found; check installation path from step 1.")


def step_log_file():
    hr("6) Tail PostgreSQL log file (last 60 lines)")
    code, out = run_ps(
        "Get-ChildItem 'C:\\Program Files\\PostgreSQL\\18\\data\\log' -Filter '*.log' "
        "-ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | "
        "Select-Object -First 1 | ForEach-Object { Get-Content $_.FullName -Tail 60 }"
    )
    print(out.strip() or "  No log file found.")


def step_kill_other_pg():
    hr("7) Kill any rogue process holding port 5432")
    code, out = run_ps(
        "Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue | "
        "ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
        "if ($p -and $p.ProcessName -ne 'postgres') { "
        "  Write-Host \"Killing $($p.ProcessName) PID $($p.Id)\"; "
        "  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue "
        "} }"
    )
    print(out.strip() or "  None.")


def step_repair_attempt():
    hr("8) Try automatic repair (pg_resetwal + restart)")
    print("This will run pg_resetwal on the default data directory...")
    pg = "C:\\Program Files\\PostgreSQL\\18\\bin"
    data = "C:\\Program Files\\PostgreSQL\\18\\data"
    if not os.path.exists(pg) or not os.path.exists(data):
        print(f"  Default path not found. Adjust pg_resetwal path manually for {pg}.")
        return
    code, out = run_ps(
        f"Stop-Service -Name 'postgresql-x64-18' -Force -ErrorAction SilentlyContinue; "
        f"Start-Sleep -Seconds 2; "
        f"& '{pg}\\pg_resetwal.exe' -f '{data}'; "
        f"Start-Service -Name 'postgresql-x64-18'; "
        f"Start-Sleep -Seconds 3; "
        f"(Get-Service -Name 'postgresql-x64-18').Status"
    )
    print(out.strip())


def main():
    print("=== PostgreSQL 18 Repair Toolkit ===")
    if not is_admin():
        print("[WARN] Not running as Administrator. Some steps will fail.")
        print("       Re-run from an elevated PowerShell/CMD.\n")

    step_pg_dir()
    step_event_log()
    step_listening_5432()
    step_kill_other_pg()
    step_check_data_dir()
    step_log_file()
    step_stop_and_start()
    step_repair_attempt()

    hr("DONE")
    print("If status is still Stopped, the most common causes are:")
    print("  1) Corrupted data dir -> reinstall PostgreSQL or restore a backup")
    print("  2) Another process holds 5432 -> identify and kill it")
    print("  3) Wrong postgresql.conf port / data_dir in the service config")
    print("  4) Insufficient permissions on the data directory")
    print("\nSend me the output of step 6 (log tail) and step 2 (event log) for next steps.")
    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
