import json
import tempfile
import unittest
from pathlib import Path

from glwa.translation.Coverage import CoverageCalculator
from glwa.translation.FlowStore import FlowStore
from glwa.translation.Provenance import classify
from glwa.translation.OpenAIFlowDiscovery import OpenAIFlowDiscovery
from glwa.translation.Availability import check
from glwa.translation.ResultStore import ResultStore


class TestTranslation(unittest.TestCase):
    def test_classifies_redirected_404_as_unavailable(self):
        result = check(404, "https://aib.gov.lk/aib", "404 Sorry")

        self.assertEqual("unavailable", result["status"])
        self.assertEqual(404, result["http_status"])

    def test_classifies_empty_success_page_as_unusable(self):
        result = check(200, "https://example.gov.lk/", "  ")

        self.assertEqual("unusable", result["status"])

    def test_allows_visible_success_page_to_reach_translation_checks(self):
        self.assertIsNone(check(200, "https://example.gov.lk/", "English"))

    def test_keeps_redirect_chain_for_final_destination(self):
        result = check(
            200,
            "https://new.example.gov.lk/",
            "English",
            ["https://old.example.gov.lk/", "https://new.example.gov.lk/"],
        )

        self.assertIsNone(result)

    def test_calculates_script_coverage_for_sinhala(self):
        result = CoverageCalculator().calculate("සිංහල පුවත් English", "si")

        self.assertEqual("si", result.language)
        self.assertLessEqual(result.percentage, 100)
        self.assertGreater(result.percentage, 40)
        self.assertFalse(result.translated)

    def test_excludes_script_combining_marks_from_coverage_denominator(self):
        result = CoverageCalculator().calculate("සිංහල", "si")

        self.assertEqual(5, result.visible_text_chars)
        self.assertEqual(3, result.counted_letter_chars)
        self.assertEqual(3, result.language_chars)
        self.assertEqual(100, result.percentage)

    def test_uses_unknown_when_no_translation_provenance_is_observed(self):
        result = classify(
            ["https://example.gov.lk/app.js", "https://cdn.example.net/a.js"],
            "https://example.gov.lk/",
        )

        self.assertEqual("unknown", result["type"])
        self.assertEqual([], result["dynamic_urls"])

    def test_detects_known_dynamic_provider(self):
        result = classify(
            ["https://translate-pa.googleapis.com/v1/translateHtml"],
            "https://example.gov.lk/",
        )

        self.assertEqual("dynamic", result["type"])

    def test_flow_store_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FlowStore(Path(directory) / "flow.json")
            store.save(
                "fingerprint",
                {
                    "languages": {"en": ".english"},
                    "pages": ["https://example.gov.lk/about"],
                },
                "https://example.gov.lk/",
                "https://example.gov.lk/",
            )

            self.assertEqual(
                {
                    "schema_version": "translation-flow-1",
                    "source_url": "https://example.gov.lk/",
                    "final_url": "https://example.gov.lk/",
                    "fingerprint": "fingerprint",
                    "pages": [
                        {"url": "https://example.gov.lk/about", "path": "/about"}
                    ],
                    "actions": {
                        "en": {"kind": "locator", "locator": ".english"}
                    },
                },
                store.load(),
            )

    def test_mapping_actions_convert_back_to_replay_flow(self):
        from glwa.translation.Verifier import TranslationVerifier

        flow = TranslationVerifier()._flow(
            {
                "pages": [{"url": "https://example.gov.lk/about", "path": "/about"}],
                "actions": {"en": {"kind": "locator", "locator": ".english"}},
            }
        )

        self.assertEqual(["https://example.gov.lk/about"], flow["pages"])
        self.assertEqual({"en": ".english"}, flow["languages"])

    def test_flow_validation_rejects_cross_origin_pages(self):
        result = OpenAIFlowDiscovery()._validate(
            {
                "languages": {"en": ".english", "si": ".sinhala"},
                "pages": ["/about", "https://other.example/contact"],
            },
            "https://example.gov.lk/",
        )

        self.assertEqual(["https://example.gov.lk/about"], result["pages"])

    def test_result_store_overwrites_result_json(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ResultStore(Path(directory) / "result.json")
            store.save({"status": "ok", "pages": []})

            self.assertEqual(
                {"status": "ok", "pages": []},
                json.loads(store.path.read_text("utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
