"""Assemble a reproducible local MkDocs tree from pinned component docs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


ROOT = Path(__file__).resolve().parent.parent
SHA = re.compile(r"[0-9a-f]{40}\Z")
HOOKS = ("docs_status.py", "docs_sagan_lexer.py")


def git(checkout: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(checkout), *args],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


def read_lock(path: Path) -> tuple[str, str, list[str]]:
    with path.open("rb") as source:
        data = tomllib.load(source)
    if data.get("schema_version") != 1:
        raise ValueError("docs source lock requires schema_version = 1")
    sagan = data.get("sagan")
    site = data.get("site")
    if not isinstance(sagan, dict) or not isinstance(site, dict):
        raise ValueError("docs source lock requires sagan and site tables")
    url, commit = sagan.get("url"), sagan.get("commit")
    if not isinstance(url, str) or not url or not isinstance(commit, str) or not SHA.fullmatch(commit):
        raise ValueError("docs source lock requires a URL and full lowercase commit SHA")
    overlays = site.get("overlay_paths")
    if not isinstance(overlays, list) or not overlays:
        raise ValueError("site overlay_paths must be a nonempty array")
    if any(not isinstance(path, str) or not path for path in overlays):
        raise ValueError("site overlay paths must be nonempty strings")
    for path in overlays:
        parts = PurePosixPath(path).parts
        if ("\\" in path or path.startswith("/") or not parts or
                any(part in (".", "..", "") for part in parts)):
            raise ValueError(f"unsafe site overlay path: {path}")
    if len(overlays) != len(set(overlays)):
        raise ValueError("site overlay paths must be unique")
    return url, commit, overlays


def verify_source(checkout: Path, url: str, commit: str) -> None:
    if not checkout.is_dir() or checkout.is_symlink():
        raise ValueError("Sagan source checkout is missing or unsafe")
    top = Path(git(checkout, "rev-parse", "--show-toplevel")).resolve()
    if top != checkout.resolve():
        raise ValueError("Sagan source path is inside a different Git checkout")
    if git(checkout, "remote", "get-url", "origin") != url:
        raise ValueError("Sagan source origin differs from docs-sources.lock")
    if git(checkout, "rev-parse", "HEAD") != commit:
        raise ValueError("Sagan source HEAD differs from docs-sources.lock")
    if git(checkout, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Sagan source checkout is dirty")
    if not (checkout / "docs").is_dir():
        raise ValueError("Sagan source has no docs directory")


def assemble(root: Path, lock_path: Path, checkout: Path, output: Path) -> None:
    url, commit, overlays = read_lock(lock_path)
    verify_source(checkout, url, commit)
    if output == checkout or output.is_relative_to(checkout):
        raise ValueError("assembled output must not be inside the Sagan source checkout")
    if output == root / "docs" or output.is_relative_to(root / "docs"):
        raise ValueError("assembled output must not be inside site-owned docs")
    owned = sorted(path.relative_to(root / "docs").as_posix()
                   for path in (root / "docs").rglob("*") if path.is_file())
    if owned != sorted(overlays):
        raise ValueError("site-owned docs differ from explicit overlay_paths")
    if output.exists() or output.is_symlink():
        raise ValueError(f"assembled output already exists: {output}")
    if any(path.is_symlink() for path in (checkout / "docs").rglob("*")):
        raise ValueError("Sagan source docs contain a symlink")
    if any(path.is_symlink() for path in (root / "docs").rglob("*")):
        raise ValueError("site-owned docs contain a symlink")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sagan-docs-assemble-", dir=output.parent) as temp:
        stage = Path(temp) / "site"
        stage.mkdir()
        shutil.copytree(checkout / "docs", stage / "docs")
        for relative in overlays:
            destination = stage / "docs" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / "docs" / relative, destination)
        shutil.copy2(root / "mkdocs.yml", stage / "mkdocs.yml")
        (stage / "scripts").mkdir()
        for hook in HOOKS:
            shutil.copy2(root / "scripts" / hook, stage / "scripts" / hook)
        (stage / "sources.json").write_text(
            json.dumps({"sagan_url": url, "sagan_commit": commit,
                        "site_overlay_paths": overlays}, indent=2) + "\n",
            encoding="utf-8",
        )
        stage.rename(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sagan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=ROOT / "docs-sources.lock")
    args = parser.parse_args()
    try:
        assemble(ROOT, args.lock, args.sagan.absolute(), args.output.absolute())
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"Documentation assembly failed: {error}", file=sys.stderr)
        return 1
    print(f"Documentation assembled at {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
