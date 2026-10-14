# 機能一覧 — 実装済みと将来構想

| 機能 | 状態 | 検証 |
|---|---|---|
| 共通規約・案件台帳・入口テンプレート（`rules/` `templates/`） | 実装済み | `init-workspace.sh` の試験 |
| ワークスペースの作成（`scripts/init-workspace.sh`） | 実装済み | 試験・CI（macOS/Linux） |
| Journal（`kukuri-journal`）: 追記、種類・出典・時刻、一覧、根拠の写しの保全 | 実装済み | 単体試験 |
| Living Wiki（`kukuri-wiki`）: plan/apply/show/check、矛盾の扱い、冪等性 | 実装済み | 単体試験・demo |
| TODO（`kukuri-tasks`）: 基準＋追記履歴、根拠検証、版の競合検知 | 実装済み | 単体試験 |
| 記録の取り込み・検索（`kukuri-memory`）: import/search/show/timeline/tasks/verify/archive | 実装済み | 単体試験 |
| 参照の解決・検査（`kukuri-paths`）: resolve/check/report | 実装済み | 単体試験 |
| 製品別の隔離起動（`kukuri-claude` `kukuri-codex`） | 実装済み（代替の実行ファイルでの試験） | 単体試験。実際のClaude Code・Codexでの自動試験は無し |
| 共通Skills 3つ（journal-wiki / recall / project） | 実装済み（文書） | 形式のみ |
| Herdr での併用 | **文書のみ**（`docs/herdr.md`）。専用のツールは無い | 確認手順と構文を記載。キットによる自動試験は無し |
| AI間のチャット・メッセージ配送 | **未実装** | — |
| 外部Subagent・外部エージェントとの連携 | **未実装** | — |
| 旧会話ログ（各製品のネイティブ履歴）の検索 | **未実装**（検討中。非公開形式への依存のため、v0.1から除外） | — |
| MCP・メール・Teams等の外部サービス連携 | **含まない** | — |
| ラジオ・音声生成 | **含まない**（音声モデルの利用条件の確認が必要） | — |
| Windows 対応 | **未対応** | — |
