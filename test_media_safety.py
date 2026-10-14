import ast
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
from media_safety import MediaProgressClock, MediaProcessWatchdog, po_token_diagnostic


class ClockTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.guard = MediaProgressClock(10, lambda: self.now)

    def test_silent_process_expires(self):
        self.now = 10
        self.assertTrue(self.guard.expired())

    def test_advancing_media_time_resets_deadline(self):
        self.now = 9
        self.guard.observe('out_time=00:00:03.500')
        self.now = 18
        self.assertFalse(self.guard.expired())
        self.now = 19
        self.assertTrue(self.guard.expired())

    def test_repeated_warnings_and_frozen_progress_do_not_reset(self):
        self.guard.observe('frame=12')
        self.now = 10
        for line in ('frame=12', 'progress=continue', 'speed=4.2x', 'warning: retrying'):
            self.guard.observe(line)
        self.assertTrue(self.guard.expired())

    def test_pause_and_resume_get_full_grace_period(self):
        self.now = 100
        self.assertFalse(self.guard.expired(paused=True))
        self.now = 1000
        self.assertFalse(self.guard.expired(paused=False))
        self.now = 1009
        self.assertFalse(self.guard.expired())
        self.now = 1010
        self.assertTrue(self.guard.expired())

    def test_output_growth_or_rewrite_is_progress(self):
        self.now = 9
        self.assertFalse(self.guard.expired(signature=(100, 1)))
        self.now = 18
        self.assertFalse(self.guard.expired(signature=(100, 2)))
        self.now = 28
        self.assertTrue(self.guard.expired(signature=(100, 2)))

    def test_standard_ffmpeg_stats(self):
        self.now = 8
        self.guard.observe('frame=  190 fps=20 time=00:00:08.0 speed=1x')
        self.now = 17
        self.assertFalse(self.guard.expired())


class DiagnosticTests(unittest.TestCase):
    def test_distinct_evidence(self):
        for message, expected in [
            ('No PO token provided: token missing', 'PO_MISSING'),
            ('PO token provider failed to generate token', 'PO_GENERATION'),
            ('PO token is not valid for this client', 'PO_CONTEXT'),
            ('bgutil connection refused', 'PO_GENERATION'),
        ]:
            self.assertEqual(po_token_diagnostic(message)[0], expected)

    def test_no_guess_from_403_or_success(self):
        for message in ('HTTP Error 403: Forbidden', 'PO token generated successfully', 'DRM protected', 'PO token provider ready'):
            self.assertIsNone(po_token_diagnostic(message))

    def test_hints_do_not_echo_tokens_or_urls(self):
        result = po_token_diagnostic('PO token missing: secret-value https://example.com/?token=abc')
        self.assertNotIn('secret-value', result[1])
        self.assertNotIn('example.com', result[1])


class ProcessTests(unittest.TestCase):
    def test_real_silent_subprocess_is_reaped(self):
        process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(lambda: process.poll() is None and process.kill())
        finished = threading.Event()
        messages = []
        def terminate(processes):
            processes[0].kill()
            processes[0].wait(timeout=2)
            finished.set()
        guard = MediaProcessWatchdog(process, lambda: False, terminate, messages.append, timeout=.05, interval=.01)
        guard.start()
        self.assertTrue(finished.wait(3))
        self.assertNotEqual(process.returncode, 0)
        self.assertTrue(process.z2se_guard_timeout)
        self.assertEqual(len(messages), 1)

    def test_stopping_guard_does_not_kill_process(self):
        process = Mock(args=['ffmpeg', '-i', 'input', 'pipe:1'])
        process.poll.return_value = None
        terminate = Mock()
        guard = MediaProcessWatchdog(process, lambda: False, terminate, Mock(), timeout=0, interval=.01)
        guard.stop()
        guard.run()
        terminate.assert_not_called()

    def test_completed_process_is_not_killed(self):
        process = Mock(args=['ffmpeg', 'output.mp4'])
        process.poll.return_value = 0
        terminate = Mock()
        guard = MediaProcessWatchdog(process, lambda: False, terminate, Mock(), timeout=0, interval=.001)
        guard.run()
        terminate.assert_not_called()

    def test_application_wires_all_output_loops_and_cleanup(self):
        tree = ast.parse(Path('current_app.py').read_text())
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and ast.unparse(node.iter) == 'process.stdout':
                self.assertEqual(node.body[0].value.func.id, '_observe_media_output')
                count += 1
        self.assertEqual(count, 9)
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertIn('_start_media_watchdog(process, current_job)', ast.unparse(funcs['register_process']))
        self.assertIn('guard.stop()', ast.unparse(funcs['unregister_process']))


if __name__ == '__main__':
    unittest.main()
