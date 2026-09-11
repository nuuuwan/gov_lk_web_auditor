from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit


class UptimeStore:
    FILENAME = "checks.jsonl"

    def __init__(self, root: Path = Path("uptime_history")):
        self.root = root

    def path(self, host: str) -> Path:
        return self.root / host / self.FILENAME

    def append(self, record: dict) -> Path:
        host = str(record.get("host") or "unknown")
        path = self.path(host)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path

    def read(self, host: str) -> list[dict]:
        path = self.path(host)
        if not path.is_file():
            return []
        checks = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if isinstance(item, dict) and item.get("checked_at"):
                checks.append(item)
        checks.sort(key=lambda item: str(item.get("checked_at", "")))
        return checks

    def hosts(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            path.name for path in self.root.iterdir()
            if (path / self.FILENAME).is_file()
        )

    @staticmethod
    def host_of(url: str) -> str:
        return urlsplit(url).hostname or url
