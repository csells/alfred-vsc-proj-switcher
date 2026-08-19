# alfred-vsc-proj-switcher

An [Alfred](https://www.alfredapp.com/) workflow for switching among VS Code
projects: type `proj` plus a few characters of a project name, press ⏎, and
you're in that project's window — **focused if it's already open, launched if
it isn't**.

## Why it works

No window enumeration is needed. VS Code's own CLI refuses to open a folder
that's already open in another window and focuses that window instead — a
documented, by-design behavior ([microsoft/vscode#35207](https://github.com/microsoft/vscode/issues/35207)).
So the workflow simply lists the depth-2 leaf folders under a projects root
(`~/Code/<org>/<project>` by default) and hands the selected path to `code`.
That makes it strictly more capable than a running-windows switcher: it reaches
every project, running or not, with no AppleScript, no native binaries, and no
Screen Recording or Accessibility permissions.

`research.md` has the verified deep-dive behind this design: the prior-art
survey (no existing Alfred workflow lists running VS Code windows), the
focus-reuse behavior, Script Filter mechanics, and the Electron/AppleScript
dead ends to avoid.

## Usage

- `proj <query>` — fuzzy-filter your projects; matches project and org names,
  and Alfred's frecency learns your favorites
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
- `research.md` — the research findings the design rests on

## Roadmap

- "● running" indicator per project: `code --status` lists every open window
  with no permissions required (verified), so this needs only title parsing —
  no CGWindowList binary
- Recents from VS Code's `state.vscdb` for workspaces outside the projects root
- Alfred Gallery submission (needs an original icon first — the current one is
  VS Code's own, fine for personal use only)
