import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlsplit

from src.glwa.translation import TranslationVerifier
from src.glwa.translation.ResultStore import ResultStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--flow-dir", default="translation_mappings")
    parser.add_argument("--mapping")
    parser.add_argument("--result")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--rediscover", action="store_true")
    parser.add_argument("--model")
    args = parser.parse_args()
    result = asyncio.run(
        TranslationVerifier(args.flow_dir, args.model).run(
            args.url, args.mapping, args.replay, args.rediscover
        )
    )
    result_path = Path(args.result or "translation_results")
    if result_path.suffix != ".json":
        result_path /= f"{urlsplit(args.url).hostname}.json"
    ResultStore(result_path).save(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
