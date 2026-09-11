import unittest

from glwa.uptime.UptimeProbe import UptimeProbe


class _Dns:
    def __init__(self, status="resolved", detail="Public DNS resolved"):
        self.status = status
        self.detail = detail

    def resolve(self, host):
        return self

    def to_dict(self):
        return {"host": "x", "status": self.status, "detail": self.detail}


class _Http:
    def __init__(self, status_code, error=None, url="https://a.gov.lk/"):
        self.url = url
        self.status_code = status_code
        self.final_url = url
        self.elapsed_ms = 120
        self.error = error

    def probe(self, url):
        return _Http(self.status_code, self.error, url)


class _Tls:
    def inspect(self, host):
        return self

    def to_dict(self):
        return {"host": "x", "status": "valid"}


def _probe(dns=None, http=None):
    return UptimeProbe(
        dns=dns or _Dns(), http=http or _Http(200), tls=_Tls(),
    )


class TestUptimeProbe(unittest.TestCase):
    def test_up_on_200(self):
        record = _probe().check("https://a.gov.lk/")
        self.assertEqual("up", record["status"])
        self.assertIn("HTTP 200", record["reason"])
        self.assertEqual("a.gov.lk", record["host"])

    def test_up_on_404(self):
        record = _probe(http=_Http(404)).check("https://a.gov.lk/")
        self.assertEqual("up", record["status"])

    def test_down_on_all_5xx(self):
        record = _probe(http=_Http(503)).check("https://a.gov.lk/")
        self.assertEqual("down", record["status"])
        self.assertIn("503", record["reason"])

    def test_down_on_dns_failure(self):
        record = _probe(dns=_Dns("absent", "No addresses")).check(
            "https://a.gov.lk/"
        )
        self.assertEqual("down", record["status"])
        self.assertIn("DNS", record["reason"])

    def test_down_on_http_errors(self):
        record = _probe(http=_Http(None, "connect timeout")).check(
            "https://a.gov.lk/"
        )
        self.assertEqual("down", record["status"])

    def test_down_on_invalid_url(self):
        record = _probe().check("ftp://a.gov.lk/")
        self.assertEqual("down", record["status"])

    def test_record_shape(self):
        record = _probe().check("https://a.gov.lk/")
        for key in (
            "url", "normalized_url", "host", "checked_at", "status",
            "reason", "dns", "http", "tls", "duration_ms",
        ):
            self.assertIn(key, record)
        self.assertEqual(2, len(record["http"]))


if __name__ == "__main__":
    unittest.main()
