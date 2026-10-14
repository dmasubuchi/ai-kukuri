"""Relocation and runtime isolation at the executable boundary."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'relocated ai'
        (self.root / 'bin').mkdir(parents=True)
        (self.root / 'runtime').mkdir()
        for name in ('kukuri-claude', 'kukuri-codex', 'kukuri-launch.py'):
            path = ROOT / 'bin' / name
            self.assertTrue(path.is_file(), 'shared launcher is not implemented: ' + name)
            shutil.copy2(path, self.root / 'bin' / name)
        for name in ('AGENTS.md', 'CLAUDE.md'):
            (self.root / name).write_text('new-entry')
        (self.root / 'runtime/mcp.json').write_text('{"mcpServers":{}}')
        self.tool = Path(self.temp.name) / 'fake-cli'
        self.tool.write_text('#!/usr/bin/env python3\nimport os,json,sys\nprint(json.dumps({"cwd":os.getcwd(),"argv":sys.argv[1:],"codex_home":os.environ.get("CODEX_HOME"),"claude_home":os.environ.get("CLAUDE_CONFIG_DIR"),"path":os.environ["PATH"],"updater":os.environ.get("DISABLE_AUTOUPDATER")}))\n')
        self.tool.chmod(0o700)
        (self.root / 'runtime/launchers.json').write_text(json.dumps({'claude':str(self.tool), 'codex':str(self.tool)}))

    def run_launcher(self, name, *args):
        env = dict(os.environ, CODEX_HOME=str(Path(self.temp.name)/'old-codex'), CLAUDE_CONFIG_DIR=str(Path(self.temp.name)/'old-claude'))
        result = subprocess.run([str(self.root/'bin'/name), *args], cwd=self.temp.name, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_codex_relocates_and_overrides_inherited_home(self):
        data = self.run_launcher('kukuri-codex', 'debug', 'prompt-input', 'space argument')
        self.assertEqual(data['cwd'], str(self.root))
        self.assertEqual(data['codex_home'], str(self.root/'runtime/codex'))
        self.assertEqual(data['argv'], ['--no-daemon','--sandbox','workspace-write','--ask-for-approval','on-request','debug','prompt-input','space argument'])

    def test_claude_preserves_explicit_mcp_and_new_entry(self):
        data = self.run_launcher('kukuri-claude', 'auth', 'status')
        self.assertEqual(data['cwd'], str(self.root))
        self.assertEqual(data['claude_home'], str(self.root/'runtime/claude'))
        self.assertEqual(data['updater'], '1')
        self.assertEqual(data['argv'], ['--setting-sources','user','--permission-mode','manual','--strict-mcp-config','--mcp-config',str(self.root/'runtime/mcp.json'),'--append-system-prompt-file',str(self.root/'CLAUDE.md'),'auth','status'])

    def test_check_reports_separation_without_starting_cli(self):
        data = self.run_launcher('kukuri-codex', '--check')
        self.assertEqual(data['root'], str(self.root))
        self.assertEqual(data['config_directory'], str(self.root/'runtime/codex'))
        self.assertNotIn('argv', data)

    def test_configured_wrapper_is_rejected_before_recursive_execution(self):
        wrapper = self.root/'bin/kukuri-codex'
        (self.root/'runtime/launchers.json').write_text(json.dumps({'codex':str(wrapper)}))
        result = subprocess.run([str(wrapper), '--check'], capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('recursive', result.stderr.lower())

    def test_path_lookup_skips_own_wrapper_and_finds_real_cli(self):
        (self.root/'runtime/launchers.json').unlink()
        wrapper = self.root/'bin/kukuri-codex'
        cli_dir = Path(self.temp.name)/'cli-body'
        cli_dir.mkdir()
        body = cli_dir/'codex'
        shutil.copy2(self.tool, body)
        env = dict(os.environ, PATH=str(self.root/'bin')+os.pathsep+str(cli_dir)+os.pathsep+os.environ['PATH'])
        result = subprocess.run([str(wrapper), '--check'], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['binary'], str(body))

    def test_wrappers_of_other_workspaces_on_path_are_never_used_as_the_cli_body(self):
        (self.root/'runtime/launchers.json').unlink()
        other = Path(self.temp.name)/'other workspace'
        (other/'bin').mkdir(parents=True)
        for name in ('kukuri-launch.py', 'codex'):
            shutil.copy2(ROOT/'bin'/('kukuri-codex' if name == 'codex' else name), other/'bin'/name)
        # the other workspace's wrapper is named "codex" and is first on PATH
        cli_dir = Path(self.temp.name)/'real-cli'
        cli_dir.mkdir()
        body = cli_dir/'codex'
        shutil.copy2(self.tool, body)
        env = dict(os.environ, PATH=str(other/'bin')+os.pathsep+str(cli_dir)+os.pathsep+os.environ['PATH'])
        result = subprocess.run([str(self.root/'bin/kukuri-codex'), '--check'], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['binary'], str(body))
        self.assertEqual(data['root'], str(self.root))

    def test_explicit_setting_pointing_to_another_workspaces_wrapper_is_refused(self):
        other = Path(self.temp.name)/'other2'
        (other/'bin').mkdir(parents=True)
        shutil.copy2(ROOT/'bin/kukuri-launch.py', other/'bin/kukuri-launch.py')
        shutil.copy2(ROOT/'bin/kukuri-codex', other/'bin/codex')
        (self.root/'runtime/launchers.json').write_text(json.dumps({'codex': str(other/'bin/codex')}))
        result = subprocess.run([str(self.root/'bin/kukuri-codex'), '--check'], capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('recursive', result.stderr.lower())

    def test_a_large_wrapper_script_of_another_workspace_is_still_recognised(self):
        (self.root/'runtime/launchers.json').unlink()
        other = Path(self.temp.name)/'other-large'
        (other/'bin').mkdir(parents=True)
        (other/'bin/kukuri-launch.py').write_text('# marker\n')
        big = other/'bin'/'codex'
        big.write_text('#!/bin/sh\n' + '# padding\n' * 2000 + 'exec python3 "$(dirname "$0")/kukuri-launch.py" codex "$@"\n')
        big.chmod(0o755)
        self.assertGreater(big.stat().st_size, 8192)
        # the marker file is NOT beside the wrapper here, so recognition must come from its content
        (other/'bin/kukuri-launch.py').unlink()
        cli_dir = Path(self.temp.name)/'real-cli-2'
        cli_dir.mkdir()
        body = cli_dir/'codex'
        shutil.copy2(self.tool, body)
        env = dict(os.environ, PATH=str(other/'bin')+os.pathsep+str(cli_dir)+os.pathsep+os.environ['PATH'])
        result = subprocess.run([str(self.root/'bin/kukuri-codex'), '--check'], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['binary'], str(body))


if __name__ == '__main__':
    unittest.main()
