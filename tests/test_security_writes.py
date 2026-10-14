"""Writes must never resolve outside the workspace (symlinked data directories)."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

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
        return subprocess.run([sys.executable, '-B', str(self.ai / 'bin' / tool), *args], capture_output=True, text=True)


class MemoryWriteTests(Base):
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
    def test_check_refuses_symlinked_state_directory(self):
        (self.ai / 'runtime').mkdir()
        (self.ai / 'runtime/path-repair').symlink_to(self.outside)
        p = self.run_tool('kukuri-paths', 'check')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(list(self.outside.iterdir()), [])


class TasksWriteTests(Base):
    def test_tasks_directory_symlinked_outside_is_refused(self):
        (self.ai / 'tasks').symlink_to(self.outside)
        p = self.run_tool('kukuri-tasks', 'init')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(list(self.outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
