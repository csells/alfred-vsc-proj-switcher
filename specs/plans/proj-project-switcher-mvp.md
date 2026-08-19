# Plan: `proj` project switcher — MVP

Implements the vision in `specs/vision/proj-project-switcher.md`. Everything here is
grounded in `research.md` (Script Filter JSON schema, `code <folder>` focus-reuse
behavior, prior-art pitfalls) and in facts verified on this machine on 2026-08-18:
projects root `~/Code` with 102 depth-2 leaves across 9 org folders, `code` CLI at
`/usr/local/bin/code`, Alfred 5.7.3 with prefs at the default location
(`~/Library/Application Support/Alfred/Alfred.alfredpreferences`).

## Architecture

Two Alfred objects connected in one workflow — no native code, no polling:

```
[Script Filter: keyword "proj"] --arg=<abs path>--> [Run Script: open-or-focus]
        |                                                  |
        |  runs scripts/list_projects.py once per          |  runs scripts/open_project.sh
        |  invocation; emits all leaves as JSON;           |  resolves `code`, then:
        |  "Alfred filters results" = ON                   |  ⏎  → code "$path"
        |                                                  |  ⌘⏎ → code -n "$path"
        |                                                  |  ⌥⏎ → open -R "$path" (Finder)
```

Key choice: **"Alfred filters results" ON**. The script runs once and emits all
~102 items; Alfred does the per-keystroke fuzzy matching, honors `uid` frecency,
and ⇥-completes the `autocomplete` field. This is what makes `proj gas-⇥` work and
keeps the script trivially simple (no query parsing at all).

## Repo layout

```
alfred-vsc-switcher/
├── src/
│   ├── info.plist              # workflow definition (objects, connections, config)
│   ├── icon.png                # workflow icon
│   └── scripts/
│       ├── list_projects.py    # Script Filter body
│       └── open_project.sh     # Run Script body
├── build.sh                    # zips src/ → dist/proj.alfredworkflow
├── specs/…, research.md, README.md
```

Source of truth is the repo; the `.alfredworkflow` is a build artifact
(`dist/` gitignored). This keeps the workflow reviewable and version-controlled
rather than trapped inside Alfred's prefs bundle.

## Step 1 — `list_projects.py` (Script Filter)

Python 3 (present on this dev machine; no third-party deps), because hand-building
JSON in bash breaks on paths with quotes/spaces and `json.dumps` doesn't.

Behavior:

1. Read `PROJECTS_ROOT` from the environment (Alfred injects user-config variables
   as env vars); default `~/Code`; `expanduser` it.
2. `os.scandir` two levels: for each non-hidden org dir, each non-hidden child dir
   is a project. Skip files, skip dot-dirs at both levels. Sort by project name.
3. Emit `{"items": [...]}` to stdout, one item per leaf:
   - `title`: leaf folder name (`gas-city-inc`)
   - `subtitle`: `org/leaf` (`gascity/gas-city-inc`)
   - `arg`: absolute path — this is what flows to the action
   - `uid`: absolute path — stable, lets Alfred learn frecency
   - `autocomplete`: leaf name — powers ⇥ completion
   - `match`: `"<leaf> <org> <org>/<leaf>"` — with "Alfred filters results" the
     `match` field is what Alfred matches against, so org names narrow too
   - `icon`: `{"type": "fileicon", "path": <abs path>}` — each row shows the
     folder's own Finder icon (custom folder icons carry through for free)
4. Edge case: root missing/empty → emit one invalid item (`"valid": false`) titled
   "No projects found under <root>" so the user sees a diagnosis, not silence.

## Step 2 — `open_project.sh` (Run Script action)

```bash
#!/bin/bash
# $1 = absolute project path, $2 = mode ("" | "new-window")
```

1. Resolve the CLI once: `command -v code`, else
   `/usr/local/bin/code`, else
   `"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"`.
   (Prior-art workflows hardcode `/usr/local/bin/code`, which breaks on default
   Apple Silicon installs — research.md, Finding 1.)
2. Default ⏎: `"$CODE" "$1"` — VS Code focuses the existing window if the folder is
   open, opens it otherwise (research.md, Finding 3). This is the entire
   switch-or-launch mechanism; there is deliberately no window-detection code.
