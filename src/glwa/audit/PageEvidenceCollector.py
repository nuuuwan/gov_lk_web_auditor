import html
import re

from ..classification.ContentDetector import ContentDetector
from ..models.Evidence import Evidence
from .EvidenceBuilder import EvidenceBuilder
from .Level2EvidenceCollector import Level2EvidenceCollector
from .Level3EvidenceCollector import Level3EvidenceCollector


class PageEvidenceCollector:
    MIN_SUBSTANCE = 200

    def __init__(self):
        self.detector = ContentDetector()
        self.builder = EvidenceBuilder()
        self.level2 = Level2EvidenceCollector()
        self.level3 = Level3EvidenceCollector()

    def collect(self, items, original):
        evidence = []
        usable = [
            item for item in items if item.body and item.final_url
        ]
        for item in usable:
            evidence.extend(self.detector.detect(item.body, item.final_url))
            evidence.extend(self.level2.collect(item.body, item.final_url))
            evidence.extend(self.level3.collect(item.body, item.final_url))
            redirect = self.builder.redirect(original, item.final_url)
            if redirect:
                evidence.append(redirect)
        substance = self._substance(usable, original)
        if substance:
            evidence.append(substance)
        return evidence

    def _substance(self, items, original):
        if not items:
            return None
        most = max(len(self._visible(item.body)) for item in items)
        if most >= self.MIN_SUBSTANCE:
            return Evidence(
                "page_text",
                "pass",
                f"Substantive page content: {most} visible characters "
                f"across {len(items)} pages",
                original,
            )
        return Evidence(
            "page_text",
            "fail",
            f"Only {most} visible characters across {len(items)} "
            f"pages; below substance threshold {self.MIN_SUBSTANCE}",
            original,
        )

    def _visible(self, body: str) -> str:
        without_scripts = re.sub(
            r"<(script|style|noscript)[^>]*>.*?</\1>",
            " ",
            body,
            flags=re.S | re.I,
        )
        without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
        return " ".join(html.unescape(without_tags).split())
