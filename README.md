# termdash

A tiny `fzf`-powered dashboard for browsing and resuming your recent
[Claude Code](https://claude.com/claude-code) sessions from the terminal —
across every project, not just the one you're currently in.

```
termdash            # last 20 sessions, most recent first
termdash finance    # last 20 sessions whose name contains "finance"
```

Navigate with the arrow keys, then:

- **Enter** — resume the selected session in this terminal
- **Ctrl-T** — open a new terminal tab and resume there (leaves your current
  window untouched)
- **Esc** — cancel

The session "name" shown is whatever you renamed the session to in Claude
Code (`/rename` or the title editor), or Claude's auto-generated title if
you never renamed it.

## How it works

- `bin/termdash-list.py` scans `~/.claude/projects/*/*.jsonl` (every Claude
  Code session transcript on your machine), pulls out each session's id,
  name, last-activity time, and working directory, sorts by recency, and
  prints the top N as a table.
- `shell/termdash.sh` defines the `termdash` shell function: it pipes that
  table into `fzf` for interactive selection, then runs
  `claude --resume <session_id>` in the right directory (or in a new tab,
  for Ctrl-T).

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
  - the filter logic (`query in info["name"].lower()`) if you want to match
    on something other than the session name — e.g. project path
- **`shell/termdash.sh`**
  - the `fzf` flags (colors, layout, height, keybindings)
  - the new-tab logic — currently supports iTerm2, Terminal.app, and tmux
    via `TERM_PROGRAM`/`$TMUX`; add another `elif` branch for your terminal
    of choice (e.g. WezTerm, Kitty, Alacritty)

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