3. ⌘⏎ passes `new-window` → `"$CODE" -n "$1"`.
4. ⌥⏎ is a separate tiny action: `open -R "$1"` (reveal in Finder). Wire it as a
   modifier `mods.alt` on the Script Filter item (subtitle "Reveal in Finder")
   feeding the same Run Script with a mode argument, or as a second connection —
   whichever keeps info.plist simpler; one Run Script with a mode switch preferred.

## Step 3 — `info.plist`

Author directly in the repo (XML plist). Structure cribbed from the unzipped
prior-art bundles examined in research (luwes, phartenfeller) and the Alfred docs:

- Workflow metadata: name "VS Code Project Switcher", bundle id
  `com.sellsbrothers.proj`, createdby, description, webaddress (GitHub repo).
- **User configuration** (Alfred 5 `userconfigurationconfig`): single field
  `PROJECTS_ROOT`, type filepicker (folders), default `~/Code`, with a description.
- **Script Filter object**: keyword `proj`, "with space", argument optional,
  `alfredfiltersresults` = true, script = `python3 scripts/list_projects.py`
  (language `/bin/bash` invoking python3, or scriptfile reference — use
  type "external script" pointing at `scripts/list_projects.py` so the file stays
  editable on disk).
- **Run Script object**: `/bin/bash` with input as argv, body invoking
  `scripts/open_project.sh`.
- **Connections**: Script Filter → Run Script for default and ⌘ modifier (mode
  arg differs), ⌥ per Step 2.
- `mods` on each item set the modifier subtitles (⌘: "Force new window",
  ⌥: "Reveal in Finder").

## Step 4 — `build.sh`

`cd src && zip -r ../dist/proj.alfredworkflow .` (a `.alfredworkflow` is just a
zip of the workflow dir with `info.plist` at its root). Double-clicking the
artifact installs/updates it in Alfred.

## Step 5 — verification

Scripted (no Alfred needed):
1. `python3 src/scripts/list_projects.py | python3 -m json.tool` — valid JSON;
   item count equals `find ~/Code -mindepth 2 -maxdepth 2 -type d ! -name '.*' | wc -l`
   (102 today); spot-check an item's fields.
2. `PROJECTS_ROOT=/nonexistent python3 …` — emits the invalid "no projects" item,
   exit 0.
3. `src/scripts/open_project.sh` with a scratch folder — VS Code opens it; run
   again — the same window focuses (no second window); with `new-window` — a
   second window opens. Clean up the scratch window only.

In Alfred, after installing the build:
4. `proj` lists projects; typing narrows; `proj gas-⇥` completes to a full name;
   subtitle disambiguates same-named leaves in different orgs.
5. ⏎ on this repo (already open) focuses the existing window; ⏎ on a cold project
   opens it; ⌘⏎ forces a new window; ⌥⏎ reveals in Finder.
6. Change `PROJECTS_ROOT` in the workflow's Configure sheet to a scratch root and
   confirm the list follows it; change it back.

## Risks / open items

- **Same-named leaves in two orgs**: both listed; subtitle + `match` disambiguate.
  ⇥ completion of the shared name leaves both visible — acceptable; ⏎ acts on the
  selected row's `arg`, which is unambiguous.
- **`code` CLI absent** (never installed via "Shell Command: Install 'code'"):
  open_project.sh falls back to the app-bundle bin path, which exists whenever the
  app does; if even that misses, surface a macOS notification via Alfred's output.
- **Focus quirks**: CLI-initiated activation can occasionally lose a
  focus-stealing race (research.md, Finding 3 caveats). Accept for MVP; revisit
  with an `open -b com.microsoft.VSCode` chaser only if it actually bites.
- **Multi-root workspaces / untitled windows**: out of scope (vision non-goal);
  the folder-reopen mechanism can't target them.

## Milestone 2 (separate plan when we get there)

Running-window "●" annotation: first experiment with parsing `code --status`
(research.md open question 1 — no permissions needed if parseable); fall back to a
CGWindowList helper + Screen Recording permission only if `--status` is a dead end.
Then: recents augmentation from `state.vscdb`, and Alfred Gallery submission.
