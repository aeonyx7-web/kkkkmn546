"""
Stop the running GasStation API and free the locked DLL.
Usage: python stop_gasstation.py
On Windows: Run as Administrator to ensure we can kill the process.
"""

import os
import sys
import time
import subprocess
import socket

PID_FROM_ERROR = 7300
PORT = 5000
TARGET_NAMES = {"GasStationApi", "GasStation.Api"}


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_ps(cmd: str) -> str:
    res = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True, text=True
    )
    return (res.stdout or "") + (res.stderr or "")


def list_processes():
    out = run_ps("Get-Process | Select-Object Id,ProcessName,Path | ConvertTo-Json -Depth 2")
    if not out.strip():
        return []
    import json
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        return data
    except Exception:
        return []


def list_listening_pids(port: int):
    out = run_ps(
        f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "
        f"| Select-Object OwningProcess | ConvertTo-Json"
    )
    if not out.strip():
        return []
    import json
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        return [d.get("OwningProcess") for d in data if d.get("OwningProcess")]
    except Exception:
        return []


def kill_pid(pid: int):
    try:
        run_ps(f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue")
        return True
    except Exception:
        return False


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    print("=== Stop GasStation API and free the locked DLL ===")

    if not is_admin():
        print("[WARN] Not running as Administrator. Kill may fail if the process is protected.")
        print("       Re-run this script from an elevated PowerShell/CMD.\n")

    killed = []

    target_pid = PID_FROM_ERROR
    pids = list_processes()
    proc = next((p for p in pids if p.get("Id") == target_pid), None)
    if proc:
        name = proc.get("ProcessName", "?")
        print(f"Killing PID {target_pid} ({name}) from the build error...")
        if kill_pid(target_pid):
            killed.append((target_pid, name))
    else:
        print(f"PID {target_pid} is not running.")

    print("\nScanning for any GasStationApi processes...")
    for p in pids:
        name = (p.get("ProcessName") or "").lower()
        path = (p.get("Path") or "").lower()
        if name in {n.lower() for n in TARGET_NAMES} or "gasstationapi" in path:
            pid = p.get("Id")
            if pid and pid not in [k[0] for k in killed]:
                print(f"Killing {p.get('ProcessName')} (PID {pid}) - {p.get('Path')}")
                if kill_pid(pid):
                    killed.append((pid, p.get("ProcessName")))

    print(f"\nChecking what holds port {PORT}...")
    port_pids = list_listening_pids(PORT)
    for pid in port_pids or []:
        proc = next((p for p in pids if p.get("Id") == pid), None)
        name = proc.get("ProcessName") if proc else "?"
        if pid not in [k[0] for k in killed]:
            print(f"Killing {name} (PID {pid}) - holds port {PORT}")
            if kill_pid(pid):
                killed.append((pid, name))

    time.sleep(2)

    print()
    if port_in_use(PORT):
        print(f"[FAIL] Port {PORT} is STILL in use.")
        print("       Close the process manually from Task Manager and re-run.")
        sys.exit(1)
    else:
        print(f"[OK] Port {PORT} is now free.")

    if killed:
        print("\nKilled processes:")
        for pid, name in killed:
            print(f"  - {name} (PID {pid})")
    else:
        print("\nNo processes were killed.")

    print("\nYou can now re-run the publish/start script.")
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
