# Security Audit

Audit date: 2026-09-18  
Scope: application source, workflows, dependency lockfile, report generation, and security-relevant committed data  
Auditor: Codex static review plus local automated checks

## Executive summary

The codebase has several meaningful security issues. The most important risk is that it deliberately visits untrusted websites with a real browser while running in CI, including on a persistent self-hosted runner that holds an OpenAI API key and a repository write token. The browser has no private-network or redirect policy, so a controlled audited site can redirect navigation into services reachable from the runner. The ordinary HTTP client tries to prevent this class of attack, but its DNS check is subject to DNS rebinding because the checked address is not the address pinned for the connection.

The GitHub Actions workflows also interpolate the `shards` dispatch input directly into shell source, the locked `cryptography` version has current published vulnerabilities, and workflow permissions and third-party action pinning do not follow least-privilege/supply-chain best practices.

No hard-coded secrets, direct Python command execution, unsafe deserialization, SQL injection surface, or unescaped HTML injection into the generated dashboard was found. Report HTML consistently escapes the examined untrusted values. The test suite passes, but it does not exercise the trust-boundary failures described below.

### Finding summary

| ID | Severity | Finding | Status |
| --- | --- | --- | --- |
| GLWA-001 | High | Untrusted browser navigation can reach private services from privileged CI runners | Open |
| GLWA-002 | High | HTTP/TLS SSRF protection is vulnerable to DNS rebinding and proxy resolution | Open |
| GLWA-003 | Medium | Workflow-dispatch input is interpolated into shell source | Open |
| GLWA-004 | High | Locked `cryptography` dependency has published vulnerabilities and cannot upgrade within the declared constraint | Open |
| GLWA-005 | Medium | Browser jobs receive unnecessary repository write permissions | Open |
| GLWA-006 | Medium | GitHub Actions use mutable version tags instead of immutable commits | Open |
| GLWA-007 | Medium | Snapshot rechecking trusts arbitrary paths and does not verify snapshot hashes | Open |
| GLWA-008 | Medium | Browser collection has no effective response, DOM, or subresource budget | Open |
| GLWA-009 | Low | Raw active HTML from untrusted sites is stored and distributed as `.html` | Open |
| GLWA-010 | Low | Vantage metadata uses an unauthenticated HTTP lookup | Open |

## Threat model

The principal untrusted inputs are:

- HTML, scripts, redirects, DNS responses, certificates, headers, and URLs controlled by an audited website;
- workflow-dispatch inputs;
- cached audit JSON and snapshot paths;
- LLM-generated page URLs and selectors; and
- third-party packages and GitHub Actions.

Important assets include the self-hosted runner, services reachable from CI networks, `OPENAI_API_KEY`, `GITHUB_TOKEN`, repository contents, generated reports, and the integrity of published audit results.

## Detailed findings

### GLWA-001 — Untrusted browser navigation can reach private services from privileged CI runners

Severity: **High**  
CWE: CWE-918 (Server-Side Request Forgery), CWE-653 (Insufficient Compartmentalization)

The translation verifier launches Chromium and navigates directly to the supplied URL without validating the address before or after redirects. It later revisits both cached and LLM-selected page URLs. There is no request interception, private/link-local/loopback address rejection, origin check after navigation, or network sandbox:

