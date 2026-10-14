"""Exercise operator guards with fake tmux/flock; never touch a live server."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.name == 'posix' and shutil.which('bash'), 'Linux/POSIX lifecycle fixture; run in Linux CI')
class DetachedStartTests(unittest.TestCase):
    def run_case(self, present=False, busy=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'server').mkdir()
            (root/'bin').mkdir()
            for name in ['start-detached.sh','runtime.env.sh']:
                shutil.copyfile(ROOT/'server'/name, root/'server'/name)
            calls = root/'calls.txt'
            tmux = root/'bin/tmux'
            tmux.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$CALL_LOG"\n'
                'if [[ "$*" == *has-session* ]]; then [[ "$PRESENT" == 1 ]]; else exit 0; fi\n')
            flock = root/'bin/flock'
            flock.write_text('#!/usr/bin/env bash\nif [[ "$1" == -n && "$BUSY" == 1 ]]; then exit 1; fi\nexit 0\n')
            tmux.chmod(0o700)
            flock.chmod(0o700)
            env = {**os.environ, 'PATH':str(root/'bin')+os.pathsep+os.environ['PATH'],
                   'CALL_LOG':str(calls), 'PRESENT':str(int(present)), 'BUSY':str(int(busy))}
            result = subprocess.run(['bash',str(root/'server/start-detached.sh')], env=env,
                                    capture_output=True, text=True, timeout=10)
            invocations = calls.read_text() if calls.exists() else ''
            return result, invocations, str(root)

    def test_existing_dedicated_session_is_reused(self):
        result, calls, _ = self.run_case(present=True)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('new-session', calls)

    def test_locked_foreground_instance_is_not_interrupted(self):
        result, calls, _ = self.run_case(busy=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('new-session', calls)
        self.assertIn('already holds the lock', result.stderr)

    def test_launch_uses_dedicated_folder_socket(self):
        result, calls, root = self.run_case()
        self.assertEqual(result.returncode, 0)
        self.assertIn(root+'/run/tmux.sock', calls)
        self.assertIn('new-session -d -s giis-rag', calls)
        self.assertNotIn('kill-server', calls)

if __name__ == '__main__':
    unittest.main()
