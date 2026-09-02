"""
Read appsettings.json of the published API and find the PostgreSQL connection string.
Also list which ports each PG version uses.
Run as Administrator:  python inspect_db.py
"""

import os
import json
import re
import subprocess
import sys
from pathlib import Path

PUBLISH = Path(r"C:\Users\isabelle\Desktop\project\GasStationApi\publish")


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_ps(cmd: str) -> str:
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        capture_output=True, text=True
    )
    return (res.stdout or "") + (res.stderr or "")


def hr(t):
    print(f"\n=== {t} ===")


def find_publish_dir():
    print("Searching for appsettings.json under isabelle's project...")
    candidates = list(Path(r"C:\Users\isabelle\Desktop\project").rglob("appsettings*.json"))
    if not candidates:
        candidates = list(Path(r"C:\Users\isabelle").rglob("appsettings*.json"))
    for p in candidates[:20]:
        print(f"  found: {p}")
    return candidates


def parse_connection_strings(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"cannot read: {e}"
    results = []
    for m in re.finditer(r"ConnectionStrings\"|Host=|Server=|Port=|Database=|Username=|User Id=|Password=|Data Source", text, re.IGNORECASE):
        pass
    try:
        data = json.loads(text)
        cs = data.get("ConnectionStrings", {})
        for name, val in cs.items():
            results.append((name, val))
    except Exception:
        for m in re.finditer(r'"([^"]*ConnectionString[^"]*)"\s*:\s*"([^"]+)"', text):
            results.append((m.group(1), m.group(2)))
    return results


def main():
    print("=== DB Connection Diagnostic ===\n")

    hr("appsettings.json locations")
    files = find_publish_dir()
    if not files:
        print("  None found. Aborting.")
        sys.exit(1)

    hr("Connection strings (raw)")
    for f in files:
        print(f"\n--- {f} ---")
        cs = parse_connection_strings(f)
        if isinstance(cs, str):
            print(cs)
        elif not cs:
            print("  (no ConnectionStrings section)")
        else:
            for name, val in cs:
                print(f"  [{name}]")
                print(f"     {val}")
                if "Host=" in val or "Server=" in val:
                    host = re.search(r"(?:Host|Server)=([^;]+)", val, re.IGNORECASE)
                    port = re.search(r"Port=([^;]+)", val, re.IGNORECASE)
                    db   = re.search(r"Database=([^;]+)", val, re.IGNORECASE)
                    if host: print(f"     -> Host={host.group(1).strip()}")
                    if port: print(f"     -> Port={port.group(1).strip()}")
                    if db:   print(f"     -> Database={db.group(1).strip()}")

    hr("PostgreSQL service ports (from postgresql.conf)")
    for ver in (17, 18):
        conf = Path(f"C:/Program Files/PostgreSQL/{ver}/data/postgresql.conf")
        if not conf.exists():
            print(f"  v{ver}: config not found at {conf}")
            continue
        try:
            txt = conf.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  v{ver}: cannot read ({e})")
            continue
        port_m = re.search(r"^\s*port\s*=\s*(\d+)", txt, re.MULTILINE | re.IGNORECASE)
        listen_m = re.search(r"^\s*listen_addresses\s*=\s*'([^']*)'", txt, re.MULTILINE)
        port = port_m.group(1) if port_m else "?"
        listen = listen_m.group(1) if listen_m else "?"
        print(f"  PG {ver}: port={port}, listen_addresses={listen}")
        print(f"     data dir: C:/Program Files/PostgreSQL/{ver}/data")

    hr("Who is listening on 5432 right now")
    out = run_ps(
        "Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue | "
        "ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
        "  [PSCustomObject]@{ PID=$_.OwningProcess; Port=$_.LocalPort; Process=$p.ProcessName; Path=$p.Path } } | "
        "Format-Table -AutoSize | Out-String"
    )
    print(out.strip() or "  nothing")

    hr("CONCLUSION")
    print("Look at the ConnectionStrings section above:")
    print("  - If the host is 'localhost' or '127.0.0.1' and Port=5432 -> both PG versions compete for 5432.")
    print("  - Whichever version's port matches the appsettings Port= is the one we must keep running.")
    print("  - The other version must be stopped/disabled, or moved to a different port.")

    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
