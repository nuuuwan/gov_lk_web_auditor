# Website Audit: https://navy.lk/

- Completed: 2026-09-22 06:14
- Overall result: ⚫ Level 0
- Vantage: 20.220.110.149 (CA, github-actions)

## ⚫ Level 0: ✅

A site is classified as `⚫ Level 0` when it is unavailable or unusable, or when there is not enough evidence to establish that it meets `🔴 Level 1`.

Baseline website grade

## 🔴 Level 1: ❓

To pass `🔴 Level 1`, the website must be available, usable, and clearly associated with the government institution. It must load reliably with valid DNS, HTTP, and TLS behavior.

_ssl.c:993: The handshake operation timed out; _ssl.c:993: The handshake operation timed out

| Test | Result | Details |
| --- | --- | --- |
| dns_resolves | ✅ | Public DNS resolved |
| domain_not_parked | ✅ | No parked-domain marker found |
| site_not_defaced | ✅ | No defacement marker found |
| content_relevant | ✅ | No unrelated-content marker found |
| hosting_configured | ✅ | No generic-hosting marker found |
| http_available | ✅ | HTTP probes did not all fail |
| redirect_related | ✅ | No unrelated redirect found |
| tls_browser_trusted | ✅ | No browser-blocking TLS error found |
| tls_not_expired | ❓ | _ssl.c:993: The handshake operation timed out |
| tls_hostname_matches | ❓ | _ssl.c:993: The handshake operation timed out |

## 🟠 Level 2: ❓

To pass `🟠 Level 2`, citizens must be able to identify and contact the correct office for the service they need.

Not run because 🔴 Level 1 did not pass

## 🟢 Level 3: ❓

To pass `🟢 Level 3`, citizens must find complete and current instructions, requirements, fees, times, and usable forms.

Not run because 🟠 Level 2 did not pass
