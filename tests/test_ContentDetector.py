import unittest

from glwa.classification.ContentDetector import ContentDetector


class TestContentDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ContentDetector()

    def test_detects_parked_and_defaced_pages(self):
        body = "<html>Domain is for sale. Hacked by Example.</html>"
        checks = {
            item.check for item in self.detector.detect(body, "https://x")
        }
        self.assertEqual({"parked", "defaced"}, checks)

    def test_detects_maintenance_stub_as_generic_hosting(self):
        body = "<html>www.example.gov.lk Under construction... " \
            "We will be back soon...</html>"
        checks = {
            item.check for item in self.detector.detect(body, "https://x")
        }
        self.assertEqual({"generic_hosting"}, checks)


if __name__ == "__main__":
    unittest.main()
