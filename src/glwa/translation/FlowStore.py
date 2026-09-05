from __future__ import annotations

import hashlib
import json
from pathlib import Path


class FlowStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict | None:
        if not self.path.is_file():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, fingerprint: str, flow: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"fingerprint": fingerprint, "flow": flow}, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def fingerprint(structure: str) -> str:
        return hashlib.sha256(structure.encode("utf-8")).hexdigest()
