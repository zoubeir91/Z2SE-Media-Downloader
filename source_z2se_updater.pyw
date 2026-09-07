import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def safe_rel(path):
    value = str(path or "").replace("\\", "/")
    if not value or value.startswith("/") or ":" in value:
        return False
    parts = [p for p in value.split("/") if p not in ("", ".")]
    return bool(parts) and ".." not in parts


def wait_for_pid(pid, timeout=45):
    if not pid:
        return

    if os.name == "nt":
        SYNCHRONIZE = 0x00100000
        WAIT_TIMEOUT = 0x00000102
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))

        if handle:
            try:
                milliseconds = int(timeout * 1000)
                kernel32.WaitForSingleObject(handle, milliseconds)
            finally:
                kernel32.CloseHandle(handle)
            return

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(int(pid), 0)
        except Exception:
            return
        time.sleep(0.25)


def load_manifest(staging):
    path = os.path.join(staging, "update_manifest.json")
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise RuntimeError("Invalid update manifest.")

    for item in files:
        rel = str(item.get("path", "")).replace("\\", "/")
        if not safe_rel(rel):
            raise RuntimeError("Unsafe manifest path: " + rel)

        source = os.path.join(staging, *rel.split("/"))
        if not os.path.isfile(source):
            raise RuntimeError("Missing payload file: " + rel)

        expected = str(item.get("sha256", "")).lower()
        if not expected or sha256_file(source) != expected:
            raise RuntimeError("Payload SHA-256 mismatch: " + rel)

    return manifest


def write_result(app_dir, status, version, backup_dir="", error=""):
    path = os.path.join(app_dir, "last_update_result.json")
    payload = {
        "status": status,
        "version": version,
        "backup_dir": backup_dir,
        "error": error,
        "time": datetime.now().isoformat(),
    }

    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass


def apply_update(staging, app_dir, version):
    manifest = load_manifest(staging)

    backup_root = os.path.join(app_dir, "BACKUPS")
    os.makedirs(backup_root, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(
        backup_root,
        f"AUTO_UPDATE_TO_{version}_{stamp}",
    )
    os.makedirs(backup_dir, exist_ok=True)

    applied = []
    originals = {}

    try:
        for item in manifest["files"]:
            rel = str(item["path"]).replace("\\", "/")
            source = os.path.join(staging, *rel.split("/"))
            target = os.path.join(app_dir, *rel.split("/"))

            os.makedirs(os.path.dirname(target), exist_ok=True)

            existed = os.path.isfile(target)
            originals[rel] = existed

            if existed:
                backup_target = os.path.join(backup_dir, *rel.split("/"))
                os.makedirs(os.path.dirname(backup_target), exist_ok=True)
                shutil.copy2(target, backup_target)

            temp_target = target + ".z2se_new"
            if os.path.isfile(temp_target):
                os.remove(temp_target)

            shutil.copy2(source, temp_target)

            if sha256_file(temp_target) != str(item["sha256"]).lower():
                raise RuntimeError("Staged target verification failed: " + rel)

            os.replace(temp_target, target)
            applied.append(rel)

        # Keep the manifest used for this successful install.
        shutil.copy2(
            os.path.join(staging, "update_manifest.json"),
            os.path.join(backup_dir, "APPLIED_UPDATE_MANIFEST.json"),
        )

        return True, backup_dir, ""

    except Exception as exc:
        # Roll back every path already replaced.
        for rel in reversed(applied):
            target = os.path.join(app_dir, *rel.split("/"))
            backup_target = os.path.join(backup_dir, *rel.split("/"))

            try:
                if originals.get(rel) and os.path.isfile(backup_target):
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    shutil.copy2(backup_target, target)
                elif not originals.get(rel) and os.path.isfile(target):
                    os.remove(target)
            except Exception:
                pass

        return False, backup_dir, str(exc)


def choose_pythonw(launch_exe):
    exe = str(launch_exe or "").strip()

    if exe and os.path.isfile(exe):
        if exe.lower().endswith("python.exe"):
            candidate = os.path.join(os.path.dirname(exe), "pythonw.exe")
            if os.path.isfile(candidate):
                return candidate
        return exe

    return sys.executable


def restart_app(app_dir, launch_exe):
    app = os.path.join(app_dir, "app.py")
    if not os.path.isfile(app):
        return

    executable = choose_pythonw(launch_exe)

    subprocess.Popen(
        [executable, app],
        cwd=app_dir,
        creationflags=(
            subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        ),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", required=True)
    parser.add_argument("--app-dir", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--parent-pid", type=int, default=0)
    parser.add_argument("--launch-exe", default="")
    args = parser.parse_args()

    staging = os.path.abspath(args.apply)
    app_dir = os.path.abspath(args.app_dir)

    wait_for_pid(args.parent_pid)

    ok, backup_dir, error = apply_update(
        staging,
        app_dir,
        args.version,
    )

    if ok:
        write_result(
            app_dir,
            "success",
            args.version,
            backup_dir=backup_dir,
        )
    else:
        write_result(
            app_dir,
            "rolled_back",
            args.version,
            backup_dir=backup_dir,
            error=error,
        )

    restart_app(
        app_dir,
        args.launch_exe,
    )


if __name__ == "__main__":
    main()
