# Reviewed occurrence context and held-out evaluation

Freeze v2 logic before scoring: only explicit conflicts between two reviewed
canonical episode keys, location keys or non-overlapping occurrence windows
can veto an otherwise v1-eligible pair. Agreement cannot create a pair. Missing
metadata cannot reject it. Keep lexical thresholds and discovery unchanged.

The supplied 24-pair synthetic contract holdout was frozen before its first
execution, SHA-256 `4120ddff27be3ab44203d9d2e2d234ce34212c1653cb01242e41148bbb4caf1a`
(CRLF normalized to LF for cross-platform checkout reproducibility).
It has new flood/drought/grid/cyber incident names, eight positives and sixteen
negatives, with same-episode, touching intervals, separate episodes, nearby
places, disjoint times and unknown metadata cases. Source claims are stipulated,
not acquired evidence. Four templates are correlated, not 24 independent
incidents. Author knew the proposed guard: this is design-aware synthetic
acceptance evidence, NOT independent human-reviewed quality validation.
The benchmark fixture from Phase 3.4 is unchanged. No thresholds were tuned.

Production-quality independent holdout remains UNAVAILABLE. Required protocol:

1. Acquire free/eligible original evidence into the existing canonical store.
   Cover war, disasters, drought/water, agriculture, energy/infrastructure,
   health, geopolitics and technology/cyber with no BTC/price gate.
2. Freeze incident/origin clusters and split development versus holdout by
   whole cluster before tuning; keep syndicated copies, corrections, nearby
   episodes and aliases within their appropriate clusters. Audit cross-split
   duplicates. Preserve immutable IDs, source URLs, publication/acquisition
   times and origin provenance; source inequality is not independence.
3. Have a named metadata reviewer annotate each article independently of pair
   labels, using documented canonical location granularity and globally
   namespaced occurrence IDs. Occurrence bounds describe the episode, not the
   report date or arbitrary reporting interval. Leave uncertain values null.
   Preserve review acquisition time; never backfill review availability.
4. A separate reviewer adjudicates same/different/unknown pair labels, with
   date, rationale, evidence and confidence. Freeze labels/data hashes before
   scoring. Neither labels nor pair rationales enter matching or SQLite.
   Never derive metadata from pair labels or reuse test outcomes as features.
5. Compare frozen v1 and v2 on identical early/late PIT views and budgets.
   Report TP/FP/TN/FN, precision, recall, unknown/unavailable exclusions,
   candidate truncation, review coverage and family/channel strata. Reopen
   the same store and require identical results. Audit labels and metadata
   separately. Include ambiguous and missing-context hard negatives.
6. Retire a holdout from independent use after inspecting its outcomes; future
   tuning needs a new incident-cluster holdout. For adequate independent
   samples use cluster-aware uncertainty, not article-level confidence
   intervals on correlated synthetic templates. Report any recall losses.

No real-world accuracy or independent-source corroboration claim is permitted
from the current synthetic data. No new live repository/store or paid API.
