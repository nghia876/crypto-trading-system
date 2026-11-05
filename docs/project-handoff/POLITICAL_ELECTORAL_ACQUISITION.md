# Bounded political and electoral acquisition — 2026-11-05

Phase 3 IN_PROGRESS. User-approved acquisition extension only. The separately
requested November 6 (Asia/Saigon) longitudinal real-collection checkpoint remains
pending and can proceed separately. No new production collection, scheduler,
forecast, political ranking, causal BTC finding, trade signal or Phase 4/5 work.

## Starting state and scope

Actual local branch: `phase-3-event-narrative-slice`, starting HEAD
`c3974799683277911d8605a6956e98d1c4f38672`. Fresh read-only GitHub connector check:
remote branch still `c54af8c18e4418f4d34032b422d1c2bf02cc0082`. No push,
merge, rebase or main changes. Initially tracked tree clean; existing untracked
`.phase12-tools/` and `PHASE_3_BOTTLENECK_DIAGNOSIS.md` preserved/excluded from staging.

Read the adopted workspace v1.1 revised Blueprint, Master Prompt and Resource
Manifest; current source coverage, secure-execution guidance, canonical activation
resume and post-live visibility repair. Synced `sources/` are untouched. The
referenced Phase 3 chat was read for the approved scope and pending checkpoint.

## Implemented contracts

- `WORLD_DISCOVERY_DOMAINS` explicitly accepts `POLITICS_ELECTIONS`,
  `FISCAL_REGULATORY_POLICY`, `INTERNATIONAL_RELATIONS`.
- Existing adaptive topic coverage now reports election calendars, vote counting,
  reported official results, reported polling, legislative/executive control,
  fiscal/tax/crypto policy, international relations/sanctions/trade, and public
  political claims/rumors/denials/corrections. Labels guide collection, never
  require BTC words, price movements, official confirmation, popularity or English.
  They are search hints, not semantic fact extraction or a completeness claim.
- Each research run plans at most **two** additional political manual queries.
  Existing local expansion remains 1..16 queries (default eight), one hop, 200
  corpus rows. Existing two broad feeds plus at most one related feed, retention,
  host/backoff/robots limits are unchanged. No automated external search API.
  Exact political query IDs/text, run/time, evidence inputs and pending channel
  state are journaled. Actual external query/channel/time/operator/result receipts
  use the existing manual-import lane; at most eight results/eight candidate URLs
  per receipt, with existing atomic rights rejection and local availability floor.
- A grounded expansion preserves the bounded headline including supplied year,
  country/race/institution words, followed by `election policy jurisdiction date`.
  Lexical matches never authorize event merging. Independent seed plans work even
  with an empty corpus; they rotate past seeds planned within the prior 24 hours.
  Pending plans are not executed searches or proof of coverage.
- `record_political_context` appends attributed reviews on exact immutable evidence:
  factual claim, opinion, speculation, rumor, denial, correction, or reported poll
  measurement; separate unknown/developing count/publisher-reported result/
  documented official result status. A documented result is a reviewer-attributed
  description, not independent verification by the program. No winner prediction.
  Population/fieldwork date missing from a poll stay explicitly incomplete.
  Jurisdiction, institution, race, source-reported election date, instrument,
  entities and location remain unknown unless supplied. No headline fabrication.
- Political acquisition link review wraps the existing bounded matcher (128
  records/32 suggestions), vetoing comparable explicit jurisdiction, institution,
  race, date/year or instrument conflicts. Agreement never promotes identity;
  unknown fields never establish agreement. Existing matcher suggestions still
  require review and never automatically merge articles. Generic historical
  matcher/context bytes and frozen evaluation manifests are unchanged. Political
  overlay decisions live in the research-run report; they do not rewrite earlier
  candidate journals or manually curated incident memberships.
- Optional attributed political reviews reach the existing Market Analyst render
  only at their actual availability cutoff. They participate in whole-record
  budget fit and omission accounting. Original headlines/claims, publisher/copy
  lineage, URLs, source attribution, first-seen history and evidence IDs survive.
  No migration or new authoritative store. Existing publisher/domain sampling,
  narrative 6,000 and mixed-context 28,000 character limits remain in force.

Exact seed inventory (see `POLITICAL_QUERY_SEEDS`):

1. `global election calendar electoral commission voting dates`
2. `election vote counting recount developing reported official results`
3. `opinion polling reported measurement population fieldwork date methodology`
4. `legislative executive control parliament coalition government formation`
5. `fiscal tax budget crypto regulation legislative instrument jurisdiction`
6. `international relations sanctions trade tariffs policy institution country`
7. `political public claims rumors denials corrections election reporting`
8. `eleições resultados apuração sondagens país data instituição`
9. `élections dépouillement résultats sondages pays date institution`
10. `bầu cử kiểm phiếu kết quả thăm dò quốc gia ngày cơ quan`

## Source/access evidence and honest fallback

No new publisher, endpoint allowlist entry or source fingerprint was activated.
`POLITICAL_METADATA_FALLBACKS` explicitly reuses the two existing registered
channels, and research manifests name their IDs:

