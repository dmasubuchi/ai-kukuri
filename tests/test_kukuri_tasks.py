import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TasksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ai = Path(self.temp.name)
        (self.ai/'bin').mkdir(); (self.ai/'tasks').mkdir()
        script = ROOT/'bin/kukuri-tasks'
        if script.exists():
            shutil.copy2(script, self.ai/'bin/kukuri-tasks')
        (self.ai/'tasks/reviewed.json').write_text(json.dumps({'items':[
            {'id':'old:1','content':'契約の下書きを確認','owner':None,'due':'2026-10-14',
             'status':'unconfirmed_after_source_date','evidence':[], 'next_action':'確認する'}]}))

    def cli(self, *args, ok=True):
        run = subprocess.run(['python3','-B',str(self.ai/'bin/kukuri-tasks'),*args],text=True,capture_output=True)
        if ok:
            self.assertEqual(run.returncode,0,run.stderr)
            return json.loads(run.stdout)
        self.assertNotEqual(run.returncode,0)
        return run

    def payload(self, data):
        path=self.ai/'proposal.json'; path.write_text(json.dumps(data)); return str(path)

    def test_seed_keeps_unknowns_and_overdue_is_only_a_candidate(self):
        self.cli('init')
        result=self.cli('list','--through','2026-10-15')
        self.assertEqual(len(result['items']),1)
        task=result['items'][0]
        self.assertIsNone(task['owner'])
        self.assertEqual(task['status'],'unconfirmed')
        self.assertEqual(task['due'],'2026-10-14')
        before=(self.ai/'tasks/baseline.json').read_bytes()
        self.cli('init')
        self.assertEqual((self.ai/'tasks/baseline.json').read_bytes(),before)

    def test_update_requires_evidence_and_rejects_stale_revision(self):
        self.cli('init')
        no_proof=self.payload({'status':'done'})
        self.cli('update','old:1','--expected-revision','0','--file',no_proof,ok=False)
        proof={'type':'owner_instruction','quote':'契約確認は完了した','recorded_at':'2026-10-14T12:00:00+09:00'}
        change=self.payload({'status':'done','evidence':[proof]})
        self.cli('update','old:1','--expected-revision','0','--file',change)
        self.cli('update','old:1','--expected-revision','0','--file',change,ok=False)
        row=self.cli('list','--all')['items'][0]
        self.assertEqual(row['revision'],1)
        self.assertEqual(row['completion_evidence'],[proof])
        self.assertEqual(len(self.cli('history')['events']),1)
        self.assertEqual(self.cli('list')['items'],[])
        change=self.payload({'title':'確認完了の記録','evidence':[{'type':'owner_instruction','quote':'タイトルを整理する','recorded_at':'2026-10-15'}]})
        self.cli('update','old:1','--expected-revision','1','--file',change)
        self.assertEqual(self.cli('list','--all')['items'][0]['completion_evidence'],[proof])

    def test_explicit_overdue_annotation_is_included_without_changing_raw_due(self):
        path=self.ai/'tasks/reviewed.json'; data=json.loads(path.read_text()); data['items'][0]['due']='2026-10-09（超過）'; path.write_text(json.dumps(data))
        self.cli('init')
        rows=self.cli('list','--through','2026-10-13')['items']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['due'],'2026-10-09（超過）')

    def test_external_issue_is_a_reference_not_a_second_status_authority(self):
        self.cli('init')
        issue='https://github.com/example/project/issues/7'
        data=self.payload({'title':'Issueを参照','system_of_record':issue,'evidence':[{'type':'owner_instruction','quote':'このIssueを追跡','recorded_at':'2026-10-14'}]})
        item=self.cli('add','--file',data)
        patch=self.payload({'status':'done','evidence':[{'type':'owner_instruction','quote':'完了扱いにする','recorded_at':'2026-10-14'}]})
        self.cli('update',item['id'],'--expected-revision','0','--file',patch,ok=False)
        row=next(x for x in self.cli('list')['items'] if x['id']==item['id'])
        self.assertEqual(row['system_of_record'],issue)
        self.assertEqual(row['status'],'external')

    def test_forged_source_quote_and_partial_log_do_not_silently_update(self):
        self.cli('init')
        source=self.ai/'source.md'; source.write_text('まだ確認中\n')
        data=self.payload({'status':'done','evidence':[{'type':'source','path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'line':1,'quote':'完了'}]})
        self.cli('update','old:1','--expected-revision','0','--file',data,ok=False)
        (self.ai/'tasks/events.jsonl').write_text('{"incomplete":')
        self.cli('list',ok=False)


if __name__=='__main__': unittest.main()
