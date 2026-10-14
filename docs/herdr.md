# Herdr との併用

KUKURI Kit は、Herdr の機能を再実装しません。Herdr は、複数のAIエージェントを動かす端末ワークスペースです。ここでは、併用の考え方と、使うコマンドの確認方法を書きます。専用のツールは、v0.1にはありません（[機能一覧](features.md)）。

## 併用の考え方

- Herdr のペインの中で `bin/kukuri-claude` と `bin/kukuri-codex` を起動する。製品ごとの設定は `runtime/` に隔離される。
- 担当ファイルを分けて、同時編集を避ける。分担は、ワークスペース内のMarkdownに書く。
- 完了や依頼の連絡に、Herdr のペイン読み取りとプロンプト送信を使う。連絡できないときは、自動化せず、待ち状態を明示する。

## 使う前の確認

Herdr のクライアントとサーバーは、版が合っている必要があります。使う前に、次を確認してください。

```sh
command -v herdr          # 実行されるCLIの場所
herdr --version           # クライアントの版
herdr status server       # サーバーの版・プロトコル・互換性（compatible: yes か）
herdr agent --help        # その版で使えるサブコマンド
```

古いクライアントで新しいサーバーへ接続すると、サブコマンドが「不明」になったり、対象が見つからなかったりします。これは、機能が無いのではなく、版の不一致です。`herdr update`、または対応するクライアントの実行ファイルを使ってください。

## 連絡の例（Herdr 0.8 系で確認された構文）

```sh
herdr agent list                                 # 起動中のエージェントとペインID
herdr agent read <pane-id|agent-name> --lines 30 # 端末の出力を読む
herdr agent prompt <pane-id|agent-name> "確認してください: docs/handoff.md" # プロンプトを送る
herdr agent start <name> --kind <kind> --pane <pane-id>  # 既存のペインでエージェントを起動し、名前を付ける
```

- 宛先には、`herdr agent list` に出る **実在するペインID**、または **自分で付けたエージェント名**（`agent start` または `agent rename`）を使う。名前を付けていないエージェントを、名前で指定しない。
- `herdr agent send` は、0.8 系の構文ではありません（`agent prompt` を使う）。
- 具体的な構文は版で変わります。必ず `herdr agent --help` を確認してください。

## このキットが行わないこと

- Herdr の設定・セッション・キー割り当ての変更
- エージェント間のメッセージ配送の自動化（未実装）
