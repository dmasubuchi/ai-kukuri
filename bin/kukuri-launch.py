#!/usr/bin/env python3
"""Launch an existing CLI with this mother ship's dedicated runtime."""
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    product, *args = sys.argv[1:]
    if product not in ('claude', 'codex'):
        raise ValueError('Unknown CLI')
    local = root/'runtime/launchers.json'
    settings = json.loads(local.read_text()) if local.exists() else {}
    wrappers = {(root/'bin'/name).resolve() for name in ('claude', 'codex', 'kukuri-claude', 'kukuri-codex')}
    binary = settings.get(product)
    if not binary:
        for entry in os.get_exec_path():
            candidate = shutil.which(product, path=entry or os.curdir)
            if candidate and Path(candidate).resolve() not in wrappers:
                binary = str(Path(candidate).absolute())
                break
    if binary and Path(binary).resolve() in wrappers:
        raise ValueError('Recursive CLI target: set runtime/launchers.json to the CLI body')
    if binary and not Path(binary).is_absolute():
        raise ValueError('CLI body path must be absolute: ' + product)
    if not binary or not Path(binary).is_file() or not os.access(binary, os.X_OK):
        raise ValueError('CLI not found: set runtime/launchers.json for ' + product)
    directory = root/'runtime'/product
    env = dict(os.environ)
    env['PATH'] = str(Path(binary).parent) + os.pathsep + env.get('PATH', '')
    if product == 'codex':
        env['CODEX_HOME'] = str(directory)
        options = ['--no-daemon', '--sandbox', 'workspace-write', '--ask-for-approval', 'on-request']
    else:
        env['CLAUDE_CONFIG_DIR'] = str(directory)
        env['DISABLE_AUTOUPDATER'] = '1'
        options = ['--setting-sources', 'user', '--permission-mode', 'manual', '--strict-mcp-config',
                   '--mcp-config', str(root/'runtime/mcp.json'), '--append-system-prompt-file', str(root/'CLAUDE.md')]
    if args == ['--check']:
        print(json.dumps({'product':product, 'root':str(root), 'binary':binary,
                          'config_directory':str(directory), 'options':options}, ensure_ascii=False, indent=2))
        return
    os.umask(0o077)
    os.chdir(root)
    os.execve(binary, [binary, *options, *args], env)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        sys.exit('起動停止: ' + str(error))
