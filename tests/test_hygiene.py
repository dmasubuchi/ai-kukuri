"""The kit must not carry personal paths, e-mail addresses or credentials."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'home directory': re.compile(r'/(?:Users|home)/(?!you\b|user\b|name\b|example\b|<)[A-Za-z0-9._-]+'),
    'e-mail address': re.compile(r'\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|invalid|org)\b|users\.noreply\.github\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    'token': re.compile(r'\b(?:sk-ant-|ghp_|gho_|github_pat_|xox[bap]-)[A-Za-z0-9_-]{16,}|\bAKIA[A-Z0-9]{16}\b'),
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}


def tracked_files():
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True)
    if out.returncode == 0 and out.stdout:
        return [ROOT / p for p in out.stdout.decode().split('\0') if p]
    return [p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]


class HygieneTests(unittest.TestCase):
    def test_no_personal_data_patterns(self):
        hits = []
        for path in tracked_files():
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            for name, pattern in PATTERNS.items():
                for m in pattern.finditer(text):
                    hits.append('%s: %s: %r' % (path.relative_to(ROOT), name, m.group(0)))
        self.assertEqual(hits, [])

    def test_no_runtime_or_data_directories_are_tracked(self):
        for name in ('runtime', 'knowledge', 'tasks', 'input', 'output', 'projects'):
            self.assertFalse((ROOT / name).exists(), name + '/ must not exist in the kit')


if __name__ == '__main__':
    unittest.main()
