from __future__ import annotations

from urllib.parse import urlsplit


KNOWN_DYNAMIC_HOSTS = {
    "translate.googleapis.com",
    "translate-pa.googleapis.com",
    "translate.google.com",
}


def classify(request_urls: list[str], page_url: str) -> dict:
    page_host = urlsplit(page_url).hostname or ""
    dynamic = []
    same_origin = []
    candidates = []
    for value in dict.fromkeys(request_urls):
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if host in KNOWN_DYNAMIC_HOSTS:
            dynamic.append(value)
            continue
        if host == page_host:
            same_origin.append(value)
            if any(term in value.lower() for term in ("lang", "locale", ".json", "sinhala", "tamil")):
                candidates.append(value)
    if dynamic:
        kind = "dynamic"
    elif candidates:
        kind = "static_candidate"
    else:
        kind = "unknown"
    return {
        "type": kind,
        "dynamic_urls": dynamic,
    }
