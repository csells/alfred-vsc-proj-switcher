# Alfred Gallery — actual submission process (corrected 2026-08-19)

The Gallery is **invitation-based** — there is no direct submission form. Per
[alfred.app/submit](https://alfred.app/submit/):

1. **Share the workflow on the forum first**, in the
   [Share your Workflows](https://www.alfredforum.com/forum/3-share-your-workflows/)
   section. (The `forum/62-…` URL in an earlier draft of this file never
   existed.)
2. Once the workflow is "generally stable and trusted by a number of users,"
   the Alfred team **may invite** an official Gallery submission.

## Gallery requirements checklist (all met)

- Icon at least 256×256 px — ✓ 512×512 original
- Keyword three characters or more — ✓ `proj`
- User configuration offered — ✓ Projects Root, VS Code CLI
- No unsigned binaries, no auto-updaters, never downloads/runs external
  software, no `pip/gem/brew install` or curl'd binaries — ✓ two plain-text
  scripts, fully auditable on GitHub
- README follows the [Gallery style guide](https://alfred.app/submit/styleguide/)
  — ✓ the workflow's embedded readme uses the `## Usage` + `<kbd>` modifier
  format

## Forum post draft (Share your Workflows)

---

**Title:** VS Code Project Switcher — open-or-focus your projects via a keyword

**Body:**

Search for your VS Code projects via the `proj` keyword and press
<kbd>↩</kbd> — the project's window is focused if it's already open (shown
with a • indicator) and launched if it isn't.

[screenshot: docs/images/proj-search.png]

Unlike the existing VS Code workflows that list recent or saved workspaces,
this one scans your actual projects folder — git repos at any depth plus
plain `org/project` folders — and marks the ones with an open window live,
using no Accessibility or Screen Recording permissions. The open-or-focus
behavior is VS Code's own CLI semantics (`code <folder>` focuses the existing
window rather than opening a duplicate), so there's no AppleScript or window
scraping. Matching is word-level: "trading" finds `auto-trading`.

- <kbd>↩</kbd> Open or focus the project
- <kbd>⌘</kbd><kbd>↩</kbd> Force a new window
- <kbd>⌥</kbd><kbd>↩</kbd> Reveal the folder in Finder
- <kbd>⇥</kbd> Autocomplete the project name

Projects Root and the VS Code CLI (stable, Insiders, or VSCodium) are set in
the Workflow's Configuration.

Download: https://github.com/csells/alfred-vsc-proj-switcher/releases/latest
Source: https://github.com/csells/alfred-vsc-proj-switcher

Requires the Powerpack, VS Code, and macOS `python3` (Xcode Command Line
Tools).
