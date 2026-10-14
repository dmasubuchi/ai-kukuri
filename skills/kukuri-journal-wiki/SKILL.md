---
name: kukuri-journal-wiki
description: 日々の仕事をJournal（何が起きたか）に記録し、Living Wiki（現在分かっていること）とTODO（これから行うこと）を根拠付きで更新する。
---

3つを分ける。Journal=過去の記録と根拠、Living Wiki=現在の知識、TODO=担当・期限・状態・根拠つきの未来の仕事。同じ内容を3か所へ重複して正本にしない。

## 記録 → 更新の流れ

1. **記録**: `bin/kukuri-journal add --kind <種類> --text '<1行の事実>' --source '<出典>' --author <claude|codex|人名> [--wiki 'wiki:<slug>#<key> = <現在分かっていること>'] [--task <ID>]`
   種類は `decision`（本人の決定）／`request`（相手の依頼）／`proposal`（AIの提案）／`result`（実作業の結果）／`observation`（観察・未確認）。AIの提案を本人の決定として書かない。出典がない事実は書かない。追記のみ。過去の記録を書き換えない。
2. **計画**: `bin/kukuri-wiki plan [--date YYYY-MM-DD]`。何も書かない。各項目の `action` と `reason` を読む。
3. **反映**: 内容を確認してから `bin/kukuri-wiki apply --write`。既存の自由形式ページ（`manual_legacy_page`）は自動更新されない。人が内容を確認して移す。
3b. 旧版のページ（反映済みの記録の欄が無い）は、`migration_required` で止まる。`bin/kukuri-wiki migrate <slug> --through <最後に反映した日付> --write` で範囲を明示する（日付は人が決める）。
4. **検査**: `bin/kukuri-wiki check`。出典の欠落・未来日付・競合の件数を見る。

## 矛盾の扱い（自動で決めてよいのは日付と種類で優劣が明確なときだけ）

- 後日の `decision`/`result` → 旧記述を履歴へ出典・日付つきで移して置換（supersede）
- `proposal`/`observation`/`request`、または同日・古い日付 → 両方を「未確認・矛盾」に残す（conflict）。確定扱いにしない
- 未確認事項は、後日の `decision`/`result` で解消（resolve）。旧候補は履歴に残す
- 判断できないものは未確認のまま。両方の出典と日付を提示する

## TODOとの接続

- 完了・状態変更の根拠: `bin/kukuri-journal evidence <記録ID>` が返すJSONを、`bin/kukuri-tasks add/update` の `evidence` に使う。日次ファイルは追記されるため、その時点の写しを `knowledge/records/` に保全して根拠にする
- 状態変更は `bin/kukuri-tasks` を使う。Wikiの文面だけでTODOを完了にしない。Journalの `TODO:` 欄は参照であり、状態の正本ではない
- 未確認のTODOを完了扱いにしない。外部Issueの状態をローカルで上書きしない

## 注意

- 顧客名・金額・人物の記録は、本人の指示と出典の範囲だけ。秘密情報（認証・トークン・口座）は書かない
- 複数AIが同時に同じページを編集しない。`apply` の前に最新のページを読み直す
- 検索は `bin/kukuri-memory search`（整理済みページ・新ジャーナルが先に返る）。回答時は出典ID・日付を添える
