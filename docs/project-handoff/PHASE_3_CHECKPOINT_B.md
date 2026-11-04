# Checkpoint B — Adaptive broad WORLD discovery — 2026-11-02

November 4: [B2 session 03](PHASE_3_CHECKPOINT_B2.md) completes three separate
user-invoked acquisition sessions. Overall B2 NOT PROVEN pending same-incident
origin/context evidence and independent human review. Counts/next actions below
are historical. No C/4/5 advancement or push.

Implementation is LOCAL ONLY. Operational acceptance is **NOT PROVEN**.
Phase 3 remains IN_PROGRESS. No Checkpoint C, Phase 4 or Phase 5 advancement.

Follow-up: [Checkpoint B2](PHASE_3_CHECKPOINT_B2.md) demonstrates IPS plus Global
Voices in one November 2 bounded live test and actual open-topic manual imports.
Three separated user-invoked sessions remain unmet. The source/access results
below are historical Checkpoint B evidence, not current active-source selection.

## Authority and verified starting state

Existing repo `nghia876/crypto-trading-system`, branch
`phase-3-event-narrative-slice`, starting HEAD
`46c1641b2ddfc7889d2e99427b11e05e35a19e74`. Tracked tree clean;
preexisting `.phase12-tools/` and untracked bottleneck diagnosis preserved.
Ancestor `a619fe40e67606c92277eb886bd8b5c4aa03b93e` verified locally.
Initial remote lookup failed DNS. After explicit network permission, a fresh
credential-helper-disabled read-only lookup returned that exact remote feature SHA.
No push, merge, reset, rebase, main edit or scheduler installation.

Read adopted parent-workspace PRODUCT_BLUEPRINT_REVISED, MASTER_PROMPT_REVISED,
RESOURCE_MANIFEST_REVISED v1.1, Checkpoint A, coverage, diagnosis and
SECURE_EXECUTION. Synced sources are read-only and unchanged.

## Implemented behavior

`discovery_sources.py` registers two distinct non-government publisher candidates,
plus two related Global Voices topic feeds. The new `adaptive_discovery` CLI calls
the existing collector, parser, immutable observation/coverage/source tables and
SQLite PIT implementation. No new schema or operational store.

Every run starts with unfiltered broad publisher feeds. BTC words, price moves,
popularity, recognized topic and official confirmation are never intake gates.
Eight transparent heuristic topic labels cover geopolitics/war, trade,
climate/disaster, water/agriculture/food, energy/grid, health, science/AI/tech/cyber,
and regulation. Labels are incomplete English lexical diagnostics, not semantic
understanding, event confirmation or economic impact prediction. Unmatched and
non-English headlines remain eligible.

Actual adaptive acquisition: newly retained headline topics select one reviewed
environment or technology feed; its collector request runs through the same
robots/rights/parser/store/PIT path. One expansion hop, at most three feed requests
per run, 100 parser items/2MB per snapshot, default 40 retained records per source,
seven-day publication-else-update window. Topic overlap cannot add corroboration.

Queries derive from the first four distinct non-stop headline tokens. Up to eight
by default (hard maximum 16) execute against at most 200 canonical collected
metadata records, with eight result IDs/query. This is **local corpus search**,
not an automated worldwide search engine. Query decisions preserve input IDs,
available-at, reason, result IDs and provisional relations. Run manifest preserves
run ID/start/cutoff, topics/gaps, limits, omissions, repeated-query suppression,
feed attempts, health/backoff, robots and errors. Query repetition window is 24h.
Generic WORLD is a feed carrier, not an eleventh thematic readiness requirement.

Complementary JSON manual search import requires an existing available run and
exact recorded query, method, operator, observed time, status/error and <=8
results. Only registered publisher headline/link/date metadata is accepted;
snippets and unreviewed hosts fail closed. Rights cannot be granted by input JSON.
Manual observation time cannot precede the run or follow import. Availability is
the actual import time, not publication or a claimed earlier manual sighting.
Manual serialization is explicitly distinguished from a fetched response.
Validation completes before a single atomic store append. Same run/import retries
return recorded results without refetching. Caller serializes with existing job lock.

No compulsory model/search API, training, article-body requests, inference of
inaccessible text, autonomous web crawling, paid source, cloud or daemon.
Run coverage warnings reach existing narrative rendering and the actual Market
Analyst graph. A reserve keeps the research warning within the 6k narrative slot;
the existing mixed-context bound stays 28k. Raw copies, canonical articles,
syndication and independent origins remain separate; all relations provisional.

## Exact source/rights review (agent assessment, 2026-11-02)

### Global Voices — operational headline metadata demonstrated

