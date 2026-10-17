import ast
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import engine_health as health

SAMPLE = '[debug] yt-dlp version stable@2026.08.19 from yt-dlp/yt-dlp\n[debug] Optional libraries: Cryptodome-3.23.0, certifi-2026.1.1\nERROR: You must provide at least one URL.\n'

class EngineHealthTests(unittest.TestCase):
    def test_legacy_namespace(self):
        result = health.parse_engine_health(SAMPLE, 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['crypto'], 'Cryptodome-3.23.0')

    def test_new_namespace_is_reported_without_claiming_decryption(self):
        result = health.parse_engine_health(SAMPLE.replace('Cryptodome-3.23.0', 'Crypto-4.0.0'), 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['crypto'], 'Crypto-4.0.0')
        self.assertIn('not an HLS/cookie decryption test', result['detail'])

    def test_missing_crypto_is_explicit(self):
        result = health.parse_engine_health(SAMPLE.replace('Cryptodome-3.23.0, ', ''), 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['crypto'], 'not reported')
        self.assertIn('unverified', result['detail'])

    def test_unexpected_exit_traceback_and_empty_output_fail(self):
        self.assertFalse(health.parse_engine_health(SAMPLE, 1)['ok'])
        self.assertFalse(health.parse_engine_health(SAMPLE+'Traceback (most recent call last)',2)['ok'])
        self.assertFalse(health.parse_engine_health('',2)['ok'])
        self.assertFalse(health.parse_engine_health(SAMPLE.replace('You must provide at least one URL','unknown option'),2)['ok'])

    def test_sensitive_debug_lines_not_retained(self):
        result=health.parse_engine_health('[debug] Proxy map: secret-password\n'+SAMPLE,2)
        self.assertNotIn('secret-password',str(result))

    def test_offline_arguments_cache_and_file_change(self):
        health._engine_health_cache=None
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'yt-dlp.exe';exe.write_text('fixture')
            with patch.object(health.subprocess,'run',return_value=subprocess.CompletedProcess([],2,SAMPLE)) as run:
                self.assertTrue(health.check_engine_health(str(exe))['ok'])
                args=run.call_args.args[0]
                self.assertEqual(args[1:],['--ignore-config','--no-plugin-dirs','--verbose','--simulate'])
                self.assertEqual(run.call_args.kwargs['timeout'],15)
                health.check_engine_health(str(exe))
                self.assertEqual(run.call_count,1)
                exe.write_text('replaced fixture')
                health.check_engine_health(str(exe))
                self.assertEqual(run.call_count,2)
                health.check_engine_health(str(exe),force=True)
                self.assertEqual(run.call_count,3)

    def test_timeout_and_missing_executable(self):
        self.assertFalse(health.check_engine_health('/does-not-exist-z2se')['ok'])
        with tempfile.NamedTemporaryFile() as f, patch.object(health.subprocess,'run',side_effect=subprocess.TimeoutExpired('yt-dlp',15)):
            self.assertFalse(health.check_engine_health(f.name,force=True)['ok'])

    def test_updater_checks_engine_before_marking_success(self):
        import os
        tree=ast.parse(Path('current_app.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='update_ytdlp')
        for ok in (False,True):
            process=Mock(returncode=0)
            process.communicate.return_value=('updated',None)
            env={'update_lock':threading.Lock(),'YTDLP':'fixture','os':os,'subprocess':subprocess,
                 'set_update_status':Mock(),'log':Mock(),'set_update_button_state':Mock(),
                 'check_engine_health':Mock(return_value={'ok':ok,'detail':'fixture'}),'save_last_update':Mock()}
            exec(compile(ast.Module(body=[fn],type_ignores=[]),'update-test','exec'),env)
            with patch.object(os.path,'exists',return_value=True),patch.object(subprocess,'Popen',return_value=process):
                self.assertEqual(env['update_ytdlp'](force=True),ok)
            self.assertEqual(env['save_last_update'].call_count,int(ok))
            env['check_engine_health'].assert_called_once_with('fixture',force=True)
            self.assertFalse(env['update_in_progress'])

if __name__=='__main__': unittest.main()
