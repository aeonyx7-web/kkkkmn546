"""
Force-recover PostgreSQL 18 when the service refuses to start.
Run PowerShell as Administrator:  python fix_postgres_lock.py

Steps:
  A) Kill all postgres processes
  B) Delete postmaster.pid lock file
  C) Verify port 5432 is free
  D) Reset WAL with pg_resetwal
  E) Re-register the Windows service if it is broken, then start it
"""

import os
import sys
import subprocess
import time

DATA_DIR = r"C:\Program Files\PostgreSQL\18\data"
PG_BIN   = r"C:\Program Files\PostgreSQL\18\bin"
SERVICE  = "postgresql-x64-18"


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run(cmd: str) -> tuple[int, str]:
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        capture_output=True, text=True
    )
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def hr(t):
    print(f"\n=== {t} ===")


def main():
    print("=== PostgreSQL 18 Force-Recovery ===")
    if not is_admin():
        print("[FAIL] Must be run as Administrator.")
        sys.exit(1)

    hr("A) Kill any leftover postgres processes")
    code, out = run(
        "Get-Process postgres -ErrorAction SilentlyContinue | "
        "ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }; "
        "Start-Sleep -Seconds 2; "
        "Get-Process postgres -ErrorAction SilentlyContinue | Select-Object Id,ProcessName | Format-Table -AutoSize | Out-String"
    )
    print(out.strip() or "  No postgres processes running.")

    hr("B) Delete postmaster.pid lock file")
    pid_file = os.path.join(DATA_DIR, "postmaster.pid")
    if os.path.exists(pid_file):
        code, out = run(f"Remove-Item -LiteralPath '{pid_file}' -Force -ErrorAction Stop; 'Deleted.'")
        print(f"  Deleted: {pid_file}")
        print(out.strip())
    else:
        print(f"  No postmaster.pid at {pid_file} (good).")

    hr("C) Verify port 5432 is free")
    code, out = run(
        "Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue | "
        "Format-Table -AutoSize | Out-String"
    )
    print(out.strip() or "  Port 5432 is FREE.")

    hr("D) Run pg_resetwal to repair WAL")
    code, out = run(
        f"Stop-Service -Name '{SERVICE}' -Force -ErrorAction SilentlyContinue; "
        f"Start-Sleep -Seconds 1; "
        f"& '{PG_BIN}\\pg_resetwal.exe' -f '{DATA_DIR}'"
    )
    print(out.strip() or "  (no output)")

    hr("E) Try starting the service")
    code, out = run(
        f"Start-Service -Name '{SERVICE}' -ErrorAction SilentlyContinue; "
        f"Start-Sleep -Seconds 4; "
        f"(Get-Service -Name '{SERVICE}' -ErrorAction SilentlyContinue) | "
        f"Select-Object Status, StartType, Name | Format-List | Out-String"
    )
    print(out.strip())

    if "Running" in out:
        print("\n[OK] Service is RUNNING. Test with: psql -U postgres -h localhost")
        input("Press Enter to close...")
        return

    hr("F) Re-register the Windows service (recreate it cleanly)")
    pg_ctl = os.path.join(PG_BIN, "pg_ctl.exe")
    print(f"  pg_ctl: {pg_ctl}")
    if not os.path.exists(pg_ctl):
        print("  pg_ctl.exe not found at default path. Edit the script to your install path.")
        input("Press Enter to close...")
        return

    code, out = run(
        f"& '{pg_ctl}' unregister -N '{SERVICE}'; "
        f"Start-Sleep -Seconds 2; "
        f"& '{pg_ctl}' register -N '{SERVICE}' -D '{DATA_DIR}'; "
        f"Start-Sleep -Seconds 1; "
        f"Start-Service -Name '{SERVICE}' -ErrorAction SilentlyContinue; "
        f"Start-Sleep -Seconds 4; "
        f"(Get-Service -Name '{SERVICE}').Status"
    )
    print(out.strip())

    hr("G) Final status")
    code, out = run(
        f"Get-Service -Name '{SERVICE}' -ErrorAction SilentlyContinue | "
        f"Select-Object Status, StartType | Format-List | Out-String; "
        f"Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue | "
        f"Format-Table -AutoSize | Out-String"
    )
    print(out.strip())

    print("\nIf still Stopped, send me the output of:")
    print("  - 'pg_ctl.exe start -D <data> -l pg_start.log' (run from cmd)")
    print("  - tail of <data>\\log\\postgresql-*.log (last 50 lines)")
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
