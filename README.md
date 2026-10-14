<p align="center">
  <img src="docs/images/kukuri-hime.jpg" alt="菊理媛神のイメージ（白い菊・鏡・虹・霊峰）" width="420">
</p>

# KUKURI Kit

**Knowledge Unification Kit for Updates, Recall & Integration**

複数のAI（Claude Code、Codex など）が、日々の仕事を記録し、過去の経緯を保持しながら、現在の知識とTODOを更新するための、小さなローカルツールキットです。外部サービスにも、常駐プロセスにも依存しません（Python 3 の標準ライブラリのみ）。

> 状態: **v0.1 候補（Private・未公開）**。実装済みの機能と将来構想は、[docs/features.md](docs/features.md) で分けています。

## 名前の由来 — KUKURI（菊理媛神）

KUKURIという名前は、日本神話に登場する女神、**菊理媛神（ククリヒメノカミ）** に由来します。

『日本書紀』の一書には、黄泉の国の境で対立するイザナギとイザナミの前に、菊理媛神が現れる場面があります。

菊理媛神が何を語ったのか、神話には記されていません。ただ、その言葉を聞いたイザナギはそれを良しとし、二神はその場を離れたと伝えられています。

その名の「くくり」は、日本語の **「括る（くくる）」** に通じるとも解釈され、菊理媛神は後世、異なるものを取り持ち、縁を結ぶ神として信仰されてきました。

現代のAIも、それぞれ異なる能力、記憶、道具、作業環境を持っています。

KUKURIは、それらを一つに置き換えるのではなく、**違いを生かしたまま、知識と仕事をつなぐ** ために生まれました。

Claude Code、Codex、その他のAIを取り持ち、過去の記録（Journal）、現在の知識（Living Wiki）、これからの仕事（TODO）を結びます。

KUKURIは、すべてのAIを支配する存在ではなく、異なるAIの間に立って、それぞれの能力を生かす仕組みです。

日本神話に着想を得た、AIと知識と仕事を「括る」ためのオープンソースプロジェクトです。

*神話の描写は『日本書紀』の一書に基づきます。「括る」との関係は語源の定説ではなく、伝統的な解釈として書いています。白山比咩神社の公式説明でも、この結び付けが紹介されています。*
<!-- TODO(公開前): 白山比咩神社の公式説明の出典URLを確認して、脚注にする -->

> 挿絵は、プロジェクトオーナーが用意したイラスト（菊理媛神のイメージ）です。コードのライセンス（MIT）の対象に含めません。出所と利用条件は、公開前にオーナーが確認します（[NOTICE](NOTICE.md)）。

## 3つを分ける

| 種類 | 問い | 場所 | 道具 |
|---|---|---|---|
| **Journal** | 何が起きたか | `knowledge/journal/YYYY-MM-DD.md` | `kukuri-journal`（追記のみ） |
| **Living Wiki** | 現在分かっていること | `knowledge/pages/` | `kukuri-wiki` |
| **TODO** | これから行うこと | `tasks/` | `kukuri-tasks` |

- Journalの各記録は、種類（本人の決定・相手の依頼・AIの提案・実作業の結果・観察）、出典、時刻を持つ。AIの提案は、決定として扱われない。
- Wikiは、Journalから `plan` → 確認 → `apply --write` で更新する。後日の決定・結果だけが旧記述を置換できる。判断できない矛盾は、出典・日付つきで「未確認・矛盾」に両方残す。
- TODOの状態変更には、根拠（原文の行・引用・ハッシュ）が必要。Journalの記録を根拠にできる（`kukuri-journal evidence`）。

## クイックスタート

必要なもの: Python 3.9 以上（Python 3.12 で検証。CIでの対象は .github/workflows/test.yml）、POSIX シェル（macOS / Linux）。

```sh
git clone <this-repo> kukuri-kit && cd kukuri-kit
sh examples/demo.sh            # 架空データで Journal → Wiki → TODO を一巡する
scripts/init-workspace.sh ~/kukuri-workspace   # 自分のワークスペースを作る
cd ~/kukuri-workspace
bin/kukuri-journal add --kind decision --author me --source "定例メモ" \
  --text "ホスティング先はクラウドAに決めた" \
  --wiki "wiki:my-portal#hosting = ホスティング先はクラウドA"
bin/kukuri-wiki plan          # 何も書かない
bin/kukuri-wiki apply --write
bin/kukuri-wiki check
```

テスト: `cd tests && python3 -B -m unittest discover -p 'test_*.py'`

## 構成

```
bin/        kukuri-journal  kukuri-wiki  kukuri-tasks  kukuri-memory  kukuri-paths
            kukuri-launch.py  kukuri-claude  kukuri-codex
rules/      common.md             製品に依存しない共通規約
skills/     kukuri-journal-wiki  kukuri-recall  kukuri-project
templates/  AGENTS.md  CLAUDE.md  registry-projects.json  workspace.gitignore
scripts/    init-workspace.sh
examples/   demo.sh
docs/       architecture.md  features.md  setup.md  herdr.md  security-and-license.md  roadmap.md
tests/
```

詳細: [アーキテクチャ](docs/architecture.md)／[機能一覧（実装済み・将来構想）](docs/features.md)／[セットアップ](docs/setup.md)／[Herdrとの使い方](docs/herdr.md)／[セキュリティ・ライセンス確認](docs/security-and-license.md)／[ロードマップ](docs/roadmap.md)

## 設計上の約束

- 原本は変更しない。保存する写しはハッシュ付き。
- 見つからないことを、存在しないことと言わない。未確認は未確認として残す。
- 送信・投稿・支払・削除・公開は、人の明示確認の後に行う。このキットは、それらを行う機能を持たない。
- 公式のClaude Code・Codex・Herdrの機能を再実装しない。起動と保存先の規約だけを提供する。

## ライセンス

MIT License（候補）。詳細は [LICENSE](LICENSE) と [docs/security-and-license.md](docs/security-and-license.md)。
