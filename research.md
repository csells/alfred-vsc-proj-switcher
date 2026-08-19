# Alfred ↔ VS Code window/project switcher — deep research

Research date: 2026-08-18. Method: 5-angle web sweep → 20 sources fetched → 97 claims
extracted → top 25 adversarially verified (3 independent votes each) → 19 confirmed,
6 refuted. All confirmed findings below passed 3-0 with primary-source (mostly
code-level) verification.

## Verdict

**No existing Alfred workflow reproduces VS Code's Window-menu list of running
windows.** Every surveyed VS Code workflow lists *persisted* recent/saved workspace
data, not live windows. The good news: the "switch to it if running, open it if not"
behavior doesn't need window enumeration at all — VS Code's own CLI provides it.

**Recommended design** (matches the `~/code` leaf-folder idea):

1. **Script Filter** (keyword e.g. `rig`) scans `~/code/*/*` leaf folders and emits
   Alfred JSON items — `title` = project name, `subtitle` = path, `arg` = path,
   `autocomplete` = project name (gives `rig gas-[tab]` completion).
2. **Run Script action** executes `code "<path>"` (no `-n`). VS Code *refuses* to open
   an already-open folder twice and focuses the existing window instead — by design,
   confirmed in [microsoft/vscode#35207](https://github.com/microsoft/vscode/issues/35207)
   and re-confirmed as NOT PLANNED to change in
   [#201939](https://github.com/microsoft/vscode/issues/201939). Not open → it opens.
3. **Optional layer**: a "● running" annotation per project, via
   `CGWindowListCopyWindowInfo` title matching (see below). Cosmetic only; the
   switching behavior works without it.

This needs no AppleScript, no accessibility permissions, no Screen Recording
permission, and covers projects whether or not they're already open.

## Finding 1 — prior art: nobody lists running windows

All four surveyed VS Code workflows read persisted state
([vanstrouble/vscode-alfred-workflow](https://github.com/vanstrouble/vscode-alfred-workflow),
[kbshl/alfred-vscode](https://github.com/kbshl/alfred-vscode) (archived 2023),
[phartenfeller/alfred-vscode-workspaces](https://github.com/phartenfeller/alfred-vscode-workspaces),
[luwes/alfred-vscode-workspaces](https://github.com/luwes/alfred-vscode-workspaces)):

| Workflow | Enumeration source | Action on select |
|---|---|---|
| vanstrouble | `state.vscdb` SQLite: `SELECT value FROM ItemTable WHERE key = 'history.recentlyOpenedPathsList'` (same list backing File → Open Recent), falling back to `storage.json`'s `lastKnownMenubarData` | `code` CLI |
| kbshl | Project Manager extension's `projects.json` | `code` CLI |
| phartenfeller | `state.vscdb`, same query | `code -n --folder-uri` |
| luwes | `mdfind "kMDItemFSName=*.code-workspace"` (Spotlight) | `code -n` / `code -a` |

None contains any AppleScript, System Events, lsof, or process-inspection code
(verified at the code level). Two gotchas worth stealing from their issue lists:
luwes hardcodes `/usr/local/bin/code`, which breaks on Apple Silicon default
installs — resolve the `code` path robustly (e.g. `command -v code` with a
`/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code` fallback).

The `state.vscdb` recents query is still useful to us: it's the natural way to
*augment* the `~/code` scan with workspaces that live outside `~/code`.

## Finding 2 — the running-window technique that actually works

[mandrigin/AlfredSwitchWindows](https://github.com/mandrigin/AlfredSwitchWindows)
(generic window switcher, dormant since 2022 but architecturally current) proves the
viable approach for the "which windows are open" half:

- **Enumerate** with a native binary calling
  `CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID)`,
  reading `kCGWindowName` / `kCGWindowOwnerName` (`EnumWindows/Windows.swift:87`).
  This sees Electron windows regardless of AppleScript support.
  **Caveat:** on macOS 10.15+, `kCGWindowName` is only populated if the calling
  process (Alfred) has **Screen Recording** permission.
- **Focus** with a generic System Events AppleScript:
  `perform action "AXRaise" of window <name>` + `activate`.

Why prefer CGWindowList over accessibility (AXTitle): VS Code 1.40 shipped an
Electron 6/Chromium 75 regression that blanked AXTitle for *every* window switcher
(Witch, Contexts, Hammerspoon, BetterTouchTool) while CGWindowList-based tools kept
working ([microsoft/vscode#84195](https://github.com/microsoft/vscode/issues/84195),
fixed via [electron/electron#21462](https://github.com/electron/electron/pull/21462)).
Long-fixed, but it demonstrates which API surface is fragile across Electron
upgrades.

If a System Events approach is ever needed and VS Code's accessibility tree isn't
exposed, it can be force-enabled from outside: `AXUIElementCreateApplication(pid)` +
set app-level attribute `AXManualAccessibility = true`, falling back to
`AXEnhancedUserInterface` on `kAXErrorAttributeUnsupported`
([set-electron-app-accessible](https://github.com/JonathanGawrych/set-electron-app-accessible),
[Electron accessibility docs](https://github.com/electron/electron/blob/main/docs/tutorial/accessibility.md)).

Addressing VS Code: bundle id is `com.microsoft.VSCode` (confirmed from the shipped
Info.plist in [vscode#46762](https://github.com/Microsoft/vscode/issues/46762));
System Events sees the process as `"Code"`. Use the bundle id to disambiguate
Insiders/VSCodium variants.

## Finding 3 — `code <folder>` is the focus mechanism

Confirmed 3-0: re-opening an already-open folder focuses its existing window instead
of opening a duplicate — even with `window.openFoldersInNewWindow: "on"`.
`-n`/`--new-window` deliberately bypasses the reuse. Caveats:

- Only works for folder/workspace windows whose path you know (fine for the `~/code`
  design, where the path *is* the identity).
- Untitled/empty windows and multi-root workspaces without a saved
  `.code-workspace` file can't be targeted this way (open question below).
- CLI-initiated activation can occasionally hit macOS focus-stealing quirks.

## Finding 4 — Alfred Script Filter mechanics

From the official docs ([Script Filter](https://www.alfredapp.com/help/workflows/inputs/script-filter/),
[JSON format](https://www.alfredapp.com/help/workflows/inputs/script-filter/json/)):

- Output a JSON object with an `items` array; `title` is the only required item
  field. `subtitle`, `icon`, `uid` (for Alfred's frecency sorting), `autocomplete`
  (tab completion), `valid`, and `mods` are optional.
- `arg` is what's passed to the connected output action on ⏎ (string, or array of
  strings on Alfred 4.1+).
- JSON is the current format; XML output is legacy.
- Requires the paid Powerpack (already owned — v5.7.3 per the screenshot).

Useful pattern for `rig`: set each item's `autocomplete` to the project name so tab
narrows, and give modifier actions via `mods` (e.g. ⌘⏎ → `code -n` force-new-window,
⌥⏎ → reveal in Finder or open in terminal).

## Where to learn from / publish: the Alfred Gallery

- [Alfred Gallery](https://alfred.app/) — the official searchable directory, backed
  by the public repo [alfredapp/gallery-workflows](https://github.com/alfredapp/gallery-workflows)
  (greppable metadata for every published workflow).
- Submissions: host on GitHub
  ([official tutorial](https://www.alfredapp.com/blog/guides-and-tutorials/share-workflow-on-github/)),
  then submit via the Alfred Forum's Gallery process
  ([announcement](https://www.alfredapp.com/blog/announcements/alfred-gallery-submit-your-favourite-workflows/)).
- Style reference: [vitorgalvao/alfred-workflows](https://github.com/vitorgalvao/alfred-workflows)
  (Vítor Galvão curates the Gallery). Packal is legacy.

Given no Gallery workflow does live-window-aware project switching, a polished
version of this would be a genuinely novel contribution.

## Refuted claims (distrust the blog-lore)

Adversarial verification killed 6 of 25 claims — worth recording so we don't
re-absorb them:

- "System Events sees VS Code as a process named `Electron` with bundle id
  `com.github.electron`" — refuted 0-3; current builds report process `Code`,
  bundle `com.microsoft.VSCode`.
- "AppleScript automation can launch a stray Electron binary from `node_modules`" —
  refuted 0-3 (2018-era lore).
- "Electron apps don't expose their UI to AppleScript by default" — refuted as a
  blanket statement (only the force-enable *mechanism* is confirmed).
- "The `code` CLI provides no way to enumerate running windows" — **refuted 0-3**,
  meaning the CLI may offer more than its docs suggest (e.g. `code --status`).
  Unresolved either way; see open questions.

## Open questions

1. Does `code --status` (or another CLI surface) expose a parseable list of open
   windows/workspaces we could use for the "running" annotation instead of
   CGWindowList + Screen Recording permission? (Cheap to test locally.)
   Note: [vscode-discussions#1815](https://github.com/microsoft/vscode-discussions/discussions/1815)
   confirms there's no *extension API* for cross-window enumeration.
2. Most robust title→workspace mapping when `window.title` is customized, two
   windows share a folder name, or Insiders/VSCodium run alongside stable.
3. Does AXRaise work on current VS Code builds without force-enabling
   `AXManualAccessibility`? Does `code <folder>` reliably raise across Spaces /
   full-screen windows?
4. How to represent/focus untitled windows and multi-root workspaces (no single
   folder path to re-open).

## Run stats

102 agents, 633 tool calls, 12.6 min, ~3.5M subagent tokens. 20 sources fetched
across 5 angles; 97 claims extracted; 25 verified (3 votes each): 19 confirmed 3-0,
6 refuted, 0 unverified.
