import argparse
import asyncio
from pathlib import Path
from urllib.parse import urlsplit

from src.glwa import AuditRunner
from src.glwa.audit.AuditHistory import AuditHistory
from src.glwa.audit.SnapshotRechecker import SnapshotRechecker
from src.glwa.classification.LevelEvaluator import LevelEvaluator
from src.glwa.directory.Directory import Directory
from src.glwa.reporting.ReadMe import ReadMe
from src.glwa.reporting.ReportWriter import ReportWriter
from src.glwa.reporting.WebsiteScore import WebsiteScore
from src.glwa.translation import TranslationBatchVerifier


class Pipeline:
    PATH_HISTORY = Path("audit.output")
    PATH_REPORTS = Path("latest_audit_reports")
    URLS = Path("static_data") / "websites.json"

    def __init__(self, max_urls=None, shard_index=0, shard_total=1,
                 concurrency=8):
        self.max_urls = max_urls
        self.shard_index = shard_index
        self.shard_total = max(1, shard_total)
        self.concurrency = concurrency

    def _level(self, audit):
        passed = [
            item.level for item in audit.levels if item.status == "pass"
        ]
        number = max(passed, default=0)
        level = LevelEvaluator.LEVELS[number]
        return level.label

    def _summary(self, audit):
        calculator = WebsiteScore()
        score = calculator.calculate(audit.to_dict())
        return f"{self._level(audit)}, {score:.1f}/{calculator.maximum}"

    def _limit(self, urls):
        total = len(urls)
        size = (total + self.shard_total - 1) // self.shard_total
        start = min(self.shard_index * size, total)
        shard = urls[start : start + size]
        if self.max_urls is None:
            return shard
        return shard[: self.max_urls]

    def _urls(self) -> list[str]:
        return Directory(self.URLS).urls()

    def run(self):
        urls = self._limit(self._urls())
        asyncio.run(self._run_all(urls))
        ReadMe().update(self.PATH_REPORTS)

    async def _run_all(self, urls: list[str]) -> None:
        semaphore = asyncio.Semaphore(self.concurrency)
        locks: dict[str, asyncio.Lock] = {}

        async def audit(index: int, url: str) -> None:
            host = urlsplit(url).hostname or url
            lock = locks.setdefault(host, asyncio.Lock())
            async with semaphore, lock:
                await asyncio.to_thread(self._audit, index, len(urls), url)

        await asyncio.gather(
            *(audit(index, url) for index, url in enumerate(urls, start=1))
        )

    def _audit(self, index: int, total: int, url: str) -> None:
        runner = AuditRunner()
        writer = ReportWriter()
        translations = TranslationBatchVerifier(self.PATH_REPORTS)
        history = AuditHistory(self.PATH_HISTORY)
        rechecker = SnapshotRechecker()
        if history.fresh(url):
            audit = rechecker.run(history.latest(url))
            writer.write(audit, self.PATH_REPORTS / history.host(url))
            translation = translations.run(url)
            print(
                f"{index}/{total}). {url}: "
                f"{self._summary(audit)} (cached), "
                f"translation {translation.get('status', 'checked')}"
            )
            return
        output = history.folder(url)
        audit = runner.run(url, output)
        history.write(audit, output)
        writer.write(audit, self.PATH_REPORTS / history.host(url))
        translation = translations.run(url)
        print(
            f"{index}/{total}). {url}: {self._summary(audit)}, "
            f"translation {translation.get('status', 'checked')}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-urls", type=int)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-total", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("concurrency must be positive")
    Pipeline(
        max_urls=args.max_urls,
        shard_index=args.shard_index,
        shard_total=args.shard_total,
        concurrency=args.concurrency,
    ).run()
