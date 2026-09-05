import html
import re

from ..models.Evidence import Evidence


class ContentDetector:
    PATTERNS = {
        "parked": (
            "domain is for sale",
            "buy this domain",
            "domain parking",
            "sedoparking",
        ),
        "defaced": (
            "hacked by",
            "owned by hacker",
            "website has been defaced",
        ),
        "generic_hosting": (
            "default web site page",
            "apache2 ubuntu default page",
            "welcome to nginx",
            "website coming soon",
            "under construction",
            "back soon",
        ),
        "unrelated": (
            "online casino",
            "sports betting bonus",
            "cryptocurrency giveaway",
        ),
    }

    def detect(self, body: str, source: str) -> list[Evidence]:
        text = self._text(body)
        found = []
        for check, patterns in self.PATTERNS.items():
            marker = next((item for item in patterns if item in text), None)
            if marker:
                detail = (
                    f"Detected {check.replace('_', ' ')} marker: {marker}"
                )
                found.append(Evidence(check, "fail", detail, source))
        return found

    def _text(self, body: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", body)
        return " ".join(html.unescape(without_tags).lower().split())
