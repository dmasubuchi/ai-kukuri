"""Workspace creation and the end-to-end demo (fictional data only)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import compat

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def sh(self, *args, ok=True):
        """Run the portable Python scripts (the .sh files are thin wrappers around them)."""
        args = [str(a) for a in args]
        script = Path(args[0])
        if script.name == 'init-workspace.sh':
            cmd = [sys.executable, '-B', str(ROOT / 'scripts/init_workspace.py'), *args[1:]]
        elif script.name == 'demo.sh':
            cmd = [sys.executable, '-B', str(ROOT / 'examples/demo.py'), *args[1:]]
        else:
            cmd = ['sh', *args]
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.base), encoding='utf-8')
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        else:
            self.assertNotEqual(p.returncode, 0)
        return p

    def test_init_creates_a_working_workspace_without_touching_the_kit(self):
        ws = self.base / 'my workspace'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        for rel in ('AGENTS.md', 'CLAUDE.md', 'rules/common.md', 'registry/projects.json', 'registry/paths.json',
                    'runtime/mcp.json', 'runtime/machine.json',
                    'tasks/baseline.json', 'bin/kukuri-journal', 'bin/kukuri-wiki', 'skills/kukuri-journal-wiki/SKILL.md',
                    'knowledge/journal', 'knowledge/pages', '.gitignore'):
            self.assertTrue((ws / rel).exists(), rel)
        machine = json.loads((ws / 'runtime/machine.json').read_text())
        self.assertEqual(machine['projects_root'], str(ws / 'projects'))
        listing = subprocess.run(['python3', '-B', str(ws / 'bin/kukuri-tasks'), 'list'], capture_output=True, text=True)
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertEqual(json.loads(listing.stdout)['items'], [])

    def test_init_refuses_a_non_empty_target(self):
        ws = self.base / 'busy'
        ws.mkdir()
        (ws / 'keep.txt').write_text('mine')
        self.sh(ROOT / 'scripts/init-workspace.sh', ws, ok=False)
        self.assertEqual((ws / 'keep.txt').read_text(), 'mine')
        self.assertEqual([p.name for p in ws.iterdir()], ['keep.txt'])

    def test_demo_runs_end_to_end(self):
        ws = self.base / 'demo-ws'
        p = self.sh(ROOT / 'examples/demo.sh', ws)
        page = (ws / 'knowledge/pages/acme-portal.md').read_text()
        self.assertIn('Acme Portal is hosted on Cloud B.', page.split('## 未確認・矛盾')[0])
        self.assertIn('j-20260302-1000-01', page.split('## 履歴')[1])
        self.assertIn('"problems": []', p.stdout)
        events = [json.loads(l) for l in (ws / 'tasks/events.jsonl').read_text().splitlines()]
        self.assertEqual([e['item']['status'] for e in events], ['active', 'done'])

    def test_logical_project_reference_resolves_from_an_empty_workspace(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        (ws / 'projects/sample-portal').mkdir(parents=True)
        (ws / 'projects/sample-portal/proof.md').write_text('# proof\n')
        p = subprocess.run(['python3', '-B', str(ws / 'bin/kukuri-paths'), 'resolve', 'project:sample-portal/proof.md'],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        data = json.loads(p.stdout)
        self.assertIn(data['status'], ('current', 'mapped'))
        self.assertEqual(Path(data['path']).resolve(), (ws / 'projects/sample-portal/proof.md').resolve())

    @unittest.skipIf(compat.IS_WINDOWS, 'POSIX only')
    def test_claude_wrapper_gets_a_valid_mcp_config(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        self.assertEqual(json.loads((ws / 'runtime/mcp.json').read_text()), {'mcpServers': {}})
        fake = self.base / 'fake-claude'
        fake.write_text('#!/bin/sh\nexit 0\n'); fake.chmod(0o755)
        (ws / 'runtime/launchers.json').write_text(json.dumps({'claude': str(fake), 'codex': str(fake)}))
        p = subprocess.run([str(ws / 'bin/kukuri-claude'), '--check'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        options = json.loads(p.stdout)['options']
        mcp = options[options.index('--mcp-config') + 1]
        self.assertEqual(mcp, str(ws / 'runtime/mcp.json'))
        self.assertTrue(Path(mcp).is_file())

    def test_repair_adds_missing_files_and_never_overwrites(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        custom = {'mcpServers': {'sample': {'command': '/bin/true'}}}
        (ws / 'runtime/mcp.json').write_text(json.dumps(custom))
        (ws / 'registry/projects.json').write_text('{"projects": []}')
        (ws / 'registry/paths.json').unlink()
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws)
        self.assertEqual(json.loads((ws / 'runtime/mcp.json').read_text()), custom)
        self.assertEqual((ws / 'registry/projects.json').read_text(), '{"projects": []}')
        self.assertTrue((ws / 'registry/paths.json').is_file())
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', self.base / 'does-not-exist', ok=False)

    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_repair_refuses_symlinks_that_lead_outside_and_creates_nothing_first(self):
        outside = self.base / 'outside'
        outside.mkdir()
        for name in ('bin', 'knowledge', 'runtime', 'skills'):
            ws = self.base / ('ws-' + name)
            ws.mkdir()
            (ws / name).symlink_to(outside)
            self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws, ok=False)
            self.assertEqual(list(outside.iterdir()), [], name)
            self.assertEqual([p.name for p in ws.iterdir()], [name], 'nothing may be created before the guard')

    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_repair_refuses_a_symlinked_file_and_a_symlinked_cli(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        target = self.base / 'outside.txt'
        target.write_text('KEEP')
        (ws / 'runtime/mcp.json').unlink()
        (ws / 'runtime/mcp.json').symlink_to(target)
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws, ok=False)
        self.assertEqual(target.read_text(), 'KEEP')
        (ws / 'runtime/mcp.json').unlink()
        (ws / 'bin/kukuri-wiki').unlink()
        (ws / 'bin/kukuri-wiki').symlink_to(target)
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws, ok=False)
        self.assertEqual(target.read_text(), 'KEEP')

    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_data_directories_may_be_symlinks_and_are_not_written(self):
        ws = self.base / 'ws'
        disk = self.base / 'other-disk'
        disk.mkdir()
        ws.mkdir()
        (ws / 'projects').symlink_to(disk)
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws)
        self.assertEqual(list(disk.iterdir()), [])

    @unittest.skipIf(compat.IS_WINDOWS, 'POSIX only')
    def test_repair_keeps_the_mode_and_bytes_of_existing_files(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        custom = ws / 'bin/custom-existing-tool'
        custom.write_text('#!/bin/sh\necho mine\n')
        custom.chmod(0o600)
        kept = ws / 'bin/kukuri-wiki'
        kept.chmod(0o640)
        before = {p: (p.stat().st_mode & 0o777, p.read_bytes()) for p in (custom, kept)}
        (ws / 'bin/kukuri-journal').unlink()           # a missing CLI is re-created, executable
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws)
        for p, (mode, data) in before.items():
            self.assertEqual((p.stat().st_mode & 0o777, p.read_bytes()), (mode, data), p.name)
        self.assertTrue(os.access(ws / 'bin/kukuri-journal', os.X_OK))

    def test_generated_gitignore_keeps_records_todos_and_runtime_out_of_git(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        env = dict(os.environ)
        def run(*a):
            return subprocess.run(a, cwd=str(ws), capture_output=True, text=True, env=env)
        self.assertEqual(run('git', 'init', '-q').returncode, 0)
        j = run('python3', '-B', 'bin/kukuri-journal', 'add', '--kind', 'decision', '--text', '架空の決定', '--source', 's',
                '--author', 'a', '--date', '2026-03-02', '--time', '10:00', '--wiki', 'wiki:acme#k = 値')
        self.assertEqual(j.returncode, 0, j.stderr)
        self.assertEqual(run('python3', '-B', 'bin/kukuri-wiki', 'apply', '--write').returncode, 0)
        status = run('git', 'status', '--short', '--untracked-files=all').stdout.splitlines()
        paths = [l[3:] for l in status]
        for forbidden in ('knowledge/', 'tasks/', 'runtime/', 'projects/', 'input/', 'output/', '.claude', '.agents'):
            self.assertFalse([p for p in paths if p.startswith(forbidden)], (forbidden, paths))
        for rel in ('knowledge/journal/2026-03-02.md', 'knowledge/pages/acme.md', 'tasks/baseline.json',
                    'tasks/events.jsonl', 'knowledge/pages/.wiki.lock'):
            if (ws / rel).exists():
                self.assertEqual(run('git', 'check-ignore', '-q', rel).returncode, 0, rel)
        self.assertIn('AGENTS.md', paths)

    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_shared_skills_are_registered_where_products_look_for_them(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        for base in ('runtime/claude/skills', '.agents/skills'):
            for name in ('kukuri-journal-wiki', 'kukuri-recall', 'kukuri-project'):
                link = ws / base / name
                self.assertTrue(link.is_symlink(), base + '/' + name)
                self.assertTrue((link / 'SKILL.md').is_file())
                self.assertTrue(os.path.realpath(link).startswith(os.path.realpath(ws)))
        (ws / '.agents/skills/kukuri-recall').unlink()
        (ws / '.agents/skills/kukuri-recall').mkdir()
        (ws / '.agents/skills/kukuri-recall/SKILL.md').write_text('mine')
        self.sh(ROOT / 'scripts/init-workspace.sh', '--repair', ws)
        self.assertEqual((ws / '.agents/skills/kukuri-recall/SKILL.md').read_text(), 'mine')

    def test_journal_and_wiki_are_searchable_before_any_import(self):
        ws = self.base / 'ws'
        self.sh(ROOT / 'scripts/init-workspace.sh', ws)
        subprocess.run(['python3', '-B', str(ws / 'bin/kukuri-journal'), 'add', '--kind', 'result', '--text', 'FRESHな結果',
                        '--source', 's', '--author', 'a', '--date', '2026-03-02', '--time', '10:00',
                        '--wiki', 'wiki:acme#k = FRESHな現状'], check=True, capture_output=True)
        subprocess.run(['python3', '-B', str(ws / 'bin/kukuri-wiki'), 'apply', '--write'], check=True, capture_output=True)
        p = subprocess.run(['python3', '-B', str(ws / 'bin/kukuri-memory'), 'search', 'FRESH'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        kinds = {r['category'] for r in json.loads(p.stdout)}
        self.assertEqual(kinds, {'curated-knowledge', 'journal'})

    @unittest.skipIf(compat.IS_WINDOWS, 'POSIX only')
    def test_posix_wrappers_delegate_to_the_python_scripts(self):
        ws = self.base / 'ws'
        p = subprocess.run(['sh', str(ROOT / 'scripts/init-workspace.sh'), str(ws)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('workspace ready', p.stdout)
        d = subprocess.run(['sh', str(ROOT / 'examples/demo.sh'), str(self.base / 'demo')], capture_output=True, text=True)
        self.assertEqual(d.returncode, 0, d.stderr)


if __name__ == '__main__':
    unittest.main()
