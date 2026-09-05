import tempfile
import unittest
from pathlib import Path

from glwa.audit.SnapshotRechecker import SnapshotRechecker


class TestSnapshotRechecker(unittest.TestCase):
    def test_rebuilds_page_evidence_and_runs_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.html"
            path.write_text(
                "<address>123 Parliament Road, Colombo 01</address>"
                "<h2>Eligibility</h2>"
                "<p>" + ("Our office serves citizens every weekday. " * 30) + "</p>",
                encoding="utf-8",
            )
            data = self._data(path)
            audit = SnapshotRechecker().run(data)
        checks = {item.check for item in audit.evidence}
        self.assertIn("postal_address", checks)
        self.assertIn("eligibility_criteria", checks)
        self.assertNotIn("service_scope", checks)
        level = audit.levels[2]
        self.assertTrue(level.executed)
        self.assertEqual("pass", level.checks[0].status)

    def _data(self, path):
        return {
            "schema_version": "1.2.0",
            "audit_id": "audit-id",
            "url": "https://example.gov.lk",
            "normalized_url": "https://example.gov.lk/",
            "started_at": "2026-09-01T10:00:00+00:00",
            "completed_at": "2026-09-01T10:01:00+00:00",
            "evidence": [
                {"check": name, "status": "pass", "detail": "Healthy"}
                for name in ("dns", "domain_registration", "tls", "http")
            ]
            + [
                {
                    "check": "service_scope",
                    "status": "review",
                    "detail": "Stale page evidence",
                },
                {
                    "check": "eligibility_criteria",
                    "status": "review",
                    "detail": "Stale Level 3 evidence",
                },
            ],
            "observations": [],
            "snapshots": [
                {"url": "https://example.gov.lk/contact", "path": str(path)}
            ],
            "reviewer_decisions": [],
        }


if __name__ == "__main__":
    unittest.main()
