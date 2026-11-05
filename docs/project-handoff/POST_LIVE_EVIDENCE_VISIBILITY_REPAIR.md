# Post-live evidence visibility repair — November 5, 2026

User-approved narrow repair; Phase 3 IN_PROGRESS. No new acquisition, database
writes/migration/switch, source-rights changes, Checkpoint C, Phase 4/5, scheduler,
installation, security-setting changes or GitHub push. All development local.

**Visibility repair gate PASS. Longitudinal real-session persistence NOT PROVEN.**

## Starting state and authority

Feature branch `phase-3-event-narrative-slice`; initial local HEAD
`faf96785320c0f513f82ccf414374340a02da3c3`. Tracked tree initially clean; existing
untracked `.phase12-tools/` and bottleneck diagnosis retained. Fresh GitHub
connector read confirms remote feature HEAD `c54af8c18e4418f4d34032b422d1c2bf02cc0082`.
The local remote-tracking ref is stale (`78ac4d5`); it was not fetched/rewritten.
No local main branch exists; origin/main remains
`1394a3f72aa4393e1a98f51b382434c4b4c2d972`. No main/merge/rebase/force operation.

Adopted v1.1 workspace revised Blueprint, Master Prompt and Resource Manifest,
activation resume, source coverage and secure execution instructions consulted.
Canonical synced sources remain read-only. The single active authority remains:

`C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`

## Confirmed cause and scope

This is selector starvation and asymmetric rendering cost, not failed intake,
wrong database, wrong cutoff, unsupported schema or a publisher/domain allowlist.
All 35 actual stored IDs resolve to `narrative.event`, `narrative-news-v1`, distinct
canonical article subjects, WORLD discovery domain, `publisher_rss` source type.
IDs/source IDs/times reach `SQLiteInformationStore.view_at` and `narrative_events`.
Their 22 IPS /13 Global Voices records have unmeasured credibility and unknown
independence. No verification, incident membership or claim-lifecycle acceptance
is an admission prerequisite. Those annotations cannot restore a budget-omitted
record. Consumer uses the selected IDs for source/evidence lineage and renders
the same selection into actual `TradingAgentsGraph.propagate` analyst context.

The old cross-domain priority tuple ranked recent official URL formats ahead of
all other recent formats. Seven specialist domains filled the budget first; both
new publishers shared one late WORLD turn. Their default generic lines repeated
identity/content/version hashes and unknown fields, costing approximately
1,500–1,600 characters versus 527–855 for the seven selected specialists. Thus
all 35 were eligible candidates but no whole new record fitted. Scripted actual
graph baseline replay is checked separately from selector inspection.

The repair gives registered publisher groups separate sampling turns inside
their discovery domains and moves publication/update recency ahead of official
URL format when mixing publisher lanes. Existing format preference within a lane
and historical ordering without publisher lanes are retained. Freshness is a
seven-day bucket, not newest-is-most-important. A newer routine notice can still
follow an older report in its lane. No credibility/attention/BTC-direction score
or semantic importance model was introduced. Repeated copies remain deduplicated
by canonical article; publisher diversity does not establish independent origins.

Publisher metadata now uses the existing compact specialist style, preserving
claim, source, attribution, URL, publication/update/availability, evidence ID and
evidence level. Existing claim/incident/context and rights provenance are retained
when present. Unknown origin, factual truth, reaction and incomplete coverage
remain explicit. No article body, summary or new rights grant is inferred.

Exact footer cost participates in whole-record fit, leaving 200 characters for
the consumer heading/allowance within the 6,000 narrative limit. Graph-visible
accounting reports canonical candidates, included/omitted totals, and included/
candidate counts for at most four sources (publisher feeds first), with the count
of other sources. Omitted IDs remain in SQLite, not expanded into the prompt.
This bounds accounting instead of spending the narrative allowance on 851 IDs.

Representative discovery visibility is justified by the blueprint's broad-world
stream, not established BTC impact. The two selected current articles are samples,
not a claim that they outrank every omitted event economically. The remaining new
records and several historical domains can be omitted honestly under the budget.
BTC/derivatives and macro retain separate consumer reservations. Meaningful
historical specialist records remain alongside current publisher samples.

## Validation

Four new privacy-safe synthetic regression tests cover 22+13 publisher candidates,
source/domain diversity, credibility/attention separation, format versus recency,
oversized-record continuation, accurate bounded counts and actual pre/post graph
PIT with core funding. No private raw evidence or fixture/manifest edits.

Final focused suite: 59 passed. Full offline suite: **1,666 passed +99 subtests**,
four unchanged skips, one integration deselected, 20 warnings, 87.46 seconds.
Ruff, syntax compilation and diff whitespace checks pass. Tests use a process-only
nonexistent authority-file reference so isolated test stores can be created;
the installation config is never edited. Canonical verification separately uses
the actual active authority and `read_only=True` / SQLite `mode=ro`, with scripted
models, legacy vendors mocked and Python sockets/requests/curl network denied.

