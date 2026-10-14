---
name: kukuri-project
description: 案件名から対象Repoを特定し、正式成果物・個人用成果物・知識の保存先を決める。
---

1. `registry/projects.json` の名前・別名と、依頼の案件名を照合する。実パスは `runtime/machine.json` の `projects_root` と台帳の `directory` を結合する。
2. 一意に特定できたら、そのRepoの `AGENTS.md` / `CLAUDE.md` / README を確認してから作業する。複数候補のときだけ確認する。未登録の案件のパスを推測しない。
3. 保存先は `rules/common.md` の表に従う。案件の正式成果物は案件Repo、単発・個人用は `output/<仕事ID>/`、再利用する知識は `knowledge/`、これからの仕事は `tasks/`。
4. 台帳に載っていることは、書き込み・公開の許可ではない。
