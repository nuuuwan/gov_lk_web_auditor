# glwa (Design)

_Evidence-based classification for government websites._

`glwa` takes a public website URL and reports the highest government-service level it can substantiate: **Level 0** (unavailable or non-functional) through **Level 5** (proactive, interoperable digital public services).

It is inspired by the Level 0–5 framework, originally described in [Grading Government Websites](README.article.md) by @nuuuwan.

## What the tool produces

```json
{
  "url": "https://example.gov.lk",
  "levels": [
    { "level": 0, "status": "pass", "executed": true },
    { "level": 1, "status": "inconclusive", "executed": false },
    { "level": 2, "status": "inconclusive", "executed": false },
    { "level": 3, "status": "inconclusive", "executed": false },
    { "level": 4, "status": "inconclusive", "executed": false },
    { "level": 5, "status": "inconclusive", "executed": false }
  ],
  "evidence": [{ "check": "https", "status": "pass", "source": "https://..." }]
}
```

## Run audits

```bash
uv sync
uv run playwright install chromium
uv run python workflows/pipeline.py
```

The pipeline audits every ministry URL in the government web directory. Each
Raw audits are stored under `audit.output/<host>/<timestamp>` with snapshots.
The latest rendered files are stored under `latest_audit_reports/<host>` and
can be regenerated from raw audit data. Each audit performs at
least two HTTPS and HTTP probes from the local vantage point. Independent
geographic probes must run the pipeline from separate environments.

Each website reports `pass`, `fail`, or `inconclusive` for Levels 0–5. A failed
level prevents all higher-level checks from running. After the pipeline
finishes, it regenerates `README.md` with a summary of the latest audits.
Level 0 is the fallback grade when Level 1 cannot be established. A site passes
Level 1 when no reproducible unavailable or unusable condition is found, fails
when such a condition is confirmed, and is otherwise inconclusive.

Level 2 publication checks pass automatically when valid page evidence is
found. Checks without sufficient automated evidence remain inconclusive.
Supported checks are `postal_address`, `phone`, `email`, and
`named_responsibility`.
The collector follows up to ten same-site pages, including ordinary links from
language-selection pages, and prioritizes contact, service, department,
division, and office URLs.

Level 3 requires published eligibility criteria, required documents, fees and
payment information, a legal basis, processing time, a downloadable non-image
form, and a visible update date. Update dates older than 730 days fail the
freshness check. Missing Level 3 evidence remains inconclusive.

## Translation verification

The first run asks the LLM to discover a flow and upserts its reusable mapping
under `translation_mappings/<host>.json`:

```bash
PYTHONPATH=. uv run python workflows/translation_verification.py https://example.gov.lk/
```

The committed mapping records the final URL, interactive DOM fingerprint,
selected pages, and one locator action for each official language. Replay it
without an LLM call:

```bash
PYTHONPATH=. uv run python workflows/translation_verification.py \
  https://example.gov.lk/ \
  --mapping translation_mappings/example.gov.lk.json \
  --replay
```

Replay refuses stale mappings when the interactive DOM fingerprint changes.
Each replay records visible-text script coverage and observed translation-related
network URLs.

## Classification rules

Levels are cumulative. The reported level is the **highest level for which all required lower-level conditions are evidenced**. If a criterion cannot be determined safely by automation, do not guess: mark it inconclusive and lower the confidence.

| Level | Citizen experience                                             | Core evidence                                                                                                                  |
| ----- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 0     | There is no usable government website.                         | Domain, DNS, HTTPS, response, page-content checks show absence, failure, takeover, or unrelated/compromised content.           |
| 1     | The official website exists and is reachable.                  | Reliable HTTPS, authentic institution identity, plausible official domain, recently maintained content.                        |
| 2     | A citizen can find the right office and contact it.            | Address, working contact routes, named responsibility.                                                                         |
| 3     | A citizen can prepare correctly before visiting.               | Eligibility, documents, fees and payment, legal basis, processing times, downloadable forms, freshness.                        |
| 4     | A citizen can complete and follow a transaction online.        | Submission, uploads, payment and receipt, tracking, outcome, standards and traceable complaints.                               |
| 5     | Government services are connected, proactive, and accountable. | Multilingual routing, interoperability, machine-readable rules, proactive entitlements, explainable decisions, open APIs/data. |
