English | [日本語](ja/herdr.md)

# Using with Herdr

KUKURI Kit does not reimplement Herdr's features. Herdr is a terminal workspace that runs multiple AI agents. This page describes the approach to using them together and how to verify the commands involved. There is no dedicated tool in v0.1 ([features](features.md)).

## Approach

- Launch `bin/kukuri-claude` and `bin/kukuri-codex` inside Herdr panes. Per-product settings are isolated under `runtime/`.
- Divide the files each agent is responsible for, to avoid concurrent edits. Write the division of work in Markdown inside the workspace.
- Use Herdr's pane reading and prompt sending for completion notices and requests. When contact is not possible, do not automate; state the waiting status explicitly.

## Verify before use

The Herdr client and server must be on matching versions. Before use, check the following.

```sh
command -v herdr          # location of the CLI that will run
herdr --version           # client version
herdr status server       # server version, protocol, compatibility (compatible: yes?)
herdr agent --help        # subcommands available in that version
```

Connecting to a newer server with an old client can make subcommands "unknown" or targets not found. This is a version mismatch, not a missing feature. Run `herdr update`, or use a matching client executable.

## Example of contacting an agent (syntax confirmed on Herdr 0.8 series)

```sh
herdr agent list                                 # running agents and pane IDs
herdr agent read <pane-id|agent-name> --lines 30 # read terminal output
herdr agent prompt <pane-id|agent-name> "確認してください: docs/handoff.md" # send a prompt
herdr agent start <name> --kind <kind> --pane <pane-id>  # start an agent in an existing pane and name it
```

- For the target, use a **real pane ID** shown by `herdr agent list`, or an **agent name you assigned yourself** (`agent start` or `agent rename`). Do not address an agent by name if you have not named it.
- `herdr agent send` is not syntax of the 0.8 series (use `agent prompt`).
- The exact syntax changes between versions. Always check `herdr agent --help`.

## What this kit does not do

- Change Herdr's settings, sessions or key bindings
- Automate message delivery between agents (not implemented)
