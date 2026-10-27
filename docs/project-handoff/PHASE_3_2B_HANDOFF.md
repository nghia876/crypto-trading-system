# Phase 3.2B: Evidence-backed claim relationships and lifecycle

Date: 2026-10-27 (Asia/Saigon). Phase 3 remains IN_PROGRESS.
Release gate: locally verified bounded implementation; operational live gate NOT PASSED.

## Baseline and preservation

Verified before edits: branch `phase-3-event-narrative-slice`, HEAD
`bb878a069d70beb9a1e78e8b46ea019ddf2a03f5`; tracked tree clean; only pre-existing
`.phase12-tools/` untracked. Origin fetch/push URL:
`https://github.com/nghia876/crypto-trading-system.git`. No push, merge, reset,
main modification, source reference edits or staging of `.phase12-tools/`.
The canonical read-only PRODUCT_BLUEPRINT, MASTER_PROMPT and RESOURCE_MANIFEST,
Phase 3 architecture, 3.2A handoff and project status were read. The referenced
Phase 3 conversation was retrieved: assistant messages remain opaque references;
the current detailed user request supplies the implementation authority.

The product continues to acquire broad financial AND nonfinancial world evidence
independently of BTC keywords and price triggers. War/geopolitics, technology,
trade, energy, cyber and crypto remain valid domains. The existing free BBC/GDELT
acquisition configurations and Fed v1 adapter are preserved. No new paid provider,
mandatory external service, second system or evidence database was introduced.
Critical causal reasoning, world/regime, scenario, risk, execution and learning
remain subsequent blueprint layers; no trading effectiveness is claimed.

## Implemented contracts

`tradingagents/information/claim_lifecycle.py` extends existing Observation,
Transformation, MarketDataBatch, InformationView and SQLiteInformationStore:

- `correlation_candidates(view)` returns exact whitespace/case-normalized headline
  matches as REVIEW CANDIDATES. It never automatically merges semantically different
  stories or treats identical headlines as confirmation.
- `record_claim_assertion` records an explicit caller-curated claim relationship
  with rationale and full source observation IDs. Claim identity is an existing
  narrative article/event subject, preserving the original domain-independent
  acquisition contracts. A support/opposition assertion explicitly correlates
  another source's report with that claim; similarity alone does not do so.
- Kinds: support, confirmation, opposition, contradiction, correction, supersession,
  resolution, origin, syndication, independence, official_report. Correction,
  supersession, resolution, origin, syndication and independence require targets. Provenance targets are source
  observations; correction/supersession/resolution targets are earlier assertions
  for the same claim. Unknown IDs, future evidence, absent claim roots, unsupported
  kinds, cross-claim retraction and self provenance relationships are rejected.
- Each assertion has its own immutable ID/subject and local timestamp; no mutable
  claim-status column or store migration. Exact retries are idempotent; changed
  assertions append new records. Source reports retain publication, first-seen,
  retrieval, conservative local availability, URL, source, parser and version
  provenance in the SAME SQLite store. Assertion timestamps represent when the
  curated relationship became locally available, not when the world event happened.
- `InformationView.evidence_history` adds eligible immutable versions, including
  superseded source copies, so old assertion evidence remains resolvable after an
  article correction. Existing `observations` current-version behavior is unchanged;
  market-state consumers continue to use that field. Only records eligible at T
  enter either view; future publication/update/local acquisition remains excluded.
- `claim_lifecycle(view, claim_id)` derives all states at cutoff T. History remains
  append-only. Corrections and supersessions retire only explicitly named assertions;
  resolution retires named assertions and reports resolved when it is the latest
  active assertion and there is no remaining opposition. Later opposition reopens
  contested state. Retraction is monotonic: correcting a correction does not silently
  resurrect its former targets; append new evidence assertions deliberately.
- Independent corroboration requires active supporting evidence on both sides AND
  an explicit evidence-backed independence relationship. Different hosts, article
  IDs, publishers or official status alone are insufficient. Same acquisition source
  or same canonical subject cannot count as independent. Origin/syndication dependency
  components override independence, including multi-hop chains and later versions of
  the same article subject. This is a conservative report-level relationship model,
  not a calibrated publisher credibility model or proof of factual truth.
- `official_report` is separate from independence. `factual_truth` remains UNKNOWN
  even for independently corroborated reporting. Opposition/contradiction produces
  contested status, not a machine judgment that one side is true.
- `lifecycle_prompt` enters the EXISTING narrative_events renderer, consumer and
  actual Market Analyst graph. It includes support/opposition IDs, source claims,
  URLs, publication/first-seen/retrieval/availability, assertion rationale and history,
  and explicit uncertainty. Lifecycle records replace redundant base presentation
  fields to fit the existing 4,000-character narrative reservation; overall context
  remains <=28,000 characters. Oversized whole claim records are omitted with the
  existing omission warning. Full histories stay in SQLite; prompt omissions are
  never evidence of absence or resolution. This is not a full-conversation/token bound.

No automatic semantic NLP extractor, origin finder, contradiction search or
independence classifier is claimed. Curated relationships are inspectable assertions,
not facts vouched for by deterministic code. Automated acquisition remains conservative
and unconfirmed until explicit relationships are supplied. Feed headlines are the
available source evidence; full article bodies/raw HTTP responses are still not archived.

