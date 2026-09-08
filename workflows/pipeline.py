import argparse
from pathlib import Path

from src.glwa import AuditRunner
from src.glwa.audit.AuditHistory import AuditHistory
from src.glwa.audit.SnapshotRechecker import SnapshotRechecker
from src.glwa.classification.LevelEvaluator import LevelEvaluator
from src.glwa.directory.Directory import Directory
from src.glwa.reporting.ReadMe import ReadMe
from src.glwa.reporting.ReportWriter import ReportWriter
from src.glwa.reporting.WebsiteScore import WebsiteScore
from src.glwa.translation import TranslationBatchVerifier


class Pipeline:
    PATH_HISTORY = Path("audit.output")
    PATH_REPORTS = Path("latest_audit_reports")
    URLS = Path("static_data") / "websites.json"

    def __init__(self, max_urls=None):
        self.max_urls = max_urls

    def _level(self, audit):
        passed = [
            item.level for item in audit.levels if item.status == "pass"
        ]
        number = max(passed, default=0)
        level = LevelEvaluator.LEVELS[number]
        return level.label

    def _summary(self, audit):
        calculator = WebsiteScore()
        score = calculator.calculate(audit.to_dict())
        return f"{self._level(audit)}, {score:.1f}/{calculator.maximum}"

    def _limit(self, urls):
        if self.max_urls is None:
            return urls
        return urls[: self.max_urls]

    def _urls(self) -> list[str]:
        return Directory(self.URLS).urls()

    def run(self):
        runner = AuditRunner()
        writer = ReportWriter()
        translations = TranslationBatchVerifier(self.PATH_REPORTS)
        history = AuditHistory(self.PATH_HISTORY)
        rechecker = SnapshotRechecker()
        urls = self._limit(self._urls())
        n_urls = len(urls)
        for index, url in enumerate(urls, start=1):
            if history.fresh(url):
                audit = rechecker.run(history.latest(url))
                writer.write(audit, self.PATH_REPORTS / history.host(url))
                translation = translations.run(url)
                print(
                    f"{index}/{n_urls}). {url}: "
                    f"{self._summary(audit)} (cached), "
                    f"translation {translation.get('status', 'checked')}"
                )
                continue
            output = history.folder(url)
            audit = runner.run(url, output)
            history.write(audit, output)
            writer.write(audit, self.PATH_REPORTS / history.host(url))
            translation = translations.run(url)
            print(
                f"{index}/{n_urls}). {url}: {self._summary(audit)}, "
                f"translation {translation.get('status', 'checked')}"
            )
        ReadMe().update(self.PATH_REPORTS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-urls", type=int)
    args = parser.parse_args()
    Pipeline(max_urls=args.max_urls).run()
