# Current M2A.1 checkpoint — 2026-10-30

M2A.1 is locally implemented and tested for the eligible subset: original Board
H.4.1 assets, reserves and distinct weekly-average/Wednesday TGA; NY Fed overnight
Treasury RRP results. All use existing contracts, canonical SQLite/view_at and
actual Market Analyst context. Daily Treasury TGA parsing is implemented and
sampled, but collection and analyst use remain gated pending detailed service
terms review. FRED remains disabled by default. See [implementation and evidence](M2A1_IMPLEMENTATION.md)
for exact metrics, rights, times, tests, live measurements and limitations.

User confirms documentation checkpoint `82c6ba6` was pushed; Gate 1 complete.
New M2A.1 commits stay local. No push is a prerequisite for local implementation.
Historical NOT STARTED statements below are superseded for this eligible subset.
M2A.2 (BLS, yield expansion, BEA GDP/PCE) remains unimplemented. Comprehensive
Phase 3 world-event radar remains required: war, drought, floods, agriculture,
energy, infrastructure, cyber, technology and pandemics, with no BTC keyword or
price-anomaly discovery gates. This macro slice does not complete world coverage.

# World scope and explicit expansion gaps — 2026-10-30

Read [binding Phase 3 roadmap](PHASE_3_ARCHITECTURE.md) and [living checkpoint](../project-settings/PROJECT_STATUS_AND_PHASE_2_HANDOFF.md). This extends the original nine-family audit below; nine families are not a product-scope limit. Documentation-only clarification: no new runtime registry or collectors.

Actual broad configuration in `tradingagents/information/sources.py` contains BBC world/technology and GDELT geopolitics/technology; `NewsDiscoveryConfig` accepts only `WAR_GEOPOLITICS` and `TECHNOLOGY`. Generic RSS/Atom capability does not prove specialized acquisition. The later manual 47-item BBC canonical-store trial in [NEXT_GITHUB_CANONICAL_STORE.md](NEXT_GITHUB_CANONICAL_STORE.md) supersedes the older no-live-corpus statement below for that bounded trial only. No continuous production or complete domain gate passed.

All families below belong to Phase 3 now. Source types are research candidates, not approved endpoints, registered collectors or cleared rights. Use broad plus specialized free legally eligible sources without BTC keywords or a price prerequisite. Per-family target cadence, regional/language recall, discovery latency, missing/stale rates and origin independence are NOT YET PROVEN. A matched headline or empty feed proves neither metric coverage nor event absence.

| Required family | Specialized free source types to assess (not clearance) | Explicit evidence / metric gaps | Current status |
|---|---|---|---|
| Wars/conflicts, geopolitics, sanctions/trade | Official sanctions/trade notices, regional and conflict/humanitarian reporting | Geography, escalation, effective dates, affected routes/entities, shipping/trade disruption, independent confirmation | PARTIAL broad discovery; specialized breadth NOT YET PROVEN |
| Drought and water scarcity | Meteorological/hydrological agencies, drought monitors, reservoir/water authorities | Severity/extent, rainfall anomalies, soil moisture, reservoir/storage and water restrictions | Incidental headlines possible; specialized collectors/metrics NOT YET PROVEN |
| Floods, wildfires, storms and disasters | Weather warnings, disaster agencies, satellite/fire and flood bulletins | Location/severity, forecasts vs observed impact, outages/damage, evacuation and update timing | Specialized collectors/metrics NOT YET PROVEN |
| Agriculture/crops and food supply | Agricultural agencies, crop reports, food-security bulletins | Crop condition/yield, planting/harvest, stocks, export restrictions, food supply/logistics disruption | Specialized collectors/metrics NOT YET PROVEN |
| Energy/oil/gas/electric grid/infrastructure | Energy agencies, grid operators, pipeline/port/infrastructure notices | Supply/production/inventory, outages, capacity, flows, restoration and physical bottlenecks | Legacy oil proxy is not physical event coverage; specialized collectors/metrics NOT YET PROVEN |
| Pandemics/public health | Health agencies, outbreak/surveillance bulletins | Outbreak geography, case/report definitions, reporting delays/revisions and restrictions | Specialized collectors/metrics NOT YET PROVEN |
| Technology breakthroughs/AI/chips/science | Research institutions, primary publications, chip/export-control and industry notices | Claimed vs validated breakthroughs, capability evidence, chip capacity/supply and deployment dates | PARTIAL broad technology; specialized verification/metrics NOT YET PROVEN |
| Cybersecurity | Official security advisories, vulnerability databases, incident disclosures | Exploit status, affected systems, severity, incident scope, fixes and infrastructure disruption | PARTIAL headline discovery; specialized collectors/metrics NOT YET PROVEN |
| Regulation and crypto | Regulator/legislative sources, protocol/exchange/issuer notices | Jurisdiction, proposed vs effective rules, enforcement, protocol/security events, operational effects | Existing Fed feed is not comprehensive regulation/crypto radar; specialized breadth NOT YET PROVEN |