- General feed: https://globalvoices.org/feed/
- Related technology: https://globalvoices.org/-/topics/technology/feed/
- Related environment: https://globalvoices.org/-/topics/environment/feed/
- Feed directory: https://globalvoices.org/feeds/
- Reuse: https://globalvoices.org/about/global-voices-attribution-policy/
- Licence: https://creativecommons.org/licenses/by/3.0/
- AI policy: https://globalvoices.org/about/global-voices-policy-on-ai/

Publisher policy allows sharing/adaptation with attribution, licence link and
change indication, excluding separately owned media. Its AI policy addresses
contributor-produced writing/translation/illustration; it is not an affirmative
grant of every AI use. Pilot retains publisher, original URL, headline, supplied
dates and licence/reference under the narrow metadata processing basis. No
AI-specific permission or model-training right claimed. Article bylines and
item-specific exceptions are not fully verified, so all four summary permissions
remain UNKNOWN. No summary, snippet, full text, images or embedded social posts
are retained or redistributed. This is not permission to republish full articles.

Live robots 200, allowed feeds, Crawl-delay 10 seconds. Initial default policy
correctly deferred; pilot explicitly waits the bounded delay before requesting.
Existing WORLD behavior still defers by default. Redirects and unavailable or
denied robots remain blocked; delays >30 seconds remain blocked. Local ordinary
cadence >=1h/config, at most two feeds/host/run. Publisher numeric quota UNKNOWN.
Robots hash `443bdc1eda6b30fcccc5b2e20e3606fcba05f2ed013766887653f8a7e7b2e936`.

### SciDev.Net — reuse basis reviewed, feed operationally BLOCKED

- Configured candidate: https://www.scidev.net/global/feed/
- Policy: https://www.scidev.net/content/media.html
- Licence: https://creativecommons.org/licenses/by/2.0/
- Published legacy feed instructions: https://www.scidev.net/webfeeds.html

Written-content policy permits attributed reuse/adaptation, with original source
credit/link and reporter byline where possible; third-party documents/photos are
exceptions. Narrow headline/link/date processing only; no explicit AI-specific
grant claimed. Summary access/retention/inference/redistribution remain UNKNOWN
pending exact item/byline/exception review. Robots 200 allowed, no crawl delay;
publisher numeric rate limit UNKNOWN, local >=1h with failure backoff.
Robots hash `3c5ff08babb1546e9bcdc59d573ecf8fca61b339890e46e1ca7b2b148eebde71`.

Actual endpoint returned HTTP 200 **text/html**, not a usable RSS snapshot;
independent XML traversal also failed. Parser correctly refused unsafe/non-feed
content. Legacy webfeed JS instructions separately lead to a 404 representation
through research surface; no script was downloaded/executed. Minimal remedy:
obtain/verify the publisher's current actual RSS endpoint, or review another
free original publisher and its exact endpoint. Do not loosen the parser.

ScienceDaily was rejected: https://www.sciencedaily.com/terms.htm restricts database
storage despite offering RSS. Mongabay's no-derivatives/exception scope was not
cleared for this processing; no collector enabled. No generic public-access grant.

## Actual live observations and reconciliation

Network permission resolved DNS in this task; earlier failures remain history.
Two initial read-only preflights ran 16:09 and 16:11 UTC (23:09/23:11 Saigon).
The second retained 15 Global Voices metadata records in its diagnostic export;
SciDev failed. No canonical writes. A later temporary-store acceptance attempt
completed requests but its report export failed on Windows temporary SQLite file
cleanup (WinError32); no success credit assigned to that missing artifact.
An attempted read-only recovery found that temporary path unavailable.
The helper was corrected to close the direct SQLite integrity connection.

Successful finite live acceptance: **16:17:53.421512–16:18:20.629763 UTC**,
**23:17:53–23:18:20 Asia/Saigon, November 2**. Run
`checkpoint-b-live-acceptance`. Main Global Voices feed supplied 15 entries,
12 inside the declared seven-day publication window; technology supplied 15,
four in window. Retained 16 acquisition copies = **12 canonical URLs**, all one
publisher. Zero retention-cap omissions. Independent XML traversal of the same
bounded responses reconciled all 16 in-window memberships, zero missing URLs.
This is independent of the product parser, not an independent global recall set.
Source order was not chronological. Upstream omissions remain UNKNOWN.

Observed publisher claims (UTC; occurrence and truth unconfirmed):

