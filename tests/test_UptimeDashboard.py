import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from glwa.dashboard.DashboardBuilder import DashboardBuilder
from glwa.dashboard.DashboardLoader import DashboardLoader
from glwa.time.SriLankaTime import SriLankaTime


def _audit(host):
    return {
        "url": f"https://{host}/",
        "normalized_url": f"https://{host}/",
        "completed_at": "2026-09-05T10:00:00+05:30",
        "levels": [
            {"level": 0, "status": "pass", "reason": "Baseline", "checks": []},
            {
                "level": 1,
                "status": "pass",
                "reason": "All good",
                "checks": [
                    {"name": "dns_resolves", "status": "pass", "reason": "ok"}
                ],
            },
        ],
        "evidence": [],
    }


def _history(host, root, statuses=("up", "up", "down", "up")):
    now = SriLankaTime.now()
    folder = root / host
    folder.mkdir(parents=True)
    with (folder / "checks.jsonl").open("w", encoding="utf-8") as handle:
        for offset, status in enumerate(statuses):
            at = now - timedelta(days=len(statuses) - offset)
            handle.write(json.dumps({
                "host": host,
                "checked_at": at.isoformat(),
                "status": status,
                "reason": status,
            }) + "\n")


class TestUptimeDashboard(unittest.TestCase):
    def _roots(self, folder):
        reports = Path(folder) / "reports"
        uptime = Path(folder) / "uptime_history"
        host = "a.gov.lk"
        target = reports / host
        target.mkdir(parents=True)
        (target / "audit.json").write_text(
            json.dumps(_audit(host)), encoding="utf-8"
        )
        _history(host, uptime)
        return reports, uptime

    def test_loader_attaches_uptime_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            reports, uptime = self._roots(folder)
            sites, errors = DashboardLoader().load(reports, None, uptime)
            self.assertEqual([], errors)
            summary = sites[0]["uptime"]
            self.assertEqual("up", summary["status"])
            self.assertEqual(75.0, summary["last_30_days"]["uptime_pct"])
            self.assertEqual(1, summary["last_30_days"]["outages"])
            self.assertEqual(4, len(summary["history"]))

    def test_loader_without_history_is_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = Path(folder) / "reports"
            target = reports / "a.gov.lk"
            target.mkdir(parents=True)
            (target / "audit.json").write_text(
                json.dumps(_audit("a.gov.lk")), encoding="utf-8"
            )
            sites, _ = DashboardLoader().load(
                reports, None, Path(folder) / "missing"
            )
            self.assertEqual("unknown", sites[0]["uptime"]["status"])

    def test_index_and_detail_show_uptime(self):
        with tempfile.TemporaryDirectory() as folder:
            reports, uptime = self._roots(folder)
            directory = Path(folder) / "websites.json"
            directory.write_text(
                json.dumps(
                    {"Depts": {"Ministry of Test": {"A": "https://a.gov.lk/"}}}
                ),
                encoding="utf-8",
            )
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, directory, uptime)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Uptime", index)
            self.assertIn("data-uptime", index)
            self.assertIn("75.0%", index)
            self.assertIn('colspan="7"', index)
            detail = (output / "sites" / "a.gov.lk" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("Uptime history", detail)
            self.assertIn("up-chart", detail)
            self.assertIn("up-bar down", detail)
            data = json.loads(
                (output / "data.json").read_text(encoding="utf-8")
            )
            self.assertIn("uptime", data["sites"][0])
            self.assertEqual("1.1.0", data["schema_version"])

    def test_index_hides_uptime_without_any_history(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = Path(folder) / "reports"
            target = reports / "a.gov.lk"
            target.mkdir(parents=True)
            (target / "audit.json").write_text(
                json.dumps(_audit("a.gov.lk")), encoding="utf-8"
            )
            output = Path(folder) / "site"
            DashboardBuilder().build(
                reports, output, None, Path(folder) / "missing"
            )
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("Uptime", index)
            self.assertNotIn("data-uptime", index)
            detail = (output / "sites" / "a.gov.lk" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("Uptime history", detail)
            self.assertNotIn("Uptime (30d)", detail)

    def test_mixed_histories_show_column_with_gap(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = Path(folder) / "reports"
            uptime = Path(folder) / "uptime_history"
            for host in ("a.gov.lk", "b.gov.lk"):
                target = reports / host
                target.mkdir(parents=True)
                (target / "audit.json").write_text(
                    json.dumps(_audit(host)), encoding="utf-8"
                )
            _history("a.gov.lk", uptime)
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None, uptime)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Uptime", index)
            self.assertIn("No data yet", index)

    def test_bar_tooltips_carry_check_detail(self):
        with tempfile.TemporaryDirectory() as folder:
            reports, uptime = self._roots(folder)
            host = "a.gov.lk"
            with (uptime / host / "checks.jsonl").open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "host": host,
                    "checked_at": SriLankaTime.now().isoformat(),
                    "status": "down",
                    "reason": "Server errors: HTTP 503",
                }) + "\n")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None, uptime)
            detail = (output / "sites" / host / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("Server errors: HTTP 503", detail)


if __name__ == "__main__":
    unittest.main()
