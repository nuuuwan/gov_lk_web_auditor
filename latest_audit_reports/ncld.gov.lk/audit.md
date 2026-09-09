# Website Audit: http://ncld.gov.lk/

- Completed: 2026-09-09 00:04
- Overall result: ⚫ Level 0

## ⚫ Level 0: ✅

A site is classified as `⚫ Level 0` when it is unavailable or unusable, or when there is not enough evidence to establish that it meets `🔴 Level 1`.

Baseline website grade

## 🔴 Level 1: ❌

To pass `🔴 Level 1`, the website must be available, usable, and clearly associated with the government institution. It must load reliably with valid DNS, HTTP, and TLS behavior.

Probe 1: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: EE certificate key too weak (_ssl.c:1032); TLS certificate has expired

| Test | Result | Details |
| --- | --- | --- |
| dns_resolves | ✅ | Public DNS resolved |
| domain_not_parked | ❓ | Insufficient substantive page content: Only 152 visible characters across 2 pages; below substance threshold 200 |
| site_not_defaced | ❓ | Insufficient substantive page content: Only 152 visible characters across 2 pages; below substance threshold 200 |
| content_relevant | ❓ | Insufficient substantive page content: Only 152 visible characters across 2 pages; below substance threshold 200 |
| hosting_configured | ❓ | Insufficient substantive page content: Only 152 visible characters across 2 pages; below substance threshold 200 |
| http_available | ✅ | HTTP probes did not all fail |
| redirect_related | ❓ | No redirect result was available |
| tls_browser_trusted | ❌ | Probe 1: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: EE certificate key too weak (_ssl.c:1032) |
| tls_not_expired | ❌ | TLS certificate has expired |
| tls_hostname_matches | ❓ | TLS hostname check did not run |
