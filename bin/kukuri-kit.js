#!/usr/bin/env node
'use strict';
// Thin launcher for `npx kukuri-kit ...`. All real work is done by the shell/Python scripts.
const { spawnSync } = require('child_process');
const path = require('path');
const root = path.resolve(__dirname, '..');
const pkg = require(path.join(root, 'package.json'));

const usage = `kukuri-kit ${pkg.version}

Usage:
  kukuri-kit init <dir> [--lang en|ja]    create a workspace (the directory must not exist or be empty)
  kukuri-kit repair <dir> [--lang en|ja]  add only the files that are missing; never overwrites
  kukuri-kit demo [dir]      run the fictional-data demo (Journal -> Wiki -> TODO)
  kukuri-kit doctor          check python (3.9+) and git
  kukuri-kit --version
`;

function pythonCommand() {
  for (const candidate of ['python3', 'python']) {
    const r = spawnSync(candidate, ['-c', 'import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)']);
    if (!r.error && r.status === 0) return candidate;
  }
  return null;
}

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: 'inherit' });
  if (r.error) { console.error('kukuri-kit: ' + r.error.message); return 127; }
  return r.status === null ? 1 : r.status;
}

function doctor() {
  let ok = true;
  const probe = (label, cmd, args, check) => {
    const r = spawnSync(cmd, args, { encoding: 'utf8' });
    const out = ((r.stdout || '') + (r.stderr || '')).trim().split('\n')[0];
    const good = !r.error && r.status === 0 && (!check || check(out));
    console.log((good ? 'ok   ' : 'NG   ') + label + (out ? '  (' + out + ')' : ''));
    if (!good) ok = false;
  };
  const py = pythonCommand() || 'python3';
  probe('python >= 3.9', py, ['-c', 'import sys;print(sys.version.split()[0]);sys.exit(0 if sys.version_info>=(3,9) else 1)']);
  probe('git (optional)', 'git', ['--version']);
  return ok ? 0 : 1;
}

const [cmd, ...rest] = process.argv.slice(2);
const python = pythonCommand();
if (!python && cmd !== '--version' && cmd !== '-v' && cmd !== '--help' && cmd !== '-h' && cmd !== undefined && cmd !== 'doctor') {
  console.error('kukuri-kit: Python 3.9 or later is required');
  process.exit(2);
}
switch (cmd) {
  case 'init':
  case 'repair': {
    const lang = rest.indexOf('--lang') >= 0 ? ['--lang', rest.splice(rest.indexOf('--lang'), 2)[1] || ''] : [];
    if (rest.length !== 1) { console.error(usage); process.exit(2); }
    const flag = cmd === 'repair' ? ['--repair'] : [];
    process.exit(run(python, ['-B', path.join(root, 'scripts/init_workspace.py'), ...lang, ...flag, rest[0]]));
  }
  case 'demo':
    process.exit(run(python, ['-B', path.join(root, 'examples/demo.py'), ...rest]));
  case 'doctor':
    process.exit(doctor());
  case '--version':
  case '-v':
    console.log(pkg.version);
    process.exit(0);
  case '--help':
  case '-h':
  case undefined:
    console.log(usage);
    process.exit(cmd === undefined ? 2 : 0);
  default:
    console.error('kukuri-kit: unknown command: ' + cmd + '\n\n' + usage);
    process.exit(2);
}
