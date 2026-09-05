import unittest

from glwa.audit.PageEvidenceCollector import PageEvidenceCollector
from glwa.models.HttpObservation import HttpObservation


class TestPageEvidenceCollector(unittest.TestCase):
    def test_collects_page_evidence_from_http_body(self):
        body = """
        <address>123 Parliament Road, Colombo 01</address>
        <a href="tel:+94 11 234 5678">Call</a>
        <a href="mailto:help@example.gov.lk">Email</a>
        <h2>Eligibility</h2>
        """
        item = HttpObservation(
            "https://example.gov.lk/",
            200,
            "https://example.gov.lk/",
            [],
            10,
            "text/html",
            body,
            None,
        )
        evidence = PageEvidenceCollector().collect([item], item.url)
        checks = {item.check for item in evidence}
        self.assertTrue({"postal_address", "phone", "email"} <= checks)
        self.assertIn("eligibility_criteria", checks)

    def test_emits_substance_evidence(self):
        collector = PageEvidenceCollector()
        rich = HttpObservation(
            "https://example.gov.lk/",
            200,
            "https://example.gov.lk/",
            [],
            10,
            "text/html",
            "<html><body><p>" + ("Substantive content. " * 100) + "</p></body></html>",
            None,
        )
        stub = HttpObservation(
            "https://stub.gov.lk/",
            200,
            "https://stub.gov.lk/",
            [],
            10,
            "text/html",
            "<html><body>Under construction...</body></html>",
            None,
        )
        rich_text = [
            item
            for item in collector.collect([rich], rich.url)
            if item.check == "page_text"
        ]
        stub_text = [
            item
            for item in collector.collect([stub], stub.url)
            if item.check == "page_text"
        ]
        self.assertEqual("pass", rich_text[0].status)
        self.assertEqual("fail", stub_text[0].status)


if __name__ == "__main__":
    unittest.main()
