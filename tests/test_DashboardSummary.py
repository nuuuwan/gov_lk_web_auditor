import unittest

from glwa.dashboard.DashboardSummary import DashboardSummary


def _site(level, score, completed="2026-09-05T10:00:00+05:30"):
    return {
        "level": level,
        "score": score,
        "completed_at": completed,
    }


class TestDashboardSummary(unittest.TestCase):
    def test_counts_levels_averages_scores_and_last_audit(self):
        sites = [
            _site(0, 0.3, "2026-09-04T10:00:00+05:30"),
            _site(1, 1.7, "2026-09-05T10:00:00+05:30"),
            _site(2, 2.1, "2026-09-05T11:00:00+05:30"),
        ]
        summary = DashboardSummary().summarize(sites)
        self.assertEqual(3, summary["total"])
        self.assertEqual(1, summary["by_level"][0])
        self.assertEqual(1, summary["by_level"][1])
        self.assertEqual(1, summary["by_level"][2])
        self.assertEqual(0, summary["by_level"][3])
        self.assertEqual(1.4, summary["average_score"])
        self.assertEqual("2026-09-05T11:00:00+05:30", summary["last_audit"])
        self.assertEqual(3, summary["max_score"])

    def test_empty_input_has_sane_defaults(self):
        summary = DashboardSummary().summarize([])
        self.assertEqual(0, summary["total"])
        self.assertEqual(0.0, summary["average_score"])
        self.assertEqual("", summary["last_audit"])


if __name__ == "__main__":
    unittest.main()
