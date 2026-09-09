from __future__ import annotations

import json
from pathlib import Path


class ResultStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def save(self, result: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