M2A is only structured economic/macroeconomic restoration (H.4.1, RRP, TGA, CPI/employment, yields, GDP/PCE), NOT STARTED. It complements every world family above. M2B-D market data remain separate. Phase 4 tests causal transmission, alternatives and uncertainty from PIT evidence; no row implies automatic BTC direction. Older undifferentiated M2 priorities below are refined by the linked roadmap.

# Source coverage matrix — M0 audit, 2026-10-29

Status: code audit VERIFIED; runtime live coverage UNKNOWN. This is documentation,
not another runtime registry. Source IDs below refer to `Source` definitions and
`SourceRegistry` in `tradingagents/information/sources.py`; collector registries
remain authoritative. All paths are repository-relative. Canonical project files
in the parent `sources/` remain read-only. Baseline inspected: 78ac4d5.

Implemented means executable adapter/contract exists, not live readiness or complete
family coverage. Evidence names are exact symbols/tests. No source family is
certified complete. No nine-family production scheduler is claimed by M1.

| Family / audit status | Actual code and exact test evidence | Cadence / origin / independence | PIT, free-use caveats, gaps and next priority/fallback |
|---|---|---|---|
| 1. Global liquidity — MISSING core series; PARTIAL adjacent macro | `information/macro_series.py:FRED_SERIES` enumerates only DTWEXBGS, DCOILWTICO, DGS2, NFCI, SP500, VIXCLS. `tests/test_macro_series.py:test_fred_graph_csv_is_available_only_from_local_retrieval`. WALCL, TGA, RRP and reserves are absent from this manifest. | Existing daily/weekly reference values; caller-driven collection. FRED is a distributor, original providers differ by series; FRED and original-source copies are not independent. | Local ingestion bounds availability; graph CSV lacks upstream vintages. P1/M2: evaluate official Fed H.4.1 balance sheet/reserves, Treasury operating cash balance, NY Fed RRP first; exact vintage/frequency/access validation remains UNKNOWN. No net-liquidity formula implemented. Existing NFCI is NOT a substitute. FRED AI-use restriction below requires resolution. |
| 2. BTC spot/orderbook/microstructure — PARTIAL | `information/binance_spot.py:BINANCE_SPOT_SOURCE`, `BinanceSpotOHLCVCollector.collect`; `tests/test_binance_spot_collector.py:test_collect_normalizes_closed_bars_with_ingestion_time_availability`, `test_missing_and_latest_stale_candles_are_explicit`. | Source ID `market.binance.spot`; 1-minute BTCUSDT candles, caller-driven. Exchange-local Binance public REST. | Closed-bar timestamps differ from local knowledge time. No depth book, trade tape, spread/depth or independent exchange collector. P1/M2 prospective public book/trades and second venue evaluation; no synthetic historical book fallback. Public/auth-free does not establish redistribution rights; provider access/region and request weights apply. Live unverified in this session. |
| 3. Derivatives/options — PARTIAL | `information/binance_usdm.py:BinanceUsdmDerivativesCollector` funding/OI/mark/index/contract methods; `binance_usdm_streams.py:parse_binance_usdm_liquidation_event`. `tests/test_binance_usdm_collector.py:test_current_open_interest_is_stamped_with_local_availability`, `test_funding_backfill_keeps_settlement_time_separate_from_availability`; `tests/test_binance_usdm_streams.py:test_force_order_stream_snapshot_uses_exchange_event_and_local_availability`. | Funding settlement/backfill; current OI/mark/index snapshots, caller-driven. Liquidation parser accepts supplied stream events; no continuous stream worker. Binance derivatives and spot share provider risk. | Retrieval bounds historical knowledge; incomplete liquidation snapshots are not a complete tape or heatmap. Options IV/skew/term structure missing. P1/M2 evaluate free public options venue API; missing stays UNKNOWN, not zero. Exchange terms and regional availability require review. No live verification here. |
| 4. World/geopolitical events — PARTIAL; M1 offline polling VERIFIED | `information/sources.py:BROAD_NEWS_CONFIG`: `news.bbc.world`, `news.gdelt.geopolitics`; `news.py:parse_news_snapshot`, `poll_once`; `polling.py:coordinate`. `tests/test_broad_news.py:test_non_btc_discovery_defaults_and_atom`; `tests/test_recurring_news.py:test_domains_and_hosts_fair_bounded_and_ungated`, `test_empty_error_backoff_and_late_gap`. Fed `information/narrative_events.py:parse_fed_monetary_feed` retained. | BBC world RSS + GDELT war/conflict/diplomacy/sanctions discovery. Suggested 15-minute/source target, one-minute coordinator trigger; fair bounded host/domain turns. No BTC/price/anomaly gate. GDELT indexes publishers including possible BBC copies; two acquisition providers are not two independent confirmations. | Publication source-reported; first-seen is local, availability conservative; immutable corrections and evidence history. War/energy/trade/finance may appear in broad world RSS; complete domain/language/region coverage is not guaranteed. GDELT configured 1-day/100-item window can omit events. P0 resolve DNS and access terms; P1/M2 diversify official/regional feeds and energy/trade coverage after validation. BBC terms page fetch timed out; prior terms caveat retained, current clearance UNKNOWN. No article-body scraping. |
| 5. Technology/cyber/science — PARTIAL; M1 offline polling VERIFIED | Same adapters; IDs `news.bbc.technology`, `news.gdelt.technology`; GDELT query technology/semiconductor/artificial intelligence/cybersecurity. `tests/test_recurring_news.py:test_correction_and_non_btc_replay`; `tests/test_broad_news.py:test_non_btc_discovery_defaults_and_atom`. | Same target cadence, separate domain request budget. BBC tech and world are one publisher; GDELT host metadata does not establish authorship or syndication independence. | RSS/Atom supported, no default Atom endpoint configured. Science only incidental through broad headlines; dedicated science/security-advisory coverage missing. P1/M2 evaluate free official science and cyber advisory feeds plus regional reporting. No paid dependency. Same local first-seen/revision semantics as family 4; BBC sample fetch/parse verified; GDELT read timed out. |
| 6. BTC on-chain network activity — MISSING | No information-layer network/RPC/block/fee/hashrate/mempool collector or source manifest; repository search of `tradingagents`/`tests` for on-chain/network metrics finds no such implementation. Generic Observation/Store are contracts, not a collector. | No cadence or origin measured. | P1/M2 evaluate local Bitcoin Core/public explorer endpoints for blocks/fees/mempool, recording acquisition and reorg semantics. Public endpoint capacity/terms and node storage cost UNKNOWN. No exchange-flow inference from raw chain activity. Human sensor is only a proposed fallback, not implemented coverage. |
| 7. Institutional/stablecoin flows — MISSING | No ETF creation/redemption, stablecoin issuance/redemption/supply, exchange reserve/flow collectors or registered source contracts in information layer. Symbol aliases/USDT pairs in `dataflows/symbols.py` are not flow data. | No cadence or independently verified origin. | P1/M2 evaluate issuer disclosures and official fund reports; validate release times/revisions and avoid double-counting issuer/dashboard copies. No paid flow vendor, no estimated flow presented as observed. Manual sourced input remains future fallback; no current runtime capability claimed. |
| 8. Cross-asset conditions — PARTIAL | `macro_series.py:FRED_SERIES`; `treasury_rates.py:TREASURY_DGS10_SOURCE`, `TreasuryYieldCollector`; `tests/test_macro_series.py:test_macro_state_replays_only_known_latest_values_and_reports_freshness`; `tests/test_treasury_rates.py:test_treasury_revised_value_is_visible_only_after_new_ingestion`. Scheduled BLS/FOMC/BEA in `scheduled_events.py`, `tests/test_scheduled_events.py:test_fomc_date_change_replays_latest_schedule_under_stable_meeting_id`. | Daily dollar/WTI/2y/SP500/VIX, weekly NFCI; Treasury 10y daily; schedules caller-driven. Treasury via FRED and Treasury direct share underlying origin. Broad dollar proxy is not ICE DXY. | Backfills become known only on ingestion; reschedules/revisions replay locally. No global rates/FX/equity coverage certification. P1/M2 original-source alternatives and license review; no silent substitution of proxies. FRED-related AI use unresolved. Legacy Yahoo tools outside canonical evidence guarantee. |
| 9. Sentiment/expectations — PARTIAL legacy; durable PIT coverage MISSING | `agents/analysts/sentiment_analyst.py:create_sentiment_analyst` and `dataflows/vendors/stocktwits.py` and Reddit fetchers; `tests/test_social_lookahead.py`, `tests/test_stocktwits_resilience.py`, `tests/test_reddit_fallback.py`, `tests/test_post_screen.py:test_the_sentiment_analyst_hands_the_screen_to_both_social_fetchers`. Scheduled calendars describe upcoming events, not market consensus. | Analyst-request-driven news/social, platform search bias and shared reposts; no measured representative sample or expectations curve. | Legacy social/news filtering does not archive reproducible intraday vintages. No options-implied distribution/consensus/survey collector. P2/M2 assess public expectations and durable acquisition; don't count LLM sentiment output as raw evidence. Existing vendor routes can require keys/paid access: M1 never invokes them and adds no paid requirement. |

