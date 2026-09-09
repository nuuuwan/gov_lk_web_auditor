from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from ..classification.Classifier import Classifier
from ..classification.LevelEvaluator import LevelEvaluator
from ..levels.Level1 import Level1
from ..network.DnsResolver import DnsResolver
from ..network.DomainInspector import DomainInspector
from ..network.HttpProbe import HttpProbe
from ..network.TlsInspector import TlsInspector
from ..network.UrlNormalizer import UrlNormalizer
from ..network.VantageProbe import VantageProbe
from ..reporting.SnapshotStore import SnapshotStore
from ..time.SriLankaTime import SriLankaTime
from .Audit import Audit
from .EvidenceBuilder import EvidenceBuilder
from .Level2Crawler import Level2Crawler
from .PageEvidenceCollector import PageEvidenceCollector


class AuditRunner:
    def __init__(self, probe_count: int = 2):
        self.probe_count = max(2, probe_count)
        self.normalizer = UrlNormalizer()
        self.resolver = DnsResolver()
        self.domain_inspector = DomainInspector()
        self.http_probe = HttpProbe()
        self.tls_inspector = TlsInspector()
        self.builder = EvidenceBuilder()
        self.page_collector = PageEvidenceCollector()
        self.level_evaluator = LevelEvaluator()
        self.snapshot_store = SnapshotStore()

    def run(self, url: str, output: Path) -> Audit:
        started = SriLankaTime.now().isoformat()
        normalized = self.normalizer.normalize(url)
        host = urlsplit(normalized).hostname or ""
        dns, evidence, observations = self._initial(host)
        snapshots = []
        if dns.status == "resolved":
            tls = self.tls_inspector.inspect(host)
            evidence.append(self.builder.tls(tls))
            observations.append(tls.to_dict())
            http_items = self._probe(normalized)
            observations.extend(item.to_dict() for item in http_items)
            evidence.extend(
                self.builder.http(item, index + 1)
                for index, item in enumerate(http_items)
            )
            evidence.extend(
                self.page_collector.collect(http_items, normalized)
            )
            persistent = self.builder.persistent_http(http_items)
            if persistent:
                evidence.append(persistent)
            snapshots = self._snapshots(http_items, output)
        result = Classifier(Level1()).classify(evidence)
        levels = self.level_evaluator.evaluate(evidence)
        return Audit(
            "1.3.0",
            str(uuid4()),
            url,
            normalized,
            started,
            SriLankaTime.now().isoformat(),
            result,
            evidence,
            observations,
            snapshots,
            [],
            levels,
            VantageProbe().probe(),
        )

    def _initial(self, host):
        dns = self.resolver.resolve(host)
        domain = self.domain_inspector.inspect(host)
        evidence = [self.builder.dns(dns), self.builder.domain(domain)]
        observations = [dns.to_dict(), domain.to_dict()]
        return dns, evidence, observations

    def _probe(self, url: str):
        variants = self.normalizer.variants(url)
        items = [
            self.http_probe.probe(variant)
            for _ in range(self.probe_count)
            for variant in variants
        ]
        return [*items, *Level2Crawler(self.http_probe).crawl(items)]

    def _snapshots(self, items, output):
        usable = [item for item in items if item.body]
        return [
            self.snapshot_store.save(item, output / "snapshots", index + 1)
            for index, item in enumerate(usable)
        ]
