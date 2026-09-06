from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from ..classification.LevelEvaluator import LevelEvaluator
from ..reporting.WebsiteScore import WebsiteScore

COPIED_FILES = ("audit.json", "audit.md", "evidence.csv", "levels.csv", "report.html")


class DashboardLoader:
    def load(
        self, reports: Path, directory: Path | None = None
    ) -> tuple[list[dict], list[dict]]:
        names, ministries = self._institutions(directory) if directory else ({}, {})
        sites: list[dict] = []
        errors: list[dict] = []
        paths = sorted(reports.glob("*/audit.json")) if reports.is_dir() else []
        for path in paths:
            try:
                audit = json.loads(path.read_text(encoding="utf-8"))
                sites.append(self._site(path, audit, names, ministries))
            except (OSError, ValueError) as exc:
                errors.append(
                    {"host": path.parent.name, "message": str(exc)}
                )
        sites.sort(
            key=lambda item: (
                item.get("ministry", ""),
                -item["level"],
                -item["score"],
                item["normalized_url"],
            )
        )
        return sites, errors

    def _site(
        self, path: Path, audit: dict, names: dict, ministries: dict
    ) -> dict:
        if not isinstance(audit, dict) or not isinstance(
            audit.get("levels"), list
        ):
            raise ValueError("audit.json has no levels list")
        host = path.parent.name
        url = str(audit.get("url", ""))
        normalized = str(audit.get("normalized_url", url))
        level = self._level(audit)
        score = WebsiteScore().calculate(audit)
        checks = [
            check
            for item in audit["levels"]
            if isinstance(item, dict)
            for check in (item.get("checks") or [])
            if isinstance(check, dict)
        ]
        evidence = audit.get("evidence") or []
        institution = self._institution(normalized, url, host, names)
        ministry = self._ministry(normalized, url, host, ministries)
        return {
            "host": host,
            "url": url,
            "normalized_url": normalized,
            "institution": institution,
            "ministry": ministry,
            "level": level,
            "level_label": LevelEvaluator.LEVELS[level].label,
            "score": score,
            "max_score": WebsiteScore().maximum,
            "completed_at": str(audit.get("completed_at", "")),
            "failed_checks": sum(
                check.get("status") == "fail" for check in checks
            ),
            "inconclusive_checks": sum(
                check.get("status") == "inconclusive" for check in checks
            ),
            "status_group": self._group(checks),
            "levels": audit["levels"],
            "evidence": evidence if isinstance(evidence, list) else [],
            "files": [
                name
                for name in COPIED_FILES
                if (path.parent / name).is_file()
            ],
        }

    def _level(self, audit: dict) -> int:
        passed = [
            item["level"]
            for item in audit["levels"]
            if isinstance(item, dict) and item.get("status") == "pass"
        ]
        return max(passed, default=0)

    def _group(self, checks: list[dict]) -> str:
        if any(check.get("status") == "fail" for check in checks):
            return "attention"
        if any(check.get("status") == "inconclusive" for check in checks):
            return "inconclusive"
        return "clean"

    def _institution(
        self, normalized: str, url: str, host: str, names: dict
    ) -> str:
        for key in (normalized, url, normalized.rstrip("/"), url.rstrip("/")):
            if key and key in names:
                return names[key]
        parsed = urlparse(normalized or url)
        if parsed.hostname and parsed.hostname in names:
            return names[parsed.hostname]
        return host

    def _ministry(
        self, normalized: str, url: str, host: str, ministries: dict
    ) -> str:
        for key in (normalized, url, normalized.rstrip("/"), url.rstrip("/")):
            if key and key in ministries:
                return ministries[key]
        parsed = urlparse(normalized or url)
        if parsed.hostname:
            bare = parsed.hostname
            for key in ministries:
                if key == bare or key == f"https://{bare}/" or key == f"http://{bare}/":
                    return ministries[key]
        return ""

    def _institutions(self, directory: Path) -> tuple[dict, dict]:
        try:
            data = json.loads(directory.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}, {}
        names: dict = {}
        ministries: dict = {}
        self._walk(data, [], names, ministries)
        return names, ministries

    def _walk(
        self, node, trail: list, names: dict, ministries: dict
    ) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                self._walk(value, [*trail, str(key)], names, ministries)
            return
        if isinstance(node, list):
            for value in node:
                self._walk(value, trail, names, ministries)
            return
        if isinstance(node, str) and node.startswith("http"):
            label = self._flatten_name(trail)
            names[node] = label
            names[node.rstrip("/")] = label
            host = urlparse(node).hostname or ""
            if host and host not in names:
                names[host] = label
            ministry = self._extract_ministry(trail)
            if ministry:
                ministries[node] = ministry
                ministries[node.rstrip("/")] = ministry
                if host:
                    ministries[host] = ministry

    def _flatten_name(self, trail: list) -> str:
        if len(trail) <= 2:
            return " / ".join(trail[1:]) if len(trail) > 1 else trail[0]
        return " / ".join(trail[1:3])

    def _extract_ministry(self, trail: list) -> str:
        for part in trail:
            lower = part.lower()
            if "minister" in lower or "ministry" in lower:
                return part
        if len(trail) >= 3:
            return trail[1]
        return ""
