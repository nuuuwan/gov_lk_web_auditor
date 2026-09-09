from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlsplit

from .ResultStore import ResultStore
from .Verifier import TranslationVerifier


class TranslationBatchVerifier:
    def __init__(
        self,
        reports: Path = Path("latest_audit_reports"),
        verifier: TranslationVerifier | None = None,
    ):
        self.reports = Path(reports)
        self.verifier = verifier or TranslationVerifier()

    def run(
        self, url: str, replay: bool = True, rediscover: bool = False
    ) -> dict:
        host = urlsplit(url).hostname or "unknown"
        try:
            result = asyncio.run(
                self.verifier.run(url, replay=replay, rediscover=rediscover)
            )
        except ValueError as error:
            result = {
                "url": url,
                "status": "mapping_outdated" if replay else "error",
                "reason": str(error),
                "pages": [],
            }
        except Exception as error:
            result = {
                "url": url,
                "status": "error",
                "reason": str(error),
                "pages": [],
            }
        ResultStore(self.reports / host / "translation.json").save(result)
        return result
