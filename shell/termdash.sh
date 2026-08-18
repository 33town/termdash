# termdash: browse recent Claude Code sessions with fzf
#
#   termdash            -> last N sessions across all your Claude Code projects
#   termdash finance    -> last N sessions whose (renamed) session name contains "finance"
#
# Keys inside the picker:
#   Enter   = resume the selected session in this terminal
#   Ctrl-T  = open a new terminal tab and resume there (current window untouched)
#   Esc     = cancel
#
# Requirements: fzf, python3, the `claude` CLI, and `bin/termdash-list.py`
# from this repo on your PATH (the install.sh does that for you).
#
# Customize:
#   TERMDASH_LIMIT=50 termdash        # show more/fewer rows (default 20)
#   TERMDASH_NAME_WIDTH=60 termdash   # widen the name column (default 42)

termdash() {
  local query="$1"
  local rows
  rows=$(termdash-list.py "$query")

  if [[ -z "$rows" ]]; then
    echo "termdash: no sessions found${query:+ matching \"$query\"}"
    return 1
  fi

  local result key selected session_id cwd
  result=$(printf '%s\n' "$rows" | fzf \
    --delimiter=$'\t' \
    --with-nth=1 \
    --height=~20 \
    --layout=reverse \
    --border \
    --expect=ctrl-t \
    --header="Enter=resume here  Ctrl-T=resume in new tab${query:+   [filter: $query]}" \
    --prompt='termdash > ')

  [[ -z "$result" ]] && return 1

  key=$(printf '%s\n' "$result" | sed -n '1p')
  selected=$(printf '%s\n' "$result" | sed -n '2p')
  [[ -z "$selected" ]] && return 1

  session_id=$(printf '%s' "$selected" | awk -F'\t' '{print $2}')
  cwd=$(printf '%s' "$selected" | awk -F'\t' '{print $3}')

  if [[ "$key" == "ctrl-t" ]]; then
    local esc_cwd esc_id script
    esc_cwd=${cwd//\\/\\\\}
    esc_cwd=${esc_cwd//\"/\\\"}
    esc_id=${session_id//\\/\\\\}

    if [[ "$TERM_PROGRAM" == "iTerm.app" ]]; then
      script="tell application \"iTerm2\"
        tell current window
          create tab with default profile
          tell current session of current tab
            write text \"cd \\\"$esc_cwd\\\" && claude --resume $esc_id\"
          end tell
        end tell
      end tell"
      osascript -e "$script"
    elif [[ "$TERM_PROGRAM" == "Apple_Terminal" ]]; then
      script="tell application \"Terminal\"
        activate
        tell application \"System Events\" to keystroke \"t\" using command down
        delay 0.3
        do script \"cd \\\"$esc_cwd\\\" && claude --resume $esc_id\" in front window
      end tell"
      osascript -e "$script"
    elif command -v tmux >/dev/null 2>&1 && [[ -n "$TMUX" ]]; then
      tmux new-window -c "$cwd" "claude --resume '$session_id'"
    else
      echo "termdash: don't know how to open a new tab in \"$TERM_PROGRAM\" — resuming here instead"
      cd "$cwd" && command claude --resume "$session_id"
    fi
  else
    cd "$cwd" && command claude --resume "$session_id"
  fi
}
