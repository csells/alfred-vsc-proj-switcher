# Plan: • running indicator (milestone 2) — shipped 2026-08-18

The "separate plan" promised by `proj-project-switcher-mvp.md`. Adds a • title
suffix to projects that already have an open VS Code window. Cosmetic only:
open-or-focus never depends on it (vision principle 1).

## Decision: `code --status`, not CGWindowList

Research left two candidate mechanisms. The `code --status` experiment won
decisively when run on this machine: it lists every open window
(`window [N] (<title>)` lines) with **no permissions** — no Screen Recording,
no Accessibility, no native binary. CGWindowList remains the documented
fallback nobody needs.

Title → project mapping: under the default `window.title`, titles end in the
workspace root name; take the segment after the last " — " (em dash), strip a
trailing " (Workspace)", compare casefolded against leaf folder names. A
customized `window.title` hides the indicator and breaks nothing else.

## Latency design

`code --status` measures ~1.5s — unacceptable inline (vision: "Instant"). So:

- The running set is cached as JSON (`$alfred_workflow_cache`, or
  `$TMPDIR/com.sellsbrothers.proj` outside Alfred) with a 10s TTL.
- The Script Filter only ever reads the cache. When stale, it spawns a
  detached `list_projects.py --refresh-running` child (lockfile-guarded, 20s
  stale threshold) and emits Alfred's `rerun: 1.0` key so Alfred re-invokes
  the filter until fresh indicators appear — dots pop in ~2s after invocation,
  the list itself is never delayed.
- The refresh **always rewrites the cache**, empty on any failure (VS Code not
  running, CLI missing, timeout): the fresh mtime is what terminates the rerun
  loop.

## Empirical gotchas (cost real time; don't rediscover)

- The VS Code is-running guard is `pgrep -fq "MacOS/Code"`. `pgrep -x Code`
  matches nothing (the executable name isn't the process match), and `-f`
  patterns containing spaces ("Visual Studio Code.app/…") silently fail.
  The guard matters because `code --status` should not risk launching the app.
- Verified end-to-end on 2026-08-18: 31 of 102 projects showed dots, matching
  the open-window list; cold cache → 0 dots + rerun, fresh 4s later → 31 dots,
  rerun stops; works under Alfred's minimal-PATH environment.
