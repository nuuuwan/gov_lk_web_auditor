import json
import tempfile
import unittest
from pathlib import Path

from glwa.dashboard.DashboardLoader import DashboardLoader


def _audit(levels, **extra):
    audit = {
        "url": "https://example.gov.lk/",
        "normalized_url": "https://example.gov.lk/",
        "completed_at": "2026-09-05T10:00:00+05:30",
        "levels": levels,
        "evidence": [],
    }
    audit.update(extra)
    return audit


def _level(number, status, checks=()):
    return {
        "level": number,
        "status": status,
        "reason": f"level {number} {status}",
        "checks": [
            {"name": name, "status": status, "reason": status}
            for name in checks
        ],
    }


class TestDashboardLoader(unittest.TestCase):
    def _reports(self, folder, audits):
        root = Path(folder)
        for host, audit in audits.items():
            target = root / host
            target.mkdir(parents=True)
            if audit is not None:
                (target / "audit.json").write_text(
                    audit if isinstance(audit, str) else json.dumps(audit),
                    encoding="utf-8",
                )
        return root

    def test_loads_sites_with_level_score_and_host(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._reports(
                folder,
                {
                    "a.gov.lk": _audit(
                        [
                            _level(0, "pass"),
                            _level(1, "pass", ["dns_resolves"]),
                            _level(2, "fail", ["postal_address"]),
                        ]
                    )
                },
            )
            sites, errors = DashboardLoader().load(root)
            self.assertEqual([], errors)
            self.assertEqual(1, len(sites))
            self.assertEqual("a.gov.lk", sites[0]["host"])
            self.assertEqual(1, sites[0]["level"])
            self.assertEqual(1.0, sites[0]["score"])
            self.assertEqual("attention", sites[0]["status_group"])
            self.assertIn("ministry", sites[0])

    def test_skips_malformed_reports_without_breaking_build(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._reports(
                folder,
                {
                    "good.gov.lk": _audit([_level(0, "pass")]),
                    "bad.gov.lk": "{not json",
                    "empty.gov.lk": {"url": "https://empty.gov.lk/"},
                },
            )
            sites, errors = DashboardLoader().load(root)
            self.assertEqual(["good.gov.lk"], [site["host"] for site in sites])
            self.assertEqual(
                {"bad.gov.lk", "empty.gov.lk"},
                {item["host"] for item in errors},
            )

    def test_resolves_institution_from_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "reports"
            host = root / "daph.gov.lk"
            host.mkdir(parents=True)
            (host / "audit.json").write_text(
                json.dumps(
                    _audit(
                        [_level(0, "pass")],
                        url="https://daph.gov.lk/",
                        normalized_url="https://daph.gov.lk/",
                    )
                ),
                encoding="utf-8",
            )
            directory = Path(folder) / "websites.json"
            directory.write_text(
                json.dumps({"Group": {"Dept of Health": "https://daph.gov.lk/"}}),
                encoding="utf-8",
            )
            sites, _ = DashboardLoader().load(root, directory)
            self.assertEqual("Dept of Health", sites[0]["institution"])

    def test_falls_back_to_host_without_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self._reports(folder, {"solo.gov.lk": _audit([_level(0, "pass")])})
            sites, _ = DashboardLoader().load(root)
            self.assertEqual("solo.gov.lk", sites[0]["institution"])

    def test_resolves_ministry_from_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "reports"
            host = root / "daph.gov.lk"
            host.mkdir(parents=True)
            (host / "audit.json").write_text(
                json.dumps(
                    _audit(
                        [_level(0, "pass")],
                        url="https://daph.gov.lk/",
                        normalized_url="https://daph.gov.lk/",
                    )
                ),
                encoding="utf-8",
            )
            directory = Path(folder) / "websites.json"
            directory.write_text(
                json.dumps(
                    {
                        "Depts": {
                            "Minister of Health": {
                                "Dept of Health": "https://daph.gov.lk/"
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            sites, _ = DashboardLoader().load(root, directory)
            self.assertEqual("Minister of Health", sites[0]["ministry"])

    def test_groups_sorted_by_ministry_then_level(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "reports"
            for host, levels in [
                ("a.gov.lk", [_level(0, "pass")]),
                ("b.gov.lk", [_level(1, "pass", ["dns"])]),
            ]:
                d = root / host
                d.mkdir(parents=True)
                (d / "audit.json").write_text(
                    json.dumps(_audit(levels, url=f"https://{host}/")), encoding="utf-8"
                )
            directory = Path(folder) / "websites.json"
            directory.write_text(
                json.dumps(
                    {
                        "Depts": {
                            "Min Z": {"A": "https://a.gov.lk/"},
                            "Min A": {"B": "https://b.gov.lk/"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            sites, _ = DashboardLoader().load(root, directory)
            self.assertEqual("Min A", sites[0]["ministry"])
            self.assertEqual("Min Z", sites[1]["ministry"])


if __name__ == "__main__":
    unittest.main()
