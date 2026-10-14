"""Writes must never resolve outside the workspace (symlinked data directories)."""
import hashlib
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import compat

ROOT = Path(__file__).resolve().parents[1]


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.ai = self.base / 'ws'
        (self.ai / 'bin').mkdir(parents=True)
        for name in ('kukuri-memory', 'kukuri-paths', 'kukuri-tasks'):
            shutil.copy(ROOT / 'bin' / name, self.ai / 'bin' / name)
        self.outside = self.base / 'outside'
        self.outside.mkdir()

    def run_tool(self, tool, *args):
        return subprocess.run([sys.executable, '-B', str(self.ai / 'bin' / tool), *args], capture_output=True, text=True, encoding='utf-8')


class MemoryWriteTests(Base):
    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_import_refuses_symlinked_records_directory(self):
        notes = self.base / 'notes'; notes.mkdir()
        (notes / 'a.md').write_text('# 架空メモ\n本文\n')
        (self.ai / 'registry').mkdir()
        (self.ai / 'registry/knowledge-sources.json').write_text(json.dumps({'sources': [{'id': 'notes', 'root': str(notes)}]}))
        (self.ai / 'knowledge').mkdir()
        (self.ai / 'knowledge/records').symlink_to(self.outside)
        p = self.run_tool('kukuri-memory', 'import')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(list(self.outside.iterdir()), [])
        self.assertFalse((self.ai / 'knowledge/imports').exists(), 'nothing may be created before the guard passes')


class PathsWriteTests(Base):
    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_check_refuses_symlinked_state_directory(self):
        (self.ai / 'runtime').mkdir()
        (self.ai / 'runtime/path-repair').symlink_to(self.outside)
        p = self.run_tool('kukuri-paths', 'check')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(list(self.outside.iterdir()), [])


class TasksWriteTests(Base):
    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_tasks_directory_symlinked_outside_is_refused(self):
        (self.ai / 'tasks').symlink_to(self.outside)
        p = self.run_tool('kukuri-tasks', 'init')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(list(self.outside.iterdir()), [])


class AppendFileSymlinkTests(Base):
    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    def test_paths_history_and_lock_files_are_not_followed(self):
        (self.ai / 'registry').mkdir()
        (self.ai / 'registry/projects.json').write_text('{"projects": [{"id": "sample-portal", "directory": "sample-portal"}]}')
        (self.ai / 'runtime/path-repair').mkdir(parents=True)
        for name in ('history.jsonl', 'lock'):
            victim = self.base / ('victim-' + name)
            victim.write_text('ORIGINAL\n')
            link = self.ai / 'runtime/path-repair' / name
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(victim)
            p = self.run_tool('kukuri-paths', 'resolve', 'project:sample-portal/missing.md')
            self.assertNotEqual(p.returncode, 0, name)
            self.assertEqual(victim.read_text(), 'ORIGINAL\n', name)
            link.unlink()


class LauncherIsolationTests(Base):
    @unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
    @unittest.skipIf(compat.IS_WINDOWS, 'POSIX only')
    def test_check_refuses_a_product_directory_that_resolves_outside(self):
        shutil.copy(ROOT / 'bin/kukuri-launch.py', self.ai / 'bin/kukuri-launch.py')
        (self.ai / 'runtime').mkdir()
        (self.ai / 'runtime/codex').symlink_to(self.outside)
        fake = self.base / 'fake-cli'
        fake.write_text('#!/bin/sh\nexit 0\n'); fake.chmod(0o755)
        (self.ai / 'runtime/launchers.json').write_text(json.dumps({'codex': str(fake)}))
        p = self.run_tool('kukuri-launch.py', 'codex', '--check')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('ワークスペース外', p.stderr)


@unittest.skipUnless(compat.CAN_SYMLINK, 'symlinks are not available on this platform')
class MemoryReadTests(Base):
    def test_show_refuses_page_and_journal_documents_that_resolve_outside(self):
        outside = self.base / 'secret.txt'
        outside.write_text('SECRET-OUTSIDE\n')
        pages = self.ai / 'knowledge/pages'; journal = self.ai / 'knowledge/journal'
        pages.mkdir(parents=True); journal.mkdir(parents=True)
        (pages / 'leak.md').symlink_to(outside)
        (journal / '2026-03-01.md').symlink_to(outside)
        for doc in ('page:leak', 'journal:2026-03-01'):
            p = self.run_tool('kukuri-memory', 'show', doc)
            self.assertNotEqual(p.returncode, 0, doc)
            self.assertNotIn('SECRET-OUTSIDE', p.stdout)
        # search must not index them either
        p = self.run_tool('kukuri-memory', 'search', 'SECRET-OUTSIDE')
        self.assertNotIn('SECRET-OUTSIDE', p.stdout)


class VerifyReadTests(Base):
    def _import(self):
        notes = self.base / 'notes'; notes.mkdir()
        (notes / 'a.md').write_text('# memo\nbody\n', encoding='utf-8')
        (self.ai / 'registry').mkdir()
        (self.ai / 'registry/knowledge-sources.json').write_text(
            json.dumps({'sources': [{'id': 'notes', 'root': str(notes)}]}), encoding='utf-8')
        self.assertEqual(self.run_tool('kukuri-memory', 'import').returncode, 0)

    def test_verify_does_not_accept_a_snapshot_that_resolves_outside(self):
        self._import()
        self.assertEqual(self.run_tool('kukuri-memory', 'verify').returncode, 0)
        current = json.loads((self.ai / 'knowledge/current.json').read_text(encoding='utf-8'))
        manifest = self.ai / current['run'] / 'manifest.jsonl'
        rows = [json.loads(l) for l in manifest.read_text(encoding='utf-8').splitlines()]
        row = next(r for r in rows if r['status'] == 'imported')
        outside = self.base / 'outside-copy.txt'
        outside.write_bytes((self.ai / row['snapshot']).read_bytes())      # same bytes, same hash
        row['snapshot'] = os.path.relpath(outside, self.ai)
        manifest.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')
        p = self.run_tool('kukuri-memory', 'verify')
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn('ワークスペース外', p.stdout)

    def test_verify_does_not_accept_review_evidence_outside_the_workspace(self):
        self._import()
        outside = self.base / 'outside-evidence.txt'
        outside.write_text('line\n', encoding='utf-8')
        (self.ai / 'tasks').mkdir(exist_ok=True)
        (self.ai / 'tasks/reviewed.json').write_text(json.dumps({'items': [{
            'id': 'r1', 'evidence': [{'snapshot': os.path.relpath(outside, self.ai),
                                       'sha256': hashlib.sha256(outside.read_bytes()).hexdigest(),
                                       'line': 1, 'quote': 'line'}]}]}), encoding='utf-8')
        p = self.run_tool('kukuri-memory', 'verify')
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn('review_evidence_unreadable', p.stdout)


if __name__ == '__main__':
    unittest.main()
