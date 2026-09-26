# Website Audit: https://www.pmoffice.gov.lk/

- Completed: 2026-09-26 07:14
- Overall result: ⚫ Level 0
- Vantage: 134.33.77.208 (US, github-actions)

## ⚫ Level 0: ✅

A site is classified as `⚫ Level 0` when it is unavailable or unusable, or when there is not enough evidence to establish that it meets `🔴 Level 1`.

Baseline website grade

## 🔴 Level 1: ❓

To pass `🔴 Level 1`, the website must be available, usable, and clearly associated with the government institution. It must load reliably with valid DNS, HTTP, and TLS behavior.

[Errno 104] Connection reset by peer; [Errno 104] Connection reset by peer

| Test | Result | Details |
| --- | --- | --- |
| dns_resolves | ✅ | Public DNS resolved |
| domain_not_parked | ✅ | No parked-domain marker found |
| site_not_defaced | ✅ | No defacement marker found |
| content_relevant | ✅ | No unrelated-content marker found |
| hosting_configured | ✅ | No generic-hosting marker found |
| http_available | ✅ | HTTPS probes passed; failing variants: https://www.pmoffice.gov.lk/: Probe 1: [Errno 104] Connection reset by peer |
| redirect_related | ✅ | No unrelated redirect found |
| tls_browser_trusted | ✅ | No browser-blocking TLS error found |
| tls_not_expired | ❓ | [Errno 104] Connection reset by peer |
| tls_hostname_matches | ❓ | [Errno 104] Connection reset by peer |

## 🟠 Level 2: ❓

To pass `🟠 Level 2`, citizens must be able to identify and contact the correct office for the service they need.

Not run because 🔴 Level 1 did not pass

## 🟢 Level 3: ❓

To pass `🟢 Level 3`, citizens must find complete and current instructions, requirements, fees, times, and usable forms.

Not run because 🟠 Level 2 did not pass
