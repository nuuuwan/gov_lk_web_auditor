from __future__ import annotations

from datetime import datetime, timedelta


class UptimeStats:
    @classmethod
    def summarize(cls, checks: list[dict], now: datetime | None = None) -> dict:
        ordered = sorted(checks, key=lambda item: str(item.get("checked_at", "")))
        latest = ordered[-1] if ordered else None
        last_down = next(
            (item.get("checked_at") for item in reversed(ordered)
             if item.get("status") == "down"),
            None,
        )
        return {
            "status": str(latest.get("status", "unknown")) if latest else "unknown",
            "last_checked_at": latest.get("checked_at") if latest else None,
            "last_down_at": last_down,
            "total_checks": len(ordered),
            "last_7_days": cls._window(ordered, 7, now),
            "last_30_days": cls._window(ordered, 30, now),
            "history": [
                {
                    "checked_at": item.get("checked_at"),
                    "status": item.get("status"),
                    "reason": item.get("reason"),
                }
                for item in ordered[-30:]
            ],
        }

    @classmethod
    def _window(cls, ordered: list[dict], days: int, now=None) -> dict:
        from ..time.SriLankaTime import SriLankaTime

        current = SriLankaTime.normalize(now) if now else SriLankaTime.now()
        cutoff = current - timedelta(days=days)
        window = [item for item in ordered if cls._at(item) >= cutoff]
        up = sum(1 for item in window if item.get("status") == "up")
        down = sum(1 for item in window if item.get("status") == "down")
        return {
            "total": len(window),
            "up": up,
            "down": down,
            "uptime_pct": round(100.0 * up / len(window), 1) if window else None,
            "outages": cls._outages(window),
        }

    @staticmethod
    def _at(item: dict):
        from ..time.SriLankaTime import SriLankaTime

        try:
            return SriLankaTime.parse(str(item.get("checked_at", "")))
        except ValueError:
            return SriLankaTime.now() - timedelta(days=3650)

    @staticmethod
    def _outages(window: list[dict]) -> int:
        outages = 0
        was_down = False
        for item in window:
            is_down = item.get("status") == "down"
            if is_down and not was_down:
                outages += 1
            was_down = is_down
        return outages
