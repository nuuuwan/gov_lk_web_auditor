from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import unicodedata


@dataclass(frozen=True)
class Coverage:
    language: str
    visible_text_chars: int
    counted_letter_chars: int
    language_chars: int
    percentage: float
    translated: bool

    def to_dict(self) -> dict:
        return asdict(self)


class CoverageCalculator:
    RANGES = {
        "en": re.compile(r"[A-Za-z]"),
        "si": re.compile(r"[\u0D80-\u0DFF]"),
        "ta": re.compile(r"[\u0B80-\u0BFF]"),
    }
    MINIMUM = 0.55

    def calculate(self, text: str, language: str) -> Coverage:
        pattern = self.RANGES[language]
        visible = "".join(text.split())
        letters = [
            char
            for char in visible
            if unicodedata.category(char).startswith("L")
        ]
        language_chars = sum(bool(pattern.fullmatch(char)) for char in letters)
        total = len(letters)
        percentage = language_chars / total if total else 0.0
        return Coverage(
            language,
            len(visible),
            total,
            language_chars,
            round(percentage * 100, 2),
            percentage >= self.MINIMUM,
        )
