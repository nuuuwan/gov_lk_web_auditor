from ..classification.Classifier import Classifier
from ..classification.LevelEvaluator import LevelEvaluator
from ..levels.Level1 import Level1
from ..models.Evidence import Evidence
from ..time.SriLankaTime import SriLankaTime
from .Audit import Audit


class AuditReclassifier:
    def __init__(self):
        self.classifier = Classifier(Level1())
        self.evaluator = LevelEvaluator()

    def reclassify(self, data: dict) -> Audit:
        evidence = [self._evidence(item) for item in data["evidence"]]
        return Audit(
            data["schema_version"],
            data["audit_id"],
            data["url"],
            data["normalized_url"],
            SriLankaTime.iso(data["started_at"]),
            SriLankaTime.iso(data["completed_at"]),
            self.classifier.classify(evidence),
            evidence,
            [self._observation(item) for item in data["observations"]],
            data["snapshots"],
            data["reviewer_decisions"],
            self.evaluator.evaluate(evidence),
            data.get("vantage") or {},
        )

    def _evidence(self, item: dict) -> Evidence:
        data = item.copy()
        if data.get("observed_at"):
            data["observed_at"] = SriLankaTime.iso(data["observed_at"])
        return Evidence(**data)

    def _observation(self, item: dict) -> dict:
        data = item.copy()
        if data.get("expires_at"):
            data["expires_at"] = SriLankaTime.iso(data["expires_at"])
        return data
