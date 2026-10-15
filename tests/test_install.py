"""Installation entry points: install.sh, the npm launcher and the package contents."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

import compat

ROOT = Path(__file__).resolve().parents[1]
HAS_NODE = shutil.which('node') is not None
NPM = shutil.which('npm')
HAS_NPM = NPM is not None
NODE = shutil.which('node')
HAS_CURL = shutil.which('curl') is not None


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def run_cmd(self, *args, env=None, ok=True, cwd=None):
        p = subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding='utf-8', env=env, cwd=cwd or str(self.base))
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout)
        return p

    def assert_workspace(self, ws):
        for rel in ('AGENTS.md', 'bin/kukuri-journal', 'bin/kukuri-wiki', 'registry/paths.json', 'runtime/mcp.json',
                    'rules/common.md', 'tasks/baseline.json'):
            self.assertTrue((ws / rel).exists(), rel)


@unittest.skipIf(compat.IS_WINDOWS, 'install.sh is POSIX; use install.ps1 or npx on Windows')
class InstallScriptTests(Base):
    def test_install_from_a_checkout(self):
        ws = self.base / 'ws'
        p = self.run_cmd(ROOT / 'install.sh', ws)
        self.assert_workspace(ws)
        self.assertIn('workspace ready', p.stdout)

    def test_refuses_a_non_empty_target(self):
        ws = self.base / 'ws'
        ws.mkdir()
        (ws / 'keep').write_text('x')
        self.run_cmd(ROOT / 'install.sh', ws, ok=False)
        self.assertEqual([p.name for p in ws.iterdir()], ['keep'])

    @unittest.skipUnless(HAS_CURL, 'curl is required')
    def test_remote_mode_installs_from_an_archive_and_checks_the_checksum(self):
        src = self.base / 'src'
        shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns('.git', '__pycache__', 'node_modules'))
        archive = self.base / 'kit.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            tar.add(src, arcname='ai-kukuri-main')
        script = self.base / 'install.sh'                    # simulate `curl ... | sh`: no checkout beside the script
        shutil.copy(ROOT / 'install.sh', script)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        env = dict(os.environ, KUKURI_KIT_TARBALL='file://' + str(archive), KUKURI_KIT_SHA256=digest)
        ws = self.base / 'remote-ws'
        self.run_cmd('sh', script, ws, env=env)
        self.assert_workspace(ws)
        bad = dict(env, KUKURI_KIT_SHA256='0' * 64)
        ws2 = self.base / 'bad-ws'
        self.run_cmd('sh', script, ws2, env=bad, ok=False)
        self.assertFalse(ws2.exists())
        missing = dict(os.environ)
        missing.pop('KUKURI_KIT_TARBALL', None)
        self.run_cmd('sh', script, self.base / 'x', env=missing, ok=False)


@unittest.skipUnless(HAS_NODE, 'node is required')
class NodeLauncherTests(Base):
    def test_version_matches_package_json(self):
        p = self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', '--version')
        self.assertEqual(p.stdout.strip(), json.loads((ROOT / 'package.json').read_text())['version'])

    def test_init_repair_and_doctor(self):
        ws = self.base / 'ws'
        self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', 'init', ws)
        self.assert_workspace(ws)
        (ws / 'registry/paths.json').unlink()
        self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', 'repair', ws)
        self.assertTrue((ws / 'registry/paths.json').is_file())
        self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', 'doctor')

    def test_unknown_command_and_missing_argument_fail(self):
        self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', 'nope', ok=False)
        self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', 'init', ok=False)

    def test_demo_runs(self):
        self.run_cmd(NODE, ROOT / 'bin/ai-kukuri.js', 'demo', self.base / 'demo-ws')
        self.assertTrue((self.base / 'demo-ws/knowledge/pages/acme-portal.md').is_file())


@unittest.skipUnless(HAS_NPM, 'npm is required')
class PackageTests(Base):
    def test_package_contains_what_is_needed_and_nothing_private(self):
        p = self.run_cmd(NPM, 'pack', '--dry-run', '--json', '--ignore-scripts', cwd=str(ROOT))
        files = {f['path'] for f in json.loads(p.stdout)[0]['files']}
        for needed in ('bin/ai-kukuri.js', 'bin/kukuri-wiki', 'scripts/init-workspace.sh', 'install.sh',
                       'README.md', 'README.ja.md', 'LICENSE', 'rules/common.md', 'examples/demo.sh'):
            self.assertIn(needed, files)
        for path in files:
            self.assertFalse(path.startswith(('tests/', '.github/', '.git/', 'runtime/', 'knowledge/', 'tasks/')), path)
            self.assertFalse('__pycache__' in path or path.endswith('.pyc'), 'build artefacts may contain local paths: ' + path)

    def test_package_platform_list_includes_every_supported_platform(self):
        platforms = json.loads((ROOT / 'package.json').read_text())['os']
        for needed in ('darwin', 'linux', 'win32'):
            self.assertIn(needed, platforms)

    def test_package_cannot_be_published_by_accident(self):
        self.assertTrue(json.loads((ROOT / 'package.json').read_text())['private'])

    def test_packed_tarball_installs_a_workspace(self):
        out = self.base / 'out'
        out.mkdir()
        p = self.run_cmd(NPM, 'pack', '--json', '--ignore-scripts', '--pack-destination', out, cwd=str(ROOT))
        tgz = out / json.loads(p.stdout)[0]['filename']
        extract = self.base / 'pkg'
        extract.mkdir()
        with tarfile.open(tgz) as tar:
            if hasattr(tarfile, 'data_filter'):
                tar.extractall(extract, filter='data')
            else:
                tar.extractall(extract)
        ws = self.base / 'ws'
        self.run_cmd(NODE, extract / 'package/bin/ai-kukuri.js', 'init', ws)
        self.assert_workspace(ws)


class ReadmeNavigationTests(unittest.TestCase):
    def test_english_readme_is_primary_and_links_to_japanese(self):
        en = (ROOT / 'README.md').read_text(encoding='utf-8')
        ja = (ROOT / 'README.ja.md').read_text(encoding='utf-8')
        self.assertIn('README.ja.md', en)
        self.assertIn('README.md', ja)
        head = en.split('# ai-kukuri')[0]
        self.assertIn('English', head)
        # the English README body is English: kana (hiragana/katakana) only inside the quoted Japanese terms
        body = en.split('## Install')[1].split('## License')[0]
        self.assertFalse([c for c in body if '぀' <= c <= 'ヿ'], 'Japanese prose in the English README body')


if __name__ == '__main__':
    unittest.main()
