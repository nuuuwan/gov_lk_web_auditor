from abc import ABC, abstractmethod

from ..models.CheckResult import CheckResult
from ..models.Evidence import Evidence


class Check(ABC):
    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level

    @abstractmethod
    def run(self, evidence: list[Evidence]) -> CheckResult:
        raise NotImplementedError()

    def result(self, status: str, reason: str) -> CheckResult:
        return CheckResult(self.name, self.level, status, reason)

    def substance_gate(self, evidence: list[Evidence]) -> str | None:
        for item in evidence:
            if item.check == "page_text" and item.status == "fail":
                return (
                    "Insufficient substantive page content: " + item.detail
                )
        return None
