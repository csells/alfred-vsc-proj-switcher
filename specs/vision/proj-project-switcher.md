# Vision: `proj` — Alfred project switcher for VS Code

## One sentence

Type `proj gas-⇥⏎` in Alfred and be in the right VS Code window — focused if that
project is already open, launched if it isn't — for any project under `~/Code`.

## The problem

Switching among many concurrent VS Code projects today means mousing through VS
Code's Window menu (a long, unsorted list of ~30 windows named by whatever file was
last active) or cycling with ⌘\`. And that only reaches projects that are *already
running*; opening a cold project is a separate trip through Finder or a terminal.
Alfred is already the muscle-memory launcher for everything else (⌃⌥⇧⌘Space), so
project switching should live there too.

## The insight that shapes the design

The obvious framing — "list the running VS Code windows like the Window menu does" —
is the hard road: no existing Alfred workflow does it, there is no extension/CLI API
for cross-window enumeration, and reading window titles requires a native
CGWindowList binary plus Screen Recording permission, with title→folder mapping at
the mercy of the `window.title` setting (see `research.md`).

The better framing: **the filesystem already knows every project, and the `code` CLI
already implements switch-or-launch.** `code <folder>` focuses the existing window
when that folder is open (VS Code refuses to open a folder twice — by design,
confirmed in microsoft/vscode#35207) and opens it when it isn't. So a workflow that
lists *leaf folders* instead of *windows* is simpler, needs zero permissions and
zero AppleScript, and is strictly more capable: it reaches projects whether or not
they're running.

## User experience

- **Invoke**: `proj` in Alfred, then a few characters of the project name.
- **See**: every leaf project folder (depth-2 directory) under the projects root —
  `~/Code/<org>/<project>`, 102 of them today — title = project name, subtitle =
  `org/project` so same-named projects in different orgs are distinguishable.
- **Narrow**: Alfred's own fuzzy matching filters as you type; ⇥ autocompletes the
  selected project's name (`proj gas-⇥` → `proj gas-city-inc`). Matching also hits
  the org name, so `proj gascity` narrows to that org's projects.
- **⏎**: open-or-focus that project in VS Code. That's the whole loop: hotkey,
  a few characters, ⏎, and you're in the window.
- **Learns**: Alfred's frecency (via item `uid`) floats your most-used projects to
  the top, so frequent projects become `proj` + ⏎.
- **Modifiers**: ⌘⏎ forces a new window (`code -n`) for the deliberate
  second-window case; ⌥⏎ reveals the folder in Finder.
- **Sees what's running**: projects with an open VS Code window carry a •
  indicator (from `code --status`, cached so the list stays instant).

## Principles

1. **Folders are the backbone, windows are decoration.** Running-window awareness
   (e.g. a "• running" annotation) is an optional later layer, never a dependency.
2. **No permissions, no daemons, no native binaries.** A Script Filter and the
   `code` CLI. If a feature demands Screen Recording or accessibility permissions,
   it belongs in a future enhancement, not the core.
3. **Instant.** One directory scan of ~100 folders per invocation; Alfred filters
   keystrokes itself. The project list is never cached; only the cosmetic
   running indicator uses a short-lived cache, refreshed off the critical path.
4. **Configurable, not hardcoded.** Projects root (default `~/Code`) is an Alfred
   workflow user-configuration field; the `code` CLI path is resolved dynamically
   (the hardcoded `/usr/local/bin/code` in prior-art workflows breaks on default
   Apple Silicon installs).

## Non-goals (v1)

- Enumerating or focusing untitled windows, multi-root workspaces, or windows on
  folders outside the projects root.
- `.code-workspace` file support, recents from `state.vscdb`, Insiders/VSCodium
  variants — all possible later, all out of the first cut.
- Windows/Linux, other launchers (Raycast), other editors.

## Later, maybe

- **Recents augmentation**: merge in `state.vscdb`'s `history.recentlyOpenedPathsList`
  for workspaces living outside the projects root.
- **Alfred Gallery publication**: no Gallery workflow does live-aware project
  switching today; a polished version is a genuinely novel contribution
  (host on GitHub → submit via the Alfred Forum's Gallery process).

## Success criteria

- From anywhere: hotkey → `proj` → ≤4 keystrokes → ⏎ lands in the intended
  project's window in under a second, whether or not it was running.
- A newly created folder under `~/Code/<org>/` appears in the next `proj`
  invocation with no refresh step.
- The workflow installs by double-clicking a `.alfredworkflow` file and works with
  no setup beyond (optionally) pointing it at a different projects root.
