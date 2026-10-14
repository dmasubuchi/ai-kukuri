import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import shutil

SCRIPT = Path(__file__).resolve().parents[1] / "bin/kukuri-memory"
loader = importlib.machinery.SourceFileLoader("kukuri_memory", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
memory = importlib.util.module_from_spec(spec)
loader.exec_module(memory)


class MemoryTests(unittest.TestCase):
    def test_task_fields_preserve_raw_due_and_do_not_invent_owner(self):
        text = '# ACME\n- [ ] 入金確認 | 期限: 2026-10-14（見込み）\n- [x] 実装完了、実機は未確認 | 担当: 佐藤\n'
        rows = memory.extract_tasks({'id':'doc','source':'company','relative':'secretary/todos/2026-10-13.md'}, text)
        self.assertEqual(rows[0]['owner'], None)
        self.assertEqual(rows[0]['due'], '2026-10-14（見込み）')
        self.assertEqual(rows[0]['context'], 'ACME')
        self.assertEqual(rows[1]['owner'], '佐藤')
        self.assertEqual(rows[1]['recorded_status'], 'checked')
        self.assertTrue(rows[1]['needs_review'])
        self.assertEqual(rows[1]['current_status'], 'unconfirmed')

    def test_table_tasks_keep_content_owner_due_and_status(self):
        text = '| TODO | 担当 | 期限 | 状態 |\n|---|---|---|---|\n| 見積確認 | 吉井 | 10月中旬 | 先方待ち |\n'
        rows = memory.extract_tasks({'id':'doc','source':'company','relative':'secretary/todos/test.md'}, text)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['text'], rows[0]['owner'], rows[0]['due'], rows[0]['recorded_status']), ('見積確認','吉井','10月中旬','先方待ち'))

    def test_import_preserves_source_and_reports_exclusions_and_searches_japanese(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); old = root/'old'; ai = root/'ai'
            old.mkdir(); ai.mkdir()
            body = '# 株式会社テスト\n担当は田中。判断理由は費用。\n- [ ] 請求INV-0001を確認 | 期限: 2026-10-14\n'
            source = old/'client.md'; source.write_text(body)
            (old/'manual.pdf').write_bytes(b'PDF dummy')
            (old/'secret.md').write_text('-----BEGIN ' + 'PRIVATE KEY-----\nprivate')
            (old/'link.md').symlink_to(source)
            before = source.read_bytes()
            config = {'sources':[{'id':'company','root':str(old)}], 'current_task_sources':['company:client.md']}
            run = memory.import_sources(ai, config)
            report = memory.verify(ai, original=True)
            self.assertEqual(report['errors'], [])
            self.assertEqual(source.read_bytes(), before)
            hits = memory.search(ai, ["田中","費用"], limit=5)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]['sha256'], hashlib.sha256(before).hexdigest())
            manifest = [json.loads(x) for x in (ai/run/'manifest.jsonl').read_text().splitlines()]
            statuses = {r['relative']:r['status'] for r in manifest}
            self.assertEqual(statuses['manual.pdf'], 'reference_only')
            self.assertEqual(statuses['secret.md'], 'sensitive_excluded')
            self.assertEqual(statuses['link.md'], 'symlink_reference')
            tasks = memory.read_tasks(ai, current=True)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]['due'], '2026-10-14')
            (ai/hits[0]['snapshot']).write_text('corrupted')
            self.assertTrue(memory.verify(ai, original=False)['errors'])

    def test_historical_unchecked_item_is_not_a_current_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); old=root/'old'; ai=root/'ai'; old.mkdir(); ai.mkdir()
            (old/'old.md').write_text('- [ ] 昔の未確認作業\n')
            memory.import_sources(ai, {'sources':[{'id':'company','root':str(old)}], 'current_task_sources':[]})
            self.assertEqual(memory.read_tasks(ai, current=True), [])
            self.assertEqual(len(memory.read_tasks(ai, current=False)), 1)

    def test_missing_root_keeps_previous_index_and_task_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ai = root/'ai'; old = root/'company'
            ai.mkdir(); old.mkdir()
            (old/'note.md').write_text('# Existing evidence\n- [ ] Original task\n')
            memory.import_sources(ai, {'sources':[{'id':'company','root':str(old)}]})
            pointer = (ai/'knowledge/current.json').read_bytes()
            current = memory.current(ai)
            database = (ai/current['database']).read_bytes()
            tasks = (ai/current['tasks']).read_bytes()
            (old/'note.md').write_text('# Replacement evidence\n')
            config = {'sources':[{'id':'company','root':str(old)},
                                 {'id':'vault','root':str(root/'missing-vault')}]}
            with self.assertRaisesRegex(RuntimeError, 'current pointer unchanged'):
                memory.import_sources(ai, config)
            self.assertEqual((ai/'knowledge/current.json').read_bytes(), pointer)
            self.assertEqual((ai/current['database']).read_bytes(), database)
            self.assertEqual((ai/current['tasks']).read_bytes(), tasks)
            self.assertEqual(len(memory.search(ai, ['Existing evidence'])), 1)
            self.assertEqual(memory.search(ai, ['Replacement evidence']), [])
            reports = [json.loads(p.read_text()) for p in (ai/'knowledge/imports').glob('*/summary.json')]
            failed = next(r for r in reports if r['errors'])
            self.assertEqual(failed['errors'][0]['source'], 'vault')
            self.assertEqual(failed['errors'][0]['error'], 'missing_root')

    def test_missing_root_on_first_import_does_not_publish_index(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ai = root/'ai'; ai.mkdir()
            for source in [root/'absent', root/'dangling']:
                if source.name == 'dangling': source.symlink_to(root/'absent')
                with self.subTest(source=source.name):
                    with self.assertRaisesRegex(RuntimeError, 'current pointer unchanged'):
                        memory.import_sources(ai, {'sources':[{'id':'company','root':str(source)}]})
                    self.assertFalse((ai/'knowledge/current.json').exists())

    def test_cp932_bank_csv_and_pdf_filename_remain_searchable_without_invented_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); old=root/'old'; ai=root/'ai'; old.mkdir(); ai.mkdir()
            (old/'bank.csv').write_bytes('取引,金額\n入金,440000\n'.encode('cp932'))
            (old/'契約原本.pdf').write_bytes(b'dummy PDF')
            memory.import_sources(ai, {'sources':[{'id':'company','root':str(old)}], 'current_task_sources':[]})
            hits=memory.search(ai,['入金'])
            self.assertEqual(hits[0]['encoding'],'cp932')
            self.assertEqual(hits[0]['matches'][0]['text'],'入金,440000')
            pdf=memory.search(ai,['契約原本'])[0]
            self.assertEqual(pdf['status'],'reference_only')
            self.assertEqual(pdf['matches'],[])
            self.assertNotIn('snapshot',pdf)

    def test_show_resolves_source_relative_links_and_timeline_uses_record_date(self):
        self.assertTrue(callable(getattr(memory,'show_document',None)), 'show must resolve citations')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); old=root/'old'; ai=root/'ai'; old.mkdir(); ai.mkdir()
            (old/'journal').mkdir(); (old/'reference.md').write_text('根拠')
            (old/'journal/2026-09-15.md').write_text('# 当日の記録\n[資料](../reference.md)\n')
            (ai/'bin').mkdir(); shutil.copy2(SCRIPT.parent/'kukuri-paths',ai/'bin/kukuri-paths')
            memory.import_sources(ai,{'sources':[{'id':'company','root':str(old)}]})
            row=memory.search(ai,['当日の記録'])[0]
            view=memory.show_document(ai,row['id'],1,10)
            self.assertEqual(view['references'][0]['path'],str(old/'reference.md'))
            dates=memory.timeline(ai,'2026-09-01','2026-09-30')
            self.assertEqual([d['id'] for d in dates['documents']],[row['id']])
            self.assertEqual(dates['documents'][0]['date_basis'],'filename')

    def test_curated_knowledge_is_separate_and_searchable_before_archives(self):
        with tempfile.TemporaryDirectory() as temp:
            ai=Path(temp)/'ai'; old=Path(temp)/'old'; ai.mkdir(); old.mkdir()
            (old/'note.md').write_text('支払方式の旧記録')
            memory.import_sources(ai,{'sources':[{'id':'company','root':str(old)}]})
            (ai/'knowledge/pages').mkdir(); (ai/'knowledge/pages/payment.md').write_text('# 支払方式\n判断理由の整理。出典: doc:example\n')
            hits=memory.search(ai,['支払方式'])
            self.assertEqual(hits[0]['category'],'curated-knowledge')
            self.assertEqual(hits[0]['authority'],'derived_not_original')
            self.assertEqual(len(hits),2)

    def test_archive_keeps_same_url_with_different_body(self):
        self.assertTrue(callable(getattr(memory,'archive_catalog',None)))
        with tempfile.TemporaryDirectory() as temp:
            ai=Path(temp)/'ai'; old=Path(temp)/'old'; ai.mkdir(); (old/'99_Inbox/old').mkdir(parents=True)
            body='---\nsource: "https://example.invalid/article"\ncreated: 2026-09-01\n---\n'
            (old/'99_Inbox/a.md').write_text(body+'version one')
            (old/'99_Inbox/old/b.md').write_text(body+'version two')
            memory.import_sources(ai,{'sources':[{'id':'vault','root':str(old)}]})
            result=memory.archive_catalog(ai)
            self.assertEqual(result['clippings']['imported'],2)
            self.assertEqual(result['same_url_different_content_groups'],1)
            saved=json.loads((ai/'archive/catalog.json').read_text())
            self.assertEqual(len(saved['documents']),2)

    def test_new_journal_appears_in_search_and_timeline(self):
        with tempfile.TemporaryDirectory() as temp:
            ai=Path(temp)/'ai'; old=Path(temp)/'old'; ai.mkdir(); old.mkdir()
            memory.import_sources(ai,{'sources':[{'id':'company','root':str(old)}]})
            (ai/'knowledge/journal').mkdir(); (ai/'knowledge/journal/2026-10-14.md').write_text('# 日次記録\n実作業結果: 検索試験成功\n')
            hits=memory.search(ai,['検索試験'])
            self.assertEqual(len(hits),1)
            self.assertEqual(hits[0]['authority'],'append_only_record')
            self.assertEqual(len(memory.timeline(ai,'2026-10-14','2026-10-14')['documents']),1)

if __name__ == '__main__':
    unittest.main()
