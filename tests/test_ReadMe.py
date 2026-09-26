import json
import tempfile
import unittest
from pathlib import Path

from glwa.reporting.ReadMe import ReadMe


class TestReadMe(unittest.TestCase):
    def test_adds_project_header(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "README.md"
            content = ReadMe(target).update().read_text(encoding="utf-8")
            self.assertIn("# Grading Government Websites (`glwa`)", content)
            self.assertIn("img.shields.io/github/license", content)
            self.assertIn("img.shields.io/badge/author-nuuuwan", content)
            self.assertIn("https://github.com/prdai", content)
            self.assertIn("https://github.com/dushmilan", content)
            self.assertIn("img.shields.io/badge/last_updated-", content)
            self.assertNotIn("github/last-commit", content)
            self.assertIn(
                "Only `⚫ Level 0`, `🔴 Level 1`, `🟠 Level 2`, and "
                "`🟢 Level 3` are implemented",
                content,
            )
            self.assertIn("## Levels and scoring", content)
            self.assertNotIn("## `🔵 Level 4`", content)
            self.assertIn("passing checks divided by total checks", content)
            self.assertIn('"🟠 Level 2" :', content)
            self.assertIn("🇱🇰", content)

    def test_adds_latest_audit_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "README.md"
            audit_folder = root / "latest_audit_reports" / "example.gov.lk"
            audit_folder.mkdir(parents=True)
            audit = {
                "normalized_url": "https://example.gov.lk/",
                "completed_at": "2026-09-01T10:00:00+00:00",
                "result": {"status": "inconclusive", "confidence": 0.7},
                "levels": [
                    {
                        "level": level,
                        "status": "pass" if level < 2 else "fail",
                    }
                    for level in range(6)
                ],
            }
            path = audit_folder / "audit.json"
            path.write_text(json.dumps(audit), encoding="utf-8")
            report_path = audit_folder / "audit.md"
            report_path.write_text("latest report", encoding="utf-8")
            ReadMe(target).update(root / "latest_audit_reports")
            content = target.read_text(encoding="utf-8")
            self.assertIn(
                "| 0.0/3 | [https://example.gov.lk/]"
                "(latest_audit_reports/example.gov.lk/audit.md)",
                content,
            )
            self.assertNotIn("## Classification rules", content)

    def test_adds_documentation_links(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "README.md"
            content = ReadMe(target).update().read_text(encoding="utf-8")
            self.assertIn("## Documentation", content)
            self.assertIn("[Article](docs/article.md)", content)
            self.assertIn("[Design](docs/design.md)", content)
            self.assertIn("[Roadmap](docs/roadmap.md)", content)

    def test_groups_by_highest_passed_level(self):
        audit = {
            "levels": [
                {"level": 0, "status": "pass"},
                {"level": 1, "status": "pass"},
                {"level": 2, "status": "inconclusive"},
            ]
        }
        self.assertEqual(1, ReadMe()._level(audit))

    def test_converts_legacy_level_zero_results(self):
        read_me = ReadMe()
        audit = {
            "result": {"status": "level_0_confirmed", "confidence": 0.98}
        }
        self.assertEqual(["pass", "fail"], read_me._statuses(audit)[:2])


if __name__ == "__main__":
    unittest.main()
