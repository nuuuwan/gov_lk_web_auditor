from __future__ import annotations

import json
import os
from urllib.parse import urljoin, urlsplit


class OpenAIFlowDiscovery:
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def discover(self, url: str, structure: str) -> dict:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                        "Return JSON only. Identify robust Playwright locator strings for language controls "
                        "and up to five same-origin content pages. CSS, text=, and role= locators are valid; "
                        "do not return prose or XPath. "
                                "Languages are en, si, and ta. Never invent a selector."
                            ),
                        },
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps({"url": url, "page_structure": structure}),
                        }
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "translation_flow",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "languages": {
                                "type": "object",
                                "properties": {
                                    "en": {"type": "string"},
                                    "si": {"type": "string"},
                                    "ta": {"type": "string"},
                                },
                                "required": ["en", "si", "ta"],
                                "additionalProperties": False,
                            },
                            "pages": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["languages", "pages"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        raw = response.output_text or "{}"
        return self._validate(json.loads(raw), url)

    def _validate(self, value: dict, source: str) -> dict:
        languages = value.get("languages")
        pages = value.get("pages")
        if not isinstance(languages, dict) or not isinstance(pages, list):
            raise ValueError("OpenAI flow response must contain languages and pages")
        clean_languages = {
            language: selector
            for language, selector in languages.items()
            if language in {"en", "si", "ta"} and isinstance(selector, str) and selector
        }
        source_host = urlsplit(source).netloc
        clean_pages = []
        for page in pages:
            if not isinstance(page, str):
                continue
            absolute = urljoin(source, page)
            if urlsplit(absolute).netloc == source_host:
                clean_pages.append(absolute)
        if not clean_languages:
            raise ValueError("OpenAI flow response did not provide language selectors")
        return {"languages": clean_languages, "pages": list(dict.fromkeys(clean_pages))[:5]}
