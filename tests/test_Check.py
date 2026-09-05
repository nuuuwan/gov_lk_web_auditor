import unittest

from glwa import Check, Evidence
from glwa.checks.level1.ContentRelevantCheck import ContentRelevantCheck
from glwa.checks.level1.DnsResolvesCheck import DnsResolvesCheck
from glwa.checks.level1.HttpAvailableCheck import HttpAvailableCheck
from glwa.levels.Level1 import Level1


class TestCheck(unittest.TestCase):
    def test_check_is_abstract(self):
        with self.assertRaises(TypeError):
            Check("base", 0)

    def test_dns_resolves_check_owns_its_logic(self):
        check = DnsResolvesCheck()
        failed = check.run(
            [Evidence("dns_absent", "fail", "DNS name does not exist")]
        )
        passed = check.run([Evidence("dns", "pass", "Public DNS resolved")])
        uncertain = check.run([Evidence("dns", "error", "DNS timed out")])
        self.assertEqual(("dns_resolves", 1), (check.name, check.level))
        self.assertEqual("fail", failed.status)
        self.assertEqual("pass", passed.status)
        self.assertEqual("inconclusive", uncertain.status)

    def test_each_level_one_check_owns_its_failure_logic(self):
        for check in Level1().checks:
            with self.subTest(check=check.name):
                evidence = [Evidence(check.FAILURE, "fail", "Failed")]
                result = check.run(evidence)
                self.assertEqual((check.name, 1), (check.name, check.level))
                self.assertEqual("fail", result.status)

    def test_http_available_passes_when_https_succeeds(self):
        evidence = [
            Evidence(
                "http",
                "pass",
                "Probe 1: HTTP 200 at https://example.gov.lk/",
                "https://example.gov.lk/",
            ),
            Evidence(
                "http",
                "error",
                "Probe 2: Server disconnected",
                "http://example.gov.lk/",
            ),
        ]
        result = HttpAvailableCheck().run(evidence)
        self.assertEqual("pass", result.status)

    def test_content_checks_hold_when_page_lacks_substance(self):
        evidence = [
            Evidence(
                "http",
                "pass",
                "Probe 1: HTTP 200 at https://example.gov.lk/",
                "https://example.gov.lk/",
            ),
            Evidence("page_text", "fail", "Only 61 visible characters"),
        ]
        result = ContentRelevantCheck().run(evidence)
        self.assertEqual("inconclusive", result.status)


if __name__ == "__main__":
    unittest.main()
