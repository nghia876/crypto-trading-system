# Phase 3.4 bounded event-link evaluation — 2026-11-01

Status: bounded offline evaluation implemented; real-world candidate quality and full semantic Phase 3 remain IN_PROGRESS. No identity auto-merge, independent corroboration, truth, causality or trading-alpha claim.

## Repository and synchronization

Existing nghia876/crypto-trading-system checkout, branch phase-3-event-narrative-slice. Starting HEAD 8717005bc505bfd66c3206c40a49140193291890. Fresh GitHub ls-remote returned f87ddbefd0126f05b0ad29b53d5065ea9796fddc before and after the attempted push. The exact authorized pending sequence is e801a80c8f7f672f64573da198dce0ccb80f65c4 then 8717005bc505bfd66c3206c40a49140193291890. Fast-forward ancestry and diff whitespace verified; tracked starting checkout clean, only existing untracked .phase12-tools/.

Authorized range: 14 code/test/document files, 1,410 additions, three deletions; no database, environment/credential file or untracked content included. Reviewed diff, credential-pattern/private-path checks and file inventory. Pattern checks are not proof of absence. Push of the exact 8717005 object to the feature ref failed in the existing Git/MSYS credential helper with BaseNamedObjects 0xC0000022. No repeat of that helper, force, merge, rebase or main operation. Host execution outside this managed process is unavailable here. A guarded Push-Phase33-Authorized.ps1 is supplied outside Git in the parent workspace for ordinary non-elevated host PowerShell. It pins the target, checks origin URLs, branch, tracked status, exact two commits, ancestry, unchanged remote base, suppresses tags/mirroring, and verifies the result. It never sends Phase 3.4, even when HEAD is newer. This document does not claim a successful push. All Phase 3.4 work remains LOCAL ONLY.

Read-only references: canonical parent sources/PRODUCT_BLUEPRINT.md, MASTER_PROMPT.md, RESOURCE_MANIFEST.md; Phase 3.3 handoff; source coverage matrix; living PROJECT_STATUS_AND_PHASE_2_HANDOFF.md. sources/ and .phase12-tools/ preserved.

## Implementation and protocol

event_evaluation.evaluate(view, labels) calls unchanged event-link-heuristic-v1 using only the existing point-in-time InformationView. Labels enter scoring afterward; no label, identity, rationale, future record or relationship is appended to SQLite or passed to feature extraction. Candidate links remain review suggestions, never incident membership, support, confirmation or independence. No source, paid dependency, network request or analyst flow was added.

The evaluator accepts at most 4,096 unique unordered pairs. Fields: evidence_ids (two distinct immutable observation IDs), label (same_event/different_event/unknown), family, stratum, reporting_relationship (cross_source/same_publisher_syndication/unknown), confidence (high/medium/low/unknown), review_status (synthetic_authored/human_reviewed/pending), provenance and rationale. Invalid/duplicate labels fail; unknown/pending and unavailable observations are excluded from denominators and reported individually. Null precision/recall means zero denominator, not zero accuracy. Only current eligible observation IDs are scoreable; superseded versions require their corresponding earlier cutoff. Candidate record/output omissions and unlabeled predictions are reported. Budget-excluded available positive pairs count as false negatives in the labeled retrieval protocol.

CLI existing-store mode opens the SAME SQLiteInformationStore with new optional read_only=True, using SQLite mode=ro, no initialization/migration. Default writable behavior is unchanged. Missing stores are refused; read-only appends fail. CLI never writes reports back into the information store.

```powershell
python -m tradingagents.information.event_evaluation --fixture tests/fixtures/event_pairs_v1.json
python -m tradingagents.information.event_evaluation --store 'EXISTING-CANONICAL-SQLITE' --labels 'REVIEWED-PAIR-LABELS.json' --cutoff '2026-01-01T12:00:00+00:00'
```

Fixture mode is bounded to 256 isolated two-record trials and 2 MB input. Each trial uses temporary canonical SQLite schema/append/view_at/reopen, then deletes its temporary file; no alternative live database or schema. It verifies exact reopened report equality. Existing-store mode also caps labels at 2 MB. Neither mode changes candidate thresholds.

## Dataset provenance and review workflow

tests/fixtures/event_pairs_v1.json is agent-authored synthetic v1: 80 pairs, 40 stipulated same-event and 40 distinct-event, eight families, ten cases each. Every case carries synthetic_authored, explicit author provenance, confidence and a scenario rationale. All source/publisher IDs are fictional; example.invalid URLs are synthetic provenance markers, not acquired articles. No human review, licensed corpus, live acquisition, representativeness, held-out accuracy or independent-source confirmation is claimed. Same-publisher copies are identity-positive when about one episode, never independent corroboration. Cross-source is a reporting channel stratum, not measured independence. Correction/denial pairs test identity despite disagreement, not the truth of either report.

