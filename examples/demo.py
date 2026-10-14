#!/usr/bin/env python3
"""Journal -> Living Wiki -> TODO, end to end, with fictional data only (portable).

Usage: python examples/demo.py [workspace-dir]     (default: a new temporary directory)
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

KIT = Path(__file__).resolve().parents[1]

for _stream in (sys.stdout, sys.stderr):      # Windows consoles default to a legacy code page
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8')


def main(argv):
    ws = Path(argv[0]) if argv else Path(tempfile.mkdtemp()) / 'workspace'
    subprocess.run([sys.executable, '-B', str(KIT / 'scripts/init_workspace.py'), str(ws)], check=True,
                   stdout=subprocess.DEVNULL)

    def tool(name, *args, show=False):
        p = subprocess.run([sys.executable, '-B', str(ws / 'bin' / name), *args], cwd=str(ws),
                           capture_output=True, text=True, encoding='utf-8')
        if p.returncode != 0:
            sys.stderr.write(p.stderr)
            sys.exit(p.returncode)
        if show:
            print(p.stdout.rstrip())
        return json.loads(p.stdout) if p.stdout.strip().startswith(('{', '[')) else p.stdout

    def journal(kind, author, date, time, source, text, wiki=None):
        args = ['add', '--kind', kind, '--author', author, '--date', date, '--time', time, '--source', source, '--text', text]
        if wiki:
            args += ['--wiki', wiki]
        return tool('kukuri-journal', *args)

    print('== 1. record what happened (Journal)')
    journal('decision', 'alice', '2026-03-02', '10:00', 'Acme kickoff meeting notes (fictional)',
            'Acme Portal will be hosted on Cloud A.', 'wiki:acme-portal#hosting = Acme Portal is hosted on Cloud A.')
    print('== 2. plan the wiki update (nothing is written)')
    tool('kukuri-wiki', 'plan', '--date', '2026-03-02', show=True)
    print('== 3. apply')
    tool('kukuri-wiki', 'apply', '--date', '2026-03-02', '--write')
    print('== 4. a later AI proposal does not override the decision')
    journal('proposal', 'bot', '2026-03-09', '09:30', 'assistant suggestion (fictional)', 'Cloud B might be cheaper.',
            'wiki:acme-portal#hosting = Acme Portal should move to Cloud B.')
    tool('kukuri-wiki', 'apply', '--date', '2026-03-09', '--write')
    print('== 5. the owner decides later: the old claim moves to history, with source and date')
    journal('decision', 'alice', '2026-03-16', '11:00', 'Acme steering meeting notes (fictional)',
            'Move Acme Portal to Cloud B.', 'wiki:acme-portal#hosting = Acme Portal is hosted on Cloud B.')
    tool('kukuri-wiki', 'apply', '--date', '2026-03-16', '--write')
    sys.stdout.buffer.write((ws / 'knowledge/pages/acme-portal.md').read_bytes() + b'\n')
    sys.stdout.flush()
    print('== 6. a TODO whose completion is backed by a journal entry')
    entry = journal('result', 'alice', '2026-03-20', '17:00', 'Acme acceptance report (fictional)',
                    'Acme Portal acceptance test passed.')['id']
    evidence = tool('kukuri-journal', 'evidence', entry)
    proposal = ws / 'proposal.json'
    done = ws / 'done.json'
    proposal.write_text(json.dumps({'title': 'Confirm Acme Portal acceptance', 'owner': 'alice', 'evidence': [evidence]}),
                        encoding='utf-8')
    done.write_text(json.dumps({'status': 'done', 'evidence': [evidence]}), encoding='utf-8')
    task = tool('kukuri-tasks', 'add', '--file', str(proposal))['id']
    tool('kukuri-tasks', 'update', task, '--expected-revision', '0', '--file', str(done))
    print('== 7. check')
    tool('kukuri-wiki', 'check', show=True)
    print('demo finished: %s' % ws)


if __name__ == '__main__':
    main(sys.argv[1:])
