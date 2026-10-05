"""Offline checks for exact-source documentation assembly."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import assemble_docs  # noqa: E402


def git(checkout: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


class AssembleDocsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sagan-docs-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "-b", "dev")
        (self.source / "docs").mkdir()
        (self.source / "docs" / "index.md").write_text("# Pinned source\n", encoding="utf-8")
        git(self.source, "add", "docs/index.md")
        git(self.source, "-c", "commit.gpgsign=false", "-c", "user.name=Sagan Test",
            "-c", "user.email=test@example.invalid", "commit", "-m", "Docs fixture")
        self.commit = git(self.source, "rev-parse", "HEAD")
        self.url = "https://example.invalid/sagan.git"
        git(self.source, "remote", "add", "origin", self.url)
        self.lock = self.root / "docs-sources.lock"
        self.overlays = assemble_docs.read_lock(ROOT / "docs-sources.lock")[2]
        self.write_lock()
        self.output = self.root / "assembled"

    def write_lock(self, *, commit: str | None = None, overlays: list[str] | None = None) -> None:
        self.lock.write_text(
            "schema_version = 1\n"
            "[sagan]\n"
            f'url = "{self.url}"\n'
            f'commit = "{commit or self.commit}"\n'
            "[site]\n"
            f"overlay_paths = {json.dumps(overlays if overlays is not None else self.overlays)}\n",
            encoding="utf-8",
        )

    def test_assembles_source_site_overlay_and_provenance(self) -> None:
        assemble_docs.assemble(ROOT, self.lock, self.source, self.output)
        self.assertEqual("# Pinned source\n",
                         (self.output / "docs" / "index.md").read_text(encoding="utf-8"))
        overlay = "contributing/documentation.md"
        self.assertEqual((ROOT / "docs" / overlay).read_bytes(),
                         (self.output / "docs" / overlay).read_bytes())
        self.assertTrue((self.output / "mkdocs.yml").is_file())
        self.assertTrue((self.output / "scripts" / "docs_status.py").is_file())
        provenance = json.loads((self.output / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual(self.commit, provenance["sagan_commit"])

    def test_existing_output_is_never_overwritten(self) -> None:
        self.output.mkdir()
        (self.output / "my-work.txt").write_text("preserve\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            assemble_docs.assemble(ROOT, self.lock, self.source, self.output)
        self.assertEqual("preserve\n", (self.output / "my-work.txt").read_text(encoding="utf-8"))

    def test_output_must_not_modify_the_source_checkout(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be inside the Sagan source"):
            assemble_docs.assemble(
                ROOT, self.lock, self.source, self.source / "docs" / "generated"
            )
        self.assertFalse((self.source / "docs" / "generated").exists())

    def test_source_must_match_pin_and_be_clean(self) -> None:
        self.write_lock(commit="1" * 40)
        with self.assertRaisesRegex(ValueError, "HEAD differs"):
            assemble_docs.assemble(ROOT, self.lock, self.source, self.output)
        self.write_lock()
        (self.source / "untracked.txt").write_text("local work\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "dirty"):
            assemble_docs.assemble(ROOT, self.lock, self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_overlay_set_is_exact_and_paths_are_safe(self) -> None:
        self.write_lock(overlays=["contributing/documentation.md"])
        with self.assertRaisesRegex(ValueError, "site-owned docs differ"):
            assemble_docs.assemble(ROOT, self.lock, self.source, self.output)
        self.write_lock(overlays=["../outside.md"])
        with self.assertRaisesRegex(ValueError, "unsafe site overlay path"):
            assemble_docs.read_lock(self.lock)


if __name__ == "__main__":
    unittest.main()
