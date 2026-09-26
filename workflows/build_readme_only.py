from pathlib import Path

from src.glwa.reporting.ReadMe import ReadMe


class BuildReadMeOnly:
    def __init__(
        self,
        target: Path = Path("README.md"),
        reports: Path = Path("latest_audit_reports"),
    ):
        self.target = target
        self.reports = reports

    def run(self) -> Path:
        return ReadMe(self.target).update(self.reports)


if __name__ == "__main__":
    BuildReadMeOnly().run()
