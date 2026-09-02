"""
Resolve the PostgreSQL 17 vs 18 port-5432 conflict on your friend's machine.
Strategy:
  1) Move PG 18 to port 5433 (so PG 17 keeps 5432, which the app expects).
  2) Ensure the database 'smartgasstationsimpledb' exists on PG 17.
  3) Verify connectivity from psql.
  4) Final summary.

Run as Administrator:  python finalize_db.py
"""

import os
import subprocess
import sys
import time

PG17_BIN  = r"C:\Program Files\PostgreSQL\17\bin"
PG18_BIN  = r"C:\Program Files\PostgreSQL\18\bin"
PG17_DATA = r"C:\Program Files\PostgreSQL\17\data"
PG18_DATA = r"C:\Program Files\PostgreSQL\18\data"
PG17_SVC  = "postgresql-x64-17"
PG18_SVC  = "postgresql-x64-18"
DB_NAME   = "smartgasstationsimpledb"
APP_USER  = "postgres"
APP_PASS  = "12345"


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run(cmd: str, shell=False) -> tuple[int, str]:
    if not shell:
        res = subprocess.run(cmd, capture_output=True, text=True)
    else:
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def run_ps(cmd: str) -> str:
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        capture_output=True, text=True
    )
    return (res.stdout or "") + (res.stderr or "")


def hr(t):
    print(f"\n=== {t} ===")


def main():
    print("=== Finalize PostgreSQL setup ===")
    if not is_admin():
        print("[FAIL] Must run as Administrator.")
        sys.exit(1)

    # 1) Stop both services cleanly
    hr("1) Stop both PG services")
    print(run_ps(f"Stop-Service -Name '{PG17_SVC}','{PG18_SVC}' -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; 'done'"))

    # Kill any leftover postgres processes
    print(run_ps(
        "Get-Process postgres -ErrorAction SilentlyContinue | "
        "ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }; Start-Sleep -Seconds 2; 'killed'"
    ))

    # Clean up stale lock file in PG 18
    pid_file = os.path.join(PG18_DATA, "postmaster.pid")
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
            print(f"Removed stale lock: {pid_file}")
        except Exception as e:
            print(f"Could not remove lock: {e}")

    # 2) Move PG 18 to port 5433
    hr("2) Move PG 18 to port 5433")
    conf18 = os.path.join(PG18_DATA, "postgresql.conf")
    if os.path.exists(conf18):
        try:
            text = open(conf18, "r", encoding="utf-8", errors="ignore").read()
            import re
            new = re.sub(r"(?im)^(\s*)port\s*=\s*\d+", r"\1port = 5433", text)
            if "port = 5433" not in new:
                new = new.replace("port = 5432", "port = 5433")
            open(conf18, "w", encoding="utf-8").write(new)
            print("PG 18 postgresql.conf updated to port=5433")
        except Exception as e:
            print(f"Could not edit config: {e}")
    else:
        print("PG 18 config not found")

    # 3) Start PG 17 (port 5432) first
    hr("3) Start PG 17 on 5432")
    print(run_ps(f"Start-Service -Name '{PG17_SVC}' -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; (Get-Service '{PG17_SVC}').Status"))

    # 4) Start PG 18 (port 5433)
    hr("4) Start PG 18 on 5433")
    print(run_ps(f"Start-Service -Name '{PG18_SVC}' -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; (Get-Service '{PG18_SVC}').Status"))

    # 5) Verify ports
    hr("5) Port verification")
    out = run_ps(
        "Get-NetTCPConnection -LocalPort 5432,5433 -State Listen -ErrorAction SilentlyContinue | "
        "ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
        "  [PSCustomObject]@{ Port=$_.LocalPort; PID=$_.OwningProcess; Process=$p.ProcessName } } | "
        "Format-Table -AutoSize | Out-String"
    )
    print(out.strip())

    # 6) Ensure target DB exists on PG 17
    hr(f"6) Check / create database '{DB_NAME}' on PG 17")
    list_dbs = run([
        os.path.join(PG17_BIN, "psql.exe"),
        "-U", APP_USER, "-h", "localhost", "-p", "5432",
        "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}';"
    ])
    print(f"  query exit code: {list_dbs[0]}")
    print(f"  query output   : {list_dbs[1].strip() or '(empty)'}")

    if list_dbs[0] != 0 or "1" not in list_dbs[1]:
        print(f"  -> Database '{DB_NAME}' NOT found. Creating it...")
        env = os.environ.copy()
        env["PGPASSWORD"] = APP_PASS
        create = run([
            os.path.join(PG17_BIN, "psql.exe"),
            "-U", APP_USER, "-h", "localhost", "-p", "5432",
            "-c", f"CREATE DATABASE \"{DB_NAME}\";"
        ], shell=False)
        # pass env manually
        create = subprocess.run(
            [os.path.join(PG17_BIN, "psql.exe"),
             "-U", APP_USER, "-h", "localhost", "-p", "5432",
             "-c", f"CREATE DATABASE \"{DB_NAME}\";"],
            capture_output=True, text=True, env=env
        )
        print(f"  create exit: {create.returncode}")
        print(f"  create out : {create.stdout}")
        print(f"  create err : {create.stderr}")
    else:
        print(f"  -> Database '{DB_NAME}' already exists.")

    # 7) Connectivity test
    hr("7) Connectivity test (psql)")
    env = os.environ.copy()
    env["PGPASSWORD"] = APP_PASS
    test = subprocess.run(
        [os.path.join(PG17_BIN, "psql.exe"),
         "-U", APP_USER, "-h", "localhost", "-p", "5432",
         "-d", DB_NAME, "-c", "SELECT version();"],
        capture_output=True, text=True, env=env
    )
    print(f"  exit: {test.returncode}")
    print(f"  out : {test.stdout.strip()}")
    if test.stderr.strip():
        print(f"  err : {test.stderr.strip()}")

    # 8) Make sure PGPASSWORD works in Windows env so Npgsql can use it
    hr("8) Optional: persist PGPASSWORD for the API process")
    print(f"  Note: the API uses password from appsettings.json, not PGPASSWORD.")
    print(f"  The password in appsettings.json is: {APP_PASS}")
    print(f"  If the API still fails to connect, set the env var before running it:")
    print(f'     setx PGPASSWORD "{APP_PASS}"')

    hr("DONE")
    print("Next steps:")
    print("  1) Stop the existing API process (port 5000).")
    print("  2) Re-run 'dotnet publish' so the new build replaces the locked DLL.")
    print("  3) Restart the API from the fresh publish folder.")
    print("  4) Open the frontend and check the connection again.")
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
