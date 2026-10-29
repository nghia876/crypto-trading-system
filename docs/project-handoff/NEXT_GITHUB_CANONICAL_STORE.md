# NEXT session: GitHub recovery and canonical live-store trial — 2026-10-29

## Observed outcome

Starting branch `phase-3-event-narrative-slice`, HEAD
`ac4e396e809db54d39221a1988b555916bda7f8a`, tracked clean except original
untracked `.phase12-tools/`. Fetch succeeded: 0 behind / 4 ahead; remote feature
`78ac4d58299dea94b3655ed98029762b6d226277` is an ancestor. Reviewed the committed
16-file diff and checked secret/private-path candidates before normal push.
No main change, history rewrite, force push, source edit or tools-directory edit.

Normal feature push failed again with MSYS BaseNamedObjects 0xC0000022 and
credential-helper waitpid failure. Credential manager 2.7.3 starts with --version;
explicit executable helper configuration still starts the failing shell. A bounded
native credential-manager lookup with interaction disabled also failed (exit
4294967295; access-denied diagnostic). Its captured credential/error output was not
printed. No credential was written to disk/config/URL. No GitHub CLI or existing
SSH setup was found. Available connector ref/commit APIs do not by themselves upload
the exact local Git object graph; reconstructing replacement commits was not used.
Code Integrity and AppLocker event-log reads were denied; no policy attribution is
proven and no OS security setting was changed. Host repair of approved Git/GCM
execution and credential-store access remains required. Then normal push this
feature branch and verify ls-remote equality. Read-only network access works.

## One canonical prospective live trial

One persistent SQLite file was created OUTSIDE the Git checkout, under the task
workspace's sibling `local-runtime/`. Local `config.local.json` holds its absolute
`information_store_path`; both acquisition and actual graph verification read the
same file. The exact host path and commands are in `local-runtime/OPERATIONS.md`,
kept outside Git. This is a manual live trial configuration, not a globally loaded
production default or production approval. It contains real feed evidence, not
synthetic demo observations. Do not create another operational news database.
The project workspace is persistent locally; relocation/backup remains a host duty.

At 13:30:02 Asia/Saigon (06:30:02 UTC), existing coordinator/poll_once adapters
persisted BBC world 27 and technology 20 items, no BTC keyword gate, no article-body
crawl, no paid API. The two bounded one-source invocations use the same store and
job lock. All 47 observations have publication times; local first-seen range
06:30:02.457771–06:30:02.538125 UTC. Reopening preserved records; pre-acquisition
cutoff excluded all. A later regular CLI poll-once respected BBC cooldown, attempted
GDELT technology and persisted ReadTimeout, with geopolitics budget-deferred by
shared-host fairness. GDELT geopolitics was not attempted in this session.
Health is persisted in this same SQLite file, not a separate operational database.

Actual TradingAgentsGraph propagated BTCUSDT at the archived cutoff using the
local configured path, existing PromptCapturingModel and mocked legacy vendors.
Network was explicitly denied during replay. Two archived evidence IDs reached
captured prompts; analysis_information was 8,299 characters. Context truncation
means this does not claim all 47 stories reached the analyst. No live LLM, trading
quality or whole-system historical PIT certification is claimed. Local JSON reports
preserve counts, timing, hashes, health and graph outcome. No scheduler installed.

Focused recurring/broad news/store/graph/FRED tests: 103 passed, 8 subtests, 9.29 s.
Full regression result is recorded in the final session report below.

## Prioritized M2 implementation order (plan only)

All adapters must use existing Observation/Source/CoverageRecord/
SQLiteInformationStore and analyst renderer; preserve raw provenance, units,
publication vs first-seen/retrieval, conservative availability, append-only
revisions, cutoff tests and explicit missing/stale coverage. Never backdate newly
fetched history. No mandatory paid API. FRED stays disabled pending permission.

1. Fed H.4.1: total assets, reserves and distinct TGA weekly average/Wednesday
   level. Archive dated release tables; validate columns and million-USD units.
   This establishes the weekly liquidity baseline before derived calculations.
2. NY Fed ON RRP: restrict overnight Treasury operation results; verify dollar
   units and operation/release times. Keep distinct from H.4.1 reverse repos.
3. Treasury daily TGA: reconcile dated DTS with API metadata, including schema
   changes and closing-balance row stored in open_today_bal. Do not substitute
   daily closing balance for a weekly average. Resolve Treasury reuse conditions.
4. BLS CPI then employment: CUSR0000SA0/CUSR0000SA0L1E,
   CES0000000001/LNS14000000. Calendar-driven releases, SA/NSA labels, indexes
   versus growth transformations, payroll/seasonal/benchmark revision histories.
5. Treasury yields: official par-curve XML, 2y/10y initially; reuse existing direct
   Treasury contracts where valid. Validate methodology vs H.15, acquisition-time
   availability, corrections and bounded timeout behavior before expanding tenors.
6. BEA GDP/PCE: free registered API or official release files; discover current
   metadata before pinning tables/lines. GDP nominal/real/annualized growth remain
   distinct; PCE headline/core price indexes separate from consumption spending.
   Save advance/second/third estimates and monthly/annual revisions prospectively.
   No key signup or paid service performed here.

Implement each with offline parsing/revision/cutoff tests, bounded official live
sample, same-store reopen/graph proof and missing/stale output before moving on.
Any assets-minus-TGA-minus-RRP series is a labeled aligned transformation, not
reserves or established BTC causality. Broader war/geopolitics, technology, energy,
trade, crypto and BTC market data stay integrated in the same architecture. Regional,
official and science feed diversification and on-chain/flow/options gaps remain M2;
M3 measures evidence origin/correlation, competing hypotheses and reaction alignment.
No full M2/M3 implementation in this session.

## Official-source eligibility recheck

- Board public-domain policy (exceptions and citation apply):
  https://www.federalreserve.gov/disclaimer.htm — successfully rechecked.
- BLS publications public domain except specified illustrations/photos; cite BLS:
  https://www.bls.gov/bls/linksite.htm — successfully rechecked.
- NY Fed permits automated access/storage/derivatives with attribution, notices,
  transformation labels and other conditions:
  https://www.newyorkfed.org/privacy/termsofuse — successfully rechecked.
- BEA official API guide retrieved; registration/UserID required:
  https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf
  Developer page https://www.bea.gov/resources/for-developers retrieved; monthly
  PCE release described at https://www.bea.gov/data/personal-consumption-expenditures-price-index/.
  Copyright FAQ timed out; previous review remains qualified, no blanket clearance.
- Treasury about/usage page returned 403 to web reader; eligibility review remains
  open. Access in the previous session does not establish rights.
- BBC feed terms remain an operational gate. Official feed directory and terms PDF
  were located, but no inference that this persistent AI use is cleared is made:
  https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm
  https://downloads.bbc.co.uk/usingthebbc/bbc_terms_of_use.pdf

These are bounded source assessments, not blanket legal clearance. No recurring
production acquisition is enabled. GDELT access, BBC persistent-use eligibility,
longer prospective operation, production launcher configuration and backup are
remaining gates. Manual live evidence/replay now passed; full live gate did not.

Full default offline regression: 1420 passed, 4 skipped, 1 deselected; 99 subtests; 33.93 s. Twenty existing model-name warnings. No application code changed. Diff whitespace check passed. Documentation-only follow-up commit remains subject to the same GitHub backup blocker; final response records its SHA.

