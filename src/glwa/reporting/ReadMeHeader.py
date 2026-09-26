from ..time.SriLankaTime import SriLankaTime


class ReadMeHeader:
    AUTHORS = ["nuuuwan", "prdai", "dushmilan"]

    def render(self, levels) -> str:
        labels = self._labels(
            level.markdown_label for level in levels if level.implemented
        )
        status = (
            f"> **Implementation status:** Only {labels} are implemented."
        )
        return "\n\n".join(
            [
                "# Grading Government Websites (`glwa`)",
                self._badges(),
                self._description(),
                status,
            ]
        )

    def _badges(self) -> str:
        updated = SriLankaTime.now().strftime("%Y--%m--%d_%H%%3A%M_SLST")
        authors = [
            "[![Author](https://img.shields.io/badge/author-"
            f"{author}-181717?logo=github)](https://github.com/{author})"
            for author in self.AUTHORS
        ]
        license_badge = (
            "[![MIT License](https://img.shields.io/github/license/"
            "nuuuwan/glwa)](LICENSE)"
        )
        updated_badge = (
            "![Last updated](https://img.shields.io/badge/last_updated-"
            f"{updated}-007ec6)"
        )
        return " ".join([license_badge, *authors, updated_badge])

    def _description(self) -> str:
        return (
            "`glwa` audits Sri Lankan government websites using "
            "an evidence-based, cumulative grading model. It records "
            "reproducible evidence for each level and publishes the "
            "latest classification and audit report for every website "
            "in Sri Lanka. 🇱🇰"
        )

    def _labels(self, values) -> str:
        values = list(values)
        if len(values) < 3:
            return " and ".join(values)
        return f"{', '.join(values[:-1])}, and {values[-1]}"
