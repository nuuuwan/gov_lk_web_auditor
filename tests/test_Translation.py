import tempfile
import unittest
from pathlib import Path

from glwa.translation.Coverage import CoverageCalculator
from glwa.translation.FlowStore import FlowStore
from glwa.translation.Provenance import classify
from glwa.translation.OpenAIFlowDiscovery import OpenAIFlowDiscovery


class TestTranslation(unittest.TestCase):
    def test_calculates_script_coverage_for_sinhala(self):
        result = CoverageCalculator().calculate("සිංහල පුවත් English", "si")

        self.assertEqual("si", result.language)
        self.assertGreater(result.percentage, 50)
        self.assertTrue(result.translated)

    def test_uses_unknown_when_no_translation_provenance_is_observed(self):
        result = classify(
            ["https://example.gov.lk/app.js", "https://cdn.example.net/a.js"],
            "https://example.gov.lk/",
        )

        self.assertEqual("unknown", result["type"])
        self.assertEqual([], result["translation_candidates"])

    def test_detects_known_dynamic_provider(self):
        result = classify(
            ["https://translate-pa.googleapis.com/v1/translateHtml"],
            "https://example.gov.lk/",
        )

        self.assertEqual("dynamic", result["type"])

    def test_flow_store_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FlowStore(Path(directory) / "flow.json")
            store.save("fingerprint", {"languages": {"en": ".english"}})

            self.assertEqual(
                {"fingerprint": "fingerprint", "flow": {"languages": {"en": ".english"}}},
                store.load(),
            )

    def test_flow_validation_rejects_cross_origin_pages(self):
        result = OpenAIFlowDiscovery()._validate(
            {
                "languages": {"en": ".english", "si": ".sinhala"},
                "pages": ["/about", "https://other.example/contact"],
            },
            "https://example.gov.lk/",
        )

        self.assertEqual(["https://example.gov.lk/about"], result["pages"])


if __name__ == "__main__":
    unittest.main()
