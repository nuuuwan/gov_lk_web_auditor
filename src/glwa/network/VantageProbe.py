import os

import httpx


class VantageProbe:
    IP_URL = "https://api.ipify.org"
    COUNTRY_URL = "http://ip-api.com/json/{ip}?fields=country,countryCode"

    def probe(self) -> dict:
        runner = (
            "github-actions"
            if os.getenv("GITHUB_ACTIONS") == "true"
            else "local"
        )
        proxy = bool(
            os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        )
        return {
            "egress_ip": self._egress_ip(),
            "country": self._country(),
            "runner": runner,
            "proxy": proxy,
        }

    def _egress_ip(self) -> str:
        try:
            response = httpx.get(self.IP_URL, timeout=10.0)
            ip = response.text.strip()
            return ip or "unknown"
        except Exception:
            return "unknown"

    def _country(self) -> str:
        try:
            ip = self._egress_ip()
            if ip == "unknown":
                return "unknown"
            response = httpx.get(
                self.COUNTRY_URL.format(ip=ip), timeout=10.0
            )
            return response.json().get("countryCode", "unknown")
        except Exception:
            return "unknown"