## Shared integrity and verification

`observations.py:Observation.available_at`, `store.py:SQLiteInformationStore.view_at`,
`claim_lifecycle.py:record_claim_assertion` and `claim_lifecycle` are the existing
contracts. Explicit independence needs curated evidence; different domains,
URLs, publishers and official-report status never automatically establish it.
`tests/test_claim_lifecycle.py:test_syndication_and_independence_unknown_until_evidenced`
and `test_source_history_survives_article_revision` demonstrate the boundary.

At cutoff T, publication/update/retrieval bounds exclude later observations and
corrections. GDELT seendate is discovery, never publication or local first-seen.
Legacy news/social tools and date-based memory remain outside full intraday PIT;
explicit graph cutoff does not certify the entire reasoning run as PIT.
The narrative reservation is 4,000 characters; overall information context 28,000
characters, not 28k tokens or a full-conversation budget. Whole records may be
omitted with disclosure. Source health is evidence of attempts, not evidence of
complete world coverage or factual truth.

Initial live validation on 2026-10-29 10:52 Asia/Saigon: all four configured feed requests
failed DNS with 11001; BBC/GDELT/Fed DNS lookups failed. No proxy types or CA override
variables configured; local CA bundle exists. No TLS handshake/HTTP/parser response
was reached. After explicit turn-scoped network permission at 10:56 Asia/Saigon, all three
DNS names resolved. Both BBC downloads succeeded; separate adapter parsing returned
27 world / 20 tech articles, all with publication times and conservative local
availability. Both GDELT requests timed out at read (10-second limit). A loopback
HTTP/reopen/repeat/replay smoke passed. Thus BBC live fetch/parse is VERIFIED for
these samples; GDELT and ongoing operation remain unverified. No live corpus was
persisted or scheduler installed; no full operational live gate is claimed. See 3.2C handoff for test details.

