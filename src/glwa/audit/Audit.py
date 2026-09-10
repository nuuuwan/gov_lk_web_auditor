from dataclasses import asdict, dataclass
from typing import Any

from ..models.Classification import Classification
from ..models.Evidence import Evidence
from ..models.LevelResult import LevelResult


@dataclass(frozen=True)
class Audit:
    schema_version: str
    audit_id: str
    url: str
    normalized_url: str
    started_at: str
    completed_at: str
    result: Classification
    evidence: list[Evidence]
    observations: list[dict[str, Any]]
    snapshots: list[dict[str, Any]]
    reviewer_decisions: list[dict[str, Any]]
    levels: list[LevelResult]
    vantage: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = [item.to_dict() for item in self.evidence]
        data["levels"] = [item.to_dict() for item in self.levels]
        return data
