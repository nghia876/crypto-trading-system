# Phase 3.8 original-evidence review — UNREVIEWED

Use [the version-bound JSON forms](PHASE_3_8_REVIEW_PACKET.json).
Three proposed pairs, five unique articles, **zero human reviews**. Agent source
checks are supporting research, never human judgments or imported event context.
The original Phase 3.7 proposals and retired Phase 3.6 holdout remain unchanged.

## Independent article review first

Review the `articles` section separately before examining pairs or matcher output.
Open the original links below. Record actual reviewer identity, aware review time,
source URL, the specific passage supporting occurrence/location, and uncertainty.
Leave occurrence/location null unless supported; publication/update is not occurrence.
Page access in web research can be cached. These checks do not authenticate the
publisher's historical claim or independently establish a real incident.

| Article | Supplied timing and location evidence | Outstanding check |
|---|---|---|
| [Florida response](https://water.usgs.gov/alerts/item_2026-10-10_11:35:45.html) | Page date Oct 10 2026 11:35:45 EDT; Florida Panhandle, Tallahassee response | Page footer says modified Sep 1 2023, inconsistent chronology. Absolute hurricane/flood occurrence unverified. |
| [Florida Day 2](https://water.usgs.gov/alerts/item_2026-10-11_11:27:02.html) | Page date Oct 11 2026 11:27:02 EDT; Florida Panhandle and Shoal River near Mossy Head | Same footer conflict; relative “second day” cannot safely supply absolute occurrence bounds. |
| [Earthquake record](https://earthquake.usgs.gov/earthquakes/eventpage/us7000ttxz) | Archived Atom title southeast of Easter Island; source update Oct 30 10:38:47.040Z | Research returned only JS shell. Event occurrence/location details require manual verification. |
| [Chickenpox news](https://www.gov.uk/government/news/new-report-shows-toll-of-chickenpox-with-over-3000-infants-hospitalised-last-year) | Page published Oct 30 2026; describes England's 2025 surveillance and links annual report | Decide event unit: report release versus individual outbreak. Do not assign 2026 occurrence from release date. |
| [Varicella report landing page](https://www.gov.uk/government/publications/varicella-epidemiological-reports) | Published Oct 30 2026; applies to England; links 2025 epidemiology report | Verify underlying report and temporal scope; same reporting origin as news. |

All original source dates, immutable article/response hashes, local first-seen,
retrieval and publisher groups are in the JSON packet. Exact check provenance is
in [URL checks](PHASE_3_8_URL_CHECKS.json). OGL material: Contains public sector
information licensed under the Open Government Licence v3.0. USGS material credited
to USGS; third-party works excluded.

## Separate pair adjudication

| Pair form | Compare | Required choices |
|---|---|---|
| phase38-1 | Florida response / Day 2 | Same incident / Different incident / Insufficient evidence |
| phase38-2 | Florida response / Easter Island earthquake | Same incident / Different incident / Insufficient evidence |
| phase38-3 | Chickenpox news / varicella report | Same incident / Different incident / Insufficient evidence |

For every judgment record `reviewer`, actual aware `reviewed_at`, `review_kind`,
`rationale`, cited `provenance`, occurrence/location evidence and confidence.
Labels map to `same_event`, `different_event`, `unknown`. No judgment is prefilled;
`unknown` plus `pending` means UNREVIEWED, not an adjudicated insufficient-evidence
decision. Disagreement stays disputed/unknown outside SQLite. All publishers in
each proposed pair are shared; no independent-origin claim is established.

Keep the source packet immutable; save completed forms to a new file, preserving
packet hash, article hashes, label version and supersession history. Reviewer
identity strings cannot authenticate human participation or reviewer independence.
Do not relabel agent research as human review. Do not tune the matcher on this
packet or recycle the retired holdout. Use the Phase 3.6 independent article,
pair, conservative connected-cluster and untouched holdout procedure before scoring.

## Reproduce the neutral packet

From repo-checkout, using the existing reviewed Python environment:

```powershell
& ../phase3-final-env/Scripts/python.exe -m tradingagents.information.operational_review --store ../canonical-information.sqlite3 --proposals tests/fixtures/phase37/pairs_unreviewed.json --checks docs/project-handoff/PHASE_3_8_URL_CHECKS.json --cutoff 2026-11-02T02:18:40.850024+00:00 --output ../review-packet-copy.json
```

Read-only SQLite access; refuses output overwrite. Checks have their own later
research date: the packet cutoff binds archived article availability, not a claim
that subsequent URL research was known at that historical cutoff. Nothing from
this packet enters replay/analyst knowledge automatically.
