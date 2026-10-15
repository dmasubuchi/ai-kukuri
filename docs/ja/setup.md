[English](../setup.md) | 日本語

# セットアップ

## 前提

- macOS または Linux
- Python 3（標準ライブラリのみ使用）と POSIX シェル
- Git
- 任意: Claude Code、Codex、Herdr（このキットが提供するのは、保存先の規約と起動の隔離だけ）

## 導入の方法（どれでも同じワークスペースができます）

```sh
# A. npm、または GitHub から直接実行
npx ai-kukuri init ~/kukuri-workspace
npx github:dmasubuchi/ai-kukuri init ~/kukuri-workspace

# B. 取得したリポジトリから
git clone <このリポジトリ> ai-kukuri && cd ai-kukuri
./install.sh ~/kukuri-workspace

# C. 1行（アーカイブのURLを指定。KUKURI_KIT_SHA256 を付けると、一致しないとき中止します）
curl -fsSL <install.shのURL> | KUKURI_KIT_TARBALL=<アーカイブのURL> sh -s -- ~/kukuri-workspace
```

- 空でない場所には作成しません。足りないファイルだけを足すには、`npx ai-kukuri repair <dir>`（または `scripts/init-workspace.sh --repair <dir>`）。既存のファイルは上書きしません。
- 環境の確認: `npx ai-kukuri doctor`（python3 3.9以上、sh、git）。動作の確認: `npx ai-kukuri demo`（架空データ）。
- コマンドは `bin/` に **コピー** されます（各コマンドは、自分の場所からワークスペースを決めます。シンボリックリンクにしないでください）。

## 動作を確かめる（任意）

```sh
sh examples/demo.sh
(cd tests && python3 -B -m unittest discover -p 'test_*.py')   # サブシェル。作業ディレクトリは変わらない
```

## 共通Skillsの登録先

`init-workspace.sh` は、`skills/<名前>/` を、製品が探す場所へ相対シンボリックリンクで登録します。

| 製品 | 登録先 | 状態 |
|---|---|---|
| Claude Code（`kukuri-claude` 経由。`CLAUDE_CONFIG_DIR=runtime/claude`） | `runtime/claude/skills/<名前>` | 私的な運用では動作を確認済み。このキットの自動試験は、リンクの存在までを検査 |
| Codex | `.agents/skills/<名前>` | 公式資料に基づく配置。実機での読み込みは、このキットでは未検証 |

入口文書（`AGENTS.md` `CLAUDE.md`）にも、Skills の場所を書いています。

## 知識・TODOを版管理するとき

生成される `.gitignore` は、`knowledge/` と `tasks/` を除外します（業務記録・顧客情報を、誤って規約のリポジトリに入れないため）。版管理したいときは、別のPrivateリポジトリを使ってください。

## 4. 案件を登録する

`registry/projects.json` に案件を追加します。`directory` は `projects/` からの相対パスです。実パスは `runtime/machine.json` で決まります。

## 5. AI製品を起動する（任意）

```sh
cd ~/kukuri-workspace
# 製品の本体のパスを runtime/launchers.json に書く（省略するとPATHから探す）
echo '{"claude": "/absolute/path/to/claude", "codex": "/absolute/path/to/codex"}' > runtime/launchers.json
bin/kukuri-claude --check     # 起動せず、設定の分離を確認
bin/kukuri-codex  --check
```

`bin/` を `PATH` に追加する必要はありません。製品ごとの設定・認証・履歴は `runtime/claude/` `runtime/codex/` に分離されます。

## 6. 記録を取り込む（任意）

`registry/knowledge-sources.json` に取り込み元のディレクトリを書き、`bin/kukuri-memory import` を実行します。

```json
{"sources": [{"id": "notes", "root": "/absolute/path/to/notes"}]}
```

取り込み元が存在しないときは、現在の索引を置き換えずに停止します。原本は変更しません。

## アンインストール

ワークスペースのディレクトリを削除するだけです。キット自体はシステムに何も書きません。
