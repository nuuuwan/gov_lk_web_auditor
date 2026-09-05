from __future__ import annotations

from pathlib import Path

from ..models.HttpObservation import HttpObservation
from .AuditReclassifier import AuditReclassifier
from .PageEvidenceCollector import PageEvidenceCollector


class SnapshotRechecker:
    PAGE_CHECKS = {
        "parked",
        "defaced",
        "generic_hosting",
        "unrelated",
        "identity",
        "page_text",
        "redirect_unrelated",
        "postal_address",
        "phone",
        "email",
        "counter_hours",
        "named_responsibility",
        "service_scope",
        "eligibility_criteria",
        "required_documents",
        "fees_and_payment",
        "legal_basis",
        "processing_time",
        "downloadable_form",
        "published_update_date",
    }

    def run(self, data: dict):
        pages = [
            page
            for snapshot in data["snapshots"]
            if (page := self._page(snapshot))
        ]
        if not pages:
            return AuditReclassifier().reclassify(data)
        evidence = [
            item
            for item in data["evidence"]
            if item["check"] not in self.PAGE_CHECKS
        ]
        collected = PageEvidenceCollector().collect(
            pages, data["normalized_url"]
        )
        refreshed = {**data, "evidence": evidence}
        refreshed["evidence"].extend(item.to_dict() for item in collected)
        return AuditReclassifier().reclassify(refreshed)

    def _page(self, snapshot: dict) -> HttpObservation | None:
        path = Path(snapshot["path"])
        if not path.is_file():
            return None
        body = path.read_text(encoding="utf-8", errors="replace")
        url = snapshot["url"]
        return HttpObservation(url, 200, url, [], 0, "text/html", body, None)
