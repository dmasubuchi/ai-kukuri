import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class PathsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.ai=self.root/'ai'; self.old=self.root/'old'
        (self.ai/'registry').mkdir(parents=True); (self.ai/'runtime').mkdir(); self.old.mkdir()
        (self.old/'projects').mkdir(); (self.ai/'projects').mkdir()
        config={'roots':[{'id':'projects','historical':[str(self.old/'projects')], 'machine_keys':['projects_root'], 'workspace_relative':'projects'}]}
        (self.ai/'registry/paths.json').write_text(json.dumps(config))
        (self.ai/'runtime/machine.json').write_text(json.dumps({'projects_root':str(self.old/'projects')}))
        script=ROOT/'bin/kukuri-paths'
        self.assertTrue(script.exists(),'Path Resolver CLI is not implemented')
        self.code=runpy.run_path(str(script)); self.resolver=self.code['Resolver'](self.ai)

    def test_registered_path_moves_and_returns_without_stale_cache(self):
        original=self.old/'projects/a.txt'; original.write_text('original')
        self.assertEqual(self.resolver.resolve(str(original))['status'],'current')
        original.rename(self.ai/'projects/a.txt')
        moved=self.resolver.resolve(str(original))
        self.assertEqual(moved['status'],'mapped')
        self.assertEqual(moved['path'],str(self.ai/'projects/a.txt'))
        (self.ai/'projects/a.txt').rename(original)
        self.assertEqual(self.resolver.resolve(str(original))['path'],str(original))
        self.assertTrue(self.code['report'](self.ai)['events'])

    def test_two_existing_targets_never_choose_wrong_company(self):
        old=self.old/'projects/a.txt'; old.write_text('A customer')
        (self.ai/'projects/a.txt').write_text('B customer')
        result=self.resolver.resolve(str(old))
        self.assertEqual(result['status'],'ambiguous')
        self.assertNotIn('path',result)

    def test_missing_is_not_labeled_lost_and_parent_prefix_is_exact(self):
        (self.ai/'projects-other').mkdir(); (self.ai/'projects-other/a.txt').write_text('unrelated')
        result=self.resolver.resolve(str(self.old/'projects-other/a.txt'))
        self.assertEqual(result['status'],'not_found')
        self.assertNotIn('path',result)
        self.assertFalse(result['loss_confirmed'])

    def test_permission_error_is_not_missing_and_external_symlink_is_not_adopted(self):
        original=self.old/'projects/a.txt'; original.write_text('source')
        real_stat=Path.stat
        def denied(path,*args,**kwargs):
            if path==original: raise PermissionError('denied')
            return real_stat(path,*args,**kwargs)
        with patch.object(Path,'stat',denied):
            self.assertEqual(self.resolver.resolve(str(original))['status'],'inaccessible')
        external=self.root/'outside.txt'; external.write_text('other')
        (self.old/'projects/link.txt').symlink_to(external)
        self.assertEqual(self.resolver.resolve(str(self.old/'projects/link.txt'))['status'],'symlink_unverified')

    def test_snapshot_fallback_validates_hash_and_does_not_claim_live_original(self):
        body=b'# past decision\n'; digest=hashlib.sha256(body).hexdigest()
        (self.ai/'knowledge/imports/test').mkdir(parents=True); (self.ai/'knowledge/records').mkdir()
        snap='knowledge/records/'+digest+'.txt'; (self.ai/snap).write_bytes(body)
        (self.ai/'knowledge/current.json').write_text(json.dumps({'run':'knowledge/imports/test'}))
        row={'id':'doc','original':str(self.old/'company/note.md'),'status':'imported','sha256':digest,'snapshot':snap,'category':'journal'}
        (self.ai/'knowledge/imports/test/manifest.jsonl').write_text(json.dumps(row)+'\n')
        resolver=self.code['Resolver'](self.ai)
        result=resolver.resolve(row['original'])
        self.assertEqual(result['status'],'archived')
        self.assertEqual(result['path'],str(self.ai/snap))
        Path(row['original']).parent.mkdir(); Path(row['original']).write_text('later decision')
        self.assertEqual(resolver.resolve('doc:doc')['path'],str(self.ai/snap))
        (self.ai/snap).write_text('wrong')
        self.assertEqual(resolver.resolve('doc:doc')['status'],'integrity_error')

    def test_relative_links_use_document_location_and_templates_are_not_missing(self):
        (self.old/'projects/docs').mkdir(); (self.old/'projects/契約 資料.md').write_text('evidence')
        refs=self.code['extract_references']('[契約](../契約%20資料.md#section)\n`/some/<project>/file.md`\nhttps://example.com\n')
        resolved=self.resolver.resolve(refs[0]['reference'],base=str(self.old/'projects/docs/journal.md'))
        self.assertEqual(resolved['path'],str(self.old/'projects/契約 資料.md'))
        self.assertEqual(self.resolver.resolve('/some/<project>/file.md')['status'],'template')

    def test_revoke_prevents_reuse_and_retry_revalidates(self):
        reference=str(self.old/'projects/a.txt'); (self.ai/'projects/a.txt').write_text('same')
        self.assertEqual(self.resolver.resolve(reference)['status'],'mapped')
        self.resolver.resolve(reference,forget=True)
        self.assertEqual(self.resolver.resolve(reference)['status'],'revoked')
        self.assertEqual(self.resolver.resolve(reference,retry=True)['status'],'mapped')

    def test_incremental_check_reuses_text_but_detects_changed_snapshot(self):
        (self.ai/'knowledge/imports/test').mkdir(parents=True); (self.ai/'knowledge/records').mkdir()
        body=('`'+str(self.old/'projects/missing.txt')+'`\n').encode(); digest=hashlib.sha256(body).hexdigest()
        snap='knowledge/records/'+digest+'.txt'; (self.ai/snap).write_bytes(body)
        (self.ai/'knowledge/current.json').write_text(json.dumps({'run':'knowledge/imports/test'}))
        row={'id':'doc','original':str(self.old/'journal.md'),'status':'imported','sha256':digest,'snapshot':snap,'category':'journal'}
        (self.ai/'knowledge/imports/test/manifest.jsonl').write_text(json.dumps(row)+'\n')
        first=self.code['check'](self.ai)
        self.assertEqual(first['statuses'],{'not_found':1})
        self.assertEqual(first['new_texts_read'],1)
        second=self.code['check'](self.ai)
        self.assertEqual(second['new_texts_read'],0)
        (self.ai/snap).write_text('corrupted')
        self.assertTrue(self.code['check'](self.ai)['errors'])

    def test_status_choices_and_slash_commands_are_not_file_references(self):
        refs=self.code['extract_references']('`/company`\n`送付待ち / 送付済み`\n`bank/aozora/`\n`YYYY-MM-DD.md`\n')
        self.assertEqual([r['reference'] for r in refs],['bank/aozora/','YYYY-MM-DD.md'])
        self.assertEqual(self.resolver.resolve('YYYY-MM-DD.md')['status'],'template')

    def test_evidence_scoped_alias_does_not_match_another_document(self):
        original=self.old/'projects/a.txt'; original.write_text('the evidence')
        proof=self.ai/'proof.md'; proof.write_text('同じ場所の a.txt\n')
        config=json.loads((self.ai/'registry/paths.json').read_text())
        config['verified_references']=[{'reference':'a.txt','base':str(self.old/'journal.md'),'target':str(original),
            'evidence':{'snapshot':'proof.md','sha256':hashlib.sha256(proof.read_bytes()).hexdigest(),'line':1,'quote':'同じ場所の a.txt'}}]
        (self.ai/'registry/paths.json').write_text(json.dumps(config))
        resolver=self.code['Resolver'](self.ai)
        self.assertEqual(resolver.resolve('a.txt',base=str(self.old/'journal.md'))['path'],str(original))
        self.assertEqual(resolver.resolve('a.txt',base=str(self.old/'different.md'))['status'],'not_found')
        proof.write_text('different')
        self.assertEqual(resolver.resolve('a.txt',base=str(self.old/'journal.md'))['status'],'integrity_error')

    def test_new_knowledge_and_tasks_are_checked_without_reimport(self):
        (self.ai/'knowledge/pages').mkdir(parents=True)
        (self.ai/'knowledge/pages/test.md').write_text('`'+str(self.old/'projects/missing.md')+'`')
        result=self.code['check'](self.ai)
        self.assertEqual(result['statuses'],{'not_found':1})

    def test_machine_root_and_logical_project_id_resolve_without_mac_home(self):
        server=self.root/'server/work'; (server/'client').mkdir(parents=True)
        (server/'client/proof.md').write_text('proof')
        (self.ai/'runtime/machine.json').write_text(json.dumps({'projects_root':str(server)}))
        (self.ai/'registry/projects.json').write_text(json.dumps({'projects':[{'id':'client-id','directory':'client'}]}))
        resolver=self.code['Resolver'](self.ai)
        self.assertEqual(resolver.resolve('project:client-id/proof.md')['path'],str(server/'client/proof.md'))
        self.assertEqual(resolver.resolve(str(self.old/'projects/client/proof.md'))['path'],str(server/'client/proof.md'))


if __name__=='__main__': unittest.main()
