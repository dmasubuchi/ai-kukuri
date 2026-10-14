# Workspace Entry Point (Codex etc.)

At the start of work, read the following three files in the same directory as this file.

- `rules/common.md` — common conventions for storage locations, project identification, and Journal/Wiki/TODO
- `registry/projects.json` — the project registry
- `runtime/machine.json` — the real paths on this machine

Identify the target Repo from the project name, and do not ask the user to `cd` each time. Present candidates only when it cannot be identified. Keep product-specific settings, credentials, and history in a dedicated area under `runtime/`, and do not mix them into the common conventions.

Common procedures (Skills) are in `skills/<name>/SKILL.md`. Read the ones relevant to the work before proceeding. Codex can also reference them from `.agents/skills/`.
