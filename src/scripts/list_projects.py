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
HOME = os.path.expanduser("~")
CODE_CLI_FALLBACKS = (
    "/usr/local/bin/code",
    "/opt/homebrew/bin/code",
    "/usr/local/bin/code-insiders",
    "/opt/homebrew/bin/code-insiders",
    "/usr/local/bin/codium",
    "/opt/homebrew/bin/codium",
    "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
    HOME + "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
    "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders",
    "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code",
    "/Applications/VSCodium.app/Contents/Resources/app/bin/codium",
)


def cache_dir():
    d = os.environ.get("alfred_workflow_cache") or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "com.sellsbrothers.proj"
    )
    os.makedirs(d, exist_ok=True)
    return d


def code_cli():
    """Same resolution order as open_project.sh: CODE_CLI config, PATH, then
    common locations for stable, Insiders, and VSCodium."""
    from shutil import which

    configured = os.path.expanduser(os.environ.get("CODE_CLI", "").strip())
    if configured and os.access(configured, os.X_OK):
        return configured
    for name in ("code", "code-insiders", "codium"):
        cli = which(name)
        if cli:
            return cli
    for path in CODE_CLI_FALLBACKS:
        if os.access(path, os.X_OK):
            return path
    return None


def app_is_running(cli):
    """True when the app bundle that owns this CLI has a running process.

    Guards `code --status` from launching the editor when it isn't running.
    Uses `ps` prefix checks rather than pgrep: pgrep -f patterns containing
    spaces ("Visual Studio Code.app/...") silently match nothing.
    """
    try:
        out = subprocess.run(
            ["/bin/ps", "-axo", "comm="], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return False
    real = os.path.realpath(cli)
    if ".app/" in real:
        prefix = real.split(".app/", 1)[0] + ".app/Contents/MacOS/"
        return any(line.startswith(prefix) for line in out.splitlines())
    return any("/Contents/MacOS/Code" in line for line in out.splitlines())


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
        cli = code_cli()
        if cli and app_is_running(cli):
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


MAX_DEPTH = 4
SKIP_DIR_NAMES = {"node_modules"}


def match_text(rel_path):
    """Alfred matches the query against this instead of the title.

    Include each separator-delimited word of every path component as a
    standalone token so word-boundary matching hits mid-name words: "trading"
    finds "auto-trading" without remembering the prefix.
    """
    parts = [rel_path.rsplit("/", 1)[-1], rel_path]
    parts += re.split(r"[-_./\s]+", rel_path)
    return " ".join(dict.fromkeys(p for p in parts if p))


def app_support_dir(cli):
    """The variant-specific Application Support dir for the resolved CLI."""
    real = os.path.realpath(cli) if cli else ""
    if "Insiders" in real:
        name = "Code - Insiders"
    elif "VSCodium" in real or real.endswith("/codium"):
        name = "VSCodium"
    else:
        name = "Code"
    return os.path.join(HOME, "Library/Application Support", name)


MAX_RECENTS = 20


def recent_projects():
    """Yield (display, abs_path, leaf) from VS Code's Open Recent list.

    Modern VS Code no longer stores history.recentlyOpenedPathsList in
    state.vscdb (the key older workflows query is gone); the surviving
    on-disk copy of the Open Recent list is the File menu snapshot in
    storage.json's lastKnownMenubarData.
    """
    storage = os.path.join(
        app_support_dir(code_cli()), "User/globalStorage/storage.json"
    )
    try:
        with open(storage) as f:
            menus = json.load(f).get("lastKnownMenubarData", {}).get("menus", {})
    except Exception:
        return []

    found = []

    def collect(node):
        if isinstance(node, dict):
            node_id = str(node.get("id", ""))
            if node_id in ("openRecentFolder", "openRecentWorkspace"):
                path = (node.get("uri") or {}).get("path", "")
                if path:
                    found.append(path)
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)

    collect(menus.get("File", {}))

    out = []
    for path in found:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            continue
        leaf = os.path.basename(path)
        if leaf.endswith(".code-workspace"):
            leaf = leaf[: -len(".code-workspace")]
        display = path.replace(HOME + "/", "~/", 1) if path.startswith(HOME + "/") else path
        out.append((display, path, leaf))
        if len(out) >= MAX_RECENTS:
            break
    return out


def include_recents():
    return os.environ.get("INCLUDE_RECENTS", "1").strip().lower() not in (
        "0",
        "false",
    )


def scan_projects(root):
    """Yield (rel_path, abs_path, leaf_name) for every project under root.

    A directory with a .git (dir or worktree file) is a project and is not
    descended into; anything else is a container to recurse. Plain depth-2
    folders with no nested repos still count as projects, so non-git projects
    (org/project layout) keep appearing. Hidden dirs are skipped everywhere,
    which also excludes .claude worktree/skill repos.
    """

    def walk(path, rel, depth):
        try:
            children = sorted(
                (
                    e
                    for e in os.scandir(path)
                    if e.is_dir()
                    and not e.name.startswith(".")
                    and e.name not in SKIP_DIR_NAMES
                ),
                key=lambda e: e.name.lower(),
            )
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return []
        found = []
        for child in children:
            child_rel = f"{rel}/{child.name}" if rel else child.name
            if os.path.exists(os.path.join(child.path, ".git")):
                found.append((child_rel, child.path, child.name))
            elif depth + 1 < MAX_DEPTH:
                nested = walk(child.path, child_rel, depth + 1)
                if nested:
                    found.extend(nested)
                elif depth + 1 == 2:
                    found.append((child_rel, child.path, child.name))
        return found

    return walk(root, "", 0)


def main():
    root = os.path.expanduser(
        os.environ.get("PROJECTS_ROOT", "").strip() or "~/Code"
    )
    running, need_rerun = load_running()

    def item(display, path, leaf):
        is_running = leaf.casefold() in running
        return {
            "uid": path,
            "title": leaf + (" •" if is_running else ""),
            "subtitle": display,
            "arg": path,
            "autocomplete": leaf,
            "match": match_text(display.lstrip("~/")),
            "icon": {"type": "fileicon", "path": path},
            "mods": {
                "cmd": {"subtitle": "Force new window"},
                "alt": {"subtitle": "Reveal in Finder"},
            },
        }

    items = []
    seen = set()
    for rel, path, leaf in scan_projects(root):
        seen.add(os.path.normpath(path).casefold())
        items.append(item(rel, path, leaf))
    if include_recents():
        for display, path, leaf in recent_projects():
            key = os.path.normpath(path).casefold()
            if key in seen:
                continue
            seen.add(key)
            items.append(item(display, path, leaf))
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
