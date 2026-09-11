# termdash

A tiny `fzf`-powered dashboard for browsing and resuming your recent
[Claude Code](https://claude.com/claude-code) sessions from the terminal —
across every project, not just the one you're currently in.

```
termdash                  # last 20 sessions, most recent first
termdash finance          # last 20 sessions whose name contains "finance"
termdash amazon-brain-2c  # find a running session by its peer name
termdash 425fa77b         # find a session by its ID (full or prefix)
```

Navigate with the arrow keys, then:

- **Enter** — resume the selected session in this terminal
- **Ctrl-T** — open a new terminal tab and resume there (leaves your current
  window untouched)
- **Esc** — cancel

Rows marked **●** are sessions that are running right now. Picking one (Enter
or Ctrl-T) jumps to the terminal tab it lives in instead of resuming a second
copy of the same session. Jumping works in iTerm2 and Terminal.app; elsewhere
termdash tells you which tty it's on.

The session "name" shown is whatever you renamed the session to in Claude
Code (`/rename` or the title editor), or Claude's auto-generated title if
you never renamed it.

### Finding a session another session told you about

Claude Code gives every running session a **peer name** (e.g.
`amazon-brain-2c`) — that's what shows up in `ListAgents` and in
cross-session messages. It's unrelated to the session's title and to its
session ID, so a renamed session is hard to recognize from it. The keyword
you pass to `termdash` matches all of these:

| What you have                        | Example                  |
| ------------------------------------ | ------------------------ |
| session name / title                 | `finance`                |
| peer name (running sessions only)    | `amazon-brain-2c`        |
| session ID, full or prefix           | `425fa77b`               |
| claude.ai session ID (running only)  | `session_0116iHro...`    |

Each row also shows the short session ID and the peer name, so you can type
either one into the fzf prompt as well.

## How it works

- `bin/termdash-list.py` scans `~/.claude/projects/*/*.jsonl` (every Claude
  Code session transcript on your machine), pulls out each session's id,
  name, last-activity time, and working directory, sorts by recency, and
  prints the top N as a table. It also reads `~/.claude/sessions/*.json`
  (one file per running Claude Code process) to learn which sessions are
  running, their peer name, and which tty they're on — keeping only pids
  that are still a live `claude` process.
- `shell/termdash.sh` defines the `termdash` shell function: it pipes that
  table into `fzf` for interactive selection, then runs
  `claude --resume <session_id>` in the right directory (or in a new tab,
  for Ctrl-T) — or, for a running session, selects the tab whose tty
  matches.

## Requirements

- [`fzf`](https://github.com/junegunn/fzf) — `brew install fzf`
- `python3` (ships with macOS)
- the `claude` CLI (Claude Code)
- zsh or bash

## Install

```
./install.sh
```

This copies `bin/termdash-list.py` to `~/.local/bin` and appends a line to
your `~/.zshrc` (or `~/.bashrc`) that sources `shell/termdash.sh` from
wherever you cloned this repo. Then:

```
source ~/.zshrc   # or open a new terminal tab
termdash
```

## Customize

Everything lives in two small, readable files — feel free to edit directly:

- **`bin/termdash-list.py`**
  - `TERMDASH_LIMIT` env var (default `20`) — how many sessions to list
  - `TERMDASH_NAME_WIDTH` env var (default `42`) — width of the name column
  - the filter logic (the `haystack` list in `main()`) if you want to match
    on something else — e.g. project path
- **`shell/termdash.sh`**
  - the `fzf` flags (colors, layout, height, keybindings)
  - the new-tab logic — currently supports iTerm2, Terminal.app, and tmux
    via `TERM_PROGRAM`/`$TMUX`; add another `elif` branch for your terminal
    of choice (e.g. WezTerm, Kitty, Alacritty)
  - the jump-to-running-tab logic — iTerm2 and Terminal.app

Example:

```
TERMDASH_LIMIT=50 termdash
```

## Uninstall

```
./uninstall.sh
```

Removes `~/.local/bin/termdash-list.py` and the source line from your rc
file.
