<p align="center">
  <img src="docs/images/kukuri-hime.jpg" alt="Illustration of Kukuri-hime: white chrysanthemums, a mirror, a rainbow and a sacred mountain" width="420">
</p>

<p align="center"><b>English</b> | <a href="README.ja.md">日本語</a></p>

# ai-kukuri

**Knowledge Unification Kit for Updates, Recall & Integration**

A small, local toolkit that lets several AIs (Claude Code, Codex and others) record their daily work, keep the history of how things came to be, and update current knowledge and TODOs from it, with sources. No services, no daemon: Python 3 standard library and plain files only.

> Status: **v0.1**. What is implemented and what is only an idea are listed separately in [docs/features.md](docs/features.md).

## The name — KUKURI (Kukuri-hime-no-kami)

The name comes from **Kukuri-hime-no-kami (菊理媛神)**, a goddess of Japanese mythology.

In one variant account of the *Nihon Shoki*, Izanagi and Izanami stand opposed to each other at the border of Yomi, the land of the dead. There, Kukuri-hime appears and speaks.

The myth does not record what she said. It only tells that Izanagi heard her, approved, and left the place.

Her name, "Kukuri", is also read as connected to the Japanese word **"kukuru" (括る, to bind, to tie together)**, and in later ages she has been revered as a deity who mediates between what is different and ties bonds.

Today's AIs each have their own abilities, memories, tools and working environments.

KUKURI is not meant to replace them with one; it exists to **connect knowledge and work while keeping the differences**.

It stands between Claude Code, Codex and other AIs, and ties together past records (Journal), current knowledge (Living Wiki) and the work ahead (TODO).

KUKURI is not a ruler over all AIs. It is a mechanism that stands between different AIs and lets each of them do what it does best.

An open-source project inspired by Japanese mythology, for "binding" AI, knowledge and work together.

