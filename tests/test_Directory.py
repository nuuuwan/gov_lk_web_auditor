import json
import tempfile
import unittest
from pathlib import Path

from glwa import Directory


class TestDirectory(unittest.TestCase):
    def test_returns_unique_urls_in_json_order(self):
        websites = {
            "Category 1": {
                "Category 2": {
                    "One": "https://one.gov.lk",
                    "Two": "https://two.gov.lk",
                },
                "Other": {"Duplicate": "https://one.gov.lk"},
            }
        }
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "websites.json"
            source.write_text(json.dumps(websites), encoding="utf-8")
            self.assertEqual(
                ["https://one.gov.lk", "https://two.gov.lk"],
                Directory(source).urls(),
            )

    def test_committed_directory_has_no_schemeless_urls(self):
        source = Directory().source
        websites = json.loads(source.read_text(encoding="utf-8"))
        bare = sorted(
            value
            for value in self._leaves(websites)
            if isinstance(value, str) and not value.startswith("http")
        )
        self.assertEqual([], bare)

    def _leaves(self, item):
        if isinstance(item, dict):
            for value in item.values():
                yield from self._leaves(value)
            return
        if isinstance(item, list):
            for value in item:
                yield from self._leaves(value)
            return
        yield item

    def test_prepends_https_to_schemeless_hosts(self):
        websites = {
            "Category 1": {
                "Institute of Sports Medicine": "www.ism.gov.lk",
            }
        }
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "websites.json"
            source.write_text(json.dumps(websites), encoding="utf-8")
            self.assertEqual(
                ["https://www.ism.gov.lk"],
                Directory(source).urls(),
            )


if __name__ == "__main__":
    unittest.main()
