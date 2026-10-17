import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import runtime_support as runtime
import release_patch

ROOT = Path(__file__).resolve().parent


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        runtime._js_runtime_cache = None
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        runtime.BASE_DIR = self.temp.name
        self.paths = {}
        for name in ('deno', 'node'):
            path = Path(self.temp.name) / (name + '.exe')
            path.write_text('fixture')
            self.paths[name] = str(path)

    def discover(self, versions):
        def probe(command, **kwargs):
            name = Path(command[0]).stem
            value = versions[name]
            if isinstance(value, Exception):
                raise value
            return subprocess.CompletedProcess(command, 0, value, '')
        with patch.object(runtime, '_js_runtime_candidates', side_effect=lambda name: [self.paths[name]]), patch.object(runtime.subprocess, 'run', side_effect=probe):
            return runtime.discover_js_runtimes()

    def test_both_valid_deno_preferred(self):
        result = self.discover({'deno': 'deno 2.3.0\nv8 13.5', 'node': 'v22.0.0\n'})
        self.assertEqual([r['name'] for r in result], ['deno', 'node'])
        with patch.object(runtime, 'discover_js_runtimes', return_value=result):
            self.assertEqual(runtime.js_runtime_args(), ['--no-js-runtimes', '--js-runtimes', 'deno:' + self.paths['deno'], '--js-runtimes', 'node:' + self.paths['node']])

    def test_old_deno_falls_back_to_node(self):
        self.assertEqual([r['name'] for r in self.discover({'deno':'deno 2.2.9', 'node':'v24.0.0'})], ['node'])

    def test_hung_deno_falls_back_to_node(self):
        result = self.discover({'deno': subprocess.TimeoutExpired('deno', 3), 'node':'v22.1.0'})
        self.assertEqual([r['name'] for r in result], ['node'])

    def test_old_and_unparseable_rejected(self):
        self.assertEqual(self.discover({'deno':'unexpected 2.3.0', 'node':'v20.19.0'}), [])

    def test_no_runtime_preserves_non_youtube(self):
        with patch.object(runtime, '_js_runtime_candidates', return_value=[]):
            self.assertEqual(runtime.js_runtime_args(), [])
            self.assertIn('Missing', runtime.js_runtime_summary())

    def test_cache_and_replaced_binary(self):
        with patch.object(runtime, '_js_runtime_candidates', side_effect=lambda name: [self.paths[name]]), patch.object(runtime.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'v22.0.0')) as run:
            runtime.discover_js_runtimes()
            self.assertEqual(run.call_count, 2)
            runtime.discover_js_runtimes()
            self.assertEqual(run.call_count, 2)
            Path(self.paths['node']).write_text('updated binary fixture')
            runtime.discover_js_runtimes()
            self.assertEqual(run.call_count, 4)
            runtime.discover_js_runtimes(force=True)
            self.assertEqual(run.call_count, 6)

    def test_failed_candidate_tries_next_path(self):
        with patch.object(runtime, '_js_runtime_candidates', side_effect=lambda name: [self.paths['deno'], self.paths['node']] if name == 'deno' else []), patch.object(runtime.subprocess, 'run', side_effect=[OSError('blocked'), subprocess.CompletedProcess([], 0, 'deno 2.5.0')]):
            self.assertEqual(runtime.discover_js_runtimes()[0]['path'], self.paths['node'])

    def test_discovery_local_path_with_spaces(self):
        base = Path(self.temp.name) / 'App With Spaces'
        base.mkdir()
        name = 'node.exe' if os.name == 'nt' else 'node'
        (base / name).write_text('fixture')
        with patch.object(runtime, 'BASE_DIR', str(base)), patch.object(runtime.shutil, 'which', return_value=None):
            self.assertIn(str(base / name), runtime._js_runtime_candidates('node'))


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'current_app.py').read_text()
        cls.tree = ast.parse(cls.source)

    def test_all_media_command_paths_enable_runtimes(self):
        found = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.List) and node.elts and isinstance(node.elts[0], ast.Name) and node.elts[0].id == 'YTDLP':
                if any(isinstance(x, ast.Constant) and x.value in ('-U', '--version') for x in node.elts):
                    continue
                self.assertIsInstance(node.elts[1], ast.Starred)
                self.assertEqual(node.elts[1].value.func.id, 'js_runtime_args')
                found.append(node)
        self.assertEqual(len(found), 5)

    def test_update_timeout_kills_and_unlocks_controls(self):
        fn = next(n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == 'update_ytdlp')
        process = Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired('yt-dlp', 120), ('', None)]
        env = {'update_lock':threading.Lock(), 'YTDLP':'fixture', 'os':os, 'subprocess':subprocess,
               'set_update_status':Mock(), 'log':Mock(), 'set_update_button_state':Mock()}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'update-test', 'exec'), env)
        with patch.object(os.path, 'exists', return_value=True), patch.object(subprocess, 'Popen', return_value=process):
            self.assertFalse(env['update_ytdlp'](force=True))
        process.kill.assert_called_once()
        self.assertFalse(env['update_in_progress'])
        self.assertEqual(env['set_update_button_state'].call_args.args, ('normal',))

    def test_release_manifest_matches_exact_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            release_patch.build('33.17', path)
            manifest = json.loads((path / 'update_manifest.json').read_text())
            self.assertEqual(manifest['version'], '33.17')
            self.assertEqual({f['path'] for f in manifest['files']}, {'app.py', 'z2se_updater.pyw'})
            for f in manifest['files']:
                data = (path / f['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), f['sha256'])
                self.assertEqual(len(data), f['size'])
                compile(data, f['path'], 'exec')

    def test_wrong_release_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                release_patch.build('33.14', Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_previous_fixes_preserved(self):
        self.assertIn('def _winget_media_tool_candidates(', self.source)
        self.assertIn('def refresh_media_tools_if_needed(', self.source)
        self.assertTrue('def cancel_download_job(index):' in self.source)


if __name__ == '__main__':
    unittest.main()
