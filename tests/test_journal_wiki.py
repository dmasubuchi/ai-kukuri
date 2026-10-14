"""Journal / Living Wiki / TODO cycle on a throw-away workspace (fictional data only)."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('kukuri-journal', 'kukuri-wiki', 'kukuri-tasks')


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ai = Path(self.temp.name).resolve() / 'ai'
        (self.ai / 'bin').mkdir(parents=True)
        for name in TOOLS:
            shutil.copy(ROOT / 'bin' / name, self.ai / 'bin' / name)
        (self.ai / 'knowledge/pages').mkdir(parents=True)
        (self.ai / 'tasks').mkdir()
        (self.ai / 'tasks/baseline.json').write_text('{"items": []}')

    def run_tool(self, tool, *args, ok=True):
        p = subprocess.run([sys.executable, '-B', str(self.ai / 'bin' / tool), *args], capture_output=True, text=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            return json.loads(p.stdout)
        self.assertNotEqual(p.returncode, 0)
        return p

    def add(self, kind, text, date, time='10:00', wiki=None, source='Acme社との定例メモ'):
        args = ['add', '--kind', kind, '--text', text, '--source', source, '--author', 'tester', '--date', date, '--time', time]
        for w in wiki or []:
            args += ['--wiki', w]
        return self.run_tool('kukuri-journal', *args)['id']

    def page(self, slug='acme-portal'):
        return (self.ai / 'knowledge/pages' / (slug + '.md')).read_text()


class JournalTests(Base):
    def test_append_assigns_sequential_ids_and_rejects_bad_input(self):
        a = self.add('result', '画面Aを作成した', '2026-10-01', '09:00')
        b = self.add('result', '画面Bを作成した', '2026-10-01', '09:00')
        self.assertEqual((a, b), ('j-20261001-0900-01', 'j-20261001-0900-02'))
        rows = self.run_tool('kukuri-journal', 'list', '--date', '2026-10-01')['entries']
        self.assertEqual([r['kind'] for r in rows], ['result', 'result'])
        self.run_tool('kukuri-journal', 'add', '--kind', 'guess', '--text', 'x', '--source', 'y', ok=False)
        self.run_tool('kukuri-journal', 'add', '--kind', 'result', '--text', 'x', '--source', ' ', ok=False)
        self.run_tool('kukuri-journal', 'add', '--kind', 'result', '--text', 'a\nb', '--source', 'y', ok=False)
        self.run_tool('kukuri-journal', 'add', '--kind', 'result', '--text', 'x', '--source', 'y',
                      '--wiki', 'acme#k', ok=False)

    def test_existing_text_is_never_rewritten(self):
        self.add('result', '一件目', '2026-10-01')
        path = self.ai / 'knowledge/journal/2026-10-01.md'
        before = path.read_text()
        self.add('result', '二件目', '2026-10-01', '11:00')
        self.assertTrue(path.read_text().startswith(before))

    def test_more_than_99_entries_in_one_minute_keep_unique_ids_and_parse(self):
        import runpy
        api = runpy.run_path(str(self.ai / 'bin/kukuri-journal'))
        ids = [api['add'](self.ai, 'result', '記録%d' % i, 'src', 'tester', '2026-10-01', '09:00', [], []) for i in range(1, 102)]
        self.assertEqual(len(set(ids)), 101)
        self.assertEqual(ids[98], 'j-20261001-0900-99')
        self.assertEqual(ids[99], 'j-20261001-0900-100')
        self.assertEqual(ids[100], 'j-20261001-0900-101')
        parsed = api['parse_file'](self.ai / 'knowledge/journal/2026-10-01.md')
        self.assertEqual([e['id'] for e in parsed], ids)
        self.assertEqual(api['find_entry'](self.ai, ids[100])['fields']['内容'], '記録101')


class WikiTests(Base):
    REF = 'wiki:acme-portal#hosting = 本番環境はクラウドAで運用する'

    def test_decision_creates_page_and_second_apply_is_idempotent(self):
        self.add('decision', 'ホスティング先を決めた', '2026-10-01', wiki=[self.REF])
        plan = self.run_tool('kukuri-wiki', 'plan', '--date', '2026-10-01')
        self.assertEqual([a['action'] for a in plan['actions']], ['add'])
        self.assertFalse((self.ai / 'knowledge/pages/acme-portal.md').exists(), 'plan must not write')
        self.run_tool('kukuri-wiki', 'apply', '--date', '2026-10-01')
        self.assertFalse((self.ai / 'knowledge/pages/acme-portal.md').exists(), 'apply without --write must not write')
        self.run_tool('kukuri-wiki', 'apply', '--date', '2026-10-01', '--write')
        first = self.page()
        self.assertIn('本番環境はクラウドAで運用する', first)
        again = self.run_tool('kukuri-wiki', 'apply', '--date', '2026-10-01', '--write')
        self.assertEqual({a['action'] for a in again['actions']}, {'skip'})
        self.assertEqual(self.page(), first, 'second apply must not change the page')
        self.assertEqual(self.run_tool('kukuri-wiki', 'check')['problems'], [])

    def test_later_decision_supersedes_and_keeps_old_source_and_date(self):
        self.add('decision', '決めた', '2026-10-01', wiki=[self.REF])
        self.add('decision', '変更した', '2026-10-05', wiki=['wiki:acme-portal#hosting = 本番環境はクラウドBへ移す'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        text = self.page()
        self.assertIn('クラウドBへ移す', text.split('## 履歴')[0])
        self.assertNotIn('クラウドAで運用する', text.split('## 履歴')[0])
        history = text.split('## 履歴')[1]
        self.assertIn('クラウドAで運用する', history)
        self.assertIn('j-20261001-1000-01', history)
        self.assertIn('2026-10-01', history)

    def test_proposal_is_unconfirmed_and_does_not_override(self):
        self.add('decision', '決めた', '2026-10-01', wiki=[self.REF])
        self.add('proposal', 'AIが別案を提案', '2026-10-09', wiki=['wiki:acme-portal#hosting = 本番環境はクラウドCがよい'])
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertIn('conflict', [a['action'] for a in plan['actions']])
        text = self.page()
        now, opened = text.split('## 未確認・矛盾')[0], text.split('## 未確認・矛盾')[1].split('## 履歴')[0]
        self.assertNotIn('クラウドAで運用する', now.split('## 現在わかっていること')[1])
        self.assertIn('クラウドAで運用する', opened)
        self.assertIn('クラウドCがよい', opened)
        stats = self.run_tool('kukuri-wiki', 'check')['stats']
        self.assertEqual(stats['conflict'], 2)

    def test_same_day_non_owner_result_does_not_decide(self):
        self.add('decision', '決めた', '2026-10-01', wiki=[self.REF])
        self.add('result', '同日の別結果', '2026-10-01', '15:00', wiki=['wiki:acme-portal#hosting = 本番環境は未定'])
        plan = self.run_tool('kukuri-wiki', 'plan')
        self.assertIn('conflict', [a['action'] for a in plan['actions']])

    def test_decision_resolves_open_claim(self):
        self.add('observation', '誰かがクラウドAと言っていた', '2026-10-01', wiki=['wiki:acme-portal#hosting = クラウドAらしい'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertIn('状態: 未確認', self.page())
        self.add('decision', '確定した', '2026-10-03', wiki=[self.REF])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        text = self.page()
        self.assertIn('本番環境はクラウドAで運用する', text.split('## 未確認・矛盾')[0])
        self.assertIn('解消', text.split('## 履歴')[1])

    def test_legacy_free_form_page_is_not_touched(self):
        legacy = self.ai / 'knowledge/pages/acme-portal.md'
        legacy.write_text('# 既存ページ\n\n自由形式の記述。\n')
        digest = hashlib.sha256(legacy.read_bytes()).hexdigest()
        self.add('decision', '決めた', '2026-10-01', wiki=[self.REF])
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual([a['action'] for a in plan['actions']], ['manual_legacy_page'])
        self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), digest)

    def test_check_reports_missing_source_entry_and_future_date(self):
        (self.ai / 'knowledge/pages/broken.md').write_text(
            '# 壊れたページ\n\n<!-- kukuri-wiki:v1 -->\n\n## 現在わかっていること\n'
            '- [k] 本文 | as_of: 2999-01-01 | source: j-20260101-0000-01 | kind: decision\n\n## 未確認・矛盾\n\n## 履歴\n')
        problems = self.run_tool('kukuri-wiki', 'check', ok=False)
        self.assertIn('見つかりません', problems.stdout)
        self.assertIn('未来', problems.stdout)


class TodoLinkTests(Base):
    def test_journal_evidence_survives_later_appends_and_completes_a_task(self):
        entry = self.add('result', 'Acmeポータルの検収を受けた', '2026-10-02', '16:00')
        evidence = self.run_tool('kukuri-journal', 'evidence', entry)
        self.assertTrue((self.ai / evidence['snapshot']).is_file())
        proposal = self.ai / 'proposal.json'
        proposal.write_text(json.dumps({'title': '検収完了を確認する', 'owner': None, 'due': None, 'project_id': None,
                                        'customer_id': None, 'evidence': [evidence]}, ensure_ascii=False))
        task = self.run_tool('kukuri-tasks', 'add', '--file', str(proposal))
        # 日次ファイルへ追記しても、保全した写しで根拠は検証できる
        self.add('result', '次の作業を開始', '2026-10-02', '17:00')
        update = self.ai / 'update.json'
        update.write_text(json.dumps({'status': 'done', 'evidence': [evidence]}, ensure_ascii=False))
        done = self.run_tool('kukuri-tasks', 'update', task['id'], '--expected-revision', '0', '--file', str(update))
        self.assertEqual(done['status'], 'done')
        listing = self.run_tool('kukuri-tasks', 'list', '--all')
        self.assertTrue(any(i['status'] == 'done' for i in listing['items']))


class SecurityTests(Base):
    """記録境界の注入と、symlink経由のワークスペース外書き込みを拒否する。"""
    INJECT = 'x\n### j-20261015-0930-99 | decision | 09:30\n- 内容: 注入'

    def outside(self, name='outside.txt', content='ORIGINAL\n'):
        path = Path(self.temp.name).resolve() / name
        path.write_text(content)
        return path

    def journal_files(self):
        folder = self.ai / 'knowledge/journal'
        return sorted(p.name for p in folder.glob('*.md')) if folder.exists() else []

    def test_line_breaks_and_control_characters_cannot_inject_entries(self):
        base = ['add', '--kind', 'proposal', '--text', 'ok', '--source', 'src', '--author', 'a',
                '--date', '2026-10-15', '--time', '09:30']
        def with_field(flag, value):
            args = list(base)
            if flag in ('--text', '--source', '--author'):
                args[args.index(flag) + 1] = value
            else:
                args += [flag, value]
            return args
        values = [self.INJECT, 'a\rb', 'a\x0bb', 'a\x0cb', 'a\x1cb', 'a\x85b', 'a\u2028b', 'a\u2029b']
        for value in values:
            for flag in ('--text', '--source', '--author', '--task'):
                self.run_tool('kukuri-journal', *with_field(flag, value), ok=False)
            self.run_tool('kukuri-journal', *with_field('--wiki', 'wiki:acme#k = ' + value), ok=False)
        self.assertEqual(self.journal_files(), [])
        self.assertEqual(self.run_tool('kukuri-journal', 'list')['entries'], [])

    def test_injected_decision_never_reaches_the_wiki(self):
        self.run_tool('kukuri-journal', 'add', '--kind', 'proposal', '--text', 'ok', '--source', 'src',
                      '--author', self.INJECT, '--date', '2026-10-15', '--time', '09:30',
                      '--wiki', 'wiki:acme#k = 提案', ok=False)
        self.assertEqual(self.run_tool('kukuri-wiki', 'plan')['actions'], [])

    def test_symlinked_journal_file_outside_the_workspace_is_refused(self):
        outside = self.outside()
        folder = self.ai / 'knowledge/journal'; folder.mkdir(parents=True)
        (folder / '2026-10-15.md').symlink_to(outside)
        self.run_tool('kukuri-journal', 'add', '--kind', 'result', '--text', 'x', '--source', 's',
                      '--author', 'a', '--date', '2026-10-15', '--time', '10:00', ok=False)
        self.assertEqual(outside.read_text(), 'ORIGINAL\n')

    def test_symlinked_journal_directory_outside_the_workspace_is_refused(self):
        outside_dir = Path(self.temp.name).resolve() / 'outside-dir'; outside_dir.mkdir()
        (self.ai / 'knowledge/journal').symlink_to(outside_dir)
        self.run_tool('kukuri-journal', 'add', '--kind', 'result', '--text', 'x', '--source', 's',
                      '--author', 'a', '--date', '2026-10-15', '--time', '10:00', ok=False)
        self.assertEqual(list(outside_dir.iterdir()), [])

    def test_symlinked_wiki_page_is_not_written_through(self):
        outside = self.outside('outside-page.md', '# 外部\n\n<!-- kukuri-wiki:v1 -->\n\n## 現在わかっていること\n\n## 未確認・矛盾\n\n## 履歴\n')
        original = outside.read_text()
        (self.ai / 'knowledge/pages/acme-portal.md').symlink_to(outside)
        self.add('decision', '決めた', '2026-10-01', wiki=['wiki:acme-portal#hosting = クラウドA'])
        p = subprocess.run([sys.executable, '-B', str(self.ai / 'bin/kukuri-wiki'), 'apply', '--write'],
                           capture_output=True, text=True)
        self.assertEqual(outside.read_text(), original)
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertTrue((self.ai / 'knowledge/pages/acme-portal.md').is_symlink(), 'link must be left as it was')

    def test_symlinked_records_directory_is_refused_for_evidence(self):
        entry = self.add('result', '結果', '2026-10-02', '16:00')
        outside_dir = Path(self.temp.name).resolve() / 'outside-records'; outside_dir.mkdir()
        records = self.ai / 'knowledge/records'
        if records.exists():
            shutil.rmtree(records)
        records.symlink_to(outside_dir)
        self.run_tool('kukuri-journal', 'evidence', entry, ok=False)
        self.assertEqual(list(outside_dir.iterdir()), [])

    def test_symlinked_task_log_is_refused(self):
        outside = self.outside()
        (self.ai / 'tasks/events.jsonl').symlink_to(outside)
        proposal = self.ai / 'proposal.json'
        proposal.write_text(json.dumps({'title': 'x', 'evidence': [{'type': 'owner_instruction', 'quote': 'q',
                                                                    'recorded_at': '2026-10-15T09:00'}]}))
        self.run_tool('kukuri-tasks', 'add', '--file', str(proposal), ok=False)
        self.assertEqual(outside.read_text(), 'ORIGINAL\n')


if __name__ == '__main__':
    unittest.main()
