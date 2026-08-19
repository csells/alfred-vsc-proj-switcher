# Alfred Gallery submission draft

Post this in the Alfred Forum's Gallery submission section
(https://www.alfredforum.com/forum/62-submit-your-workflows-to-the-alfred-gallery/)
from your account. Prerequisites are all in place: public GitHub repo with
README and screenshot, original icon, tagged release with the
`.alfredworkflow` attached, and the `alfred-workflow` repo topic.

---

**Title:** VS Code Project Switcher — open-or-focus your projects from a keyword

**Body:**

`proj` + a few characters + ⏎ puts you in the right VS Code window: focused
if that project is already open, launched if it isn't.

Repo: https://github.com/csells/alfred-vsc-proj-switcher
Latest release: https://github.com/csells/alfred-vsc-proj-switcher/releases/latest

What it does differently from the existing VS Code workflows (which list
recent/saved workspaces): it scans your actual projects folder — git repos at
any depth plus plain `org/project` folders — and shows a live • indicator on
projects that already have an open window, with no Accessibility or Screen
Recording permissions. The open-or-focus behavior is VS Code's own
documented CLI semantics (`code <folder>` refuses to open the same folder
twice and focuses the existing window), so there's no AppleScript and no
window scraping.

Features:

- Word-level matching: "trading" finds `auto-trading`; every path component
  is matched, so a grouping folder name narrows too
- ⇥ autocompletes the project name; Alfred's frecency learns your favorites
- • running indicator via `code --status`, cached off the critical path so
  the list is always instant
- ⌘⏎ forces a new window; ⌥⏎ reveals in Finder
- Configurable projects root; VS Code stable, Insiders, and VSCodium
  supported with CLI auto-detection (or pin one in the workflow config)

Requirements: Powerpack, VS Code, macOS `python3` (Xcode Command Line Tools).
