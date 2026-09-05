from urllib.parse import urlsplit

from ...models.CheckResult import CheckResult
from ...models.Evidence import Evidence
from ..Check import Check


class HttpAvailableCheck(Check):
    FAILURE = "persistent_http_failure"

    def __init__(self):
        super().__init__("http_available", 1)

    def run(self, evidence: list[Evidence]) -> CheckResult:
        for item in evidence:
            if item.check == self.FAILURE and item.status == "fail":
                return self.result("fail", item.detail)
        http = [item for item in evidence if item.check == "http"]
        errors = [item for item in http if item.status == "error"]
        https_ok = any(
            item.status == "pass"
            and urlsplit(item.source or "").scheme == "https"
            for item in http
        )
        if https_ok and errors:
            failing = "; ".join(
                f"{item.source}: {item.detail}" for item in errors
            )
            return self.result(
                "pass",
                "HTTPS probes passed; failing variants: " + failing,
            )
        if errors:
            status, reason = "inconclusive", "An HTTP probe was transient"
        elif http:
            status, reason = "pass", "HTTP probes did not all fail"
        else:
            status, reason = "inconclusive", "HTTP checks did not run"
        return self.result(status, reason)
