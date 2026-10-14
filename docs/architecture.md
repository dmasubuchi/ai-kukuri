# アーキテクチャ

## 全体像

```
ワークスペース/（Gitで追跡するのは rules・registry・skills・bin だけ）
├── AGENTS.md  CLAUDE.md         各AI製品の入口。rules/common.md などを読ませる
├── rules/common.md              製品に依存しない共通規約の正本
├── registry/projects.json       案件の台帳（名前・別名・ディレクトリ）
├── skills/                      共通の手順（Markdown）
├── bin/                         このキットのコマンド（Python標準ライブラリのみ）
├── knowledge/
│   ├── journal/YYYY-MM-DD.md    Journal: 何が起きたか（追記のみ）
│   ├── pages/                   Living Wiki: 現在分かっていること
│   ├── records/<sha256>.txt     原文の写し（ハッシュで保全）
│   └── imports/                 取り込みの版ごとの目録
├── tasks/
│   ├── baseline.json            TODOの固定した基準
│   └── events.jsonl             追記型の変更履歴
├── projects/  input/  output/   案件Repo・入力・成果物（ワークスペースのGit対象外）
└── runtime/                     マシン・製品固有の設定、認証、履歴（Git対象外）

（生成される .gitignore は knowledge/ tasks/ runtime/ も除外する。Gitで追跡するのは、規約・台帳・Skills・コマンドだけ）
```

## データの流れ

```
 出来事 ──kukuri-journal add──▶ Journal（追記のみ・出典つき）
                                   │  更新: wiki:<slug>#<key> = <現在分かっていること>
                                   ▼
                     kukuri-wiki plan（何も書かない）
                                   │  人またはAIが内容を確認
                                   ▼
                     kukuri-wiki apply --write ──▶ Living Wiki（pages/）
                                   │ 履歴・競合・未確認を出典と日付つきで保持
 Journalの記録 ──kukuri-journal evidence──▶ kukuri-tasks add/update（根拠つき）
```

## Wikiの更新規則（`kukuri-wiki`）

| 状況 | 動作 |
|---|---|
| 新しい事実が `decision`/`result` | 「現在わかっていること」に追加 |
| 新しい事実が `proposal`/`observation`/`request` | 「未確認・矛盾」に追加（確定しない） |
| 同じ内容を、より新しい記録が再確認 | 日付と出典を更新 |
| 後日の `decision`/`result` が異なる内容 | 旧記述を履歴へ（出典・日付つき）、新記述に置換 |
| 同じ日でも、同じ種類のより遅い時刻の記録 | 更新として扱う（旧記述は履歴へ） |
| 確定済み・未確認事項より古い日時の記録（後から追記された場合） | 置換・解消せず、「古い記録」として履歴に出典つきで記録 |
| 複数の記録を一度に反映 | 追記順ではなく、記録の日時順に判断する（結果が追記順に依存しない） |
| 提案・観察、または同日・古い日付が異なる内容 | 両方を「競合」として保持。確定しない |
| 未確認事項に、後日の決定・結果 | 解消。旧候補は履歴に残す |
| 既存の自由形式ページ（マーカー無し） | 自動更新しない（`manual_legacy_page`） |
| 「反映済みの記録」欄の無い旧版のWikiページ | 更新せずに停止する（`migration_required`）。`kukuri-wiki migrate <slug> --through <日付>` で、反映済みの範囲を人が明示してから、台帳を付ける |
| すでに反映した記録 | 何もしない。ページの「反映済みの記録」欄に、`記録ID#キー` を保持し、再実行しても結果を変えない |
| 確定した内容を、提案・観察が言い直す | 確定の出典・日付を置き換えない |
| 同時にapplyを実行 | 読み取り・判断・書き込みを同じロックの中で行い、更新を失わない |

## 記録の層（`kukuri-memory`）

原文（`records/`、ハッシュで保全）／整理したページ（`pages/`）／検索の索引（SQLite・再生成可能）。検索は、整理したページと新しいジャーナルを先に返し、そのあと保存した原文を返す。取り込み元が欠けたときは、現在の索引を置き換えずに停止する。

## 設計の判断

- 常駐プロセス・外部サービス・データベースサーバーを持たない。状態はファイルと追記型の履歴。
- 製品固有の設定は `runtime/<product>/` に隔離する（`kukuri-launch.py`）。共通規約には混ぜない。
- 変更の根拠（原文の行・引用・ハッシュ）が検証できないとき、更新を拒否する。
