import json
from pathlib import Path


def normalize_url(value):
    if isinstance(value, str):
        value = value.strip()
        if "://" not in value and "." in value:
            return f"https://{value}"
    return value


class Directory:
    def __init__(self, source=None):
        self.source = source or self._default_source()

    def urls(self):
        content = self.source.read_text(encoding="utf-8")
        websites = json.loads(content)
        return list(
            dict.fromkeys(normalize_url(value) for value in self._values(websites))
        )

    def _default_source(self):
        return Path(__file__).parents[3] / "static_data" / "websites.json"

    def _values(self, item):
        if isinstance(item, dict):
            for value in item.values():
                yield from self._values(value)
            return
        if isinstance(item, list):
            for value in item:
                yield from self._values(value)
            return
        yield item
