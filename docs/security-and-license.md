English | [日本語](ja/security-and-license.md)

# Security and license review

Status: **reviewed for the first public release.** What has been checked and what has not are described separately.

## 1. What is not included

| Item | Result |
|---|---|
| Real data (knowledge, records, TODOs, inputs, deliverables, runtime settings, credentials, conversation history) | Not included. `tests/test_hygiene.py` checks that directories such as `runtime/` `knowledge/` `tasks/` do not exist |
| Personal absolute home paths, email addresses, tokens, private keys | Not included. The same test checks tracked files (patterns for `/Users/<name>` `/home/<name>`, email addresses, various tokens, private keys) |
| Git history of the old environment | Not included. This repository was started from a fresh `git init` |
| Real customers, people or amounts | Not included. Samples and tests are all fictional (Acme, Sample Portal, etc.) |

## 2. Write safety (implemented and tested)

- Writes of Journal, Wiki, TODO, records, index and reference repair reject paths that resolve outside the workspace (including via symlinks). They also reject the case where the final element is a symlink.
- Structural fields of the Journal (content, source, recorder, update, TODO, date, time) do not allow newlines, control characters or Unicode line/paragraph separators. This prevents record-boundary injection.
- The history and lock of reference repair, and the settings directory of launched products, follow the same rule (rejected if they resolve outside).
- Read arguments (date, slug, record ID) are strictly validated for format and never read outside the intended directory.
- Concurrent Wiki updates are performed inside a lock.
- Originals are not modified. When an import source is missing, the current index is not replaced.
- Evidence files cited by a TODO and the stored copies read by `kukuri-memory show` must resolve inside the workspace; Journal and Wiki pages that resolve outside are never read, shown or indexed.

## 3. License

| Subject | Status |
|---|---|
| Code and documentation of this repository | MIT License (adopted by the owner) |
| External source code and libraries | **Not bundled**. Only the Python standard library is used (`import` statements checked) |
| External Skills and plugins | **Not bundled**. The three in `skills/` were written in this repository |
| Audio generation and radio production | **Not included**, because the terms of use of audio models (characters, voice libraries) must be checked |
| Illustrations (`docs/images/`) | AI-generated with ChatGPT (owner's declaration). Licensed under CC BY 4.0, separately from the MIT license of the code ([NOTICE](../NOTICE.md)). Generation records are not held in this repository |
| External CLIs used at runtime (Claude Code, Codex, Herdr) | Not bundled. Follow each product's terms of use |
| npm package | No dependencies (no `dependencies`). published as `ai-kukuri` |

### Sources checked
- README "Origin of the name": an independent review confirmed that the official website of Shirayama Hime Shrine (the "Deities enshrined" section of https://www.shirayama.or.jp/about/) contains an explanation of the two deities' mediation and a religious explanation linking "kukuri" and "kukuru" (to bind). The README does not quote the shrine's text verbatim. The depiction from one version of the Nihon Shoki follows an explanation specified by the owner.

### Not checked
- That the design of the private toolset this kit originated from was inspired by the structure of a third-party repository. No code reuse is assumed, but confirmation by an independent review is required.
- The terms of the illustration generation service, and whether commercial use and redistribution are allowed.

## 4. Pre-publication checklist

- [ ] Secret scan of the full Git history (all commits, all branches, tags)
- [ ] Reflect the independent review's findings
- [x] Finalize the license (MIT, owner)
- [x] Illustration terms decided (CC BY 4.0; owner's declaration)
- [ ] Install and test in a third-party environment (macOS, Linux)
- [x] Name `ai-kukuri` (npm and repository); visibility public (owner)
