import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import os

from glwa.audit.EvidenceBuilder import EvidenceBuilder
from glwa.models.HttpObservation import HttpObservation
from glwa.network.SafeHttpClient import SafeHttpClient


class TestSafeHttpClient(unittest.TestCase):
    def test_stream_read_stops_at_byte_limit(self):
        response = Mock()
        response.iter_bytes.return_value = iter(
            [b"1234", b"5678", b"ignored"]
        )
        content = SafeHttpClient(1)._read(response, 6)
        self.assertEqual(b"123456", content)

    def test_blocks_non_public_redirect_target(self):
        client = SafeHttpClient(1)
        client.resolver.resolve = Mock(
            return_value=SimpleNamespace(
                status="blocked", detail="Non-public address"
            )
        )
        with self.assertRaisesRegex(ValueError, "Unsafe redirect blocked"):
            client._validate("http://127.0.0.1/private")

    def test_forwards_https_proxy_to_httpx_for_openvpn_check(self):
        fake_response = Mock()
        fake_response.headers = {}
        fake_response.status_code = 200
        fake_response.url = "https://example.gov.lk/"
        fake_response.content_type = "text/html"
        fake_response.iter_bytes.return_value = iter([b"ok"])
        stream_ctx = Mock()
        stream_ctx.__enter__ = Mock(return_value=fake_response)
        stream_ctx.__exit__ = Mock(return_value=False)
        with patch.dict(
            os.environ, {"HTTPS_PROXY": "http://lk-proxy:8080"}, clear=False
        ):
            with patch(
                "glwa.network.SafeHttpClient.httpx.Client"
            ) as mock_client_cls:
                mock_client = mock_client_cls.return_value.__enter__.return_value
                mock_client.stream.return_value = stream_ctx
                client = SafeHttpClient(1)
                client.resolver.resolve = Mock(
                    return_value=SimpleNamespace(
                        status="resolved", detail="ok"
                    )
                )
                client.rate_limiter.wait = Mock()
                client.get("https://example.gov.lk/", 10)
                _, kwargs = mock_client_cls.call_args
                self.assertEqual(
                    "http://lk-proxy:8080", kwargs.get("proxy")
                )

    def test_browser_certificate_error_is_not_transient(self):
        item = HttpObservation(
            "https://example.gov.lk",
            None,
            None,
            [],
            None,
            None,
            "",
            "CERTIFICATE VERIFY FAILED",
        )
        evidence = EvidenceBuilder().http(item, 1)
        self.assertEqual("tls_browser_error", evidence.check)
        self.assertEqual("fail", evidence.status)


if __name__ == "__main__":
    unittest.main()
