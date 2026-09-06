import json
import re
import tempfile
import unittest
from pathlib import Path

from glwa.dashboard.DashboardBuilder import DashboardBuilder


def _audit(host, ministry=""):
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
            {
                "level": 2,
                "status": "inconclusive",
                "reason": "No address",
                "checks": [],
            },
        ],
        "evidence": [
            {
                "check": "dns",
                "status": "pass",
                "detail": "resolved",
                "source": f"https://{host}/",
            }
        ],
    }


class TestDashboardBuilder(unittest.TestCase):
    def _reports(self, root: Path):
        for host in ("a.gov.lk", "b.gov.lk"):
            folder = root / host
            folder.mkdir(parents=True)
            (folder / "audit.json").write_text(
                json.dumps(_audit(host)), encoding="utf-8"
            )
            (folder / "audit.md").write_text(f"# {host}\n", encoding="utf-8")
            (folder / "evidence.csv").write_text("check\n", encoding="utf-8")
        (root / "broken.gov.lk").mkdir(parents=True)
        (root / "broken.gov.lk" / "audit.json").write_text("{oops", encoding="utf-8")
        return root

    def test_builds_all_pages_and_data(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            result = DashboardBuilder().build(reports, output, None)
            self.assertEqual(2, result["sites"])
            self.assertEqual(1, len(result["errors"]))
            for name in (
                "index.html", "style.css", "app.js", "data.json",
                ".nojekyll", "favicon.svg",
            ):
                self.assertTrue((output / name).is_file(), name)
            for host in ("a.gov.lk", "b.gov.lk"):
                page = output / "sites" / host / "index.html"
                self.assertTrue(page.is_file(), str(page))
                for name in ("audit.json", "audit.md", "evidence.csv"):
                    self.assertTrue(
                        (output / "sites" / host / name).is_file(), name
                    )
            data = json.loads((output / "data.json").read_text(encoding="utf-8"))
            self.assertEqual(2, data["summary"]["total"])
            self.assertEqual(2, len(data["sites"]))
            self.assertIn("schema_version", data)
            self.assertIn("build_time", data)

    def test_data_json_has_schema_version_and_build_time(self):
        output = Path("site")
        if not (output / "data.json").is_file():
            self.skipTest("run the dashboard build first")
        data = json.loads((output / "data.json").read_text(encoding="utf-8"))
        self.assertIn("schema_version", data)
        self.assertIn("build_time", data)
        self.assertTrue(len(data["build_time"]) > 10)

    def test_counts_match_committed_data(self):
        output = Path("site")
        if not (output / "data.json").is_file():
            self.skipTest("run the dashboard build first")
        data = json.loads((output / "data.json").read_text(encoding="utf-8"))
        for site in data["sites"]:
            audit = json.loads(
                Path(f"latest_audit_reports/{site['host']}/audit.json").read_text(
                    encoding="utf-8"
                )
            )
            passed = [
                item["level"]
                for item in audit["levels"]
                if item["status"] == "pass"
            ]
            self.assertEqual(max(passed, default=0), site["level"])

    def test_no_broken_internal_links(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None)
            pages = [output / "index.html", *output.glob("sites/*/index.html")]
            self.assertTrue(pages)
            for page in pages:
                for href in re.findall(r'href="([^"#]+)"', page.read_text()):
                    if href.startswith(("http", "mailto:")):
                        continue
                    target = (page.parent / href).resolve()
                    self.assertTrue(target.exists(), f"{page} -> {href}")
                    target.relative_to(output.resolve())

    def test_index_has_search_icon_and_pagination(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="search-icon"', index)
            self.assertIn('id="pagination"', index)
            self.assertIn('id="page-size"', index)

    def test_detail_has_favicon_link(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None)
            detail = (output / "sites" / "a.gov.lk" / "index.html").read_text()
            self.assertIn('favicon.svg', detail)
            self.assertIn('rel="icon"', detail)

    def test_detail_hides_empty_check_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "reports" / "minimal.gov.lk"
            root.mkdir(parents=True)
            (root / "audit.json").write_text(
                json.dumps(
                    {
                        "url": "https://minimal.gov.lk/",
                        "normalized_url": "https://minimal.gov.lk/",
                        "completed_at": "2026-09-05T10:00:00+05:30",
                        "levels": [
                            {"level": 0, "status": "pass", "reason": "Baseline", "checks": []},
                            {"level": 1, "status": "fail", "reason": "down", "checks": []},
                        ],
                        "evidence": [],
                    }
                ),
                encoding="utf-8",
            )
            output = Path(folder) / "site"
            DashboardBuilder().build(Path(folder) / "reports", output, None)
            detail = (output / "sites" / "minimal.gov.lk" / "index.html").read_text()
            self.assertNotIn("Level 0 checks", detail)
            self.assertNotIn("Level 1 checks", detail)
            self.assertIn("No individual check results recorded.", detail)

    def test_detail_evidence_collapsible(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None)
            detail = (output / "sites" / "a.gov.lk" / "index.html").read_text()
            self.assertIn('class="collapsible"', detail)
            self.assertIn('aria-expanded="false"', detail)
            self.assertIn('collapsible-content', detail)

    def test_print_styles_present(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None)
            css = (output / "style.css").read_text(encoding="utf-8")
            self.assertIn("@media print", css)

    def test_group_heading_rendered_when_ministry_data_present(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "reports"
            for host in ("x.gov.lk", "y.gov.lk"):
                d = root / host
                d.mkdir(parents=True)
                (d / "audit.json").write_text(
                    json.dumps(_audit(host)), encoding="utf-8"
                )
            directory = Path(folder) / "websites.json"
            directory.write_text(
                json.dumps(
                    {
                        "Depts": {
                            "Ministry of Test": {
                                "X": "https://x.gov.lk/",
                                "Y": "https://y.gov.lk/",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            output = Path(folder) / "site"
            DashboardBuilder().build(root, output, directory)
            index = (output / "index.html").read_text()
            self.assertIn("Ministry of Test", index)
            self.assertIn("group-heading", index)

    def test_no_group_heading_without_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = self._reports(Path(folder) / "reports")
            output = Path(folder) / "site"
            DashboardBuilder().build(reports, output, None)
            index = (output / "index.html").read_text()
            self.assertNotIn("group-heading", index)


if __name__ == "__main__":
    unittest.main()
