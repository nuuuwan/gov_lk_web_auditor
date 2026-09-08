import argparse
import asyncio
import hashlib
from pathlib import Path
from urllib.parse import urlsplit

from src.glwa.directory.Directory import Directory
from src.glwa.translation import TranslationVerifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-urls", type=int)
    parser.add_argument("--rediscover", action="store_true")
    parser.add_argument("--worker-count", type=int, default=1)
    parser.add_argument("--worker-index", type=int, default=0)
    args = parser.parse_args()
    if args.worker_count < 1 or not 0 <= args.worker_index < args.worker_count:
        parser.error("worker index must be between 0 and worker count")
    urls = Directory(Path("static_data/websites.json")).urls()
    if args.worker_count > 1:
        urls = [
            url
            for url in urls
            if int.from_bytes(
                hashlib.sha256(
                    (urlsplit(url).hostname or url).encode("utf-8")
                ).digest(),
                "big",
            )
            % args.worker_count
            == args.worker_index
        ]
    if args.max_urls is not None:
        urls = urls[: args.max_urls]
    verifier = TranslationVerifier()
    for index, url in enumerate(urls, start=1):
        try:
            result = asyncio.run(verifier.run(url, rediscover=args.rediscover))
            print(f"{index}/{len(urls)}). {url}: {result.get('status', 'mapped')}")
        except Exception as error:
            print(f"{index}/{len(urls)}). {url}: failed: {error}")


if __name__ == "__main__":
    main()