| Headline / original link | Supplied publication | Acceptance first seen |
|---|---|---|
| [Bangladesh weighs tougher cyber law as AI-generated abuse targets women](https://globalvoices.org/2026/10/28/bangladesh-weighs-tougher-cyber-law-as-ai-generated-abuse-targets-women/) | Oct 28 07:51:42 | Nov 2 16:18:11.564545 |
| [Fish scarcity, tar balls, and stranded dolphins: The hidden costs of offshore platforms in Cameroon waters](https://globalvoices.org/2026/10/27/fish-scarcity-tar-balls-and-displaced-dolphins-the-hidden-costs-of-offshore-platforms-in-cameroon-waters/) | Oct 27 08:59:12 | Nov 2 16:18:11.564545 |
| [When chatbots become answer engines: AI, geopolitics and truth](https://globalvoices.org/2026/10/30/when-chatbots-become-answer-engines-ai-geopolitics-and-truth/) | Oct 30 19:30:47 | Nov 2 16:18:11.564545 |

These are actual retrieved headlines, not validated newly occurring incidents.
Publication is source-reported, not authenticated chronology or event time. Some
titles may describe retrospective developments. No detection-latency claim.
Acceptance first-seen is for this isolated live test, not a production backfill.

Eight grounded local queries ran; technology follow-up really fetched and parsed.
Actual uncovered lexical families: TRADE, CLIMATE_DISASTER, HEALTH. This does not
prove those topics absent from the world or from unretained full article text.
One in-chat manual query, `fish scarcity tar balls`, was checked and logged at
16:19:30 UTC; search returned apparent copies and unreviewed sources. No new
eligible publisher evidence selected. Empty eligible import is not zero search
results or independent confirmation. No copy texts were imported.

Three separated, sustained research sessions were **not completed**. These short
diagnostics/acceptance attempts cannot substitute for them. Offline PC windows,
continuous coverage, live independent corroboration and timely two-publisher
recall remain UNKNOWN/NOT PROVEN. No simulated session or human review invented.

## SQLite, graph and test evidence

Live acceptance used one discarded **temporary test store**, not a second
operational store. It exercised existing SQLite append, close/reopen and PIT;
integrity ok, zero records before first acquisition. Private canonical DB stayed
read-only and byte-identical, SHA256
`3e7548c55e59bf42e16a61c570122b98f5e056dcf2fa17c578d6c63a7595ec4b`, integrity ok.
No operational live backfill is claimed. Production CLI targets the existing store.

Live report/normalized metadata exported to
`tests/fixtures/checkpoint_b/live_acceptance.json`; raw feed bodies not retained.
Recorded manual receipt is `manual_search.json`. These are test artifacts, not a
second source of truth. Replay tests reconstitute metadata, preserve acquisition
times/hash provenance and distinguish them from original response bytes.

Offline graph tests use both synthetic and actually observed metadata, temporary
SQLite reopen and actual Market Analyst graph with a scripted model. No paid/live
model call or reasoning-quality claim. Existing mixed BTC/macro/WORLD graph tests
also run. Live initial rendering 5,563 characters; final rendering reserve and
graph tests enforce <=6,000 narrative and <=28,000 model prompt characters.

Focused suite: 149 passed before final manual provenance annotation.
Final full regression: **1,630 passed +99 subtests**, four expected skips, one
integration deselected, 20 existing warnings, 54.90 seconds. Final dedicated pilot
suite: 20 passed, including cross-feed 429/Retry-After host backoff. Full log:
parent-workspace `checkpoint-b-regression-verified.txt`.
Initial full run: one readiness-count failure,
1,626 passed +99 subtests; repaired generic-carrier classification without
weakening thematic readiness. Earlier isolated fixture-discovery error fixed.
AST syntax passed for all 244 tracked/new Python files (also checked 232
source/test files separately). Tracked project/new file lint and diff whitespace
checks passed.
An overly broad lint invocation also scanned preserved untracked dependency
files in `.phase12-tools/`, reporting 1,318 third-party issues; no fixes applied
there. Product/new-test lint and the subsequent tracked-project lint both passed.

Security: direct small patches, reviewed existing Python environment, ordinary
permissions, no installers, downloaded code, Defender settings/exclusions or
execution-policy changes. No new tool-reported security alert; no event-log audit
or established false-positive diagnosis. Sources and preexisting untracked paths
untouched. Staging is explicit; commit local only.

## Operator invocation and next gate

From existing repo/environment, invoke:

```text
python -m tradingagents.information.adaptive_discovery --store ../canonical-information.sqlite3 --run-id world-20261103-01 --report ../world-20261103-01.json
```

Use a new run ID/report path for a new session. Same run ID resumes recorded output;
it does not make another live scan. Existing source cadence/backoff may defer new
sessions. Report actions/health show next due, errors, uncovered topics and limits.
Do not install a scheduler. Parent private SQLite was not modified in this task.

For complementary search, use the receipt schema in `manual_search.json`, supply
the exact exported query/run ID, truthful method/operator/time/status and only
eligible result metadata. Invoke the same CLI with `--manual-import path.json`
and a new `--report` path. No automatic use of an in-chat search tool by Python.

Next: repair/replace SciDev's endpoint, clear exact summary author/exception scope
if useful, and collect three separated declared sessions with an independently
enumerated external benchmark and original-reporting lineage review. Stay in
Checkpoint B/Phase 3. Do not advance to C or causal/trading phases on this evidence.
