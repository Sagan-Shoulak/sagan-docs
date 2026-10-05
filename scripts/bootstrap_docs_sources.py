"""Clone only the exact active source revisions in docs-sources.lock."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tomllib

from assemble_docs import ROOT, read_lock, verify_source


def git(*arguments: str) -> None:
    result = subprocess.run(["git", *arguments], text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())


def bootstrap(lock_path: Path, source_root: Path) -> list[str]:
    url, commit, _, components = read_lock(lock_path)
    entries = [{"id": "sagan", "url": url, "commit": commit}]
    entries.extend(component for component in components if component["state"] == "active")
    if source_root.is_symlink() or (source_root.exists() and not source_root.is_dir()):
        raise ValueError("source root is unsafe or not a directory")
    source_root.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        target = source_root / entry["id"]
        if not target.exists() and not target.is_symlink():
            print(f"{entry['id']}: cloning {entry['url']} at {entry['commit'][:12]}", flush=True)
            try:
                git("clone", "--no-checkout", "--no-tags", entry["url"], str(target))
                git("-C", str(target), "checkout", "--detach", entry["commit"])
            except ValueError as error:
                raise ValueError(
                    f"{error}. Preserve partial checkout {target} for inspection."
                ) from error
        verify_source(target, entry["url"], entry["commit"], entry["id"])
        print(f"{entry['id']}: clean at locked commit {entry['commit'][:12]}")
    return [entry["id"] for entry in entries]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=ROOT / "docs-sources.lock")
    parser.add_argument("--root", type=Path, default=ROOT / "build" / "sources")
    arguments = parser.parse_args()
    try:
        bootstrap(arguments.lock.resolve(), arguments.root.absolute())
        return 0
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"Documentation source bootstrap failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
