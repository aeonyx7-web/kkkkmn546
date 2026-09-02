"""
Smart Gas Station - Diagnostic & Fix Script (Python)
Usage: python fix-gasstation.py
Requires: pip install requests
On Windows: Run as Administrator to allow firewall changes.
"""

import subprocess
import sys
import socket
import urllib.request
import urllib.error
import os
from pathlib import Path

PORT = 5000
BASE = f"http://localhost:{PORT}"


def step(msg):
    print(f"\n=== {msg} ===")


def ok(msg):
    print(f"[OK]   {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def err(msg):
    print(f"[FAIL] {msg}")


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def port_listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except (OSError, socket.timeout):
        return False


def test_api():
    for path in ("/swagger", "/swagger/index.html", "/", "/api/health"):
        try:
            req = urllib.request.Request(BASE + path, headers={"User-Agent": "diag"})
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    ok(f"API responds at {BASE}{path} (status {r.status})")
                    return True
        except urllib.error.HTTPError as e:
            if e.code < 500:
                ok(f"API responds at {BASE}{path} (status {e.code})")
                return True
        except Exception:
            pass
    err(f"Cannot reach API at {BASE}")
    return False


def add_firewall_rule():
    if not is_admin():
        warn("Not running as Administrator -> cannot modify Windows Firewall.")
        warn("Re-run PowerShell as Administrator to apply the firewall rule.")
        return
    rule_name = f"Smart Gas Station API ({PORT})"
    check = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
        capture_output=True, text=True
    )
    if rule_name in check.stdout:
        ok(f"Firewall rule already exists: {rule_name}")
        return
    cmd = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={rule_name}",
        "dir=in", "action=allow", "protocol=TCP",
        f"localport={PORT}", "profile=any"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        ok(f"Firewall rule created for TCP/{PORT}")
    else:
        err(f"Failed to create firewall rule: {res.stderr.strip()}")


def scan_frontend_config():
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "frontend",
        here.parent / "smart-gas-frontend",
        here.parent / "client",
        here.parent / "web",
        here.parent.parent / "frontend",
    ]
    patterns = ("environment.ts", "environment.prod.ts", "config.ts",
                "api.config.ts", ".env", ".env.local", "app.config.ts")
    keywords = ("localhost:5000", "127.0.0.1:5000", "baseUrl", "API_URL", "apiUrl")
    found = False
    for folder in candidates:
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if not p.is_file():
                continue
            if p.name.endswith(patterns) or p.suffix in (".ts", ".js", ".json"):
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for kw in keywords:
                    if kw in txt:
                        for line in txt.splitlines():
                            if kw in line:
                                print(f"  -> {p}: {line.strip()}")
                                found = True
                        break
    if not found:
        warn("Frontend config not found automatically. Check manually:")
        print("     - src/environments/environment*.ts (Angular)")
        print("     - src/config.ts or .env (React/Vue)")
        print("     - baseUrl must equal 'http://localhost:5000'")


def main():
    step(f"1) Check if API is listening on port {PORT}")
    if port_listening(PORT):
        ok(f"Port {PORT} is open on localhost")
    else:
        err(f"No service listening on port {PORT}!")
        print("  -> Start the backend (run the published app).")
        if not test_api():
            sys.exit(1)

    step("2) Test API response")
    api_ok = test_api()
    if not api_ok:
        err("API did not respond. Check the backend logs.")
        sys.exit(1)

    step(f"3) Ensure Windows Firewall allows TCP/{PORT}")
    add_firewall_rule()

    step("4) Scan frontend for API base URL")
    scan_frontend_config()

    step("5) Next steps for your friend")
    print(f"  - Open browser: {BASE}/swagger  (verify backend)")
    print("  - Open the frontend, then press F12 -> Console/Network")
    print("  - If CORS error: add the frontend origin in Program.cs AddCors(...)")
    print("\nDiagnostic finished.")


if __name__ == "__main__":
    main()
