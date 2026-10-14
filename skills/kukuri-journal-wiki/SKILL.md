---
name: kukuri-journal-wiki
description: Record daily work in the Journal (what happened), and update the Living Wiki (what is currently known) and TODO (what will be done) with evidence.
---

Keep the three separate. Journal = past records and their evidence; Living Wiki = current knowledge; TODO = future work with owner, deadline, state, and evidence. Do not make the same content canonical in three places.

## Flow: record -> update

1. **Record**: `bin/kukuri-journal add --kind <kind> --text '<one-line fact>' --source '<source>' --author <claude|codex|person name> [--wiki 'wiki:<slug>#<key> = <what is currently known>'] [--task <ID>]`
   Kinds are `decision` (owner decision) / `request` (request from a counterpart) / `proposal` (AI proposal) / `result` (work result) / `observation` (observation, unconfirmed). Never record an AI proposal as the owner's decision. Do not write facts that have no source. Append-only; do not rewrite past records.
2. **Plan**: `bin/kukuri-wiki plan [--date YYYY-MM-DD]`. It writes nothing. Read the `action` and `reason` of each item.
3. **Apply**: after reviewing the content, run `bin/kukuri-wiki apply --write`. Existing free-form pages (`manual_legacy_page`) are not updated automatically; a person reviews the content and moves it over.
3b. Pages from an older version (without a section for applied records) stop at `migration_required`. Review the content and rebuild from the Journal with `bin/kukuri-wiki migrate <slug> --write`. Pages edited by hand (claims whose source is not in the Journal) stop at `manual_review`.
4. **Check**: `bin/kukuri-wiki check`. Look at the counts of missing sources, future dates, and conflicts.

## Handling contradictions (decide automatically only when date/time and kind give a clear winner)

The Wiki is rebuilt from all Journal records in date/time order. The result does not change with the order of appends or the number of `apply` runs.

- A later `decision`/`result` -> move the old statement to history with source and date, and replace it (supersede)
- `proposal`/`observation`/`request`, or the same day or an older date -> keep both under "unconfirmed / contradictions" (`未確認・矛盾`) (conflict). Do not treat either as settled
- Unconfirmed items are resolved by a later `decision`/`result` (resolve). The old candidate stays in history
- Anything that cannot be judged stays unconfirmed. Present both sources and dates

## Connection to TODO

- Evidence for completion or state changes: use the JSON returned by `bin/kukuri-journal evidence <record ID>` as the `evidence` of `bin/kukuri-tasks add/update`. Because daily files are appended to, preserve a copy of the file as of that moment in `knowledge/records/` and use it as the evidence
- Change state with `bin/kukuri-tasks`. Do not mark a TODO done on the strength of Wiki wording alone. The `TODO:` field in the Journal is a reference, not the canonical source of state
- Do not treat an unconfirmed TODO as done. Do not overwrite the state of an external Issue locally

## Notes

- Record customer names, amounts, and people only within the scope of the owner's instructions and the source. Do not write secrets (credentials, tokens, bank accounts)
- Multiple AIs must not edit the same page at the same time. Re-read the latest page before `apply`
- Search with `bin/kukuri-memory search` (organized pages and new journals are returned first). When answering, attach the source ID and date
