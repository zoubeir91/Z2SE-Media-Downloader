"""Offline diagnostics for the actual yt-dlp executable, not host Python."""
import os
import re
import subprocess
import threading
import time

_engine_health_lock = threading.Lock()
_engine_health_cache = None


def parse_engine_health(output, returncode):
    # Only allowlisted fields leave this parser. Never retain debug paths,
    # environment, proxies, command-line options or credentials.
    version = re.search(r'(?m)^\[debug\] yt-dlp version (\S+)', output)
    libraries = re.search(r'(?m)^\[debug\] Optional libraries:\s*(.*)$', output)
    crypto = re.search(r'\b(Cryptodome|Crypto|pycryptodomex|pycryptodome)-([0-9][0-9A-Za-z.+-]*)', libraries.group(1)) if libraries else None
    expected_exit = returncode == 2 and 'You must provide at least one URL' in output
    ok = bool(version and libraries and expected_exit and 'Traceback (most recent call last)' not in output)
    result = {'ok': ok, 'version': version.group(1)[:80] if version else 'unknown',
              'crypto': crypto.group(0)[:80] if crypto else 'not reported'}
    if not ok:
        result['detail'] = 'Engine startup check failed or output is unrecognized; run Health Check before retrying.'
    elif not crypto:
        result['detail'] = 'Engine starts; crypto dependency not reported. Encrypted HLS/cookie compatibility is unverified.'
    else:
        result['detail'] = 'Engine starts; ' + result['crypto'] + ' detected. This is not an HLS/cookie decryption test.'
    return result


def check_engine_health(executable, force=False):
    global _engine_health_cache
    with _engine_health_lock:
        try:
            stat = os.stat(executable)
            key = (os.path.abspath(executable), stat.st_size, stat.st_mtime_ns)
        except OSError:
            return {'ok': False, 'version': 'unknown', 'crypto': 'not reported', 'detail': 'yt-dlp executable unavailable.'}
        now = time.monotonic()
        if not force and _engine_health_cache:
            saved_at, saved_key, saved = _engine_health_cache
            if key == saved_key and now - saved_at < 60:
                return dict(saved)
        try:
            # No URL means no extraction or media request. Ignore user config
            # and plugins; never inspect browser cookies for this diagnostic.
            completed = subprocess.run(
                [executable, '--ignore-config', '--no-plugin-dirs', '--verbose', '--simulate'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding='utf-8', errors='replace', timeout=15,
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0),
            )
            result = parse_engine_health(completed.stdout or '', completed.returncode)
        except (OSError, subprocess.SubprocessError):
            result = {'ok': False, 'version': 'unknown', 'crypto': 'not reported',
                      'detail': 'Engine startup check failed or timed out; no compatibility result available.'}
        _engine_health_cache = (now, key, result)
        return dict(result)
