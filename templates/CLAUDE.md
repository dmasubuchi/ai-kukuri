# Workspace Entry Point (Claude Code)

At the start of work, read the following three files in this directory.

- `rules/common.md` — common conventions for storage locations, project identification, and Journal/Wiki/TODO
- `registry/projects.json` — the project registry
- `runtime/machine.json` — the real paths on this machine

Match the project name against the registry, and do not ask the user to `cd` each time. If they cannot be loaded, report it and do not switch to other settings by guessing. You may use Claude Code's features. Settings, credentials, and history use the dedicated `CLAUDE_CONFIG_DIR` (`runtime/claude`).

Common procedures (Skills) are in `skills/<name>/SKILL.md`. Read the ones relevant to the work before proceeding. With the dedicated config directory, they are referenced from `runtime/claude/skills/`.
