#!/bin/bash
# Open-or-focus a project folder in VS Code.
#   $1 = absolute project path
#   $2 = optional mode: "new-window"
#
# `code <folder>` focuses the existing window when the folder is already open
# (VS Code refuses to open the same folder twice) and opens it otherwise.
# Alfred runs scripts with a minimal PATH, so PATH lookup alone is not enough:
# the CODE_CLI workflow configuration wins when set, then PATH, then the
# common symlink and app-bundle locations for stable, Insiders, and VSCodium.

set -euo pipefail

path="${1:?usage: open_project.sh <folder> [new-window]}"
mode="${2:-}"

resolve_cli() {
  if [[ -n "${CODE_CLI:-}" ]]; then
    local expanded="${CODE_CLI/#\~/$HOME}"
    [[ -x "$expanded" ]] && { echo "$expanded"; return 0; }
  fi
  local c
  for c in code code-insiders codium; do
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
  done
  local p
  for p in \
    /usr/local/bin/code /opt/homebrew/bin/code \
    /usr/local/bin/code-insiders /opt/homebrew/bin/code-insiders \
    /usr/local/bin/codium /opt/homebrew/bin/codium \
    "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
    "$HOME/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
    "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders" \
    "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code" \
    "/Applications/VSCodium.app/Contents/Resources/app/bin/codium" \
  ; do
    [[ -x "$p" ]] && { echo "$p"; return 0; }
  done
  return 1
}

if ! code_cli="$(resolve_cli)"; then
  osascript -e 'display notification "Could not find the code CLI. Set it in the workflow configuration, or run VS Code’s “Shell Command: Install code command in PATH”." with title "VS Code Project Switcher"'
  exit 1
fi

if [[ "$mode" == "new-window" ]]; then
  exec "$code_cli" -n "$path"
else
  exec "$code_cli" "$path"
fi
