#!/bin/bash
# Open-or-focus a project folder in VS Code.
#   $1 = absolute project path
#   $2 = optional mode: "new-window"
#
# `code <folder>` focuses the existing window when the folder is already open
# (VS Code refuses to open the same folder twice) and opens it otherwise.
# Alfred runs scripts with a minimal PATH, so `command -v code` alone is not
# enough — fall back to the common symlink and the app-bundle CLI.

set -euo pipefail

path="${1:?usage: open_project.sh <folder> [new-window]}"
mode="${2:-}"

code_cli="$(command -v code || true)"
[[ -n "$code_cli" && -x "$code_cli" ]] || code_cli="/usr/local/bin/code"
[[ -x "$code_cli" ]] || code_cli="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"

if [[ ! -x "$code_cli" ]]; then
  osascript -e 'display notification "Could not find the code CLI. In VS Code, run: Shell Command: Install code command in PATH" with title "VS Code Project Switcher"'
  exit 1
fi

if [[ "$mode" == "new-window" ]]; then
  exec "$code_cli" -n "$path"
else
  exec "$code_cli" "$path"
fi
