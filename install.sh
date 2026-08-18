#!/usr/bin/env bash
# Installs termdash: copies bin/termdash-list.py onto your PATH and wires
# shell/termdash.sh into your shell rc file.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

echo "== termdash installer =="

# --- dependency checks ---
missing=()
command -v fzf >/dev/null 2>&1 || missing+=("fzf")
command -v python3 >/dev/null 2>&1 || missing+=("python3")
command -v claude >/dev/null 2>&1 || missing+=("claude (Claude Code CLI)")

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing dependencies: ${missing[*]}"
  echo "On macOS: brew install fzf   (python3 and claude should already be present if you use Claude Code)"
  exit 1
fi

# --- install the data script ---
mkdir -p "$BIN_DIR"
cp "$REPO_DIR/bin/termdash-list.py" "$BIN_DIR/termdash-list.py"
chmod +x "$BIN_DIR/termdash-list.py"
echo "Installed $BIN_DIR/termdash-list.py"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "NOTE: $BIN_DIR is not on your PATH. Add this to your shell rc file:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    ;;
esac

# --- wire the shell function into your rc file ---
SOURCE_LINE="source \"$REPO_DIR/shell/termdash.sh\""

RC_FILE="$HOME/.zshrc"
case "$SHELL" in
  */bash) RC_FILE="$HOME/.bashrc" ;;
esac

if [ -f "$RC_FILE" ] && grep -qF "$SOURCE_LINE" "$RC_FILE" 2>/dev/null; then
  echo "$RC_FILE already sources termdash.sh, skipping"
else
  {
    echo ""
    echo "# --- termdash (customize in $REPO_DIR/shell/termdash.sh) ---"
    echo "$SOURCE_LINE"
  } >> "$RC_FILE"
  echo "Added source line to $RC_FILE"
fi

echo ""
echo "Done. Run:  source $RC_FILE   (or open a new terminal tab)"
echo "Then try:   termdash"
echo "        or: termdash <keyword>"
