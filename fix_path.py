"""
Restore Windows PATH environment variable and run a command in a clean shell.
AUTO-ELEVATES to Administrator if not already elevated.

Usage:
    python fix_path.py
If not run as Administrator, a UAC prompt will appear to relaunch itself elevated.
"""

import os
import sys
import ctypes
import subprocess


BACKUP_REG = r"HKCU\Environment"
SYS_REG    = r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
SCRIPT     = os.path.abspath(__file__)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def request_elevation():
    params = f'"{SCRIPT}"'
    rc = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    if rc <= 32:
        print("[FAIL] Could not elevate. Please right-click PowerShell and 'Run as Administrator'.")
        sys.exit(1)
    print("[OK] Elevated PowerShell window opened. Re-running script there...")
    sys.exit(0)


def run(cmd, shell=False):
    return subprocess.run(cmd, capture_output=True, text=True, shell=shell)


def reg_query(path, name):
    r = run(["reg", "query", path, "/v", name])
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        if name in line:
            parts = line.strip().split("    ")
            return parts[-1] if len(parts) >= 2 else line
    return None


def reg_set(path, name, value, reg_type="REG_EXPAND_SZ"):
    r = run(["reg", "add", path, "/v", name, "/t", reg_type, "/d", value, "/f"])
    return r.returncode == 0


def main():
    print("=== PATH Repair Toolkit ===\n")

    if not is_admin():
        print("[INFO] Not running as Administrator. Requesting elevation...")
        request_elevation()

    print("[OK] Running with Administrator privileges.\n")

    print("1) Current PATH values:")
    user_path = reg_query(BACKUP_REG, "Path")
    sys_path  = reg_query(SYS_REG,    "Path")
    print(f"   User PATH: {(user_path or '(empty)')[:200]}")
    print(f"   System PATH (head): {(sys_path or '(empty)')[:200]}")

    if sys_path and "System32" in sys_path and "cmd.exe" not in sys_path:
        sys_path = r"C:\Windows\System32;" + sys_path
    elif not sys_path:
        sys_path = (
            r"C:\Windows\System32;C:\Windows;"
            r"C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0"
        )

    needed = [
        r"C:\Windows\System32",
        r"C:\Windows",
        r"C:\Windows\System32\Wbem",
        r"C:\Windows\System32\WindowsPowerShell\v1.0",
        r"C:\Program Files\PostgreSQL\17\bin",
        r"C:\Program Files\PostgreSQL\18\bin",
    ]

    parts = [p for p in sys_path.split(";") if p]
    for n in needed:
        if n not in parts:
            parts.append(n)
    new_sys = ";".join(parts)

    print("\n2) Writing repaired System PATH...")
    if reg_set(SYS_REG, "Path", new_sys, "REG_EXPAND_SZ"):
        print("   [OK] System PATH updated.")
    else:
        print("   [FAIL] Could not update System PATH.")

    if user_path:
        up = [p for p in user_path.split(";") if p]
        for n in needed:
            if n not in up:
                up.append(n)
        new_user = ";".join(up)
    else:
        new_user = ";".join(needed)

    if reg_set(BACKUP_REG, "Path", new_user, "REG_EXPAND_SZ"):
        print("   [OK] User PATH updated.")
    else:
        print("   [FAIL] Could not update User PATH.")

    print("\n3) Broadcasting environment change to all processes...")
    run_ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @' "
         "[DllImport(\"user32.dll\", SetLastError=true, CharSet=CharSet.Auto)] "
         "public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, "
         "uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);'@; "
         "$HWND_BROADCAST = [IntPtr]0xffff; "
         "$WM_SETTINGCHANGE = 0x001A; "
         "$result = [UIntPtr]::Zero; "
         "[Win32.NativeMethods]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, "
         "\"Environment\", 2, 5000, [ref]$result) | Out-Null; "
         "Write-Host 'OK'"],
        capture_output=True, text=True
    )
    print("   " + (run_ps.stdout.strip() or run_ps.stderr.strip() or "(no output)"))

    print("\n4) Verifying cmd.exe is reachable from a new elevated shell...")
    test = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + "
         "[Environment]::GetEnvironmentVariable('Path','User'); "
         "Get-Command cmd.exe | Select-Object -ExpandProperty Source"],
        capture_output=True, text=True
    )
    print("   " + (test.stdout.strip() or test.stderr.strip() or "(no output)"))

    print("\n5) Restarting PostgreSQL services...")
    pg_ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + "
         "[Environment]::GetEnvironmentVariable('Path','User'); "
         "Restart-Service postgresql-x64-17 -ErrorAction SilentlyContinue; "
         "Restart-Service postgresql-x64-18 -ErrorAction SilentlyContinue; "
         "Start-Sleep -Seconds 3; "
         "Get-Service postgresql-x64-17,postgresql-x64-18 | "
         "Select-Object Name,Status | Format-Table -AutoSize | Out-String"],
        capture_output=True, text=True
    )
    print(pg_ps.stdout)
    if pg_ps.stderr.strip():
        print("err:", pg_ps.stderr)

    print("\n6) Test psql directly:")
    psql = subprocess.run(
        [r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
         "-U", "postgres", "-h", "localhost", "-p", "5432", "-c", "SELECT version();"],
        capture_output=True, text=True,
        env={**os.environ, "PGPASSWORD": "12345"}
    )
    print(f"   exit: {psql.returncode}")
    print(f"   out : {psql.stdout.strip()[:200]}")
    if psql.stderr.strip():
        print(f"   err : {psql.stderr.strip()[:200]}")

    print("\n=== DONE ===")
    print("Now open a NEW PowerShell window (Win+R -> powershell) and re-run:")
    print("    python finalize_db.py")
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
