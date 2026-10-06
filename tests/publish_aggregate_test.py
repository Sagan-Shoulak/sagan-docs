"""Offline rehearsal of the exact command shape used to publish an aggregate."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


def run(*arguments: str, cwd: Path) -> str:
    environment = os.environ.copy()
    environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment["PATH"]
    result = subprocess.run(
        arguments, cwd=cwd, text=True, capture_output=True, check=False, env=environment
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(arguments)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


class PublishAggregateTest(unittest.TestCase):
    def test_publishes_public_provenance_and_default_redirect(self) -> None:
        executable = "mike.exe" if sys.platform == "win32" else "mike"
        discovered = shutil.which(executable)
        candidates = (
            Path(discovered) if discovered else Path("missing"),
            Path(sys.executable).with_name(executable),
            Path(sys.executable).parent / "Scripts" / executable,
        )
        mike = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
        self.assertTrue(mike.is_file(), f"mike executable missing beside {sys.executable}")
        with tempfile.TemporaryDirectory(prefix="sagan-docs-publish-test-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            remote = root / "remote.git"
            repository.mkdir()
            run("git", "init", "--bare", str(remote), cwd=root)
            run("git", "init", "-b", "dev", cwd=repository)
            run("git", "config", "user.name", "Sagan Test", cwd=repository)
            run("git", "config", "user.email", "test@example.invalid", cwd=repository)
            docs = repository / "assembled" / "docs"
            docs.mkdir(parents=True)
            (docs / "index.md").write_text("# Exact aggregate\n", encoding="utf-8")
            (docs / "sources.json").write_text(
                '{"sagan_commit":"1111111111111111111111111111111111111111"}\n',
                encoding="utf-8",
            )
            config = repository / "assembled" / "mkdocs.yml"
            config.write_text(
                "site_name: Test\n"
                "docs_dir: docs\n"
                "site_dir: build/docs-site\n"
                "plugins:\n"
                "  - mike\n",
                encoding="utf-8",
            )
            run("git", "add", "assembled", cwd=repository)
            run("git", "commit", "-m", "fixture", cwd=repository)
            run("git", "remote", "add", "origin", str(remote), cwd=repository)
            run(
                str(mike), "deploy",
                "--config-file", "assembled/mkdocs.yml",
                "--branch", "docs-site", "--push", "--update-aliases", "experimental",
                cwd=repository,
            )
            run(
                str(mike), "set-default",
                "--config-file", "assembled/mkdocs.yml",
                "--branch", "docs-site", "--push", "experimental",
                cwd=repository,
            )
            provenance = run(
                "git", f"--git-dir={remote}", "show",
                "docs-site:experimental/sources.json", cwd=root,
            )
            redirect = run(
                "git", f"--git-dir={remote}", "show", "docs-site:index.html", cwd=root,
            )
            self.assertIn("1111111111111111111111111111111111111111", provenance)
            self.assertIn("experimental", redirect)


if __name__ == "__main__":
    unittest.main()
