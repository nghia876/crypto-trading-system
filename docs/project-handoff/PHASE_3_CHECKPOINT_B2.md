# Checkpoint B2 — Source diversity and discovery quality

Implementation LOCAL ONLY. Phase 3 IN_PROGRESS; overall acceptance **NOT PROVEN**.
Two functioning separately operated non-official publishers demonstrated in one
bounded session. Three separately user-invoked research sessions remain unmet.

## Boundary and implementation

Started on `phase-3-event-narrative-slice`, HEAD
`3c0996921f0b3a038212c2d6cc5af633e0466316`, clean tracked tree. Fresh read-only
remote lookup returned `a619fe40e67606c92277eb886bd8b5c4aa03b93e` on November 2.
No push/merge/rebase/force/main operation. Original untracked `.phase12-tools/`
and bottleneck diagnosis preserved and excluded from staging; synced `sources/`
untouched. Read adopted v1.1 parent REVISED documents, A/B handoffs, diagnosis,
coverage, security, living status and operational collector/store/graph code.

Active broad discovery replaces failing SciDev with IPS; old candidate definition
is retained but not enabled. Existing collector, Source definitions/registry,
SQLite observation/coverage/source tables, immutable history, health, host backoff,
PIT and actual Market Analyst integration remain the acquisition path.
No new production store, scheduler, paid service, body scraper or later-phase work.

Three distinct discovery lanes:

1. Registered monitoring: two broad publishers plus at most one related feed,
   100 parser items/2MB, 40 retained/source, seven-day publication-else-update window.
2. Internal adaptive topic search: up to eight grounded local metadata queries by
   default, at most 16; one expansion hop. This is not open-web search.
3. Open-topic exploration: up to four operator topics outside collected inputs,
   <=256 characters each, recorded with query IDs/origin/coverage and pending manual
   status. `--open-query` does not call a search API. Actual external research is
   imported with exact plan/query, method/operator, observed/import availability,
   covered/missed channels, errors and fanout. <=8 eligible results and <=8 URL-only
   candidate leads; snippets and unreviewed publisher content fail closed. Candidate
   URLs cannot grant rights or become evidence without trusted source/code review.

Retries preserve immutable receipts; import time is the availability floor.
Existing runs remain readable; conflicting open queries require a new run ID.
Publisher success now counts current-run acquisitions, not stale corpus publishers.
Publication-to-first-seen lag is reported explicitly. Coverage warnings and manual
receipt counts reach the graph within existing 6,000/28,000 character bounds.

## Source-specific access and rights review — November 2, 2026

| Publisher / endpoint | Rights and access | Observed result / exclusions |
|---|---|---|
| Global Voices, https://globalvoices.org/feed/ and environment topic feed | Existing CC BY 3.0 attributed headline/link/date scope; robots 200, 10-second crawl delay honored | 12 general +2 environment copies, ONE publisher. Summary/body/media/byline exceptions uncleared; no AI-specific or training grant |
| Inter Press Service, https://www.ipsnews.net/feed/ | [RSS policy](https://www.ipsnews.net/rss-feeds/) explicitly permits downloading/publishing credited titles/headlines; robots 200 allows retrieval UA, no applicable delay | 35 XML entries, 21 retained in window. Headline/link/date only; no summaries, snippets, full stories, media or logos |
| SciDev.Net, https://www.scidev.net/feed/ | Robots 200 allowed root alternative, no delay | One check returned HTTP 200 text/html, as earlier global/feed did. No parser relaxation or bypass; replaced active candidate |

