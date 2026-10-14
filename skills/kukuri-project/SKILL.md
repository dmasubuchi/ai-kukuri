---
name: kukuri-project
description: Identify the target Repo from a project name, and decide where to save official deliverables, personal deliverables, and knowledge.
---

1. Match the names and aliases in `registry/projects.json` against the project name in the request. The real path is `projects_root` in `runtime/machine.json` combined with the registry's `directory`.
2. Once uniquely identified, check that Repo's `AGENTS.md` / `CLAUDE.md` / README before working. Ask for confirmation only when there are multiple candidates. Do not guess the path of an unregistered project.
3. Follow the table in `rules/common.md` for where to save. A project's official deliverables go in the project Repo, one-off or personal work in `output/<job ID>/`, reusable knowledge in `knowledge/`, and upcoming work in `tasks/`.
4. Being listed in the registry is not permission to write or publish.
