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
        self.assertIn('manual_review', p.stdout)
        self.assertIn('"written": []', p.stdout)
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


class ReviewRegressionTests(Base):
    """独立レビューで再現した問題の回帰試験。"""

    def snapshot(self, slug='acme-portal'):
        return self.page(slug)

    def test_resolved_candidate_does_not_come_back_on_reapply(self):
        self.add('observation', 'maybe A', '2026-03-01', wiki=['wiki:acme-portal#x = maybe A'])
        self.add('decision', 'decided B', '2026-03-02', wiki=['wiki:acme-portal#x = decided B'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        first = self.snapshot()
        self.assertIn('decided B', first.split('## 未確認・矛盾')[0])
        again = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual({a['action'] for a in again['actions']}, {'skip'})
        self.assertEqual(self.snapshot(), first)
        self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual(self.snapshot(), first)

    def test_one_entry_with_several_keys_is_applied_per_key(self):
        self.add('observation', '観察', '2026-03-01',
                 wiki=['wiki:acme-portal#x = x候補', 'wiki:acme-portal#y = y候補'])
        self.add('decision', '決定', '2026-03-02',
                 wiki=['wiki:acme-portal#x = x確定', 'wiki:acme-portal#y = y確定'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        now = self.snapshot().split('## 未確認・矛盾')[0]
        self.assertIn('x確定', now)
        self.assertIn('y確定', now)

    def test_proposal_restating_a_decision_keeps_the_decision_evidence(self):
        self.add('decision', '決定A', '2026-03-01', wiki=['wiki:acme-portal#x = A'])
        self.add('proposal', '再提案A', '2026-03-02', wiki=['wiki:acme-portal#x = A'])
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertIn('skip', [a['action'] for a in plan['actions']])
        line = [l for l in self.snapshot().splitlines() if l.startswith('- [x]')][0]
        self.assertIn('kind: decision', line)
        self.assertIn('j-20260301-1000-01', line)

    def test_concurrent_apply_loses_nothing_and_leaves_no_temp_files(self):
        for i in range(6):
            self.add('decision', '決定%d' % i, '2026-03-0%d' % (i + 1), wiki=['wiki:acme-portal#k%d = 値%d' % (i, i)])
        procs = [subprocess.Popen([sys.executable, '-B', str(self.ai / 'bin/kukuri-wiki'), 'apply', '--write'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(6)]
        results = [p.communicate() + (p.returncode,) for p in procs]
        self.assertEqual([r[2] for r in results], [0] * 6, [r[1] for r in results])
        page = self.snapshot()
        for i in range(6):
            self.assertIn('値%d' % i, page.split('## 未確認・矛盾')[0])
        self.assertEqual(sorted(p.name for p in (self.ai / 'knowledge/pages').glob('.*.tmp')), [])

    def test_non_padded_date_and_time_are_rejected_not_silently_misfiled(self):
        for date, time in (('2026-3-2', '09:00'), ('2026-03-02', '9:0'), ('2026-03-02', '09:5')):
            self.run_tool('kukuri-journal', 'add', '--kind', 'result', '--text', 'x', '--source', 's',
                          '--author', 'a', '--date', date, '--time', time, ok=False)
        self.assertEqual(self.run_tool('kukuri-journal', 'list')['entries'], [])

    def test_read_arguments_cannot_leave_the_intended_directories(self):
        outside = Path(self.temp.name).resolve() / 'outside.md'
        outside.write_text('# 外部\n\n<!-- kukuri-wiki:v1 -->\n')
        self.run_tool('kukuri-wiki', 'show', '../../outside', ok=False)
        self.run_tool('kukuri-journal', 'list', '--date', '../../../outside-journal', ok=False)
        self.run_tool('kukuri-journal', 'evidence', 'j-20260101-0000-01/../../x', ok=False)

    def test_later_same_day_update_of_the_same_kind_supersedes(self):
        self.add('result', '午前の状態', '2026-03-01', '09:00', wiki=['wiki:acme-portal#status = 午前の状態'])
        self.add('result', '午後の状態', '2026-03-01', '15:00', wiki=['wiki:acme-portal#status = 午後の状態'])
        self.add('result', '同時刻より前の古い記録', '2026-03-01', '08:00', wiki=['wiki:acme-portal#status = 朝8時の状態'])
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        actions = [a['action'] for a in plan['actions']]
        self.assertEqual(actions, ['add', 'supersede', 'supersede'])       # 日時順に8:00→9:00→15:00
        text = self.snapshot()
        now = text.split('## 未確認・矛盾')[0]
        self.assertIn('午後の状態', now)
        self.assertIn('time: 15:00', now)
        history = text.split('## 履歴')[1]
        self.assertIn('午前の状態', history)
        self.assertIn('朝8時の状態', history)
        self.assertNotIn('朝8時の状態', now)
        again = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual({a['action'] for a in again['actions']}, {'skip'})

    def test_an_older_record_appended_after_a_later_apply_never_overrides_it(self):
        self.add('result', '午後の状態', '2026-03-01', '15:00', wiki=['wiki:acme-portal#status = 午後の状態'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        self.add('result', '朝の状態', '2026-03-01', '08:00', wiki=['wiki:acme-portal#status = 朝の状態'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        text = self.snapshot()
        self.assertIn('午後の状態', text.split('## 未確認・矛盾')[0])
        self.assertNotIn('朝の状態', text.split('## 未確認・矛盾')[0])
        self.assertIn('朝の状態', text.split('## 履歴')[1])
        self.assertEqual(self.run_tool('kukuri-wiki', 'apply', '--write')['written'], [])
    def old_format_page(self):
        """a46831a までの版が書いた形式（反映済みの記録の節が無い）。解消済みの候補の記録IDは履歴に残らない。"""
        (self.ai / 'knowledge/pages/acme-portal.md').write_text(
            '# acme-portal\n\n<!-- kukuri-wiki:v1 -->\n\n更新: 2026-03-02\n\n種別: Living Wiki\n\n'
            '## 現在わかっていること\n'
            '- [x] decided B | as_of: 2026-03-02 | source: j-20260302-1000-01 | kind: decision\n\n'
            '## 未確認・矛盾\n\n## 履歴\n'
            '- 2026-03-02 [x] 解消: 旧候補「maybe A」→「decided B」(j-20260302-1000-01)\n')

    def test_old_format_page_is_not_changed_until_the_applied_range_is_declared(self):
        self.add('observation', 'maybe A', '2026-03-01', '09:00', wiki=['wiki:acme-portal#x = maybe A'])
        self.add('decision', 'decided B', '2026-03-02', '10:00', wiki=['wiki:acme-portal#x = decided B'])
        self.old_format_page()
        before = self.snapshot()
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual({a['action'] for a in plan['actions']}, {'migration_required'})
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.run_tool('kukuri-wiki', 'check')['stats']['needs_migration'], 1)
        dry = self.run_tool('kukuri-wiki', 'migrate', 'acme-portal', '--through', '2026-03-02')
        self.assertFalse(dry['written'])
        self.assertEqual(self.snapshot(), before)
        done = self.run_tool('kukuri-wiki', 'migrate', 'acme-portal', '--through', '2026-03-02', '--write')
        self.assertTrue(done['written'])
        again = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual({a['action'] for a in again['actions']}, {'skip'})
        now = self.snapshot().split('## 未確認・矛盾')[0]
        self.assertIn('decided B', now)
        self.assertEqual(self.run_tool('kukuri-wiki', 'check')['stats']['needs_migration'], 0)
        self.assertNotIn('maybe A', now)

    def test_entries_after_the_declared_range_are_applied_normally(self):
        self.add('decision', 'decided B', '2026-03-02', '10:00', wiki=['wiki:acme-portal#x = decided B'])
        self.old_format_page()
        self.run_tool('kukuri-wiki', 'migrate', 'acme-portal', '--through', '2026-03-02', '--write')
        self.add('decision', 'decided C', '2026-03-05', '10:00', wiki=['wiki:acme-portal#x = decided C'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        text = self.snapshot()
        self.assertIn('decided C', text.split('## 未確認・矛盾')[0])
        self.assertIn('decided B', text.split('## 履歴')[1])

    def test_restating_the_same_content_later_in_the_day_updates_the_time(self):
        self.add('result', 'A', '2026-03-01', '09:00', wiki=['wiki:acme-portal#v = A'])
        self.add('result', 'A再確認', '2026-03-01', '15:00', wiki=['wiki:acme-portal#v = A'])
        self.add('result', 'B', '2026-03-01', '12:00', wiki=['wiki:acme-portal#v = B'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        text = self.snapshot()
        now = text.split('## 未確認・矛盾')[0]
        self.assertIn('[v] A ', now)
        self.assertIn('time: 15:00', now)
        self.assertNotIn('[v] B', now)
        self.assertIn('B', text.split('## 履歴')[1])      # 12:00のBは、履歴に残る

    def test_an_older_decision_cannot_resolve_an_open_conflict(self):
        self.add('decision', 'A', '2026-03-01', '09:00', wiki=['wiki:acme-portal#v = A'])
        self.add('result', 'B', '2026-03-01', '10:00', wiki=['wiki:acme-portal#v = B'])
        self.add('result', 'C', '2026-03-01', '08:00', wiki=['wiki:acme-portal#v = C'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        text = self.snapshot()
        self.assertEqual(self.run_tool('kukuri-wiki', 'check')['stats']['conflict'], 2)
        self.assertNotIn('[v] C', text.split('## 履歴')[0])
        self.assertIn('C', text.split('## 履歴')[1])      # 8:00のCは、履歴に残る
        self.assertEqual(self.run_tool('kukuri-wiki', 'apply', '--write')['written'], [])

    def test_decision_then_a_different_later_result_is_a_conflict_whatever_the_append_order(self):
        self.add('result', 'R', '2026-03-01', '09:00', wiki=['wiki:acme-portal#v = R'])
        self.add('decision', 'D', '2026-03-01', '08:00', wiki=['wiki:acme-portal#v = D'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual(self.run_tool('kukuri-wiki', 'check')['stats']['conflict'], 2)
        self.assertNotIn('[v]', self.snapshot().split('## 未確認・矛盾')[0])

    def _final(self, specs, order, incremental, tag):
        ws = Path(self.temp.name).resolve() / ('perm-%s-%s' % (tag, ''.join(map(str, order))))
        (ws / 'bin').mkdir(parents=True)
        for name in TOOLS:
            shutil.copy(ROOT / 'bin' / name, ws / 'bin' / name)
        (ws / 'knowledge/pages').mkdir(parents=True); (ws / 'tasks').mkdir()
        (ws / 'tasks/baseline.json').write_text('{"items": []}')
        def run(tool, *args):
            subprocess.run([sys.executable, '-B', str(ws / 'bin' / tool), *args], check=True, capture_output=True)
        for i in order:
            kind, text, time = specs[i]
            run('kukuri-journal', 'add', '--kind', kind, '--text', text, '--source', 's', '--author', 'a',
                '--date', '2026-03-01', '--time', time, '--wiki', 'wiki:acme#v = ' + text)
            if incremental:
                run('kukuri-wiki', 'apply', '--write')
        run('kukuri-wiki', 'apply', '--write')
        page = (ws / 'knowledge/pages/acme.md').read_text()
        def claims(section):
            return tuple(sorted(l.split(' | ')[0] + ' | ' + l.split(' | ')[-1] if False else l.split(' | ')[0]
                                for l in section.splitlines() if l.startswith('- [v]')))
        head = page.split('## 履歴')[0]
        return (claims(head.split('## 未確認・矛盾')[0]), claims(head.split('## 未確認・矛盾')[1]))

    def test_result_does_not_depend_on_append_order_or_on_when_apply_runs(self):
        import itertools
        suites = {
            'a': [('result', 'A', '09:00'), ('result', 'B', '12:00'), ('result', 'A', '15:00'), ('decision', 'D', '08:00')],
            'b': [('result', 'R', '09:00'), ('decision', 'D', '08:00'), ('observation', 'O', '10:00')],
            'c': [('observation', 'A', '09:00'), ('observation', 'A', '15:00'), ('result', 'B', '12:00')],
        }
        for tag, specs in suites.items():
            finals = {}
            for order in itertools.permutations(range(len(specs))):
                for incremental in (False, True):
                    finals.setdefault(self._final(specs, order, incremental, tag + str(int(incremental))), []).append((order, incremental))
            self.assertEqual(len(finals), 1, {k: v[:2] for k, v in finals.items()})

    def test_a_missing_journal_stops_the_rebuild_and_keeps_the_page(self):
        self.add('decision', 'A', '2026-03-01', '10:00', wiki=['wiki:acme-portal#v = A'])
        self.add('decision', 'B', '2026-03-02', '10:00', wiki=['wiki:acme-portal#v = B'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        before = self.snapshot()
        (self.ai / 'knowledge/journal/2026-03-01.md').unlink()
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual({a['action'] for a in plan['actions']}, {'missing_source'})
        self.assertEqual(plan['written'], [])
        self.assertEqual(self.snapshot(), before)

    def test_migrate_validates_the_confirmed_date_and_cannot_forge_claims(self):
        self.add('decision', 'D', '2026-03-02', '10:00', wiki=['wiki:acme-portal#x = D'])
        self.old_format_page()
        before = self.snapshot()
        forged = '2026-03-02\n## 現在わかっていること\n- [forged] FORGED | as_of: 2026-03-02 | source: j-20260302-1000-01 | kind: decision'
        for bad in (forged, '2026-3-2', '2026-13-40', 'x\r2026-03-02', '2026-03-02\u2028x'):
            self.run_tool('kukuri-wiki', 'migrate', 'acme-portal', '--through', bad, '--write', ok=False)
            self.assertEqual(self.snapshot(), before)
        self.run_tool('kukuri-wiki', 'migrate', 'acme-portal', '--through', '2026-03-02', '--write')
        self.assertNotIn('FORGED', self.snapshot())

    def test_migrate_rebuilds_inside_the_lock_and_keeps_a_concurrent_append(self):
        import fcntl
        self.add('decision', 'A', '2026-03-01', '10:00', wiki=['wiki:acme-portal#x = A'])
        self.old_format_page()
        lock_path = self.ai / 'knowledge/pages/.wiki.lock'
        with open(lock_path, 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            proc = subprocess.Popen([sys.executable, '-B', str(self.ai / 'bin/kukuri-wiki'), 'migrate', 'acme-portal', '--write'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            import time
            time.sleep(1.0)                       # migrate はロックの手前で待っている
            self.add('decision', 'B', '2026-03-05', '10:00', wiki=['wiki:acme-portal#x = B'])
            fcntl.flock(lock, fcntl.LOCK_UN)
        out, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0, err)
        self.assertIn('[x] B', self.snapshot().split('## 未確認・矛盾')[0])

    def test_a_claim_without_a_source_stops_with_manual_review_not_an_exception(self):
        self.add('decision', 'A', '2026-03-01', '10:00', wiki=['wiki:acme-portal#x = A'])
        self.run_tool('kukuri-wiki', 'apply', '--write')
        path = self.ai / 'knowledge/pages/acme-portal.md'
        path.write_text(path.read_text().replace(' | source: j-20260301-1000-01', ''))
        before = path.read_text()
        plan = self.run_tool('kukuri-wiki', 'apply', '--write')
        self.assertEqual({a['action'] for a in plan['actions']}, {'manual_review'})
        self.assertEqual(path.read_text(), before)

    def test_symlinked_journal_or_page_that_resolves_outside_is_never_read(self):
        outside = Path(self.temp.name).resolve() / 'outside-journal.md'
        outside.write_text('# 外部\n\n### j-20260301-1000-01 | decision | 10:00\n- 記録者: x\n- 出典: s\n- 種類: 本人の決定\n'
                           '- 内容: 外部の内容\n- 更新: wiki:acme-portal#x = 外部の値\n')
        folder = self.ai / 'knowledge/journal'; folder.mkdir(parents=True)
        (folder / '2026-03-01.md').symlink_to(outside)
        p = self.run_tool('kukuri-wiki', 'apply', '--write', ok=False)
        self.assertFalse((self.ai / 'knowledge/pages/acme-portal.md').exists())
        self.run_tool('kukuri-journal', 'list', ok=False)

    def test_entry_filter_limits_the_pages_that_are_written(self):
        one = self.add('decision', '1', '2026-03-01', '10:00', wiki=['wiki:page-one#x = 1'])
        self.add('decision', '2', '2026-03-01', '11:00', wiki=['wiki:page-two#x = 2'])
        result = self.run_tool('kukuri-wiki', 'apply', '--entry', one, '--write')
        self.assertEqual(result['written'], ['page-one'])
        self.assertFalse((self.ai / 'knowledge/pages/page-two.md').exists())


if __name__ == '__main__':
    unittest.main()
