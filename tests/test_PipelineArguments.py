import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from workflows.pipeline import Pipeline


class TestPipelineArguments(unittest.TestCase):
    def test_limits_urls_when_requested(self):
        urls = ["one", "two", "three"]
        self.assertEqual(["one", "two"], Pipeline(2)._limit(urls))

    def test_does_not_limit_urls_by_default(self):
        urls = ["one", "two", "three"]
        self.assertEqual(urls, Pipeline()._limit(urls))

    def test_selects_shard_when_requested(self):
        urls = ["one", "two", "three", "four"]
        self.assertEqual(
            ["three", "four"],
            Pipeline(shard_index=1, shard_total=2)._limit(urls),
        )

    def test_shard_combines_with_max_urls(self):
        urls = ["one", "two", "three", "four"]
        self.assertEqual(
            ["three"],
            Pipeline(
                max_urls=1, shard_index=1, shard_total=2
            )._limit(urls),
        )

    def test_loads_urls_from_json(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "static_data" / "urls.json"
            target.parent.mkdir()
            target.write_text(json.dumps(["one", "two"]), encoding="utf-8")
            with patch.object(Pipeline, "URLS", target):
                self.assertEqual(["one", "two"], Pipeline()._urls())

    def test_prints_highest_passing_level_with_color(self):
        levels = [
            SimpleNamespace(
                level=level,
                status="pass" if level <= 2 else "inconclusive",
            )
            for level in range(6)
        ]
        audit = SimpleNamespace(levels=levels)
        self.assertEqual("🟠 Level 2", Pipeline()._level(audit))

    def test_summarizes_level_and_score(self):
        levels = [
            SimpleNamespace(level=0, status="pass"),
            SimpleNamespace(level=1, status="pass"),
        ]
        data = {
            "levels": [
                {"level": 1, "checks": [{"status": "pass"}]},
            ]
        }
        audit = SimpleNamespace(levels=levels, to_dict=lambda: data)
        self.assertEqual("🔴 Level 1, 1.0/3", Pipeline()._summary(audit))


if __name__ == "__main__":
    unittest.main()
