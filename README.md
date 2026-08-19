# alfred-vsc-switcher

An Alfred workflow for switching among VS Code projects: type `proj` plus a few
characters of a project name, press ⏎, and you're in that project's window —
**focused if it's already open, launched if it isn't**.

The trick is that no window enumeration is needed: `code <folder>` already
refuses to open a folder that's open in another window and focuses that window
instead (by design — see `research.md` for the verified deep-dive). So the
workflow just lists the depth-2 leaf folders under a projects root
(`~/Code/<org>/<project>` by default) and hands the selected path to the
`code` CLI.

## Usage

- `proj <query>` — fuzzy-filter your projects (matches project and org names;
  Alfred's frecency learns your favorites)
- ⇥ — autocomplete the selected project name
- ⏎ — open or focus the project in VS Code
- ⌘⏎ — force a new window
- ⌥⏎ — reveal the folder in Finder

## Install

```sh
./build.sh
open dist/proj.alfredworkflow   # Alfred prompts to import
```

Requires Alfred with the Powerpack, VS Code, and `python3`. The projects root
is configurable in the workflow's configuration sheet (`PROJECTS_ROOT`,
default `~/Code`).

## Layout

- `src/` — workflow source (`info.plist`, scripts, icon); the
  `.alfredworkflow` in `dist/` is just a zip of this directory
- `specs/vision/` — what this is and why it's built this way
- `specs/plans/` — the implementation plan
- `research.md` — deep-research findings the design rests on (prior art,
  the `code <folder>` focus-reuse behavior, Script Filter mechanics,
  Electron/AppleScript pitfalls)

## Notes

- The workflow icon is currently VS Code's own app icon — fine for personal
  use, but it needs an original icon before any Alfred Gallery submission.
- Verified on this machine: `code --status` lists all open windows without any
  permissions, which is the planned path for a future "● running" indicator.
  System Events/AppleScript, by contrast, sees no VS Code windows at all
  without force-enabling `AXManualAccessibility` — avoid that road.
