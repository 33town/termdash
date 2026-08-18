#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

rm -f "$BIN_DIR/termdash-list.py"
echo "Removed $BIN_DIR/termdash-list.py"

for RC_FILE in "$HOME/.zshrc" "$HOME/.bashrc"; do
  [ -f "$RC_FILE" ] || continue
  if grep -qF "$REPO_DIR/shell/termdash.sh" "$RC_FILE" 2>/dev/null; then
    tmp=$(mktemp)
    grep -vF "$REPO_DIR/shell/termdash.sh" "$RC_FILE" | grep -vF "# --- termdash" > "$tmp"
    mv "$tmp" "$RC_FILE"
    echo "Removed termdash source line from $RC_FILE"
  fi
done

echo "Done. Open a new terminal tab for it to take effect."
