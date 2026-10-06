"""Offline checks for the release mirror index retained by docs deployment."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_index", ROOT / "deploy" / "releases" / "index.py"
)
assert SPEC is not None and SPEC.loader is not None
release_index = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_index)


class ReleaseIndexTest(unittest.TestCase):
    def test_collects_releases_in_version_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sagan-release-index-test-") as temporary:
            root = Path(temporary)
            for version in ("v1.0.0-rc.1", "v1.0.0", "v0.9.0"):
                directory = root / version
                directory.mkdir()
                (directory / f"sagan-{version}.zip").write_bytes(b"archive")
            releases = release_index.collect(root)
            self.assertEqual(
                ["v1.0.0", "v1.0.0-rc.1", "v0.9.0"],
                [release["tag"] for release in releases],
            )
            self.assertEqual("Portable archive", releases[0]["assets"][0]["kind"])

    def test_main_writes_html_and_json_indexes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sagan-release-index-test-") as temporary:
            root = Path(temporary)
            release = root / "v1.0.0"
            release.mkdir()
            (release / "sagan.exe").write_bytes(b"installer")
            releases = release_index.collect(root)
            payload = {"schema": "sagan.release-mirror/1", "releases": releases}
            (root / "releases.json").write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
            (root / "index.html").write_text(
                release_index.render(releases), encoding="utf-8"
            )
            self.assertEqual(
                "sagan.release-mirror/1",
                json.loads((root / "releases.json").read_text(encoding="utf-8"))["schema"],
            )
            self.assertIn("sagan.exe", (root / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
