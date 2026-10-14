English | [日本語](ja/roadmap.md)

# Roadmap

Priority goes first to being able to publish safely.

## Before publication (required)
- [ ] Owner finalizes the license (currently an MIT candidate)
- [ ] Decide distribution terms for the illustrations (declared as GPT-generated) and check the service terms
- [ ] Reflect the independent review's findings and re-review
- [ ] Security check of the full Git history (including verifying the sources of external links in the README and docs)
- [ ] Confirm installation in a third party's environment (macOS, Linux)

## v0.2 candidates
- [ ] Automated tests of launching the real Claude Code and Codex (beyond the non-interactive `--check`)
- [ ] Declare the classification rules of `kukuri-memory` in a configuration file (specify `registry/knowledge-categories.json`)
- [ ] English versions of docs, conventions and Skills (README is primarily English, Japanese is in README.ja.md)
- [ ] Localisation of the CLI messages and generated page headings, which are currently Japanese
- [ ] Decide on publication to npm (the public name `kukuri-kit` is unused on the registry; remove `"private": true` when publishing)
- [ ] Editing rules for Journal records (express corrections by appending)

## Ideas (not implemented, not decided)
- A mechanism for communication between AIs (assuming existing features such as Herdr are used)
- Integration with external agents and Subagents
- Search of each product's conversation history (a stable specification is a prerequisite, since the formats are non-public)
- Windows support
