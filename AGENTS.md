# Shared Agent Guide

Canonical project instructions for all coding agents (Codex, Claude Code,
Gemini CLI). `CLAUDE.md` and `GEMINI.md` are import shims pointing here.

## What this is

An Alfred workflow (`proj` keyword) that lists the projects under
`PROJECTS_ROOT` (default `~/Code`) and opens the selection in VS Code. A
directory containing `.git` is a project (never descended into); other
directories are containers to recurse (hidden dirs and `node_modules`
skipped, depth-capped); plain depth-2 dirs (`<org>/<project>`) with no nested
repos also count as projects. There is intentionally **no window enumeration**: the
entire switch-or-launch mechanism is that `code <folder>` focuses the existing
window when the folder is already open and launches it otherwise. Read
`research.md` before revisiting that decision — it contains adversarially
verified findings (e.g. System Events/AppleScript sees zero VS Code windows
without force-enabling `AXManualAccessibility`; `code --status` enumerates all
windows with no permissions and powers the • running indicator). `specs/vision/`
and `specs/plans/` explain the design and its non-goals.

## Commands

```sh
./build.sh                 # lint info.plist + validate JSON + zip → dist/proj.alfredworkflow
open dist/proj.alfredworkflow          # install/update via Alfred's import dialog

# Exercise the Script Filter directly (should emit {"items":[...]}):
python3 src/scripts/list_projects.py | python3 -m json.tool

# Reproduce Alfred's execution environment (minimal PATH, clean env):
env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin src/scripts/list_projects.py

# Empty/missing-root fallback (must emit one invalid diagnostic item, exit 0):
PROJECTS_ROOT=/nonexistent python3 src/scripts/list_projects.py

# Verify open-vs-focus behavior without eyeballing windows:
code --status | grep -cE 'window \['   # window count before/after an open
```

The workflow is also installed unpacked on this machine at
`~/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows/user.workflow.2E6B6237-F76F-4EF7-B55B-E1742DECA933/`
(machine-specific UUID). After editing `src/`, that copy is stale until you
re-copy the changed files there and run:

```sh
osascript -e 'tell application id "com.runningwithcrayons.Alfred" to reload workflow "com.sellsbrothers.proj"'
```

## Architecture

- `src/info.plist` — hand-authored XML defining the whole workflow: one Script
  Filter (keyword `proj`, external script `scripts/list_projects.py`) connected
  to three Run Script actions (⏎ open-or-focus, ⌘⏎ `new-window`, ⌥⏎ reveal in
  Finder). The `connections` dict is keyed by the Script Filter's `uid`;
  modifier masks are 1048576 (⌘) and 524288 (⌥). `userconfigurationconfig`
  exposes `PROJECTS_ROOT`, which Alfred injects as an env var.
- `src/scripts/list_projects.py` — emits **all** projects in one shot. "Alfred
  filters results" is ON in the plist, so Alfred does the per-keystroke
  matching (against each item's `match` field), frecency ordering (via `uid`),
  and ⇥ completion (via `autocomplete`). The script must never filter by query
  itself; adding query handling would fight Alfred's own matcher. The `match`
  field tokenizes names on `-_.` separators ("auto-trading auto trading …") so
  mid-name words match at word boundaries regardless of Alfred's match mode.
- The • running indicator must never block the filter: `code --status` takes
  ~1.5s, so the running set lives in a cache (`$alfred_workflow_cache`,
  `$TMPDIR/com.sellsbrothers.proj` outside Alfred; 10s TTL). When stale, the
  filter spawns a detached `list_projects.py --refresh-running` child (guarded
  by a lockfile) and sets Alfred's `rerun` key until the refresh lands. The
  refresh always rewrites the cache — even empty on failure — because its
  fresh mtime is what stops the rerun loop. VS Code's is-running guard is
  `pgrep -fq "MacOS/Code"`: `pgrep -x Code` matches nothing, and `-f` patterns
  containing spaces (e.g. "Visual Studio Code.app") silently fail. Titles map
  to projects by the root name after the last " — " (em dash); a customized
  `window.title` just hides the indicator.
- `src/scripts/open_project.sh` — resolves the `code` CLI through a fallback
  chain (`command -v code` → `/usr/local/bin/code` → app-bundle bin) because
  Alfred runs scripts with a minimal PATH where `command -v code` alone fails.
  Don't "simplify" this away.
- `build.sh` — a `.alfredworkflow` is just a zip of `src/` with `info.plist`
  at the zip root. `dist/` is a gitignored artifact.

## Dogfooding

How to build this repo's artifact and put it where the user actually uses it:
`./build.sh` produces `dist/proj.alfredworkflow`, but the copy the user runs is
the unpacked install in Alfred's preferences (path under Commands above). After
a nontrivial change, copy the changed `src/` files into that install dir and
run the `reload workflow` osascript so the user's next `proj` invocation
exercises the new code — never leave them running a stale artifact.

## Gotchas

- `alfredfiltersresultsmatchmode` must stay **2**. Determined empirically
  (2026-08-18, screenshot-verified): mode 1 behaves as prefix-of-the-entire-
  match-string — "gas" matched but "trading" never could — while mode 2
  matches at word boundaries of the match field ("trad" finds the "trading"
  token; mid-word fragments like "rading" don't match). The value isn't in
  Alfred's docs; don't guess it, test it via screenshot if it ever changes.
- Scripts under `src/scripts/` must stay executable (`chmod +x`) — the Script
  Filter invokes `list_projects.py` as an external script via its shebang.
- `plutil -lint src/info.plist` after any plist edit (build.sh does this).
- `src/icon.png` is VS Code's own app icon: acceptable for personal use, must
  be replaced with an original before any Alfred Gallery submission.
- The GitHub repo is `csells/alfred-vsc-proj-switcher`; the local folder is
  named `alfred-vsc-switcher`. The workflow bundle id is
  `com.sellsbrothers.proj`.
