# Website Audit: https://npa.gov.lk/

- Completed: 2026-09-09 00:00
- Overall result: ⚫ Level 0

## ⚫ Level 0: ✅

A site is classified as `⚫ Level 0` when it is unavailable or unusable, or when there is not enough evidence to establish that it meets `🔴 Level 1`.

Baseline website grade

## 🔴 Level 1: ❌

To pass `🔴 Level 1`, the website must be available, usable, and clearly associated with the government institution. It must load reliably with valid DNS, HTTP, and TLS behavior.

Probe 1: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1032)

| Test | Result | Details |
| --- | --- | --- |
| dns_resolves | ✅ | Public DNS resolved |
| domain_not_parked | ✅ | No parked-domain marker found |
| site_not_defaced | ✅ | No defacement marker found |
| content_relevant | ✅ | No unrelated-content marker found |
| hosting_configured | ✅ | No generic-hosting marker found |
| http_available | ✅ | HTTP probes did not all fail |
| redirect_related | ✅ | No unrelated redirect found |
| tls_browser_trusted | ❌ | Probe 1: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1032) |
| tls_not_expired | ✅ | TLS certificate valid |
| tls_hostname_matches | ✅ | TLS certificate valid |
