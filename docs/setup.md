# セットアップ

## 前提

- macOS または Linux
- Python 3（標準ライブラリのみ使用）と POSIX シェル
- Git
- 任意: Claude Code、Codex、Herdr（このキットが提供するのは、保存先の規約と起動の隔離だけ）

## 1. キットを取得する

```sh
git clone <このリポジトリ> kukuri-kit
cd kukuri-kit
```

## 2. 動作を確かめる（任意）

```sh
sh examples/demo.sh
cd tests && python3 -B -m unittest discover -p 'test_*.py'
```

## 3. ワークスペースを作る

```sh
scripts/init-workspace.sh ~/kukuri-workspace
```

空でないディレクトリには作成しません。コマンドは `~/kukuri-workspace/bin/` に **コピー** されます（各コマンドは、自分の場所からワークスペースを決めます。シンボリックリンクにしないでください）。

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
