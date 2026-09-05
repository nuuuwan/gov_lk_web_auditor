import argparse
import asyncio
import json

from src.glwa.translation import TranslationVerifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--flow-dir", default="translation.flows")
    parser.add_argument("--model")
    args = parser.parse_args()
    result = asyncio.run(TranslationVerifier(args.flow_dir, args.model).run(args.url))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