## Free access and licensing audit (not blanket clearance)

- No M1 dependency or key purchase. Python standard library, requests, SQLite and
  existing pytest/Ruff only. Existing optional paid vendor code remains legacy.
- [GDELT official API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
  fetched 2026-10-29 confirms article-list search and JSON. Documentation access
  is not collector live validation or a license for publishers' article bodies.
- [BBC feed directory](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm)
  could not be fetched in this audit (timeout). Prior handoff notes business reuse
  restrictions; current feed license/operational permission remains UNKNOWN.
- [FRED legal terms](https://fred.stlouisfed.org/legal/) fetched 2026-10-29 explicitly
  restrict use of FRED Services/Content in development/training of AI systems, and
  third-party series have separate rights. This is a material unresolved constraint
  for this product: do not expand or claim cleared FRED AI use. Preserve existing
  code for compatibility; resolve scope/permission or use permitted original-source
  data before production AI integration. No FRED live acquisition in this task.
- Exchange public access is not blanket reuse permission. Actual endpoint access,
  regional constraints, attribution, original-source rights and rate limits must
  be validated before operational release. No paid substitute added.

M2 priority order: resolve access/live/legal gates; liquidity core and prospective
microstructure; on-chain/flow/options contracts and official/regional/science source
coverage. M3: evaluate evidence-backed correlation, source-origin accuracy, competing
hypotheses and reaction alignment without using price moves to gate discovery.
Neither M2 nor M3 implementation is included in M0/M1.
# Release verification follow-up

The 2026-10-29 [macro eligibility review](MACRO_SOURCE_ELIGIBILITY.md) records
the default FRED disablement, exact original-publisher candidates, observed access,
cadence/vintage requirements and unresolved gaps. This supersedes earlier FRED
default guidance; it does not mark macro replacement coverage complete.