Actual canonical selection stages (UTC, November 5; add seven hours for
Asia/Saigon). No new ID fails schema/domain/source admission or canonical-article
deduplication. Before availability it is excluded by PIT, not a budget omission.

| Decision cutoff | Live PIT eligible / candidates | Old live selected / omitted | Repaired live selected / omitted | All candidates / repaired selected |
| --- | ---: | ---: | ---: | ---: |
| 03:27:13.774951, just before IPS | 0 /0 | 0 /0 | 0 /0 | 822 /7 |
| 03:27:13.774952, IPS boundary | 22 /22 | 0 /22 | 1 /21 | 844 /7 |
| 03:27:26.528490, GV boundary | 35 /35 | 0 /35 | 2 /33 | 857 /6 |
| 03:27:26.572007, after session | 35 /35 | 0 /35 | 2 /33 | 857 /6 |

The actual post-live Market Analyst prompt includes precisely these two of the
35 new stored IDs (no reconstructed/relabelled IDs):

- IPS: `news:7e124134912977194941ac599865fc05f579956dfa3cd9b17360886479b89950`
- Global Voices: `news:c0fa3590fd1352decc9378824ccd8e898a918e8b2e7162cb1c7628e1723028f5`

All six selected narrative IDs reach the actual Market Analyst, along with
source/attribution/URL/date/availability provenance and the selection disclosure.
Four retained historical specialists represent WAR_GEOPOLITICS, TECHNOLOGY,
ENERGY_GRID and AGRICULTURE_FOOD. Total 857 candidates, six included, 851 omitted;
publisher counts explicitly 1/22 IPS and 1/13 GV. Other sources' counts are bounded
and not presented as exhaustive per-source detail. No claim that all 35 belong
in a 6k prompt, or that omitted public-health/water/disaster evidence is irrelevant.

| Actual graph replay | Narrative chars | Mixed context chars | Largest prompt chars | New IDs |
| --- | ---: | ---: | ---: | ---: |
| Old code at the same post-live cutoff | 5590 | 15656 | 23168 | 0 |
| Just before collection | 5735 | 15801 | 23313 | 0 |
| IPS availability boundary | 5776 | 15702 | 23214 | 1 |
| Just after collection | 5386 | 15365 | 22877 | 2 |

The graph uses actual canonical read-only data, scripted model and denied network,
not an exported-fixture-only simulation. Every selected ID is asserted in Market
Analyst messages, not merely an intermediate state. All prompts <=28,000; all
narratives <=6,000 and mixed contexts <=28,000.

Seventy historical decision cutoffs compare exact InformationViews to the
preserved 1,219-row candidate, including availability boundaries. No one of the
35 future IDs appears there. Representative earliest and just-before selection
IDs match the old selector exactly. Accounting text intentionally changes;
byte-identical historical prompt text is not claimed. Existing historical,
claim/incident, macro, BTC and frozen holdout tests remain unchanged and pass.

Before/after SQLite integrity is `ok`; exact counts remain 1,254 observations,
143 source histories, 167 coverage, zero gaps, 85 supersession links. Exact
four-table row digests match the recorded post-live activation validation.
Canonical file SHA256 before and after:
`76d741733dc132d8583c91b88e448fba23622779e74d92eff6dcbdd4786fdca7`.

The audit fingerprints 1,706 protected files (sources, originals, backups,
candidate, frozen fixtures, existing tools and diagnosis); all hashes unchanged.
Seven original/candidate/archive/rollback hashes also match recorded activation
values. Frozen matcher bytes remain SHA256
`589901c2a5f9bc40dd6a6baabd36713563a1d259265106094a76cde8c6120c72`.
No private database, raw evidence, archive or installation configuration staged.

Private audit outputs stay in the parent workspace: visibility-verification
reports and fresh-process restart verification. An early audit completed its
assertions and wrote results but its final progress-count print raised TypeError
when adding unchecked (`None`) summary entries; corrected the diagnostic print.
This was not a data, graph or regression failure. Final gate uses successful
completed verification, not that process's exit status.

The corrected final assertion audit exits successfully: baseline/pre/intermediate/
post captures, all 70 exact views, limits and immutable data checks revalidated.
A separate fresh-process actual post-live graph replay also exits successfully:
the same selected IDs, exact mixed-context SHA256
`c89542c627de05a70b0f7055d8a6cbd4adcb83d310bee80b55151cc6508ce418`, lengths,
Market Analyst ID inclusion, database row digests/integrity and file hash match.
Offline restart is not another independent real acquisition session.

## Remaining gate and next step

Longitudinal persistence across independently invoked real acquisition sessions
remains NOT PROVEN. Later, separately invoke one rights-compliant real session
against this same active store, then reopen and replay old/new evidence through
the actual graph. No such acquisition is authorized by this repair. Then resume
the separately approved C1/C2 sequence; broad Phase 3 and independent-origin/
human-review/coverage gates remain open. No predictive/trading acceptance claim.

No new tool-reported Defender alert was observed. This is not an event-log audit
or a verified false-positive finding. No bypass, exclusion, install or policy
change was used.