IPS [terms](https://www.ipsnews.net/terms-conditions/) protect branding and disclaim
accuracy. [Full-article republication](https://www.ipsnews.net/reprinting-articles/)
requires agreement; RSS headline permission is the narrow explicit exception used.
Retention/redistribution scope: attributed RSS headlines plus link/date provenance.
Inference basis: bounded factual headline processing/classification under that
scope, **not an explicit AI-specific grant**. All four summary permissions remain
UNKNOWN; full-text inference and model training are not authorized. Robots blocks
training agents separately; its AI retrieval comments do not grant copyright.
Publisher numeric quota UNKNOWN; local hourly cadence and bounded host/backoff
controls remain. Different publisher organizations do not prove reporting independence.

Policy review also considered The Conversation but did not enable it. Existing
BBC/GDELT/EIA and other source gates remain intact. Research-surface representations
are separate from Python acquisition; no research article bodies imported.

## Actual live session, lag and reconciliation

Run `checkpoint-b2-live-01`: **November 2, 16:34:12.517428–16:34:37.622806 UTC**,
**23:34:12–23:34:37 Asia/Saigon**. Three successful finite requests. One adaptive
hop fetched Global Voices environment. No BTC/price/popularity/official prerequisites.

| Independently traversed same-response XML | Entries | Retained | Outside seven days | Missing eligible | Duplicate / future / ineligible / cap omitted |
|---|---:|---:|---:|---:|---:|
| IPS | 35 | 21 | 14 | 0 | 0 / 0 / 0 / 0 |
| Global Voices general | 15 | 12 | 3 | 0 | 0 / 0 / 0 / 0 |
| Global Voices environment | 15 | 2 | 13 | 0 | 0 / 0 / 0 / 0 |

**35 copies, 33 distinct URLs**; environment copies overlap general-feed URLs.
All three observed responses were descending by supplied publication date; future
order remains unknown. Independent traversal did not use the product parser but
used the same bounded responses: **feed-level reconciliation, not global recall**.
Independent research-surface IPS headlines listing also showed Lake Sevan/Haiti;
this selected listing check is not an exhaustive external benchmark. Upstream
omissions and offline-window coverage remain unknown. No retention-cap omissions.

Actual non-BTC reports (publisher claims, occurrence/truth not adjudicated):

- IPS: [New Biodiversity Funding Brings Hope for Armenia’s Lake Sevan](https://www.ipsnews.net/2026/11/new-biodiversity-funding-brings-hope-for-armenias-lake-sevan/),
  Nov 2 09:25:54Z; test first seen 16:34:15.760440Z; **7h08m22s lag**.
- IPS: [WFP Warnings Become a Reality as Food Insecurity in Haiti on Track to Reach Record Highs](https://www.ipsnews.net/2026/11/wfp-warnings-become-a-reality-as-food-insecurity-in-haiti-on-track-to-reach-record-highs/),
  Nov 2 05:37:39Z; same test first seen; **10h56m37s lag**.
- Global Voices: [Bangladesh weighs tougher cyber law as AI-generated abuse targets women](https://globalvoices.org/2026/10/28/bangladesh-weighs-tougher-cyber-law-as-ai-generated-abuse-targets-women/),
  Oct 28 07:51:42Z; current-copy acquisition times preserved in fixture.

Copy-weighted publication-to-first-seen age: min 7.139h, median 98.573h,
max 164.820h. Isolated test-store discovery ages are not production/incident
latency or an alert SLA. Supplied publication is not authenticated occurrence.

## Real open-web import and source lineage research

Actual ChatGPT-assisted searches and receipts at November 2 16:35:28Z:

- `Armenia Lake Sevan biodiversity funding November 2026`: one eligible IPS
  headline imported; NEWS.am and UNDP URLs held as pending rights-review leads.
- `Haiti food insecurity WFP November 2026`: no eligible selected result imported;
  WFP, IPC and AP URLs held as candidates. Empty means no eligible selected result,
  not no web results. Ranking export, social/paywall/non-English recall unverified.

First receipt re-observes an already collected IPS URL: pathway verified, no new
unique article or corroboration claimed. Import availability, PIT and idempotency
verified; both receipts include channel omissions/fanout. No search snippets kept.
Lexical uncovered families TRADE/HEALTH describe rules, not global event absence.

Follow-up query: `site.ipsnews.net "WFP Warnings Become a Reality"`. IPS category
listing credits WFP; Global Issues copy credits IPS/WFP. [WFP release](https://www.wfp.org/news/wfp-warnings-become-reality-food-insecurity-haiti-track-reach-record-highs)
is dated October 28, predating November 2 IPS publication; same title/attribution
strongly indicate shared release/syndication, not independent reporting. The
[October 28 IPC analysis](https://www.ipcinfo.org/ipc-country-analysis/details-map/en/c/1165467/?iso3=HTI)
is a shared underlying source. Direct IPS article research-surface open failed;
category attribution and original/copy representations are the limited basis.
No body text, retroactive date correction or confirmed lineage edge imported.
AP also cites IPC; independent added reporting not adjudicated.
Lake Sevan results include NEWS.am minister/GEF coverage and a separate EU/UNDP
project. Do not merge projects/amounts or infer corroboration from topic overlap.

Free discovery options reviewed:

- [Tavily](https://docs.tavily.com/documentation/api-credits): documented 1,000
  monthly free credits without card; account/key and exact platform/third-party
  rights review still needed. Not provisioned/live-tested, not claimed unavailable.
- [Brave](https://api-dashboard.search.brave.com/documentation/resources/help-feedback):
  monthly credits, no standalone free plan, card required; not enabled.
- [GDELT](https://gdeltproject.org/about.html#termsofuse): free attributed datasets
  do not clear every indexed publisher's text; existing access/rights gates retained.
- DuckDuckGo `/api` redirected to an unreadable search page in research surface;
  no reusable global-search API verified. No search-page scraping fallback.

Source/API research queries also executed: `site.theconversation.com creative commons republishing RSS`;
`site.ipsnews.net republish creative commons RSS`; `free web search API free tier terms Brave search API`;
`site.gdeltproject.org DOC API terms free`. These were manual research channels,
not Python global searches; unreviewed results were not source permissions.

## Validation, storage, sessions and next action

Focused suite **33 passed**. Full offline regression **1,643 passed +99 subtests**,
four expected skips, one integration deselected, 20 existing warnings, 61.50s.
Log: parent-workspace `checkpoint-b2-regression.txt`. Actual-metadata replay checks
SQLite reopen/PIT and actual Market Analyst graph with scripted offline model.
Live narrative render 5,548 chars; receipts render 5,732; tests enforce narrative
<=6,000 and individual model prompts <=28,000. No live paid model or quality claim.
An initial replay test expected raw-copy count rather than latest source/article
versions, then failed on JSON-escaped punctuation; assertions corrected to match
the actual store/render contracts. No product regression was hidden.

Live test database integrity `ok`, zero evidence before first acquisition, then
temporary test DB removed. Private canonical DB read-only, integrity `ok`,
byte-identical SHA256 `3e7548c55e59bf42e16a61c570122b98f5e056dcf2fa17c578d6c63a7595ec4b`.
Derived metadata and receipts: `tests/fixtures/checkpoint_b2/`; not a second store.
Final tracked-project plus new-test lint passed; AST syntax passed for 245 Python
files; diff whitespace checks passed. Final canonical integrity/hash recheck
remained identical. Commit is local only; final SHA is supplied in the completion
report (not self-embedded in its own commit).

**Sessions: one B2 user-invoked execution, not three.** Preflight/feed/search calls
inside it are not separate sessions; earlier B diagnostics are not retroactively
promoted. The continuation after a tool usage-limit interruption adds no live
research session. No artificial external timeline or continuous monitoring claim.

Future user request: “Run the next bounded B2 research session.” Work should run
and summarize it; the user need not find files or use a terminal. Repeatable CLI:

```text
python -m tradingagents.information.adaptive_discovery --store ../canonical-information.sqlite3 --run-id b2-UNIQUE-SESSION --report ../b2-UNIQUE-SESSION.json --open-query "operator selected world topic"
```

New session needs new run ID/report, actual later user invocation and cadence/backoff
compliance. `--manual-import` consumes the exact planned query receipt schema.
Next bounded action: two further separately user-invoked sessions with source
change/lag and external-list reconciliation, plus useful candidate rights review.
Do not advance to C/Phase 4/5 on tests or registration alone.

Secure execution: direct patches/small commands, existing dependencies, no installs
or security-setting changes. No new alert surfaced through tools; no Defender audit
or proven benign explanation of prior FileFix detection. Automatic approval review
temporarily failed on a usage limit while writing this handoff; that action did not
execute. Work resumed only after the user's explicit continuation.
