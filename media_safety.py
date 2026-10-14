"""Embedded watchdog and evidence-based PO-token diagnostics for Z2SE."""
import math
import os
import re
import threading
import time


class MediaProgressClock:
    def __init__(self, timeout=600, clock=time.monotonic):
        self.clock = clock
        self.timeout = timeout
        self.last = clock()
        self.values = {}
        self.signature = None
        self.was_paused = False
        self.lock = threading.Lock()

    def observe(self, line):
        # Repeated warnings, progress=continue and changing speed are not progress.
        values = []
        for key, value in re.findall(r'(?:^|\s)(frame|total_size|out_time_us|out_time_ms)\s*=\s*(\d+)', str(line)):
            values.append((key, float(value)))
        match = re.search(r'(?:out_time|time)\s*=\s*(\d+):(\d+):(\d+(?:\.\d+)?)', str(line))
        if match:
            h, m, s = map(float, match.groups())
            values.append(('time', h * 3600 + m * 60 + s))
        with self.lock:
            for key, value in values:
                if math.isfinite(value) and value > self.values.get(key, 0):
                    self.values[key] = value
                    self.last = self.clock()

    def expired(self, paused=False, signature=None):
        with self.lock:
            now = self.clock()
            if paused or self.was_paused:
                self.last = now
            self.was_paused = paused
            if signature is not None and signature != self.signature:
                self.signature = signature
                self.last = now
            return not paused and now - self.last >= self.timeout


def po_token_diagnostic(message):
    text = str(message).lower()
    if not any(x in text for x in ('po token', 'po_token', 'pot provider', 'bgutil')):
        return None
    if any(x in text for x in ('mismatch', 'wrong client', 'different client', 'not valid for', 'invalid context')):
        return ('PO_CONTEXT', 'PO Token: client/context mismatch reported; refresh the token for the requested client.')
    if any(x in text for x in ('failed to generate', 'failed to fetch', 'failed to obtain', 'generation failed', 'connection refused', 'timed out', 'unreachable')):
        return ('PO_GENERATION', 'PO Token: generation/provider request failed; check provider health and retry.')
    if any(x in text for x in ('not provided', 'missing', 'no provider', 'not available', 'not found', 'unavailable')):
        return ('PO_MISSING', 'PO Token: token/provider unavailable; check the PO provider in Health Check.')
    return None


class MediaProcessWatchdog:
    def __init__(self, process, paused, terminate, notify, timeout=600, interval=2):
        self.process = process
        self.paused = paused
        self.terminate = terminate
        self.notify = notify
        self.progress = MediaProgressClock(timeout)
        self.interval = interval
        self.done = threading.Event()
        args = getattr(process, 'args', [])
        # Direct FFmpeg commands in Z2SE have one final output file. Never stat URLs/pipes.
        candidate = str(args[-1]) if isinstance(args, (list, tuple)) and len(args) > 1 else ''
        self.output = candidate if candidate and not candidate.startswith('-') and '://' not in candidate and not candidate.startswith('pipe:') else None

    def start(self):
        threading.Thread(target=self.run, daemon=True, name='Z2SE-media-watchdog').start()

    def stop(self):
        self.done.set()

    def run(self):
        while not self.done.wait(self.interval):
            if self.process.poll() is not None:
                return
            signature = None
            if self.output:
                try:
                    stat = os.stat(self.output)
                    signature = (stat.st_size, stat.st_mtime_ns)
                except OSError:
                    pass
            if self.progress.expired(paused=self.paused(), signature=signature):
                if self.done.is_set() or self.process.poll() is not None:
                    return
                self.process.z2se_guard_timeout = True
                self.notify('FFmpeg stopped: no media progress for 10 minutes. Retry or inspect the source. This is not proof of a malicious file.')
                self.terminate([self.process])
                return
