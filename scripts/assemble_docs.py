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


def safe_paths(paths: object, label: str) -> list[str]:
    if not isinstance(paths, list) or not paths or any(
        not isinstance(path, str) or not path for path in paths
    ):
        raise ValueError(f"{label} must be a nonempty array of paths")
    for path in paths:
        parts = PurePosixPath(path).parts
        if ("\\" in path or path.startswith("/") or not parts or
                any(part in (".", "..", "") for part in parts)):
            raise ValueError(f"unsafe {label} path: {path}")
    if len(paths) != len(set(paths)):
        raise ValueError(f"{label} paths must be unique")
    return paths


def read_lock(path: Path) -> tuple[str, str, list[str], list[dict]]:
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
    overlays = safe_paths(site.get("overlay_paths"), "site overlay")
    components = data.get("components", [])
    if not isinstance(components, list):
        raise ValueError("components must be an array of tables")
    ids: set[str] = set()
    destinations = set(overlays)
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("component entry must be a table")
        identifier = component.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", identifier):
            raise ValueError(f"invalid component id: {identifier!r}")
        if identifier in ids:
            raise ValueError(f"duplicate component id: {identifier}")
        ids.add(identifier)
        if component.get("state") not in ("planned", "active"):
            raise ValueError(f"invalid component state: {identifier}")
        if not isinstance(component.get("url"), str) or not component["url"]:
            raise ValueError(f"component URL required: {identifier}")
        paths = safe_paths(component.get("paths"), f"component {identifier}")
        if destinations.intersection(paths):
            raise ValueError(f"component paths conflict with another owner: {identifier}")
        destinations.update(paths)
        component_commit = component.get("commit")
        if component["state"] == "active":
            if not isinstance(component_commit, str) or not SHA.fullmatch(component_commit):
                raise ValueError(f"active component requires full commit SHA: {identifier}")
        elif component_commit is not None:
            raise ValueError(f"planned component must not have a commit: {identifier}")
    return url, commit, overlays, components


def verify_source(checkout: Path, url: str, commit: str, label: str = "Sagan") -> None:
    if not checkout.is_dir() or checkout.is_symlink():
        raise ValueError(f"{label} source checkout is missing or unsafe")
    top = Path(git(checkout, "rev-parse", "--show-toplevel")).resolve()
    if top != checkout.resolve():
        raise ValueError(f"{label} source path is inside a different Git checkout")
    if git(checkout, "remote", "get-url", "origin") != url:
        raise ValueError(f"{label} source origin differs from docs-sources.lock")
    if git(checkout, "rev-parse", "HEAD") != commit:
        raise ValueError(f"{label} source HEAD differs from docs-sources.lock")
    if git(checkout, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError(f"{label} source checkout is dirty")
    if not (checkout / "docs").is_dir():
        raise ValueError(f"{label} source has no docs directory")


def assemble(root: Path, lock_path: Path, checkout: Path, output: Path,
             component_checkouts: dict[str, Path] | None = None) -> None:
    url, commit, overlays, components = read_lock(lock_path)
    component_checkouts = component_checkouts or {}
    verify_source(checkout, url, commit)
    active = {entry["id"]: entry for entry in components if entry["state"] == "active"}
    if set(component_checkouts) != set(active):
        raise ValueError("component checkouts must match active docs-sources.lock entries exactly")
    for identifier, entry in active.items():
        source = component_checkouts[identifier]
        verify_source(source, entry["url"], entry["commit"], identifier)
        owned_paths = sorted(path.relative_to(source / "docs").as_posix()
                             for path in (source / "docs").rglob("*") if path.is_file())
        if owned_paths != sorted(entry["paths"]):
            raise ValueError(f"{identifier} docs differ from exact locked paths")
        if any(path.is_symlink() for path in (source / "docs").rglob("*")):
            raise ValueError(f"{identifier} docs contain a symlink")
        if output == source or output.is_relative_to(source):
            raise ValueError(f"assembled output must not be inside {identifier} checkout")
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
        for identifier, entry in sorted(active.items()):
            source = component_checkouts[identifier]
            for relative in entry["paths"]:
                destination = stage / "docs" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source / "docs" / relative, destination)
        shutil.copy2(root / "mkdocs.yml", stage / "mkdocs.yml")
        (stage / "scripts").mkdir()
        for hook in HOOKS:
            shutil.copy2(root / "scripts" / hook, stage / "scripts" / hook)
        (stage / "sources.json").write_text(
            json.dumps({"sagan_url": url, "sagan_commit": commit,
                        "site_overlay_paths": overlays,
                        "components": [{"id": identifier, "url": entry["url"],
                                        "commit": entry["commit"], "paths": entry["paths"]}
                                       for identifier, entry in sorted(active.items())]}, indent=2) + "\n",
            encoding="utf-8",
        )
        stage.rename(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sagan", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=ROOT / "docs-sources.lock")
    parser.add_argument("--component", action="append", default=[], metavar="ID=CHECKOUT")
    args = parser.parse_args()
    try:
        if args.source_root is not None:
            if args.sagan is not None or args.component:
                raise ValueError("--source-root cannot be combined with --sagan or --component")
            source_root = args.source_root.absolute()
            _, _, _, entries = read_lock(args.lock)
            sagan_checkout = source_root / "sagan"
            component_checkouts = {
                entry["id"]: source_root / entry["id"]
                for entry in entries if entry["state"] == "active"
            }
        else:
            if args.sagan is None:
                raise ValueError("provide --source-root or --sagan")
            sagan_checkout = args.sagan.absolute()
            component_checkouts = {}
            for item in args.component:
                identifier, separator, path = item.partition("=")
                if not separator or not identifier or not path or identifier in component_checkouts:
                    raise ValueError(f"invalid or duplicate --component: {item!r}")
                component_checkouts[identifier] = Path(path).absolute()
        assemble(ROOT, args.lock, sagan_checkout, args.output.absolute(),
                 component_checkouts)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"Documentation assembly failed: {error}", file=sys.stderr)
        return 1
    print(f"Documentation assembled at {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
