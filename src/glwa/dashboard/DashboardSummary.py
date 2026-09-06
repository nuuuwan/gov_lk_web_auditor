from __future__ import annotations

from ..reporting.WebsiteScore import WebsiteScore


class DashboardSummary:
    def summarize(self, sites: list[dict]) -> dict:
        by_level = {number: 0 for number in range(6)}
        for site in sites:
            by_level[site["level"]] = by_level.get(site["level"], 0) + 1
        scores = [site["score"] for site in sites]
        stamps = [site["completed_at"] for site in sites if site["completed_at"]]
        return {
            "total": len(sites),
            "by_level": by_level,
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "max_score": WebsiteScore().maximum,
            "last_audit": max(stamps) if stamps else "",
        }