## API in the same integrated codebase

```python
from tradingagents.information.claim_lifecycle import (
    correlation_candidates, record_claim_assertion, claim_lifecycle,
)

# store is the existing SQLiteInformationStore at graph information_store_path.
# t is an aware LOCAL recording time, never a historical publication backdate.
candidates = correlation_candidates(store.view_at(t))
record = record_claim_assertion(
    store, claim_id=existing_article_subject, kind="opposition",
    evidence_ids=(opposing_source_observation_id,), recorded_at=t,
    rationale="Explicit source passage contradicts the reported claim",
)
state = claim_lifecycle(store.view_at(t), existing_article_subject)
# No new graph entry point: graph.propagate(..., decision_time=t) reads this store.
# To correct record later, append kind="correction" with new source evidence and
# target_ids=(record.observation_id,). Add new support separately when warranted.
```

## Network diagnosis: live gate remains unverified

At 2026-10-27 17:39:20 Asia/Saigon, the reproducible diagnostic module used each
actual default adapter configuration, including GDELT query parameters, with one
bounded request per configuration and no retries/redirects. It does not persist data.

Reproduce from checkout with the existing environment:
`../.phase2-release-env/Scripts/python.exe -m tradingagents.information.network_diagnostics`

Observed:
- All four requests failed: ConnectionError -> MaxRetryError -> NameResolutionError
  -> socket.gaierror errno **11001** (`getaddrinfo failed`). urllib3's exception name
  does not mean application retries were enabled; the default adapter performs none.
- Separate DNS lookups failed with errno 11001 for feeds.bbci.co.uk,
  api.gdeltproject.org and www.federalreserve.gov. PowerShell Resolve-DnsName for
  BBC returned Access is denied. This establishes a local resolution/access failure
  in this execution context; it does NOT establish a provider outage or its exact
  environmental cause.
- No proxy types were configured in requests/system proxy discovery; no
  REQUESTS_CA_BUNDLE/CURL_CA_BUNDLE/SSL_CERT_FILE override variables were present.
- OpenSSL 3.5.8 (25 Aug 2026); requests CA bundle exists locally.
- No TLS handshake or HTTP response was reached. Server certificate validity,
  endpoint response/parser shape, redirects, 429/rate limits and Retry-After remain
  UNKNOWN. No evidence supports blaming these later layers for this failure.
- No proxy/DNS changes, hardcoded-IP fallback, certificate disabling, policy bypass,
  paid access, network permission change or live-readiness claim. Earlier simple
  endpoint checks reproduced the same failure; the saved module provides the precise
  actual-configuration reproduction. These are separate from the offline suite.

## Verification and release gate

Normal shared conftest/no-network guard stays enabled for offline tests.
- Focused final: **106 passed**, 12.11 s (claim lifecycle, Fed/news, contract/store,
  context budget and real graph suites).
- Full suite and final static checks: see final recorded results below.
- Tests prove non-BTC geopolitical/technology evidence, exact correlation candidates,
  unknown independence despite repeated reports, explicit independence, dependency
  override including syndicated chains, official reporting separate from truth,
  T1 report/T2 contradiction/T3 correction, target retirement, resolution/reopening,
  source history after revision, future evidence rejection, idempotency, reopened
  store replay, source URL/timestamp lineage, actual graph support/opposition and
  post-T exclusion, real acquisition-ID prompt fit and oversized-history omissions.

Proven for the bounded release: explicit evidence-backed correlation/provenance
relationships, append-only lifecycle, cutoff-derived replay and existing graph
integration under the original information-context budget. Fed v1/BTC foundation
and optional-store behavior remain covered by regression tests.

Remaining: automated semantic correlation/extraction and validated contradiction
search; independently measured source-origin accuracy; article-body evidence;
continuous scheduler, collection coverage/latency and prospective live operation;
market reaction alignment, causal attribution and trading evaluation. Legacy tools
and date-based memory remain outside intraday PIT guarantees; explicit intraday
checkpoint resume remains unsupported. The release is not phase-wide completion.

Next: resolve the permitted execution environment's DNS/access problem and run a
small operational prospective free-source collection -> curated claim lifecycle ->
replay -> real analyst trial in the canonical store. Record failures/omissions and
latency, then implement/evaluate subsequent BTC market-reaction alignment without
using price moves to gate broad discovery or claiming causation from correlation.

### Final local verification (2026-10-27)

Final full default offline suite: **1,400 passed + 99 subtests passed**,
4 skipped, 1 deselected, 20 warnings, 40.57 s. Skips are three POSIX file-mode
cases on Windows and optional langchain_aws; integration remains excluded by
project defaults. The final RSS acquisition -> canonical store -> explicit
relationships -> actual analyst graph test passes in this full run.
Focused final run before that additional graph test: 106 passed, 12.11 s.
Ruff on all six changed/new Python files, AST syntax parsing and git diff --check
passed. Explicit changed/new files were reviewed before staging. No dependencies
or default acquisition configurations changed. Local release commit is on the
existing feature branch; use git log -1 for its SHA. No push was attempted.
