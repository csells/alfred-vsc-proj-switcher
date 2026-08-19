#!/usr/bin/env python3
"""Alfred Script Filter: list leaf project folders (root/org/project) as JSON.

Emits every item in one shot; Alfred itself filters per keystroke
("Alfred filters results" is ON in the Script Filter config).
"""
import json
import os
import sys


def main():
    root = os.path.expanduser(
        os.environ.get("PROJECTS_ROOT", "").strip() or "~/Code"
    )
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
            items.append(
                {
                    "uid": child.path,
                    "title": child.name,
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
    json.dump({"items": items}, sys.stdout)


if __name__ == "__main__":
    main()
