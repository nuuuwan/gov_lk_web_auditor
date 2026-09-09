import tempfile
import unittest
from pathlib import Path

from glwa import Audit, Classification, Evidence
from glwa.classification.LevelEvaluator import LevelEvaluator
from glwa.reporting.ReportWriter import ReportWriter


class TestReportWriter(unittest.TestCase):
    def test_validates_and_writes_all_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = ReportWriter().write(self._audit(), Path(folder))
            self.assertEqual(5, len(paths))
            self.assertTrue(all(path.exists() for path in paths))
            report = (Path(folder) / "report.html").read_text("utf-8")
            self.assertIn("https://example.gov.lk/", report)
            self.assertIn("2026-09-01T15:30:00+05:30", report)
            self.assertIn("Level 0", report)
            self.assertTrue((Path(folder) / "levels.csv").exists())
            markdown = (Path(folder) / "audit.md").read_text("utf-8")
            self.assertIn("- Completed: 2026-09-01 15:30", markdown)
            self.assertIn("- Overall result: 🔴 Level 1", markdown)
            self.assertIn("## ⚫ Level 0: ✅", markdown)
            self.assertIn("| dns_resolves | ✅ |", markdown)
            evidence = (Path(folder) / "evidence.csv").read_text("utf-8")
            self.assertIn("2026-09-01T15:30:00+05:30", evidence)

    def _audit(self):
        timestamp = "2026-09-01T10:00:00+00:00"
        return Audit(
            "1.3.0",
            "123e4567-e89b-42d3-a456-426614174000",
            "example.gov.lk",
            "https://example.gov.lk/",
            timestamp,
            timestamp,
            Classification("pass", 1.0, ["All Level 1 checks passed"]),
            [
                Evidence(
                    "https",
                    "pass",
                    "HTTPS returned 200",
                    observed_at=timestamp,
                )
            ],
            [],
            [],
            [],
            LevelEvaluator().evaluate(
                [
                    Evidence("dns", "pass", "DNS resolved"),
                    Evidence(
                        "domain_registration", "pass", "Domain registered"
                    ),
                    Evidence("tls", "pass", "TLS valid"),
                    Evidence("http", "pass", "HTTP available"),
                ]
            ),
            {
                "egress_ip": "192.248.41.11",
                "country": "LK",
                "runner": "local",
                "proxy": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
