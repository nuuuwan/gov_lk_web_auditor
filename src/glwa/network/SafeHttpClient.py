import time
from urllib.parse import urljoin, urlsplit

import httpx

from ..models.FetchedPage import FetchedPage
from .DnsResolver import DnsResolver
from .RateLimiter import RateLimiter


class SafeHttpClient:
    REDIRECT_CODES = {301, 302, 303, 307, 308}

    def __init__(self, timeout: float):
        self.timeout = timeout
        self.resolver = DnsResolver()
        self.rate_limiter = RateLimiter()

    def get(self, url: str, max_bytes: int) -> FetchedPage:
        redirects = []
        current = url
        with httpx.Client(
            follow_redirects=False,
            timeout=self.timeout,
            headers={"User-Agent": "lk-gov-web-auditor/0.1"},
        ) as client:
            for _ in range(11):
                self._validate(current)
                host = urlsplit(current).hostname or ""
                self.rate_limiter.wait(host)
                started = time.monotonic()
                with client.stream("GET", current) as response:
                    location = response.headers.get("location")
                    redirected = response.status_code in self.REDIRECT_CODES
                    if redirected and location:
                        response.close()
                        current = urljoin(current, location)
                        redirects.append(current)
                        continue
                    content = self._read(response, max_bytes)
                    response.close()
                    elapsed_ms = int((time.monotonic() - started) * 1000)
                    return FetchedPage(
                        response.status_code,
                        str(response.url),
                        redirects,
                        elapsed_ms,
                        response.headers.get("content-type"),
                        content,
                    )
        raise ValueError("More than 10 redirects")

    def _read(self, response, max_bytes: int) -> bytes:
        content = bytearray()
        for chunk in response.iter_bytes():
            remaining = max_bytes - len(content)
            content.extend(chunk[:remaining])
            if len(content) >= max_bytes:
                break
        return bytes(content)

    def _validate(self, url: str):
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Redirect target is not a valid HTTP URL")
        observation = self.resolver.resolve(parsed.hostname)
        if observation.status != "resolved":
            raise ValueError(f"Unsafe redirect blocked: {observation.detail}")
