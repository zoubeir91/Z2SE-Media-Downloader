from pathlib import Path
import ast, hashlib, json, sys

version = sys.argv[1]
assert version == "33.10"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:200], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.09"', 'APP_VERSION = "33.10"')

old_ping = '''def pot_ping():
    try:
        with urllib.request.urlopen(POT_PING_URL, timeout=1) as response:
            return 200 <= response.status < 300
    except Exception:
        return False
'''

new_ping = r'''def _pot_ping_info():
    """Return verified provider identity; HTTP 200 alone is not trusted."""
    try:
        request = urllib.request.Request(
            POT_PING_URL,
            headers={"Accept": "application/json", "User-Agent": "Z2SE/" + APP_VERSION},
        )
        with urllib.request.urlopen(request, timeout=1.5) as response:
            if not (200 <= int(response.status) < 300):
                return {}
            payload = json.loads(response.read(16384).decode("utf-8", errors="strict"))
        version = str(payload.get("version") or "").strip()
        if version != POT_REQUIRED_VERSION:
            return {"version": version, "mismatch": True}
        return {"version": version, "uptime": payload.get("server_uptime")}
    except Exception:
        return {}


def _pot_listener_loopback_only():
    """On Windows, reject a provider exposed beyond the local machine."""
    if os.name != "nt":
        return None
    try:
        script = (
            "$x=Get-NetTCPConnection -LocalPort 4416 -State Listen "
            "-ErrorAction SilentlyContinue|Select-Object -ExpandProperty LocalAddress -Unique;"
            "if($x){$x -join ','}"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            return None
        addresses = [item.strip().lower() for item in (result.stdout or "").split(",") if item.strip()]
        if not addresses:
            return False
        return all(item in {"127.0.0.1", "::1"} for item in addresses)
    except Exception:
        return None


def pot_ping():
    info = _pot_ping_info()
    return bool(info and not info.get("mismatch"))
'''
replace_once(old_ping, new_ping)

replace_once(
    '''def ensure_pot_fast():
    """Fast path immediately before downloads; never trust an outdated provider."""
    if pot_ready and _pot_security_current():
        return True
    return check_and_start_pot()
''',
    '''def ensure_pot_fast():
    """Fast path immediately before downloads; verify identity and listener too."""
    if (
        pot_ready
        and _pot_security_current()
        and pot_ping()
        and _pot_listener_loopback_only() is not False
    ):
        return True
    return check_and_start_pot()
''',
)

replace_once(
    '''    with pot_lock:
        if pot_ping():
            pot_ready = True
            set_pot_status("PO Token: ACTIVE ✅")
            return True

        if not os.path.exists(POT_PLUGIN):''',
    '''    with pot_lock:
        # V33.10: an old/running provider must never bypass the security update.
        # Verify the pinned plugin + server pair before accepting any /ping.
        if not _pot_security_current():
            if not _install_secure_pot_provider():
                pot_ready = False
                set_pot_status("PO Token: security update failed")
                return False

        ping_info = _pot_ping_info()
        listener_safe = _pot_listener_loopback_only()
        if ping_info and not ping_info.get("mismatch") and listener_safe is not False:
            pot_ready = True
            set_pot_status("PO Token: bgutil 2.0.0 • localhost • healthy ✅")
            return True

        if ping_info.get("mismatch"):
            log(
                "🔐 PO Token version mismatch: server="
                + str(ping_info.get("version") or "unknown")
                + ", plugin=2.0.0. Restarting the verified pair."
            )
            _stop_pot_server_process()
        elif listener_safe is False:
            log("🔐 Unsafe PO Token listener detected outside localhost; stopping it.")
            _stop_pot_server_process()

        if not os.path.exists(POT_PLUGIN):''',
)

replace_once(
    '''                        "run",
                        "--allow-net",
                        "--allow-ffi=.",
                        "--allow-read=.",
                        launch_script,
                    ],''',
    '''                        "run",
                        "--allow-env",
                        "--allow-net",
                        "--allow-ffi=.",
                        "--allow-read=.",
                        launch_script,
                        "--host",
                        "127.0.0.1",
                    ],''',
)

replace_once(
    '''                [deno, "install"],
                cwd=provider_server_dir,''',
    '''                [deno, "install", "--allow-scripts=npm:canvas", "--frozen"],
                cwd=provider_server_dir,''',
)

replace_once(
    '''                "Provider active • bgutil 2.0.0 secure • localhost only"
                if pot_live''',
    '''                "bgutil 2.0.0 • 127.0.0.1:4416 • healthy"
                if pot_live''',
)

replace_once(
    '''                "Ready • bgutil 2.0.0 verified"
                if (deno and pot_plugin_ok and pot_server_ok and pot_secure)''',
    '''                "Plugin + server 2.0.0 match • SHA-256 verified"
                if (deno and pot_plugin_ok and pot_server_ok and pot_secure)''',
)

replace_once(
    '''    add(
        "PO Token Provider",
        provider_ok,
        (
            "active after automatic repair"
            if provider_ok and repaired
            else ("active" if provider_ok else "unavailable")
        ),
    )''',
    '''    provider_info = _pot_ping_info() if provider_ok else {}
    listener_safe = _pot_listener_loopback_only() if provider_ok else None
    provider_ok = bool(
        provider_ok
        and provider_info.get("version") == POT_REQUIRED_VERSION
        and listener_safe is not False
        and _pot_security_current()
    )
    add(
        "PO Token Provider",
        provider_ok,
        (
            "bgutil 2.0.0 • 127.0.0.1:4416 • healthy"
            if provider_ok
            else "unsafe, outdated, mismatched or unavailable"
        ),
    )''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.10 enforces the pinned bgutil 2.0.0 security update, verifies the "
    "live server version, rejects non-loopback listeners, and repairs Deno "
    "dependencies using the upstream frozen install command"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.10 app.py sha256", app_hash)
