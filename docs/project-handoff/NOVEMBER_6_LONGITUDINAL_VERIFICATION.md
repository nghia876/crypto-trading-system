# November 6, 2026 longitudinal persistence verification

**Operational checkpoint PASS; fresh acquisition PASS; actual analyst visibility PASS. Phase 3 remains IN_PROGRESS.**

User-invoked second independent live session; no feature development, scheduler or later-phase implementation. Same ACTIVE absolute canonical SQLite authority:

`C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`

Baseline branch `phase-3-event-narrative-slice`, HEAD `5b9ec3a80a9c1013ad563b6b14a3e9e8317ebdb6`. Tracked tree clean before reporting; existing `.phase12-tools/` and `PHASE_3_BOTTLENECK_DIAGNOSIS.md` preserved. Origin is `https://github.com/nghia876/crypto-trading-system.git`. No push, merge, rebase, force or main operation. Remote HEAD was not re-queried in this session.

## Real sessions and canonical baseline

Prior run `canonical-activation-20261105T032710Z`: November 5, 03:27:10.223444–03:27:26.572006 UTC / 10:27:10–10:27:26 UTC+07.

New run `canonical-longitudinal-20261106T023810Z`: 2026-11-06T02:38:10.235519+00:00 through 2026-11-06T02:38:29.353156+00:00 UTC. Asia/Bangkok and Asia/Saigon local time: November 6, 09:38:10.235519–09:38:29.353156 (UTC+07). Real wall-clock invocation, not replay or synthetic session.

| Table | Before | After |
| --- | ---: | ---: |
| observations | 1254 | 1291 |
| source_definitions | 143 | 146 |
| coverage | 167 | 171 |
| data_gaps | 0 | 0 |

All 1,254 prior observations remain byte-for-byte equal as SQLite rows: original 1,219 union plus November 5’s 35. November 6 adds 37 retrieval observations, comprising **8 genuinely new articles, 29 unchanged retrieval copies, zero content revisions**. Unique content versions 863 → 871; supersession links 85 → 114. Those 29 new links preserve retrieval lineage; they do not mean 29 editorial revisions, popularity increases or independent confirmations.

Before SHA256: `76d741733dc132d8583c91b88e448fba23622779e74d92eff6dcbdd4786fdca7`.

After SHA256: `ea3739b621e02f188b0f19c45203ba29e632bcd8464679b2cd214140874800f2`.

## Bounded collection and rights

Reused inspected `activation_live_once.py` wrapper via private November 6 adapter, calling existing production `coordinate` / `poll_once`, `job_lock` and `PolicySession`; only exact registered IPS/GV configs, 40-item cap each, seven-day supplied-date window, no retries. Attempt marker prevents accidental repeat invocation.

| Feed | Fetched items | Retained/eligible | New articles | Unchanged | Content revised | Outside window | Slice/rights dropped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| news.discovery.ips | 35 | 24/24 | 5 | 19 | 0 | 11 | 0/0 |
| news.discovery.globalvoices | 15 | 13/13 | 3 | 10 | 0 | 2 | 0/0 |

Exactly two feed and two robots requests, all HTTP 200, no article requests, redirects, paid APIs, bodies or summaries retained. Robots allowed both feeds; Global Voices declared 10 seconds, measured robots-to-feed request-start interval **11.375 seconds**. No duplicate items, parser overflow, slice omission, transport errors or rights denials. Rights references checked on November 6:

- [IPS RSS headline permission](https://www.ipsnews.net/rss-feeds/): attributed titles/headlines; complete stories excluded.
- [Global Voices republishing guidelines](https://globalvoices.org/about/global-voices-attribution-policy/): existing conservative headline/link/date scope retained, summaries/body/media excluded; no rights expansion.

Zero data_gaps rows does not imply uninterrupted coverage. Health journals disclose approximately 79,863 seconds of unknown coverage after the prior one-hour due time until this invocation; no historical polls were invented. Both sources responding and fresh_24h at completion; rolling-feed omissions and source completeness remain unknown. Exact original reporting/syndication independence is unverified. BBC/GDELT and legacy EIA were not requested or newly authorized. Political manual queries remain plans, not live search API results.

## Political/electoral metadata observations

New IPS metadata includes the attributed headline “INDIA: ‘The Protest Movement Refuses to Die down, and the Government’s Legitimacy Is Now in Doubt’” (published November 5 06:39 UTC). New Global Voices metadata includes “What comes after networked authoritarianism?” (November 5 16:17 UTC). These are publisher-attributed headline observations, not verified factual or causal claims.

Repeated metadata includes the IPS Strait of Hormuz / midterm-election headline and Global Voices Flávio Bolsonaro / Brazilian press headline already seen November 5. They are unchanged, not new electoral developments or independent confirmations. No inference that either publisher systematically covered midterms, no election forecast, BTC-keyword filter or BTC causality claim. Dedicated official election-results/calendar/polling coverage remains a gap.

## Restart, PIT and actual graph

Two separate verification processes reopened the exact canonical path read-only and produced identical reports/context hashes. SQLite integrity and foreign keys, all application source/evidence references, content versions and revision lineage passed. All original table rows preserved; all 70 recorded historical cutoff views exactly equal both the original 1,219-row union and the pre-session backup. Seven new session/start/availability boundaries passed; no future IDs or first_seen leakage. Repeated records retain November 5 first_seen; their new retrieval copies become available only November 6.

Actual `TradingAgentsGraph.propagate` ran with scripted models and socket/DNS/requests/curl networking denied. Pre-session prompts contain zero November 6 IDs. Post-session prompts contain two genuinely new IDs:

- news.discovery.ips: `news:f39d0d3242799f7585245b7d44e114e7cea242e7f40c580cc8f2a9a537dd6ba2` — I Also Accuse. First_seen = available_at `2026-11-06T02:38:16.906304+00:00`.
- news.discovery.globalvoices: `news:d2c0870c85b4c22ef51019b67d6004d5f11685169eb0ce482f136130bf62b436` — Global Voices condemns the attacks on Albanian fact-checking service Faktoje. First_seen = available_at `2026-11-06T02:38:29.300218+00:00`.

**865 canonical narrative candidates, 7 included, 858 omitted** by whole-record budget; IPS 1/27, Global Voices 1/16. Of eight genuinely new articles, two included and six omitted by budget/lane selection; all eight remain stored and PIT eligible. Repeated copies did not inflate candidates: 857 → 865, exactly eight new canonical articles.

Narrative **5,781 / 6,000** characters; mixed information **15,771 / 28,000**; largest single prompt **23,283 / 28,000**. Official/specialist WORLD selection retains FCDO, NASA, UK energy and UK food (five records), alongside the two publishers. Existing macro/liquidity evidence and BTC spot/derivatives freshness/unknown disclosures remain in mixed context. This session did not refresh BTC/macro observations or establish their current freshness. Scripted model BUY text is test scaffolding, not a trading recommendation.

## Private recovery and preservation

Fresh SQLite backup: `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\longitudinal-20261106T023740Z\pre-session.sqlite3`.

Backup SHA256: `02c35949bb1cd4bc1e4d5f1914f4aa060b17495e28522affd96c1a853549f918`.

Isolated restoration: `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\longitudinal-20261106T023740Z\isolated-restored.sqlite3`; exact schema/all rows/application integrity match the 1,254-observation pre-session baseline. Known November 5 recovery archives rechecked against recorded hashes and validations. No production rollback. 1705 pre-existing reference/fixture/tool/diagnosis/authority/recovery files retained unchanged. Synced sources and frozen manifests untouched. No security-setting changes, bypasses, exclusions, installations or observed tool-reported Defender block; no Defender event-log audit claimed.

No production code changed, so full regression was not rerun. Operational exact-row/PIT/recovery/actual-graph verification is the relevant validation; documentation whitespace checked before local commit. Private database, backup, prompt and JSON evidence remain outside Git.

## Next step

Longitudinal gate PASS. Proceed next under the planned implementation scope to **C1 event identity and narrative propagation across sessions**, preserving repeats/origins and attention-versus-credibility distinctions; then **C2 bounded BTC spot order-book and executed-trade acquisition**. Phase 3 remains IN_PROGRESS. Any guarded GitHub backup is separate; nothing pushed here.

## Complete November 6 retrieval identity ledger

| Source | Kind | Observation ID | Prior observation ID | First seen UTC | Available UTC |
| --- | --- | --- | --- | --- | --- |
| news.discovery.ips | new_article | `news:f39d0d3242799f7585245b7d44e114e7cea242e7f40c580cc8f2a9a537dd6ba2` | none | 2026-11-06T02:38:16.906304+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | new_article | `news:76e6b4b276a4acd682a4c289ff3eeef00a125b0abae5b92da8b601ee973d34a4` | none | 2026-11-06T02:38:16.906304+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | new_article | `news:d042d5f9695db969150251cb2dcc525651acbab37bdd3681959502a0185813f9` | none | 2026-11-06T02:38:16.906304+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | new_article | `news:c4057fa73e957f37c0a008b007c4a5d198630070b47f7308782b237f8c0dc8c1` | none | 2026-11-06T02:38:16.906304+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | new_article | `news:ee9a15175a8de9092640b15503e97dea88c6637348bbafcc0361d02593a3b8a4` | none | 2026-11-06T02:38:16.906304+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:c0d5c6e19c74e7450d0c0b8a9af9d57a3c97a4a0f54d8769f2790d4fb734e633` | `news:7e124134912977194941ac599865fc05f579956dfa3cd9b17360886479b89950` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:16e0ca810a8377a5601e660f53b5981177b6830307a0600b3e411dd3f6fbde06` | `news:933d66cc44027f84d1995e3da6157dcb5969e7ac949cf35204a8b8820f084d9d` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:2e3edaf7e803797beec401b8f16177befe5b98f6e35bd0daea9586b0c717c8bc` | `news:4a4088f203426b988a6ffa4315d7113a76320ebae707499f0652984f68adf2d5` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:a318bb07169bf5f651696cb123b21302bdb67cb7c6b67bbd8b4158d217ff422c` | `news:b6b2b413df18acbe67f0ca9fead3b8e812636543c14cfb45285fe996105af14c` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:933299a17e00053f4263c8f07c3bf8b6e779871d2b80269347a0e183dcfc593c` | `news:66632118552fe0e5bb40b96547b174f31ea84d264d80f06c44fa58ae11b9abb8` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:7776ca770ab5e3f4b5ae53e95de3ac3b2bd0819d8fc27468d5bfe2ce425675c0` | `news:e555f67d68bd2408a8992c8e815a5d49fa4e3862650080ff732ec20f62aab6a0` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:e6fb2db4786ce4a3ee3fe5122204431700b43621549a33005f8433193b93d096` | `news:fff46d14b21d2fb47eb0dd0b87bd4a7ca823762de456c9d41c65821775a70905` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:771198851cb0f6890a34491c9971f9b652f330cfe8aed54b5083b4f39edf2d95` | `news:af2e7deafe93413185ae9c21c5b279ecc263052166e92f524e1979e1a093be1f` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:d468814475b150292c00143de791920546f11f7ae5af7fd6fba1cec3f40f88c5` | `news:10f72daa61421e64fa9b6c514e2ebb1cd58d23ea11ea2cffb859f6da8b98ee05` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:42e0ab84827223fb3f01dbc8593ebe47ef70f584fb18128868049edd4ad2dfc1` | `news:0ba4f48f2cfd965f2a6c5b92ad45b261bfec9e3f7d21d1b3825799eb2883763e` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:b1e0edd76eb99640eacc1c0ead66537d15caadc9ef4bb31deb2bedd7cf5b2bc5` | `news:1d84af64bb4fd166e607763ce67a8e4a7538141ba5e909d741ede900d74739e4` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:2cab81021e2a531fd3333ccae7e0c599864df76f744638cfee61ffbd0afc3452` | `news:25da6eb475fa7ece2186dd19e98b72cb1100cb0aefee2ac5835f7e68f313cad5` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:a20bec49e0af45693d738749c01dc6dbfbace698b662c8ec74a0bdc9d12c7a7e` | `news:333ae9e86127d64cbb293a104dc2ce96efff34f5ee3e67c4cb30d21f7c9a2820` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:2fdcfbb745b24aa328b2dd93a56a978e6da7be81893601d7adb0bf823f399a36` | `news:5cd59588009e8cc3d35725e960e45ec872f3f50896c609f9b7fc7e32e73ae498` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:5356be9c19428ac829a20426ecb62f7f65f43efd787752a80257e909b8898d8a` | `news:b980bb1fda7bf48920e1dd0e4c86955578ea3cb3d505e710d55722fd88205c8f` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:1738df8c9499ab580851cea2479a8e94c24188f4f542d1eae835853d11873502` | `news:14245c924ac43a872af42ed9b5d7bbe6b00d36aa4a2c8e05e994206e6d766c48` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:3a22d2ba95db8417d926240eb1412c499bd1cd0062d541310be699ca6ee5fdb3` | `news:29b3ccfd16be4c75f3b3b000408ad590cd69b97a0b37cc31384ec93769e0ee1b` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:924d1d76ef0b53f74e28e7bccf7a2100308cca5f683f7ed9d69e1601077ecba1` | `news:0b1940747bd2fd31f0351eab9101e829901b0e51ac28cd382672f5997ac85560` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.ips | unchanged | `news:806f8603e2d25807ac845569947dc86d4ac7d6cd1016479c529d9b56eec98b9e` | `news:275c13141e91154f125d3b80f83f1b4d94184fb8799c76c7d7084f647e8595dc` | 2026-11-05T03:27:13.774952+00:00 | 2026-11-06T02:38:16.906304+00:00 |
| news.discovery.globalvoices | new_article | `news:d2c0870c85b4c22ef51019b67d6004d5f11685169eb0ce482f136130bf62b436` | none | 2026-11-06T02:38:29.300218+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | new_article | `news:140a1e649f0698d2b597a047e70354cb03ea7e973c97f68a78308f7068cdfb2c` | none | 2026-11-06T02:38:29.300218+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | new_article | `news:7a3adf353f8187a1a2e295d1bb8b346c6beedc512d077d80b0eb8dfb338de157` | none | 2026-11-06T02:38:29.300218+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:d96530bc88cfde443fe068c3518cf736203a863ff859a9c767453596fe1fa9b3` | `news:c0fa3590fd1352decc9378824ccd8e898a918e8b2e7162cb1c7628e1723028f5` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:fcf48af94c3e94cf25206ddbf0943a5d2415716f49f4bf4d01ead29b2223ee73` | `news:2bf7c90a1b0556010c0f51e8f999179acf1537ad7a11f63cc99cbaff605744ad` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:94f34192d7135df97c8d58ccee0f99598c96c63c7c55ded146156056021663e5` | `news:5ab9976121803f9a21832e355b785c82b9e073907f3455b8bd04ef1a27f0ed5a` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:6607cf5474ff03d568c5f73063a141ef350c37e6fbe8ded61b219efc3714f73f` | `news:065c785118c0225608e974990136e98896e9271658536825a8a6237d67ad0742` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:9296979a952e1fdd39d884f4754fbed39bbbdf46bece6f7a501088697fe41d2a` | `news:5f57f2fe5111d04ae5e3e4f7f703c63d3908bbee3dfa88d0cd4597baf05cb14f` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:909310b79f5f30623111e7a4c8782c3785394849046705ba06967ed1e3483843` | `news:21b5a76d3c5710ff4b52d810debb9fd55348bfebf2cd8408a726aa76452ce8b1` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:dfc23050f512d958cfc5aeb872d37385392515a8e195dc1cc75ace89dad78a51` | `news:36dd4015dad477a6ea4de9d2721ad7708c26e1a26c2bfc374e7bb59e45890537` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:62934f0e5da205a86e52a09022b75a7b196b5cd0f8f1310643fd875ed8e8e640` | `news:fce345dce2819cd2b804b1dc36b1ff098a26c70bbe5e2b6c07192664f1f4a76a` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:ef217719e5357dc679a173fe7d29b0845f964303770fc0eea0ef6052d836522b` | `news:eae8c9aaba71b3343b6048ef46b05e09c4e67b130b1ef2d28cd7ab6d5253881d` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |
| news.discovery.globalvoices | unchanged | `news:fde311e4ab4a94f6593a9c93b5a9241d8db68ce7f1bb12aeaf473355ed33b84f` | `news:a6335ab69d6bf4f32ff304779e70f33c07959791d01fccf226f3226260319b44` | 2026-11-05T03:27:26.528490+00:00 | 2026-11-06T02:38:29.300218+00:00 |

All 29 repeat prior IDs resolve to the November 5 run; zero cross-feed canonical-URL matches among the retained November 6 observations. This does not prove independent reporting origins.

After-table row SHA256 digests:

- observations: `a65251751d89b0da5e538942a4578695612cfaa2610cbd8c9d09be5ad264921d`.
- source_definitions: `dbfea72a99b6685f6b653ce8e84bdd9e71895cee9a00893697bf9ec357e74025`.
- coverage: `7e8fcf79b59f260af36acb5d086b2f5e62ad3da33d8c13423c7e341e208ed7d2`.
- data_gaps: `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