| Registered source | Exact endpoint | Retained scope / eligibility |
| --- | --- | --- |
| `news.discovery.globalvoices` | https://globalvoices.org/feed/ | Existing reviewed headline/link/supplied-date scope; attributed CC BY 3.0 metadata; no expanded body, summary, media, translation or training grant |
| `news.discovery.ips` | https://www.ipsnews.net/feed/ | Existing explicit attributed RSS headline permission; no full articles, summaries, media or training grant |

The [GV feed directory](https://globalvoices.org/feeds/) documents topic/country
feeds; its [attribution policy](https://globalvoices.org/about/global-voices-attribution-policy/)
permits attributed reuse subject to exceptions. Its
[AI policy](https://globalvoices.org/about/global-voices-policy-on-ai/) describes
contributor/editorial restrictions; it is not a new blanket inference/training
license. [IPS RSS terms](https://www.ipsnews.net/rss-feeds/) expressly allow
downloading/publishing credited titles/headlines, excluding complete stories.
These policy pages were accessible through the session web tool on November 5.
Existing bounded metadata factual processing is retained; unknown summary rights
remain separately gated for access, retention, inference and redistribution.

Sought a dedicated GV political/election topic channel. The Elections topic page
`https://globalvoices.org/-/topics/elections/` was reachable, but the attempted
`https://globalvoices.org/-/topics/politics/feed/` and robots endpoint were not
accessible through the tool. A topic page is not a verified RSS endpoint. No
dedicated endpoint was registered, requested by the collector or declared cleared.
No source-access probe wrote a store. Existing fallback endpoints' most recent
actual collector success remains the separate November 5 activation run; this
change does not claim a new live success or continuing accessibility.

Official-source acquisition remains possible through the existing rights-reviewed
WORLD agency/config lanes, including policy announcements. There is no newly
cleared official election-results or polling API, nor full global calendar, race,
language, polling or official-result coverage. Eligible nonofficial reports do
not await official confirmation. Unknown publishers found by manual search remain
candidate URLs only until exact endpoint/rights/robots review; their contents are
rejected by the importer. BBC/GDELT/EIA and other existing gates remain closed.

## Validation and state preservation

Full offline regression: **1,686 passed +99 subtests**, four unchanged skips,
one integration deselected, 20 warnings, 77.81 seconds. Final political focused
suite: **20 passed**, including actual matcher-overlay conflict verification.
Ruff, syntax and whitespace checks pass for changed code.

An earlier run caught the frozen matcher/context fingerprint gate and an outdated
ten-domain assertion. Restored generic context code, placing political vetoes in
the separate acquisition overlay. Frozen manifests/scorer/fixtures/checks remain
unchanged; readiness now tests the complete domain set. No regression test was
skipped or weakened. Final full regression includes the frozen gate.

Tests cover global/non-English/non-BTC intake, seed rotation, manual provenance/
rights rejection, incomplete polling, attributed opinion/speculation/denial,
reported official status without truth upgrade, correction/PIT/reopen, missing
evidence, race/year/jurisdiction/instrument conflicts and copy lineage. Sixty
political records retain disaster/energy/technology sampling. An actual scripted
Market Analyst sees a synthetic non-BTC Kenya count and its attributed developing
status alongside other domains within 6,000/28,000 limits. Existing actual-graph
funding/macro reservation tests pass.

Read-only canonical audit passes **70 exact historical InformationViews**, future
ID exclusion and actual Market Analyst visibility. Original post-live behavior
remains **5,386 narrative / 15,365 mixed / 22,877 largest-prompt characters**, both
original IPS/GV IDs visible, six of 857 candidates included/851 budget omitted.
Four graph captures include pre-collection and IPS boundary. This replays stored
live evidence; it is not new political collection.

Before/after integrity `ok`; exact row digests unchanged: **1,254 observations,
143 source histories, 167 coverage, zero gaps, 85 supersession links**. All **1,706
protected-file hashes** match, including sources, originals/backups/candidate,
frozen fixtures, tools and diagnosis. Private audit output is parent-workspace
`visibility-verification-7-private.json`, excluded from Git. Database SHA256 before
and after matches below.

All new election,
policy, polling, rumor and correction specimens are **synthetic**, including the
US midterm and non-BTC Kenya analyst examples. They prove acquisition mechanics,
not current election facts, recall, official certification or market impact.

The production authority remains the private absolute
`local-runtime/information.sqlite3` under the project workspace. Expected SHA256:
`76d741733dc132d8583c91b88e448fba23622779e74d92eff6dcbdd4786fdca7`.
All tests use isolated stores with process-only authority isolation. Read-only
canonical replay uses the real authority, scripted models and denied networking.
No production data, archive, configuration, source mirror or frozen fixture is
staged. No new security alert was observed through the tools; no security-setting
changes, installs, bypasses or credential-helper operations were attempted.

## Remaining work

Political coverage remains PARTIAL: free official results/polling/calendar channels,
multilingual recall, real political-run evidence and longitudinal source health
are not proven. Existing C1 propagation and C2 BTC microstructure work stays in its
approved order after the separate November 6 persistence session. No roadmap or
phase completion gate is advanced by this extension.
