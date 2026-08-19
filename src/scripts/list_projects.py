#!/usr/bin/env python3
"""Alfred Script Filter: list leaf project folders (root/org/project) as JSON.

Emits every item in one shot; Alfred itself filters per keystroke
("Alfred filters results" is ON in the Script Filter config).

Projects with an open VS Code window get a " •" title suffix. `code --status`
takes ~1.5s, far too slow to run inline, so the running set is cached: the
filter reads the cache instantly, spawns a detached `--refresh-running` child
when the cache is stale, and asks Alfred to re-run it (the `rerun` key) until
the refresh lands. Window titles end in the workspace root name under the
default `window.title` setting; a customized title means no indicator, which
degrades harmlessly.
"""
import json
import os
import re
import subprocess
import sys
import time

CACHE_TTL_SECONDS = 10
LOCK_STALE_SECONDS = 20
CODE_CLI_FALLBACKS = (
    "/usr/local/bin/code",
    "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
)


def cache_dir():
    d = os.environ.get("alfred_workflow_cache") or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "com.sellsbrothers.proj"
    )
    os.makedirs(d, exist_ok=True)
    return d


def code_cli():
    from shutil import which

    cli = which("code")
    if cli:
        return cli
    for path in CODE_CLI_FALLBACKS:
        if os.access(path, os.X_OK):
            return path
    return None


def parse_window_roots(status_text):
    """Extract workspace root names from `code --status` window lines."""
    roots = []
    for m in re.finditer(r"window \[\d+\] \((.*)\)$", status_text, re.MULTILINE):
        root = m.group(1).rsplit(" — ", 1)[-1].strip()
        if root.endswith(" (Workspace)"):
            root = root[: -len(" (Workspace)")]
        if root:
            roots.append(root)
    return roots


def refresh_running():
    """Write the set of open-window root names to the cache, then drop the lock.

    Always writes the cache (empty on any failure) so its fresh mtime stops
    the filter's rerun loop even when VS Code is closed or the CLI is missing.
    """
    d = cache_dir()
    names = []
    try:
        vscode_running = (
            subprocess.run(["/usr/bin/pgrep", "-fq", "MacOS/Code"]).returncode == 0
        )
        cli = code_cli()
        if vscode_running and cli:
            out = subprocess.run(
                [cli, "--status"], capture_output=True, text=True, timeout=15
            ).stdout
            names = parse_window_roots(out)
    except Exception:
        pass
    tmp = os.path.join(d, "running.json.tmp")
    with open(tmp, "w") as f:
        json.dump(sorted(set(names)), f)
    os.replace(tmp, os.path.join(d, "running.json"))
    try:
        os.remove(os.path.join(d, "refresh.lock"))
    except FileNotFoundError:
        pass


def load_running():
    """Return (running root names casefolded, need_rerun)."""
    d = cache_dir()
    cache = os.path.join(d, "running.json")
    lock = os.path.join(d, "refresh.lock")
    now = time.time()
    names, fresh = set(), False
    try:
        stat = os.stat(cache)
        with open(cache) as f:
            names = {n.casefold() for n in json.load(f)}
        fresh = now - stat.st_mtime < CACHE_TTL_SECONDS
    except Exception:
        pass
    if fresh:
        return names, False
    try:
        refreshing = now - os.stat(lock).st_mtime < LOCK_STALE_SECONDS
    except FileNotFoundError:
        refreshing = False
    if not refreshing:
        open(lock, "w").close()
        subprocess.Popen(
            [sys.executable, os.path.realpath(__file__), "--refresh-running"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    return names, True


def main():
    root = os.path.expanduser(
        os.environ.get("PROJECTS_ROOT", "").strip() or "~/Code"
    )
    running, need_rerun = load_running()
    items = []
    try:
        orgs = sorted(
            (e for e in os.scandir(root) if e.is_dir() and not e.name.startswith(".")),
            key=lambda e: e.name.lower(),
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        orgs = []
    for org in orgs:
        try:
            children = list(os.scandir(org.path))
        except PermissionError:
            continue
        for child in children:
            if not child.is_dir() or child.name.startswith("."):
                continue
            is_running = child.name.casefold() in running
            items.append(
                {
                    "uid": child.path,
                    "title": child.name + (" •" if is_running else ""),
                    "subtitle": f"{org.name}/{child.name}",
                    "arg": child.path,
                    "autocomplete": child.name,
                    "match": f"{child.name} {org.name} {org.name}/{child.name}",
                    "icon": {"type": "fileicon", "path": child.path},
                    "mods": {
                        "cmd": {"subtitle": "Force new window"},
                        "alt": {"subtitle": "Reveal in Finder"},
                    },
                }
            )
    items.sort(key=lambda i: i["title"].lower())
    if not items:
        items = [
            {
                "title": f"No projects found under {root}",
                "subtitle": "Set Projects Root in this workflow's configuration",
                "valid": False,
            }
        ]
    output = {"items": items}
    if need_rerun:
        output["rerun"] = 1.0
    json.dump(output, sys.stdout)


if __name__ == "__main__":
    if "--refresh-running" in sys.argv[1:]:
        refresh_running()
    else:
        main()
