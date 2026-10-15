#!/usr/bin/env python3
"""Create a KUKURI workspace from this kit, or repair an existing one (portable: macOS, Linux, Windows).

  init_workspace.py [--lang en|ja] [--repair] <target-dir>

Create: the target must not exist or must be empty.  --repair: add only the files that are missing;
nothing that exists is ever overwritten.  Nothing outside <target-dir> is written.
Symlinks are never written through; they are checked before anything is created.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

KIT = Path(__file__).resolve().parents[1]
SKILL_LINK_DIRS = (('runtime', 'claude', 'skills'), ('.agents', 'skills'))


def stop(message):
    print('stop: ' + message, file=sys.stderr)
    sys.exit(2)


def parse(argv):
    mode, lang, target = 'create', 'en', None
    it = iter(argv)
    for arg in it:
        if arg == '--repair':
            mode = 'repair'
        elif arg == '--lang':
            lang = next(it, '')
        elif arg.startswith('--lang='):
            lang = arg.split('=', 1)[1]
        elif arg.startswith('-'):
            stop('unknown option: ' + arg)
        elif target is None:
            target = arg
        else:
            stop('too many arguments')
    if not target:
        print('usage: init_workspace.py [--lang en|ja] [--repair] <target-dir>', file=sys.stderr)
        sys.exit(2)
    if lang not in ('en', 'ja'):
        stop('--lang must be en or ja')
    return mode, lang, Path(target)


WORKSPACE_SKIP = {'ai-kukuri.js'}      # package launcher: needs the npm package files, so it is not copied into a workspace


def is_link(path):
    """Symlink, or a Windows junction / other reparse point (is_symlink() is False for junctions)."""
    if path.is_symlink():
        return True
    try:
        attrs = getattr(os.lstat(str(path)), 'st_file_attributes', 0)
    except OSError:
        return False
    return bool(attrs & 0x400)              # FILE_ATTRIBUTE_REPARSE_POINT


def put(src, dest, executable=False):
    """Copy only when the destination does not exist (a dangling symlink counts as existing)."""
    if os.path.lexists(dest):
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    if executable and os.name != 'nt':
        os.chmod(dest, 0o755)
    return True


def main(argv):
    mode, lang, target = parse(argv)
    if lang == 'ja':
        base = KIT / 'locales' / 'ja'
        if not base.is_dir():
            stop('locales/ja is missing')
        rules_src, skills_src, entry_src = base / 'rules', base / 'skills', base / 'templates'
    else:
        rules_src, skills_src, entry_src = KIT / 'rules', KIT / 'skills', KIT / 'templates'
    templates = KIT / 'templates'

    if mode == 'create' and target.exists() and any(target.iterdir()):
        stop('target is not empty: %s (use --repair to add missing files)' % target)
    if mode == 'repair' and not target.is_dir():
        stop('not a directory: ' + str(target))
    target.mkdir(parents=True, exist_ok=True)
    target = Path(os.path.realpath(target))

    # Refuse to write through symlinks. Checked before anything is created.
    # projects/ input/ output/ may be symlinks (e.g. another disk): they are only created if missing, never written.
    skills = sorted(p.name for p in skills_src.iterdir() if p.is_dir())
    guarded = ['bin', 'rules', 'rules/common.md', 'skills', 'registry', 'registry/projects.json', 'registry/paths.json',
               'runtime', 'runtime/mcp.json', 'runtime/machine.json', 'runtime/claude', 'runtime/claude/skills',
               '.claude', '.agents', '.agents/skills', 'tasks', 'tasks/baseline.json', 'knowledge',
               'knowledge/journal', 'knowledge/pages', 'knowledge/records', 'AGENTS.md', 'CLAUDE.md', '.gitignore']
    guarded += ['bin/' + p.name for p in (KIT / 'bin').iterdir() if p.name not in WORKSPACE_SKIP]
    for name in skills:
        guarded += ['skills/' + name, 'skills/%s/SKILL.md' % name]
    for rel in guarded:
        if is_link(target / rel):
            stop('refusing to write through a symlink: %s' % (target / rel))

    for d in ('bin', 'rules', 'skills', 'registry', 'runtime', 'tasks', 'projects', 'input', 'output',
              'knowledge/journal', 'knowledge/pages', 'knowledge/records'):
        (target / d).mkdir(parents=True, exist_ok=True)
    for src in sorted((KIT / 'bin').iterdir()):
        if src.is_file() and src.name not in WORKSPACE_SKIP:
            put(src, target / 'bin' / src.name, executable=True)
    put(rules_src / 'common.md', target / 'rules/common.md')
    for name in skills:
        put(skills_src / name / 'SKILL.md', target / 'skills' / name / 'SKILL.md')
    # Register the shared skills where each product looks for them (relative links; copies if links are not allowed)
    for parts in SKILL_LINK_DIRS:
        link_dir = target.joinpath(*parts)
        link_dir.mkdir(parents=True, exist_ok=True)
        for name in skills:
            link = link_dir / name
            if os.path.lexists(link):
                continue
            rel = os.path.relpath(target / 'skills' / name, link_dir)
            try:
                os.symlink(rel, link, target_is_directory=True)
            except OSError:                                     # e.g. Windows without the symlink privilege
                shutil.copytree(target / 'skills' / name, link)
    put(entry_src / 'AGENTS.md', target / 'AGENTS.md')
    put(entry_src / 'CLAUDE.md', target / 'CLAUDE.md')
    put(templates / 'registry-projects.json', target / 'registry/projects.json')
    put(templates / 'registry-paths.json', target / 'registry/paths.json')
    put(templates / 'mcp.json', target / 'runtime/mcp.json')
    put(templates / 'workspace.gitignore', target / '.gitignore')
    machine = target / 'runtime/machine.json'
    if not os.path.lexists(machine):
        root = str(target)
        machine.write_text(json.dumps({
            'machine': 'this-machine', 'workspace_root': root,
            'projects_root': str(target / 'projects'), 'input_root': str(target / 'input'),
            'output_root': str(target / 'output'), 'knowledge_root': str(target / 'knowledge'),
            'tasks_root': str(target / 'tasks'), 'writable_roots': [root],
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not (target / 'tasks/baseline.json').exists():
        subprocess.run([sys.executable, '-B', str(target / 'bin/kukuri-tasks'), 'init'], check=True,
                       stdout=subprocess.DEVNULL)
    print('workspace ready (%s, lang=%s): %s' % (mode, lang, target))


if __name__ == '__main__':
    main(sys.argv[1:])
