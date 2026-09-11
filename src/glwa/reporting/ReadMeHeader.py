from ..time.SriLankaTime import SriLankaTime


class ReadMeHeader:
    def render(self, levels) -> str:
        updated = SriLankaTime.now().strftime("%Y--%m--%d_%H%%3A%M_SLST")
        labels = self._labels(
            level.markdown_label for level in levels if level.implemented
        )
        return (
            "# Grading Government Websites (`glwa`)\n\n"
            "[![MIT License](https://img.shields.io/github/license/"
            "nuuuwan/glwa)](LICENSE) "
            "[![Author](https://img.shields.io/badge/author-nuuuwan-"
            "181717?logo=github)](https://github.com/nuuuwan) "
            "[![Author](https://img.shields.io/badge/author-Dushmilan-"
            "181717?logo=github)](https://github.com/Dushmilan) "
            f"![Last updated](https://img.shields.io/badge/last_updated-"
            f"{updated}-007ec6)\n\n"
            "`glwa` audits Sri Lankan government websites using "
            "an evidence-based, cumulative grading model. It records "
            "reproducible evidence for each level and publishes the "
            "latest classification and audit report for every website "
            "in Sri Lanka. 🇱🇰\n\n"
            f"> **Implementation status:** Only {labels} are "
            "implemented."
        )

    def _labels(self, values) -> str:
        values = list(values)
        if len(values) < 3:
            return " and ".join(values)
        return f"{', '.join(values[:-1])}, and {values[-1]}"