Per family: reorder/paraphrase, substantially different vocabulary, update, denial, recovery; negatives cover identical recurring templates with omitted identity details, nearby named incidents, seven-day-separated reports, unrelated type and overlapping separate episodes. These intentionally ambiguous synthetic negatives expose information limits rather than establish that text alone can recover hidden episode identity. This is 80 isolated pair retrieval trials, NOT pooled 160-article corpus recall. Repeated templates are correlated; no confidence intervals or statistical generalization claimed. Global 128-record/32-candidate truncation is tested separately, not hidden by the isolated protocol.

To build the real benchmark: collect eligible available evidence into the existing canonical store; preserve URLs, publisher/origin and acquisition/publication metadata; export immutable evidence-ID pairs; have a named reviewer record identity rationale, provenance (reviewer/date and evidence basis), confidence and status in a separate versioned label JSON. Leave ambiguous pairs unknown/pending. Confirm syndicated origin separately from source-ID inequality. Freeze labels and SHA before scoring; partition by incident/origin cluster, not article, for a future held-out set. Run at early and late acquisition cutoffs. Corrections acquired later must not alter early candidate views. Add real drought/flood/agriculture/geopolitics/grid/cyber and correction/syndication examples before any quality claim or threshold tuning. No human review is inferred from this workflow's existence.

## Measured baseline

Machine-readable PHASE_3_4_METRICS.json includes every trial outcome, exact fixture SHA-256, policy and all grouped counts. No target accuracy was invented. Candidate policy was not tuned on these results.

| Family | TP | FP | TN | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| Drought | 4 | 2 | 3 | 1 | 66.67% | 80% |
| Flood/disaster | 4 | 2 | 3 | 1 | 66.67% | 80% |
| Agriculture/food | 3 | 2 | 3 | 2 | 60% | 60% |
| War/geopolitics | 4 | 2 | 3 | 1 | 66.67% | 80% |
| Energy/grid | 3 | 2 | 3 | 2 | 60% | 60% |
| Technology/cyber | 4 | 1 | 4 | 1 | 80% | 80% |
| Corrections | 4 | 2 | 3 | 1 | 66.67% | 80% |
| Syndication | 4 | 2 | 3 | 1 | 66.67% | 80% |
| Overall | 30 | 15 | 25 | 10 | 66.67% | 75% |
| Cross-source reporting channel (70 pairs) | 26 | 13 | 22 | 9 | 66.67% | 74.29% |
| Same-publisher syndication channel (10 pairs) | 4 | 2 | 3 | 1 | 66.67% | 80% |

All 40 negative trials form the nearby/unrelated/recurring stratum (15 FP, 25 TN). Positive-only correction and syndication strata must not be read as channel precision; use reporting:* groups, which include negatives. Cross-source positive-only stratum is 22 TP/8 FN. Eight divergent-vocabulary paraphrases are missed; agriculture and energy also miss recovery updates. Fifteen false positives are identical/overlapping recurring templates, with cyber's extra explicit anchor preventing one. Strong location/time/type negatives are rejected. Inspect per-case outcomes rather than averaging away failures.

Next targeted improvement: acquire explicit occurrence/episode identifiers and location/origin metadata, retain unknown when absent, and evaluate a versioned guard on independently reviewed held-out incident clusters. Separately investigate conservative lexical false negatives with real paraphrases. Do not silently merge on textual similarity, loosen geography guards or count syndication as support.

## Verification and limits

Focused initial suite: 51 passed (evaluation, candidate and actual graph cases). Final full offline suite: **1,544 passed + 99 subtests**, four skipped, one integration test deselected, 20 existing model warnings, 46.82 seconds. Project Ruff, changed-Python AST syntax and git diff whitespace checks passed. Parent workspace phase34-regression-final.txt preserves output outside Git. Skips are three Windows/POSIX permission checks and optional langchain_aws. Regression guards freeze measured confusion counts, enforce label isolation, unknown/pending exclusion, late acquisition despite old publication, reopen equality, input validation, missing-store refusal, read-only store bytes/append rejection, and candidate-budget omissions. Existing actual TradingAgentsGraph tests cover BTC + H.4.1/RRP/BLS + broad WORLD/candidates under 28,000 characters; no BTC keyword gate. Existing immutable candidate history/correction tests remain unchanged.

Full suite first run: 1,543 passed + 99 subtests, one failure because the test's child interpreter lacked the verification environment's typer dependency. No application fix was made for that environment error; rerun propagates the existing dependency directory to child processes. No live LLM, feed polling or trading test is claimed.

No live canonical database was created or audited. Real-world precision/recall, original independent origins, global source breadth, multilingual identity, occurrence-time normalization and operational freshness remain unverified. Broad original WORLD coverage remains required, free/legally eligible only. Daily TGA and Treasury yields remain rights-gated; BEA GDP/PCE incomplete; BLS live calendar unavailable; FRED disabled. No source rights were expanded.