*The myth follows a variant account of the Nihon Shoki. The link with "kukuru" is a traditional interpretation, not an established etymology; the official explanation of Shirayama-hime Shrine also presents this connection ([Shirayama-hime Shrine: about / enshrined deities](https://www.shirayama.or.jp/about/), Japanese).*

> The illustration is AI-generated (ChatGPT, as declared by the project owner) and is licensed separately under CC BY 4.0; see [NOTICE.md](NOTICE.md).

## Three things, kept apart

| Kind | Question | Where | Tool |
|---|---|---|---|
| **Journal** | What happened? | `knowledge/journal/YYYY-MM-DD.md` | `kukuri-journal` (append only) |
| **Living Wiki** | What do we know now? | `knowledge/pages/` | `kukuri-wiki` |
| **TODO** | What will we do? | `tasks/` | `kukuri-tasks` |

- Every Journal entry has a kind (owner decision / request / AI proposal / work result / observation), a source and a time. An AI proposal is never treated as a decision.
- The Wiki is rebuilt from the Journal in date-time order (`plan` → review → `apply --write`). The result does not depend on append order or on when `apply` ran. A later decision or result replaces an older statement; contradictions that cannot be decided are kept side by side, with sources and dates, as "unconfirmed".
- Changing a TODO's state needs evidence (a quoted line with its hash). A Journal entry can be that evidence (`kukuri-journal evidence`).

## Install

Requires Python 3.9+. Node.js is only needed for `npx`. Runs on macOS, Linux and Windows (see [Platform notes](#platform-notes)).

```sh
# 1. npm, or straight from GitHub:
npx ai-kukuri init ~/kukuri-workspace
npx github:dmasubuchi/ai-kukuri init ~/kukuri-workspace

# 2. From a checkout
git clone <this repository> ai-kukuri && cd ai-kukuri
./install.sh ~/kukuri-workspace

# 3. Windows (PowerShell), from a checkout
.\install.ps1 $HOME\kukuri-workspace

# 4. One line, macOS / Linux (give the URL of the archive)
curl -fsSL <URL of install.sh> | KUKURI_KIT_TARBALL=<URL of the archive> sh -s -- ~/kukuri-workspace
```

Check your environment with `npx ai-kukuri doctor`, or just watch it work with `npx ai-kukuri demo` (fictional data only).

## Platform notes

| Platform | Status |
|---|---|
| macOS, Linux | The Python CLIs, the installer, the demo and the launcher wrappers are tested in CI (Python 3.9 and 3.12). |
| Windows | The Python CLIs, `init_workspace.py`, `install.ps1`, `npx ai-kukuri` and the demo are tested in CI on `windows-latest` (Python 3.9 and 3.12). The shell wrappers (`install.sh`, `kukuri-claude`, `kukuri-codex`) are POSIX only; on Windows run `python bin/kukuri-launch.py claude` instead. Tests that need symlinks or POSIX permissions are skipped there. The launcher has not been run against the real Claude Code or Codex on Windows. |

The AI itself does not care where it runs; the platform notes above are only about this kit's own scripts (file locks, symlink guards, installer).

## Verify with your real CLIs (manual, once)

The automated tests use a fake CLI. To confirm the real thing on your machine:

1. Run `bin/kukuri-claude` (or `bin/kukuri-codex`) inside the workspace and sign in once; settings stay under `runtime/`.
2. Ask it to list the available skills. `kukuri-journal-wiki`, `kukuri-recall` and `kukuri-project` should appear.
3. Check that your usual `~/.claude` / `~/.codex` was not read or modified.

## First steps

```sh
cd ~/kukuri-workspace
bin/kukuri-journal add --kind decision --author me --source "weekly meeting notes" \
  --text "Hosting is decided: Cloud A" \
  --wiki "wiki:my-portal#hosting = Hosted on Cloud A"
bin/kukuri-wiki plan            # writes nothing
bin/kukuri-wiki apply --write
bin/kukuri-wiki check
```

Run the tests from the repository root (a subshell, so your working directory does not change):

```sh
(cd tests && python3 -B -m unittest discover -p 'test_*.py')
```

## What is in the box

```
bin/        kukuri-journal  kukuri-wiki  kukuri-tasks  kukuri-memory  kukuri-paths
            kukuri-launch.py  kukuri-claude  kukuri-codex
            (bin/ai-kukuri.js is the npm package launcher only; it is not copied into a workspace)
rules/      common.md             the shared, product-independent rules
skills/     kukuri-journal-wiki  kukuri-recall  kukuri-project
templates/  AGENTS.md  CLAUDE.md  registry-projects.json  ...
locales/ja/ Japanese rules, skills and entry files (init --lang ja)
scripts/    init_workspace.py (portable)  init-workspace.sh (wrapper)
examples/   demo.py (portable)  demo.sh (wrapper)
docs/       architecture.md  features.md  setup.md  herdr.md  security-and-license.md  roadmap.md
docs/ja/    the same documents in Japanese
install.sh  install.ps1  package.json (npm package)
tests/
```

The documentation, rules, skills and entry files are English by default; Japanese versions live in `docs/ja/` and `locales/ja/` (`init --lang ja`). The tools' own messages and the headings of generated Wiki pages are still Japanese; localisation is on the [roadmap](docs/roadmap.md).

## Design promises

- Originals are never modified; copies are kept with their hash.
- "Not found" is never reported as "does not exist". Unconfirmed stays unconfirmed.
- Sending, posting, paying, deleting and publishing happen only after a human confirms. This kit has no feature that does them.
- It does not re-implement the official Claude Code, Codex or Herdr. It only provides storage rules and isolated launching.
- It never writes outside the workspace, through symlinks or otherwise.

## License

Code and documentation: MIT License. The illustration `docs/images/kukuri-hime.jpg`: CC BY 4.0. See [NOTICE.md](NOTICE.md), [LICENSE](LICENSE) and [docs/security-and-license.md](docs/security-and-license.md).