- [`src/glwa/translation/Verifier.py`](src/glwa/translation/Verifier.py#L31-L36)
- [`src/glwa/translation/Verifier.py`](src/glwa/translation/Verifier.py#L183-L220)

This verifier runs in two sensitive contexts:

- the translation-discovery job uses a persistent self-hosted runner and supplies `OPENAI_API_KEY` while the workflow has repository write permissions ([`.github/workflows/translation-mappings.yml`](.github/workflows/translation-mappings.yml#L12-L43));
- the main audit workflow also runs the verifier while the job has a write-capable token ([`.github/workflows/audit.yml`](.github/workflows/audit.yml#L34-L36), [`workflows/pipeline.py`](workflows/pipeline.py#L73-L96)).

An attacker who controls or compromises an audited public site can redirect top-level navigation to `127.0.0.1`, link-local metadata endpoints, RFC 1918 services, or other hosts reachable only from the runner. Unlike a normal cross-origin `fetch`, top-level navigation lets the verifier read the resulting DOM. In discovery mode, control text and attributes from that DOM can be sent to OpenAI. Browser exploitation would also have a materially larger impact because the browser shares a job with secrets and a write-capable repository token. A persistent self-hosted runner increases the persistence and lateral-movement consequences.

Remediation:

1. Run all browser work in a disposable, non-privileged container or VM with an egress firewall/proxy that permits only public HTTP(S) destinations and re-resolves/validates every connection.
2. Deny loopback, private, link-local, multicast, reserved, and cloud-metadata ranges for IPv4 and IPv6 at the network layer. Do not rely solely on page-level URL checks.
3. Validate every navigation and redirect destination, and abort if the final origin is outside the approved public origin policy.
4. Split collection from publication. The browser job should have `contents: read`, no repository write token, and no long-lived secret. Transfer a bounded, inert result artifact to a separate publisher job.
5. Prefer an ephemeral self-hosted runner. If the OpenAI call must remain, give it a short-lived, narrowly scoped credential in a process isolated from Chromium.

### GLWA-002 — HTTP/TLS SSRF protection is vulnerable to DNS rebinding and proxy resolution

Severity: **High**  
CWE: CWE-918 (Server-Side Request Forgery), CWE-367 (Time-of-check Time-of-use Race Condition)

`SafeHttpClient` resolves a hostname and confirms that all returned addresses are public, but discards those addresses. `httpx` then performs a separate resolution when opening the connection:

- validation: [`src/glwa/network/SafeHttpClient.py`](src/glwa/network/SafeHttpClient.py#L65-L71)
- later connection: [`src/glwa/network/SafeHttpClient.py`](src/glwa/network/SafeHttpClient.py#L30-L35)
- resolution result that is never pinned: [`src/glwa/network/DnsResolver.py`](src/glwa/network/DnsResolver.py#L17-L26)

A domain under attacker control can return a public address during validation and a private address during connection. When an HTTP(S) proxy is configured, the proxy may perform its own resolution, also bypassing the local check ([`src/glwa/network/SafeHttpClient.py`](src/glwa/network/SafeHttpClient.py#L23-L29)). The same class of race exists in the raw TLS inspection: an earlier public DNS result gates the operation, but `socket.create_connection((host, port))` resolves the hostname again ([`src/glwa/network/TlsInspector.py`](src/glwa/network/TlsInspector.py#L43-L50)).

The crawler intentionally processes untrusted domains, so control of DNS is a realistic attacker capability. Impact includes scanning or reading runner-reachable HTTP services and making connections to sensitive ports. Retrieved HTML is parsed and stored, increasing the potential for disclosure.

Remediation:

1. Resolve once, validate every resolved address, and connect to a selected validated IP while preserving the original HTTP `Host` header and TLS SNI/hostname verification.
2. Verify the actual connected peer address before accepting data. Repeat the policy on every redirect.
3. If proxies are supported, require a trusted proxy that enforces the same destination ACL. Otherwise disable proxy inheritance for security-sensitive requests.
4. Apply the same connection primitive to HTTP probing and TLS inspection.
5. Add DNS-rebinding tests that make validation and connection resolve to different addresses, plus IPv4, IPv6, redirect, and proxy cases.

### GLWA-003 — Workflow-dispatch input is interpolated into shell source

Severity: **Medium**  
CWE: CWE-78 (OS Command Injection)

Both shard setup jobs place `${{ inputs.shards }}` directly into a `run:` script:

- [`.github/workflows/audit.yml`](.github/workflows/audit.yml#L49-L55)
- [`.github/workflows/uptime.yml`](.github/workflows/uptime.yml#L39-L45)

GitHub expression substitution occurs before the shell parses the script. A value containing shell syntax such as command substitution therefore becomes executable shell source. Workflow dispatch normally requires repository privileges, which limits who can exploit this, but the jobs inherit workflow-level write permissions. This can turn limited workflow-dispatch access or an account mistake into arbitrary commands under a write-capable `GITHUB_TOKEN`.

Remediation:

- Pass the value through `env`, then validate it with a strict numeric expression before arithmetic use, for example `[[ "$SHARDS" =~ ^[1-9][0-9]*$ ]]`.
- Enforce a sensible upper bound to prevent matrix/resource abuse.
- Keep the setup job at `contents: read` or `permissions: {}`.
- Add a workflow test covering metacharacters, negative values, zero, very large values, and non-numeric input.

### GLWA-004 — Locked `cryptography` dependency has published vulnerabilities

Severity: **High**  
CWE: CWE-1395 (Dependency on Vulnerable Third-Party Component)

The lockfile selects `cryptography==46.0.7` ([`uv.lock`](uv.lock#L153-L155)), while the project constraint is `cryptography>=45.0,<47` ([`pyproject.toml`](pyproject.toml#L6-L11)). A current `pip-audit` scan reported seven advisory records representing four unique advisories against this version:

- [GHSA-537c-gmf6-5ccf](https://github.com/advisories/GHSA-537c-gmf6-5ccf), fixed in 48.0.1;
- [CVE-2026-69248 / GHSA-m2h6-j472-rp4c](https://github.com/advisories/GHSA-m2h6-j472-rp4c), fixed in 49.0.0;
- [CVE-2026-69249 / GHSA-jwv3-5hgf-82ww](https://github.com/advisories/GHSA-jwv3-5hgf-82ww), fixed in 49.0.0; and
- [CVE-2026-69247 / GHSA-g6cj-pr64-35w5](https://github.com/advisories/GHSA-g6cj-pr64-35w5), fixed in 50.0.0.

Some vulnerable APIs, notably PKCS#7 decryption and the newer chain verifier, are not called by this repository. However, the package is used to parse certificates obtained from untrusted servers ([`src/glwa/network/TlsInspector.py`](src/glwa/network/TlsInspector.py#L10-L17)), and the bundled-OpenSSL advisory is rated high for remote availability impact. The `<47` ceiling prevents every available complete fix.

Remediation:

- Raise the allowed range to a tested release at or above 50.0.0, regenerate `uv.lock`, and rerun tests and `pip-audit`.
- Add Dependabot/Renovate and a CI advisory scan so a restrictive upper bound cannot silently block security updates.
- If immediate upgrade is impossible, document why each advisory is unreachable and install `cryptography` from a build linked to a patched OpenSSL where applicable; this is only a temporary mitigation.

### GLWA-005 — Browser jobs receive unnecessary repository write permissions

Severity: **Medium**  
CWE: CWE-250 (Execution with Unnecessary Privileges)

`contents: write` and `pull-requests: write` are set at workflow scope in the audit, uptime, and translation workflows. This grants the setup and network-processing jobs permissions they do not require:

- [`.github/workflows/audit.yml`](.github/workflows/audit.yml#L34-L36)
- [`.github/workflows/uptime.yml`](.github/workflows/uptime.yml#L24-L26)
- [`.github/workflows/translation-mappings.yml`](.github/workflows/translation-mappings.yml#L12-L14)

The audit and translation jobs process hostile network content and run a browser. `pull-requests: write` is unused in the audit and uptime workflows. Broad tokens magnify any dependency, browser, shell-injection, or action compromise.

Remediation:

- Default each workflow to `permissions: contents: read` (or `{}` where checkout is not needed).
- Put commits/PR creation in a separate job with only the exact write permission it needs.
- Pass reviewed artifacts to that job; do not expose its token to browser or crawler processes.
- Consider GitHub environments with approval for publication.

### GLWA-006 — GitHub Actions use mutable version tags

Severity: **Medium**  
CWE: CWE-494 (Download of Code Without Integrity Check)

Every third-party action is referenced through a mutable major-version tag, including `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`, `astral-sh/setup-uv@v6`, and `peter-evans/create-pull-request@v7`. The last action runs in a workflow with an API key and repository write permissions.

If an upstream action tag or publisher account is compromised, the replacement code executes with the job's credentials. The lockfile protects Python packages but does not protect action code.

Remediation:

- Pin every action to a full audited commit SHA and keep a version comment beside it.
- Use Dependabot's `github-actions` ecosystem to propose controlled SHA updates.
- Combine pinning with the per-job permission reduction in GLWA-005.

### GLWA-007 — Snapshot rechecking trusts arbitrary paths and does not verify hashes

Severity: **Medium**  
CWE: CWE-22 (Path Traversal), CWE-345 (Insufficient Verification of Data Authenticity)

Snapshot metadata includes a SHA-256 digest and byte count when created ([`src/glwa/reporting/SnapshotStore.py`](src/glwa/reporting/SnapshotStore.py#L8-L21)), but rechecking ignores both. It constructs `Path(snapshot["path"])` and reads any existing file ([`src/glwa/audit/SnapshotRechecker.py`](src/glwa/audit/SnapshotRechecker.py#L54-L60)). There is no requirement that the path be relative, remain under the selected audit directory, or match the recorded hash and size.

A tampered or externally supplied audit record can therefore make the rechecker read an arbitrary file available to the process and treat it as HTML. Extracted email, phone, address, and other matching fragments can flow into generated reports. Even without disclosure, this breaks the claimed reproducibility and integrity of cached audit evidence.

Remediation:

- Resolve snapshot paths against an explicit audit root, reject absolute paths and traversal, and verify `resolved_path.is_relative_to(root.resolve())`.
- Recompute and constant-time compare the SHA-256 digest and verify the byte count before parsing.
- Reject, rather than silently skip, integrity failures and surface them in the audit result.
- Store paths relative to the audit folder to avoid trusting process-working-directory state.

### GLWA-008 — Browser collection has no effective response, DOM, or subresource budget

Severity: **Medium**  
CWE: CWE-400 (Uncontrolled Resource Consumption)

The ordinary HTTP crawler limits decoded response content to 1 MB, but the Playwright path has no equivalent cap. It loads page scripts and subresources, obtains the entire body text, and evaluates over every matching interactive element before truncating the resulting Python string to 20,000 characters ([`src/glwa/translation/Verifier.py`](src/glwa/translation/Verifier.py#L36-L64)). Up to eight independent verification tasks run by default ([`workflows/translation_pipeline.py`](workflows/translation_pipeline.py#L13-L18), [`workflows/translation_pipeline.py`](workflows/translation_pipeline.py#L42-L58)).

A malicious site can create an extremely large DOM, stream or allocate data, spawn expensive workers, or request large/continuous subresources. String truncation occurs after browser evaluation and transfer, so it is not a resource limit. On the six-hour self-hosted workflow this can exhaust memory, CPU, bandwidth, or worker availability.

Remediation:

- Enforce per-site wall-clock, request-count, response-byte, DOM-node, and total-resource budgets.
- Abort images, media, fonts, downloads, WebSockets, workers, and unrelated third-party requests unless necessary.
- Limit elements inside the browser expression (for example, slice before mapping and cap every text/attribute length).
- Run each site in a disposable process/container with OS memory, CPU, process, and network quotas.
- Ensure browser/context cleanup occurs in `finally` blocks.

### GLWA-009 — Raw active HTML is stored and distributed as `.html`

Severity: **Low**  
CWE: CWE-79 (Improper Neutralization of Input During Web Page Generation)

`SnapshotStore` writes fetched, attacker-controlled HTML byte-for-byte to files with an `.html` extension ([`src/glwa/reporting/SnapshotStore.py`](src/glwa/reporting/SnapshotStore.py#L12-L20)). The audit workflow uploads the snapshot tree as an artifact ([`.github/workflows/audit.yml`](.github/workflows/audit.yml#L102-L111)), and snapshot files are also committed in this repository.

The dashboard does not directly serve these files, which limits exposure. Nevertheless, a reviewer who opens a downloaded snapshot in a browser executes its scripts as active local content and may trigger network requests, deceptive UI, or browser-specific local-file attacks.

Remediation:

- Store snapshots as `.txt`/`.html.txt`, compressed inert blobs, or escaped source views.
- If browser viewing is required, sanitize active content and serve it with a restrictive `Content-Security-Policy` and sandboxed iframe from an isolated origin.
- Add a warning to artifact/report documentation not to open raw snapshots directly.

### GLWA-010 — Vantage metadata uses an unauthenticated HTTP lookup

Severity: **Low**  
CWE: CWE-319 (Cleartext Transmission of Sensitive Information)

Country lookup requests use `http://ip-api.com` in application code and CI logging:

- [`src/glwa/network/VantageProbe.py`](src/glwa/network/VantageProbe.py#L7-L8)
- [`src/glwa/network/VantageProbe.py`](src/glwa/network/VantageProbe.py#L34-L42)
- [`.github/workflows/audit.yml`](.github/workflows/audit.yml#L80-L83)
- [`.github/workflows/uptime.yml`](.github/workflows/uptime.yml#L66-L69)

A network observer can see the queried egress IP and alter the country/organization response, corrupting provenance metadata. This does not affect the core classification logic, so severity is low.

Remediation: use an HTTPS endpoint, require a successful status, validate the returned IP/country-code shape, and avoid duplicate egress-IP lookups.

## Positive security controls observed

- URL normalization accepts only HTTP(S) and rejects embedded credentials.
- Redirect count and ordinary crawler body size are bounded.
- DNS validation rejects non-global addresses in the common, non-rebinding case.
- Generated HTML reports and dashboard pages consistently use `html.escape` for examined untrusted text.
- Audit JSON has a restrictive schema with enums and `additionalProperties: false` in important objects.
- Python dependencies are locked with hashes in `uv.lock`.
- No unsafe `pickle`, `eval`, `exec`, `shell=True`, dynamic SQL, or YAML deserialization was found.
- No likely hard-coded credentials or private keys were found by repository pattern search.
- The translation flow rejects LLM-proposed pages whose `netloc` differs from the source URL.

## Verification performed

- Manual review of all Python application modules, workflow entry points, report/dashboard renderers, GitHub Actions workflows, and dependency declarations.
- Security-focused data-flow review for network requests, redirects, DNS, TLS, filesystem paths, HTML/Markdown/CSV output, browser automation, secrets, and CI permissions.
- Secret-pattern scan across tracked source/configuration files; no likely secrets found.
- `python -m unittest discover -s tests -v`: **145 passed, 2 skipped**.
- `pip-audit` against requirements exported from `uv.lock`: **7 advisory records in one package**, representing the four unique `cryptography` advisories listed in GLWA-004; no advisories were reported for the other locked packages.

## Recommended remediation order

1. Isolate browser execution, block private-network destinations at egress, remove write tokens/secrets from browser jobs, and make the self-hosted runner ephemeral (GLWA-001, GLWA-005).
2. Replace the check-then-resolve HTTP/TLS design with address-pinned connections and peer validation (GLWA-002).
3. Upgrade `cryptography` to at least 50.0.0 and refresh the lockfile (GLWA-004).
4. Fix workflow input handling and pin actions to commits (GLWA-003, GLWA-006).
5. Add snapshot containment/integrity checks and browser resource budgets (GLWA-007, GLWA-008).
6. Make stored snapshots inert and move vantage lookup to HTTPS (GLWA-009, GLWA-010).

## Limitations

This was a source and configuration audit, not an authorized penetration test of the listed government websites or GitHub infrastructure. No live targets were attacked. Repository settings outside the checkout—branch protection, environment approvals, runner network ACLs, secret scopes, organization policies, and token restrictions—were not visible and may reduce or increase the practical impact. The dependency assessment reflects advisories available on 2026-09-18.
