import re
from pathlib import Path

from ...audit.Audit import Audit
from ...classification.LevelEvaluator import LevelEvaluator
from ...time.SriLankaTime import SriLankaTime
from .MarkdownReportPreparationMixin import MarkdownReportPreparationMixin


class MarkdownReport(MarkdownReportPreparationMixin):
    SYMBOLS = {"pass": "✅", "fail": "❌", "inconclusive": "❓"}

    def write(self, audit: Audit, output: Path) -> Path:
        path = output / "audit.md"
        return self.write_data(audit.to_dict(), path)

    def write_data(self, audit: dict, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        audit = self.prepare(audit)
        vantage = audit.get("vantage") or {}
        lines = [
            f"# Website Audit: {audit['normalized_url']}",
            "",
            f"- Completed: {self._time(audit['completed_at'])}",
            f"- Overall result: {self._label(self._overall(audit))}",
            f"- Vantage: {vantage.get('egress_ip', 'unknown')} "
            f"({vantage.get('country', 'unknown')}, "
            f"{vantage.get('runner', 'unknown')})",
        ]
        for level in audit["levels"]:
            if not LevelEvaluator.LEVELS[level["level"]].implemented:
                continue
            lines.extend(self._level(level))
            if level["status"] == "fail":
                break
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _overall(self, audit: dict) -> int:
        passed = [
            item["level"]
            for item in audit["levels"]
            if item["status"] == "pass"
        ]
        return max(passed, default=0)

    def _level(self, level) -> list[str]:
        definition = LevelEvaluator.LEVELS[level["level"]]
        lines = [
            "",
            f"## {definition.label}: {self._symbol(level['status'])}",
            "",
            self._references(level["description"]),
            "",
            self._references(level["reason"]),
        ]
        if level["checks"]:
            lines.extend(
                [
                    "",
                    "| Test | Result | Details |",
                    "| --- | --- | --- |",
                    *[self._check(item) for item in level["checks"]],
                ]
            )
        return lines

    def _check(self, check) -> str:
        reason = check["reason"].replace("|", "\\|").replace("\n", " ")
        symbol = self._symbol(check["status"])
        return f"| {check['name']} | {symbol} | {reason} |"

    def _symbol(self, status: str) -> str:
        return self.SYMBOLS.get(status, "❓")

    def _label(self, number: int) -> str:
        return LevelEvaluator.LEVELS[number].label

    def _references(self, text: str) -> str:
        def replace(match):
            level = LevelEvaluator.LEVELS[int(match.group(1))]
            if match.group(0)[0] == "`":
                return level.markdown_label
            return level.label

        return re.sub(r"`?Level ([0-5])`?", replace, text)

    def _time(self, value: str) -> str:
        return SriLankaTime.parse(value).strftime("%Y-%m-%d %H:%M")
