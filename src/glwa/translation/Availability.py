from __future__ import annotations


def check(status: int | None, final_url: str, visible_text: str) -> dict | None:
    if status is None:
        return {
            "status": "unavailable",
            "reason": "browser navigation returned no HTTP response",
            "final_url": final_url,
        }
    if status >= 400:
        return {
            "status": "unavailable",
            "reason": f"browser navigation returned HTTP {status}",
            "http_status": status,
            "final_url": final_url,
        }
    if not visible_text.strip():
        return {
            "status": "unusable",
            "reason": "page contains no visible text",
            "http_status": status,
            "final_url": final_url,
        }
    return None
