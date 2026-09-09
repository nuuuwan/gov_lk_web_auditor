import unittest
from unittest.mock import Mock, patch

from glwa.network.VantageProbe import VantageProbe


class TestVantageProbe(unittest.TestCase):
    def test_reports_github_actions_runner(self):
        with patch.dict(
            "os.environ", {"GITHUB_ACTIONS": "true"}, clear=False
        ):
            with patch(
                "glwa.network.VantageProbe.httpx.get",
                return_value=Mock(
                    status_code=200, text="20.1.2.3\n"
                ),
            ):
                vantage = VantageProbe().probe()
        self.assertEqual("20.1.2.3", vantage["egress_ip"])
        self.assertEqual("github-actions", vantage["runner"])

    def test_reports_local_runner_by_default(self):
        env = {
            key: value
            for key, value in __import__("os").environ.items()
            if key != "GITHUB_ACTIONS"
        }
        with patch.dict("os.environ", env, clear=True):
            with patch(
                "glwa.network.VantageProbe.httpx.get",
                return_value=Mock(
                    status_code=200, text="192.248.41.11\n"
                ),
            ):
                vantage = VantageProbe().probe()
        self.assertEqual("local", vantage["runner"])
        self.assertIn("proxy", vantage)

    def test_never_raises_when_network_fails(self):
        with patch(
            "glwa.network.VantageProbe.httpx.get",
            side_effect=Exception("no network"),
        ):
            vantage = VantageProbe().probe()
        self.assertEqual("unknown", vantage["egress_ip"])
        self.assertEqual("unknown", vantage["country"])


if __name__ == "__main__":
    unittest.main()
