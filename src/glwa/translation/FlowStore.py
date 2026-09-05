from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit


class FlowStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict | None:
        if not self.path.is_file():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(
        self,
        fingerprint: str,
        flow: dict,
        source_url: str | None = None,
        final_url: str | None = None,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        mapping = {
            "schema_version": "translation-flow-1",
            "source_url": source_url,
            "final_url": final_url,
            "fingerprint": fingerprint,
            "pages": [
                {"url": url, "path": urlsplit(url).path}
                for url in flow["pages"]
            ],
            "actions": {
                language: {"kind": "locator", "locator": selector}
                for language, selector in flow["languages"].items()
            },
        }
        self.path.write_text(
            json.dumps(mapping, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def fingerprint(structure: str) -> str:
        return hashlib.sha256(structure.encode("utf-8")).hexdigest()
