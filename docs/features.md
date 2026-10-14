English | [日本語](ja/features.md)

# Features — implemented and future ideas

| Feature | Status | Verification |
|---|---|---|
| Common conventions, project ledger, entry-point templates (`rules/` `templates/`) | Implemented | Tests of `init-workspace.sh` |
| Workspace creation (`scripts/init-workspace.sh`, `--repair`) | Implemented | Tests and CI (macOS/Linux) |
| Entry points: `install.sh` (checkout / archive URL + SHA-256), npm package `kukuri-kit` (`npx kukuri-kit init/repair/demo/doctor`) | Implemented. **Not published to npm** (`private: true`) | Tests (including the `npm pack` contents and installation from the unpacked package) |
| Journal (`kukuri-journal`): append, kind/source/timestamp, listing, preserving copies of evidence | Implemented | Unit tests |
| Living Wiki (`kukuri-wiki`): plan/apply/show/check, handling of conflicts, idempotency | Implemented | Unit tests and demo |
| TODO (`kukuri-tasks`): baseline + append-only history, evidence verification, version-conflict detection | Implemented | Unit tests |
| Record import and search (`kukuri-memory`): import/search/show/timeline/tasks/verify/archive | Implemented | Unit tests |
| Reference resolution and checking (`kukuri-paths`): resolve/check/report | Implemented | Unit tests |
| Isolated launch per product (`kukuri-claude` `kukuri-codex`) | Implemented (tested with substitute executables) | Unit tests. No automated test with the real Claude Code or Codex |
| Three common Skills (journal-wiki / recall / project), and registration (symlinks) in each product's discovery locations | Implemented (documentation + registration). Loading in the actual products is not verified by this kit ([setup](setup.md)) | Registration tests only |
| Use with Herdr | **Documentation only** (`docs/herdr.md`). There is no dedicated tool | Verification steps and syntax are documented. No automated test by the kit |
| Chat / message delivery between AIs | **Not implemented** | — |
| Integration with external Subagents / external agents | **Not implemented** | — |
| Search of old conversation logs (each product's native history) | **Not implemented** (under consideration; excluded from v0.1 because it depends on non-public formats) | — |
| Integration with external services such as MCP, email, Teams | **Not included** | — |
| Radio / audio generation | **Not included** (the terms of use of audio models must be checked) | — |
| Windows (native) | **Python CLIs, installer, npm launcher and demo: tested in CI on `windows-latest`.** POSIX-only: the shell wrappers; the launcher is untested against the real products on Windows | CI (Python 3.9 / 3.12) |
