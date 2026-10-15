# ai-kukuri Common Rules (v0.1)

This file is the canonical source of the workspace's common conventions, independent of any AI product (Claude Code, Codex, etc.). Product-specific settings, credentials, and conversation history are not mixed in here.

## 1. Entry point and project identification

1. At the start of work, read `rules/common.md`, `registry/projects.json`, and `runtime/machine.json` directly under the workspace root.
2. Match the project name or alias in the request against `registry/projects.json`, and combine it with `projects_root` in `runtime/machine.json` to identify the target Repo. Do not ask the user to `cd` each time.
3. Only when the project cannot be identified uniquely, present the candidates and ask for confirmation. Do not settle the path of an unregistered project by guessing.

## 2. Decide where to save by purpose

| Content | Location |
|---|---|
| Official designs, code, and deliverables of a project | `projects/<project>/` (an independent Git Repo per project) |
| One-off work, personal materials, prototypes | `input/` -> `output/<job ID>/` |
| Knowledge and past records reused across projects | `knowledge/` |
| Work to be done (TODOs, commitments, progress) | `tasks/` |
| Product- and machine-specific settings, credentials, history | `runtime/` (not under Git) |

Do not decide the location by format or file extension alone. Do not update the same canonical source in multiple places. Do not copy secret values (credentials, tokens) into knowledge or registries.

## 3. Keep Journal, Living Wiki, and TODO separate

| Kind | Question | Location | Tool |
|---|---|---|---|
| Journal | What happened | `knowledge/journal/YYYY-MM-DD.md` | `bin/kukuri-journal` (append-only) |
| Living Wiki | What is currently known | `knowledge/pages/` | `bin/kukuri-wiki` |
| TODO | What will be done | `tasks/` | `bin/kukuri-tasks` |

- Each Journal entry carries a kind (`decision` owner decision / `request` request from a counterpart / `proposal` AI proposal / `result` work result / `observation` observation), a source, and a time. Never record an AI proposal as the owner's decision.
- The Wiki is updated from Journal entries via `plan` -> review -> `apply --write`. Only a later `decision`/`result` can replace an older statement. Any other contradiction is kept on both sides, with source and date, under "unconfirmed / contradictions" (`未確認・矛盾`).
- Changing a TODO's state requires evidence (a line, quote, or hash of the original text, or the owner's own statement). Do not treat an unconfirmed TODO as done. If an external Issue is the canonical source, do not overwrite its state locally.

## 4. Work safety

- Do not modify originals. Keep copies of records separately, with hashes attached.
- Do not send, post, pay, delete, or publish until you have the owner's explicit confirmation.
- Multiple AIs must not edit the same file at the same time. Divide responsibilities and integrate after review.
- Do not say that something does not exist merely because it was not found. Leave unconfirmed items as unconfirmed.
