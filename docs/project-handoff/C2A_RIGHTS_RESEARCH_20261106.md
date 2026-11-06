# C2-A venue eligibility investigation — November 6, 2026

**Kraken and Bitstamp remain BLOCKED. No venue is approved or enabled.**
This is a bounded official-document review, not a legal determination that all
API use is prohibited. Public documentation and anonymous endpoint availability
do not establish all required rights. No live market endpoint was called, no
provider response retained, no account created and no provider contacted.

## Review scope and interpretation

Retrieved official legal, developer and support pages on November 6, 2026.
The user's applicable contracting entity, residence and account eligibility
were not established; Asia/Saigon timezone is not evidence of jurisdiction.
Permission attributes must be independently evidenced for the exact source,
endpoints, user and intended uses. UNKNOWN must fail closed. Technical
documentation establishes advertised behavior, not observed behavior or a
durable licence. Redistribution is separate from third-party model processing.

## Rights by use

| Use | Kraken prospective BTC/USD | Bitstamp prospective BTC/USD |
| --- | --- | --- |
| Automated acquisition | UNKNOWN applicable API exception; documentation supports automation but terms restrict it | UNKNOWN exact applicable scope; public API documented |
| Private durable retention | UNKNOWN | UNKNOWN |
| Internal AI inference | UNKNOWN; no affirmative permission established | UNKNOWN; no affirmative permission established |
| Third-party model processing | UNKNOWN; making content available to third parties is restricted | UNKNOWN |
| Redistribution | Restricted absent applicable permission | UNKNOWN; no redistribution licence established |
| Activation | BLOCKED | BLOCKED |

For Kraken, the [Global Terms](https://www.kraken.com/legal/global-terms),
last updated October 30, 2026, section 8 grants revocable own-benefit use.
Section 9 restricts copying, extraction, automation and third-party availability;
it also says: “develop any third-party applications that interact with Our
Content without our prior written consent”. These provisions and the API
documentation require reconciliation for this exact workflow. The reviewed
terms identify separate Canadian, EEA and Brazilian terms. This review does
not select one for the user or infer an AI licence from silence.

The [Bitstamp API documentation](https://www.bitstamp.net/api/) says commercial
company use requires a signed Data License Agreement; short exact excerpt:
“receive and sign a commercial use Data License Agreement”. It directs such
requests to partners@bitstamp.net. Whether this private project is commercial
was not determined. Neither its [terms page](https://www.bitstamp.net/terms-of-use/)
nor [legal landing page](https://www.bitstamp.net/legal/) yielded readable
substantive text through the available retrieval surface. This is a retrieval
limitation, not permission. No workaround or acceptance flow was attempted.

## Advertised technical surface, never probed

### Kraken

- [Depth documentation](https://docs.kraken.com/api-reference/market-data/get-order-book):
  GET `https://api.kraken.com/0/public/Depth`, required `pair`, optional `count`
  1–500 (default 100). L2 aggregates quantities at price levels. Examples use
  `XXBTZUSD` and bid/ask arrays of decimal price, quantity and level timestamp.
  No global snapshot time or monotonic snapshot sequence was established.
- [Trades documentation](https://docs.kraken.com/api-reference/market-data/get-recent-trades):
  GET `https://api.kraken.com/0/public/Trades`, required `pair`, `since`, `count`
  1–1000 (default 1000); response includes pair rows and `last` cursor. Example
  rows contain price, quantity, fractional timestamp, b/s, m/l, miscellaneous
  field and numeric identifier. The retrieved REST text did not explicitly
  define aggressor semantics or guarantee raw versus aggregated granularity.
  Preserve provider side separately; normalized aggressor stays UNKNOWN.
  `assetVersion=1` advertises display names including `BTC/USD`; defaults use
  internal names. Actual pair metadata remains unverified.
- [Advanced API FAQ](https://support.kraken.com/articles/advanced-api-faq),
  updated November 5, 2026: documents historical time-and-sales retrieval using
  Trades and a nanosecond-resolution `since` value. This supports technical
  pagination, not guaranteed completeness, retention rights or AI permission.
- [Rate limits](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-),
  updated October 1, 2026: public requests at one per second or less stay within
  stated limits; Trades/OHLC are scoped by IP and pair, others by IP. Any future
  eligible probe should run below the shared limit and stop on denials.

### Bitstamp

The [API page](https://www.bitstamp.net/api/) advertises:

- GET `https://www.bitstamp.net/api/v2/order_book/btcusd/`; `group=1` defaults
  to price aggregation, 0 ungrouped, 2 ungrouped with order IDs. Example fields:
  `timestamp`, `microtimestamp`, `bids`, `asks` of price/amount pairs.
- GET `https://www.bitstamp.net/api/v2/transactions/btcusd/`; `time` minute,
  hour (default), day. Example: `date`, `tid`, `price`, `amount`, `type`.
  Aggressor meaning and raw/aggregate guarantees were not established.
- Standard rate limits: 400 requests/second and 10,000 per 10 minutes.
  The narrower applicable limit always governs. No polling was configured.
- `/api/v2/markets/` documents instrument/precision fields, but examples are
  not verified live BTC/USD metadata. No depth level cap or snapshot sequence
  guarantee was established; consumers must apply their own bounded cap.

Do not reuse authenticated account history, order submission or recovery
endpoints as substitutes. REST samples do not establish continuous L2 replay,
missing-trade counts, exchange clock quality or provider uptime.

## Next narrow step

Seek a free written clarification or applicable official licence covering the
specific public spot depth/trades endpoints, automated collection, private
durable retention and internal inference, explicitly separating local inference,
third-party model processing and redistribution. No message was sent. Paid
licences are outside scope. Until evidence resolves every required attribute,
retain provider denial and continue only synthetic offline contracts/tests.
Even established rights would require separate user authorization for a bounded
live probe with exact request count, timing, retention and stop conditions.
