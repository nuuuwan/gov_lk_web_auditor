import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from glwa.time.SriLankaTime import SriLankaTime
from glwa.uptime.UptimeStats import UptimeStats
from glwa.uptime.UptimeStore import UptimeStore


def _check(status, hours_ago=0, now=None):
    at = (now or SriLankaTime.now()) - timedelta(hours=hours_ago)
    return {"checked_at": at.isoformat(), "status": status}


class TestUptimeStore(unittest.TestCase):
    def test_append_and_read_roundtrip_in_order(self):
        with tempfile.TemporaryDirectory() as folder:
            store = UptimeStore(Path(folder))
            now = SriLankaTime.now()
            store.append({**_check("down", 1, now), "host": "a.gov.lk"})
            store.append({**_check("up", 0, now), "host": "a.gov.lk"})
            checks = store.read("a.gov.lk")
            self.assertEqual(["down", "up"], [c["status"] for c in checks])

    def test_skips_malformed_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            store = UptimeStore(Path(folder))
            path = store.path("a.gov.lk")
            path.parent.mkdir(parents=True)
            path.write_text(
                "{oops\n" + json.dumps({**_check("up"), "host": "a.gov.lk"}) + "\n"
                + json.dumps({"host": "a.gov.lk"}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(1, len(store.read("a.gov.lk")))

    def test_missing_host_reads_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual([], UptimeStore(Path(folder)).read("nope.gov.lk"))

    def test_hosts_lists_only_finished_histories(self):
        with tempfile.TemporaryDirectory() as folder:
            store = UptimeStore(Path(folder))
            store.append({**_check("up"), "host": "a.gov.lk"})
            (Path(folder) / "empty.gov.lk").mkdir()
            self.assertEqual(["a.gov.lk"], store.hosts())


class TestUptimeStats(unittest.TestCase):
    def test_empty_is_unknown(self):
        summary = UptimeStats.summarize([])
        self.assertEqual("unknown", summary["status"])
        self.assertIsNone(summary["last_30_days"]["uptime_pct"])
        self.assertEqual([], summary["history"])

    def test_pct_and_outages(self):
        now = SriLankaTime.now()
        checks = [
            _check("up", 72, now),
            _check("down", 48, now),
            _check("down", 24, now),
            _check("up", 1, now),
            _check("down", 0, now),
        ]
        summary = UptimeStats.summarize(checks, now)
        self.assertEqual(40.0, summary["last_30_days"]["uptime_pct"])
        self.assertEqual(2, summary["last_30_days"]["outages"])
        self.assertEqual("down", summary["status"])
        self.assertEqual(5, summary["total_checks"])

    def test_old_checks_fall_out_of_window(self):
        now = SriLankaTime.now()
        checks = [_check("down", 24 * 40, now), _check("up", 1, now)]
        summary = UptimeStats.summarize(checks, now)
        self.assertEqual(100.0, summary["last_30_days"]["uptime_pct"])
        self.assertEqual(1, summary["last_30_days"]["total"])
        self.assertEqual(1, summary["last_7_days"]["total"])

    def test_history_capped_at_30(self):
        now = SriLankaTime.now()
        checks = [_check("up", hour, now) for hour in range(40, -1, -1)]
        summary = UptimeStats.summarize(checks, now)
        self.assertEqual(30, len(summary["history"]))


if __name__ == "__main__":
    unittest.main()
