[English](../roadmap.md) | 日本語

# ロードマップ

優先度は、安全に公開できることを先にする。

## 公開前（必須）
- [ ] 所有者によるライセンスの確定（現在はMIT候補）
- [ ] 挿絵（GPT生成と申告）の配布条件の決定とサービス規約の確認
- [ ] 独立レビューの指摘の反映と再レビュー
- [ ] Git全履歴のセキュリティ確認（README・docsの外部リンクの出典確認を含む）
- [ ] 第三者の環境でのインストール確認（macOS・Linux）

## v0.2 候補
- [ ] 実際のClaude Code・Codexでの起動の自動試験（非対話の `--check` 以外）
- [ ] `kukuri-memory` の分類規則を設定ファイルで宣言する（`registry/knowledge-categories.json` の仕様化）
- [ ] docs・規約・Skillsの英語版（READMEは英語が主、日本語は README.ja.md）
- [ ] npmへの公開の判断（公開名 `kukuri-kit` はレジストリで未使用。公開する際に `"private": true` を外す）
- [ ] Journal記録の編集規則（訂正を追記で表す）

## 構想（未実装・未確定）
- AI間の連絡の仕組み（Herdr等の既存機能を使う前提）
- 外部エージェント・Subagentとの連携
- 各製品の会話履歴の検索（非公開形式のため、安定した仕様が前提）
- Windows 対応
