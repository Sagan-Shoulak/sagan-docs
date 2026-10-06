"""Offline checks for non-production documentation preview evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import docs_preview_evidence  # noqa: E402


class DocsPreviewEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sagan-docs-preview-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.assembled = self.root / "assembled"
        (self.assembled / "docs").mkdir(parents=True)
        (self.assembled / "build" / "docs-site").mkdir(parents=True)
        (self.assembled / "docs" / "index.md").write_text("# Preview\n", encoding="utf-8")
        (self.assembled / "build" / "docs-site" / "index.html").write_text(
            "<h1>Preview</h1>\n", encoding="utf-8"
        )
        (self.assembled / "sources.json").write_text(
            json.dumps({"sagan_commit": "1" * 40}) + "\n", encoding="utf-8"
        )
        self.output = self.root / "evidence.json"

    def test_records_provenance_paths_and_content_hashes(self) -> None:
        evidence = docs_preview_evidence.record(self.assembled, self.output)
        self.assertEqual("1" * 40, evidence["provenance"]["sagan_commit"])
        self.assertEqual(["index.md"], evidence["source_files"])
        self.assertEqual("index.html", evidence["site_files"][0]["path"])
        self.assertEqual(64, len(evidence["site_files"][0]["sha256"]))
        self.assertEqual(evidence, json.loads(self.output.read_text(encoding="utf-8")))

    def test_requires_complete_preview_and_preserves_existing_output(self) -> None:
        (self.assembled / "sources.json").unlink()
        with self.assertRaisesRegex(ValueError, "no sources.json"):
            docs_preview_evidence.record(self.assembled, self.output)
        (self.assembled / "sources.json").write_text("{}\n", encoding="utf-8")
        self.output.write_text("preserve\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            docs_preview_evidence.record(self.assembled, self.output)
        self.assertEqual("preserve\n", self.output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
