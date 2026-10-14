# ワークスペースの入口（Claude Code）

作業の開始時に、このディレクトリの次の3ファイルを読んでください。

- `rules/common.md` — 保存先・案件特定・Journal/Wiki/TODO の共通規約
- `registry/projects.json` — 案件の台帳
- `runtime/machine.json` — このマシンの実パス

案件名は台帳と照合し、毎回 `cd` を依頼しないでください。読み込めない場合は報告し、推測で別の設定へ切り替えないでください。Claude Code の機能は活用して構いません。設定・認証・履歴は専用の `CLAUDE_CONFIG_DIR`（`runtime/claude`）を使います。
