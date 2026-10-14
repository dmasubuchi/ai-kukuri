English | [日本語](ja/setup.md)

# Setup

## Prerequisites

- macOS or Linux
- Python 3 (standard library only) and a POSIX shell
- Git
- Optional: Claude Code, Codex, Herdr (this kit provides only the storage conventions and launch isolation)

## Installation methods (all produce the same workspace)

```sh
# A. npm (after publication to npm). Before publication you can run it directly from GitHub
npx kukuri-kit init ~/kukuri-workspace
npx github:<owner>/kukuri-kit init ~/kukuri-workspace

# B. From a cloned repository
git clone <this repository> kukuri-kit && cd kukuri-kit
./install.sh ~/kukuri-workspace

# C. Windows (PowerShell), from a checkout
.\install.ps1 $HOME\kukuri-workspace

# D. One line (macOS / Linux) (specify the archive URL. If you add KUKURI_KIT_SHA256, it aborts when the hash does not match)
curl -fsSL <URL of install.sh> | KUKURI_KIT_TARBALL=<archive URL> sh -s -- ~/kukuri-workspace
```

- It does not create a workspace in a non-empty location. To add only the missing files, use `npx kukuri-kit repair <dir>` (or `scripts/init-workspace.sh --repair <dir>`). Existing files are not overwritten.
- Check the environment: `npx kukuri-kit doctor` (python3 3.9 or later, sh, git). Check operation: `npx kukuri-kit demo` (fictional data).
- Commands are **copied** into `bin/` (each command determines the workspace from its own location. Do not turn them into symlinks).
- `package.json` has `"private": true` for safety before publication (so `npm publish` cannot happen by mistake). The owner decides on publication.

## Verifying operation (optional)

```sh
sh examples/demo.sh
(cd tests && python3 -B -m unittest discover -p 'test_*.py')   # subshell; the working directory does not change
```

## Where common Skills are registered

`init-workspace.sh` registers `skills/<name>/` by relative symlink in the locations each product searches.

| Product | Registered at | Status |
|---|---|---|
| Claude Code (via `kukuri-claude`; `CLAUDE_CONFIG_DIR=runtime/claude`) | `runtime/claude/skills/<name>` | Operation confirmed in private use. This kit's automated tests check only that the links exist |
| Codex | `.agents/skills/<name>` | Placement based on official documentation. Loading on a real machine is not verified by this kit |

The entry-point documents (`AGENTS.md` `CLAUDE.md`) also state where the Skills are.

## Putting knowledge and TODOs under version control

The generated `.gitignore` excludes `knowledge/` and `tasks/` (to avoid accidentally putting business records or customer information into the conventions repository). If you want version control, use a separate private repository.

## 4. Register a project

Add the project to `registry/projects.json`. `directory` is a path relative to `projects/`. The actual path is determined by `runtime/machine.json`.

## 5. Launch an AI product (optional)

```sh
cd ~/kukuri-workspace
# Write the path of each product's executable to runtime/launchers.json (if omitted, it is searched on PATH)
echo '{"claude": "/absolute/path/to/claude", "codex": "/absolute/path/to/codex"}' > runtime/launchers.json
bin/kukuri-claude --check     # does not launch; checks that settings are isolated
bin/kukuri-codex  --check
```

You do not need to add `bin/` to `PATH`. Each product's settings, credentials and history are isolated under `runtime/claude/` and `runtime/codex/`.

## 6. Import records (optional)

Write the directories to import from in `registry/knowledge-sources.json`, then run `bin/kukuri-memory import`.

```json
{"sources": [{"id": "notes", "root": "/absolute/path/to/notes"}]}
```

If an import source does not exist, it stops without replacing the current index. The originals are not modified.

## Uninstall

Just delete the workspace directory. The kit itself writes nothing to the system.
