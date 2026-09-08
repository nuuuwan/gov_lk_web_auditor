import argparse
import asyncio
from pathlib import Path

from src.glwa.directory.Directory import Directory
from src.glwa.translation import TranslationVerifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-urls", type=int)
    parser.add_argument("--rediscover", action="store_true")
    args = parser.parse_args()
    urls = Directory(Path("static_data/websites.json")).urls()
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
