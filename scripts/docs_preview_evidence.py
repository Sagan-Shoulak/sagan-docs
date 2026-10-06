"""Record reproducible evidence for a non-production exact-lock docs preview."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record(assembled: Path, output: Path) -> dict:
    provenance_path = assembled / "sources.json"
    docs_path = assembled / "docs"
    site_path = assembled / "build" / "docs-site"
    if not provenance_path.is_file():
        raise ValueError("assembled preview has no sources.json provenance")
    if not docs_path.is_dir() or not site_path.is_dir():
        raise ValueError("assembled preview must contain source docs and a built site")
    if output.exists() or output.is_symlink():
        raise ValueError(f"evidence output already exists: {output}")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    source_files = sorted(
        path.relative_to(docs_path).as_posix()
        for path in docs_path.rglob("*") if path.is_file()
    )
    site_files = sorted(
        (
            {
                "path": path.relative_to(site_path).as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in site_path.rglob("*") if path.is_file()
        ),
        key=lambda entry: entry["path"],
    )
    evidence = {
        "schema_version": 1,
        "provenance": provenance,
        "source_file_count": len(source_files),
        "source_files": source_files,
        "site_file_count": len(site_files),
        "site_files": site_files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembled", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = record(args.assembled.resolve(), args.output.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Preview evidence failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Recorded {evidence['source_file_count']} source files and "
        f"{evidence['site_file_count']} built files in {args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
