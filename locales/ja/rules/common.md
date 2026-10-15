# ai-kukuri 共通ルール（v0.1）

このファイルは、AI製品（Claude Code・Codex など）に依存しない、ワークスペースの共通規約の正本です。製品ごとの設定・認証・会話履歴をここに混ぜません。

## 1. 入口と案件の特定

1. 作業の開始時に、ワークスペース直下の `rules/common.md`、`registry/projects.json`、`runtime/machine.json` を読む。
2. 依頼に含まれる案件名・別名を `registry/projects.json` と照合し、`runtime/machine.json` の `projects_root` と結合して対象Repoを特定する。毎回 `cd` を依頼しない。
3. 一意に特定できないときだけ、候補を示して確認する。未登録の案件のパスを推測で確定しない。

## 2. 用途で保存先を決める

| 内容 | 保存先 |
|---|---|
| 案件の正式な設計・コード・納品資料 | `projects/<案件>/`（案件ごとに独立したGit Repo） |
| 単発の作業・個人用の資料・試作 | `input/` → `output/<仕事ID>/` |
| 複数案件で再利用する知識・過去の記録 | `knowledge/` |
| これから行う仕事（TODO・約束・進捗） | `tasks/` |
| 製品・マシン固有の設定、認証、履歴 | `runtime/`（Git管理しない） |

形式や拡張子だけで保存先を判断しない。同じ正本を複数の場所で更新しない。秘密の値（認証情報・トークン）を知識や台帳へコピーしない。

## 3. Journal・Living Wiki・TODO は分離する

| 種類 | 問い | 場所 | 道具 |
|---|---|---|---|
| Journal | 何が起きたか | `knowledge/journal/YYYY-MM-DD.md` | `bin/kukuri-journal`（追記のみ） |
| Living Wiki | 現在分かっていること | `knowledge/pages/` | `bin/kukuri-wiki` |
| TODO | これから行うこと | `tasks/` | `bin/kukuri-tasks` |

- Journalの各記録には、種類（`decision` 本人の決定／`request` 相手の依頼／`proposal` AIの提案／`result` 実作業の結果／`observation` 観察）・出典・時刻を付ける。AIの提案を本人の決定として書かない。
- Wikiは、Journalの記録から `plan` → 確認 → `apply --write` で更新する。後日の `decision`/`result` だけが旧記述を置換できる。それ以外の矛盾は、出典・日付つきで「未確認・矛盾」に両方残す。
- TODOの状態変更には根拠（原文の行・引用・ハッシュ、または本人の発言）が必要。未確認のTODOを完了扱いにしない。外部Issueが正本なら、その状態をローカルで上書きしない。

## 4. 作業の安全

- 原本は変更しない。記録の写しは、ハッシュを付けて別に保全する。
- 送信・投稿・支払・削除・公開は、本人の明示確認を受けるまで行わない。
- 複数のAIが同じファイルを同時に編集しない。担当を分け、レビューを経て統合する。
- 見つからないことを、存在しないことと言わない。未確認は未確認として残す。
