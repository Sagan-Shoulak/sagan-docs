"""Offline tests for exact-revision documentation source bootstrap."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bootstrap_docs_sources  # noqa: E402
import assemble_docs  # noqa: E402


def git(*arguments: str, cwd: Path) -> str:
    result = subprocess.run(["git", *arguments], cwd=cwd, text=True,
                            capture_output=True, check=True)
    return result.stdout.strip()


class BootstrapDocsSourcesTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="sagan-docs-bootstrap-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sources = self.root / "sources"
        self.lock = self.root / "docs-sources.lock"
        self.sagan_url, self.sagan_commit = self.create_repo(
            "sagan", "index.md", "# Sagan fixture\n"
        )
        self.physics_url, self.physics_commit = self.create_repo(
            "physics", "standard-library/physics.md", "# Physics fixture\n"
        )
        self.write_lock()

    def create_repo(self, name: str, path: str, content: str) -> tuple[str, str]:
        checkout = self.root / f"{name}-source"
        checkout.mkdir()
        git("init", "-b", "dev", cwd=checkout)
        document = checkout / "docs" / path
        document.parent.mkdir(parents=True)
        document.write_text(content, encoding="utf-8")
        git("add", "docs", cwd=checkout)
        git("-c", "commit.gpgsign=false", "-c", "user.name=Sagan Test",
            "-c", "user.email=test@example.invalid", "commit", "-m", "Fixture", cwd=checkout)
        commit = git("rev-parse", "HEAD", cwd=checkout)
        bare = self.root / f"{name}.git"
        git("clone", "--bare", str(checkout), str(bare), cwd=self.root)
        return bare.as_posix(), commit

    def write_lock(self, *, physics_state: str = "active") -> None:
        overlays = assemble_docs.read_lock(ROOT / "docs-sources.lock")[2]
        physics_commit = f'commit = "{self.physics_commit}"\n' if physics_state == "active" else ""
        self.lock.write_text(
            "schema_version = 1\n"
            "[sagan]\n"
            f'url = "{self.sagan_url}"\n'
            f'commit = "{self.sagan_commit}"\n'
            "[site]\n"
            f"overlay_paths = {json.dumps(overlays)}\n"
            "[[components]]\n"
            'id = "sagan-physics"\n'
            f'state = "{physics_state}"\n'
            f'url = "{self.physics_url}"\n'
            f"{physics_commit}"
            'paths = ["standard-library/physics.md"]\n',
            encoding="utf-8",
        )

    def test_bootstrap_clones_only_active_pins_and_is_idempotent(self) -> None:
        self.assertEqual(["sagan", "sagan-physics"],
                         bootstrap_docs_sources.bootstrap(self.lock, self.sources))
        self.assertEqual(self.sagan_commit,
                         git("rev-parse", "HEAD", cwd=self.sources / "sagan"))
        self.assertEqual(self.physics_commit,
                         git("rev-parse", "HEAD", cwd=self.sources / "sagan-physics"))
        self.assertEqual(["sagan", "sagan-physics"],
                         bootstrap_docs_sources.bootstrap(self.lock, self.sources))

    def test_dirty_or_wrong_origin_is_preserved(self) -> None:
        bootstrap_docs_sources.bootstrap(self.lock, self.sources)
        document = self.sources / "sagan-physics" / "docs" / "local.md"
        document.write_text("preserve me\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "dirty"):
            bootstrap_docs_sources.bootstrap(self.lock, self.sources)
        self.assertTrue(document.is_file())
        document.unlink()
        git("remote", "set-url", "origin", "https://example.invalid/wrong.git",
            cwd=self.sources / "sagan-physics")
        with self.assertRaisesRegex(ValueError, "origin differs"):
            bootstrap_docs_sources.bootstrap(self.lock, self.sources)

    def test_planned_component_is_not_cloned(self) -> None:
        self.write_lock(physics_state="planned")
        self.assertEqual(["sagan"], bootstrap_docs_sources.bootstrap(self.lock, self.sources))
        self.assertFalse((self.sources / "sagan-physics").exists())

    def test_source_root_can_be_assembled(self) -> None:
        bootstrap_docs_sources.bootstrap(self.lock, self.sources)
        output = self.root / "assembled"
        assemble_docs.assemble(ROOT, self.lock, self.sources / "sagan", output,
                               {"sagan-physics": self.sources / "sagan-physics"})
        self.assertEqual("# Physics fixture\n",
                         (output / "docs" / "standard-library" / "physics.md")
                         .read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
