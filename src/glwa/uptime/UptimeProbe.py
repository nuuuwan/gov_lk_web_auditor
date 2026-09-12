from __future__ import annotations

import time
from urllib.parse import urlsplit

from ..network.DnsResolver import DnsResolver
from ..network.HttpProbe import HttpProbe
from ..network.TlsInspector import TlsInspector
from ..network.UrlNormalizer import UrlNormalizer
from ..time.SriLankaTime import SriLankaTime


class UptimeProbe:
    def __init__(
        self,
        dns: DnsResolver | None = None,
        http: HttpProbe | None = None,
        tls: TlsInspector | None = None,
        timeout: float = 30.0,
    ):
        self.normalizer = UrlNormalizer()
        self.dns = dns or DnsResolver()
        self.http = http or HttpProbe(timeout=timeout)
        self.tls = tls or TlsInspector()

    def check(self, url: str, now=None) -> dict:
        started = time.monotonic()
        checked_at = SriLankaTime.iso(now or SriLankaTime.now())
        try:
            normalized = self.normalizer.normalize(url)
        except ValueError as error:
            return self._record(
                url, url, checked_at, "down", str(error), None, [], None,
                started,
            )
        host = urlsplit(normalized).hostname or ""
        dns = self.dns.resolve(host)
        http = [self.http.probe(variant) for variant in self._variants(url)]
        tls = self._tls(host, normalized)
        status, reason = self._decide(dns, http)
        return self._record(
            url, normalized, checked_at, status, reason,
            dns.to_dict(),
            [self._http(item) for item in http],
            tls.to_dict() if tls else None,
            started,
        )

    def _variants(self, url: str) -> list[str]:
        try:
            return self.normalizer.variants(url)
        except ValueError:
            return []

    def _tls(self, host: str, normalized: str):
        if urlsplit(normalized).scheme != "https":
            return None
        return self.tls.inspect(host)

    def _decide(self, dns, http: list) -> tuple[str, str]:
        if dns.status != "resolved":
            return "down", f"DNS {dns.status}: {dns.detail}"
        answered = [item for item in http if item.status_code is not None]
        if not answered:
            errors = "; ".join(
                f"{item.url}: {item.error or 'no response'}" for item in http
            )
            return "down", f"No HTTP response: {errors}" if errors else (
                "down", "No HTTP response"
            )
        ok = [item for item in answered if item.status_code < 500]
        if ok:
            best = min(ok, key=lambda item: item.status_code)
            return "up", f"HTTP {best.status_code} at {best.final_url}"
        codes = ", ".join(str(item.status_code) for item in answered)
        return "down", f"Server errors: HTTP {codes}"

    def _http(self, item) -> dict:
        return {
            "url": item.url,
            "status_code": item.status_code,
            "final_url": item.final_url,
            "elapsed_ms": item.elapsed_ms,
            "error": item.error,
        }

    def _record(
        self, url, normalized, checked_at, status, reason,
        dns, http, tls, started,
    ) -> dict:
        return {
            "url": url,
            "normalized_url": normalized,
            "host": urlsplit(normalized).hostname
            if "://" in normalized else "",
            "checked_at": checked_at,
            "status": status,
            "reason": reason,
            "dns": dns,
            "http": http,
            "tls": tls,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
