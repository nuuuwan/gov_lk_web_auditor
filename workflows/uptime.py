import argparse
import asyncio
from pathlib import Path
from urllib.parse import urlsplit

from src.glwa.directory.Directory import Directory
from src.glwa.uptime.UptimeProbe import UptimeProbe
from src.glwa.uptime.UptimeStore import UptimeStore


class UptimePipeline:
    URLS = Path("static_data") / "websites.json"

    def __init__(self, max_urls=None, shard_index=0, shard_total=1,
                 concurrency=8, history=Path("uptime_history"), timeout=30.0):
        self.max_urls = max_urls
        self.shard_index = shard_index
        self.shard_total = max(1, shard_total)
        self.concurrency = concurrency
        self.store = UptimeStore(history)
        self.timeout = timeout

    def _urls(self) -> list[str]:
        return Directory(self.URLS).urls()

    def _limit(self, urls):
        total = len(urls)
        size = (total + self.shard_total - 1) // self.shard_total
        start = min(self.shard_index * size, total)
        shard = urls[start: start + size]
        if self.max_urls is None:
            return shard
        return shard[: self.max_urls]

    def run(self):
        urls = self._limit(self._urls())
        asyncio.run(self._run_all(urls))

    async def _run_all(self, urls: list[str]) -> None:
        semaphore = asyncio.Semaphore(self.concurrency)
        locks: dict[str, asyncio.Lock] = {}

        async def check(index: int, url: str) -> None:
            host = urlsplit(url).hostname or url
            lock = locks.setdefault(host, asyncio.Lock())
            async with semaphore, lock:
                await asyncio.to_thread(self._check, index, len(urls), url)

        await asyncio.gather(
            *(check(index, url) for index, url in enumerate(urls, start=1))
        )

    def _check(self, index: int, total: int, url: str) -> None:
        try:
            record = UptimeProbe(timeout=self.timeout).check(url)
            path = self.store.append(record)
            print(
                f"{index}/{total}). {url}: {record['status']} "
                f"({record['reason']}) -> {path}"
            )
        except Exception as error:
            print(f"{index}/{total}). {url}: FAILED {error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily website status check")
    parser.add_argument("--max-urls", type=int)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-total", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--history", type=Path, default=Path("uptime_history"))
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("concurrency must be positive")
    UptimePipeline(
        max_urls=args.max_urls,
        shard_index=args.shard_index,
        shard_total=args.shard_total,
        concurrency=args.concurrency,
        history=args.history,
        timeout=args.timeout,
    ).run()
