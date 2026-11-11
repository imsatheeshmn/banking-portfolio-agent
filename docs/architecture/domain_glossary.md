# Investment Management & Banking Domain Glossary

This glossary defines standard industry terminology, accounting invariants, and data engineering concepts applied throughout the platform.

---

### 1. Architectural Views: IBOR vs. ABOR

* **IBOR (Investment Book of Record):**
  * The operational, real-time view of portfolio holdings, cash, and risk used by portfolio managers and traders.
  * Driven by **Trade Date ($T$)**.
  * Reflects economic commitments immediately upon trade execution, before actual cash settlement occurs.
* **ABOR (Accounting Book of Record):**
  * The official accounting, legal, and financial ledger used for custodian reconciliation, regulatory filings, financial statements, and official tax reporting.
  * Driven by **Settlement Date ($T+n$)**.
  * Recognizes positions and cash movements only when ownership and funds have legally exchanged.

---

### 2. Time Horizons & Bitemporality

* **Valid Time (Business Time):**
  * The real-world date on which an event took effect in the market.
  * Examples: `trade_date`, `settlement_date`, `effective_date`, `ex_date`.
* **System Time (Transaction Time):**
  * The timestamp when our data platform recorded or ingested the row.
  * Represented as `recorded_at_utc`.
* **Bitemporal "As-Of" Querying:**
  * Capability to reconstruct portfolio state along two axes:
    1. *Effective As-Of Date:* What was the portfolio valuation on 2026-06-30?
    2. *Knowledge As-Of Date:* What did we believe the 2026-06-30 valuation was, as known to our system at 17:00 UTC on 2026-07-02 (prior to a backdated late trade adjustment)?

---

### 3. Transaction Lifecycle States

All financial movements progress through immutable state machines:
1. **`NEW`**: Trade created or ingested from external source; raw payload registered.
2. **`VALIDATED`**: Passed schema, currency, precision, and business logic checks (e.g. quantity > 0, price > 0, valid ISIN).
3. **`CONFIRMED`**: Matched with counterparty / broker confirmation.
4. **`SETTLED`**: Legal exchange of cash and securities confirmed by custodian ($T+1$).
5. **`CANCELLED`**: Cancelled prior to settlement, or negated via a counterbalancing reversal entry (`CANCELLATION_REVERSAL`).
6. **`REJECTED`**: Validation failure (routed to `quarantine` schema with specific reason codes).

---

### 4. Valuation, Pricing & NAV

* **NAV (Net Asset Value):**
  $$\text{NAV} = \sum (\text{Quantity}_i \times \text{Market Price}_i \times \text{FX Rate}_i) + \text{Cash Balance} + \text{Accrued Income} - \text{Accrued Liabilities}$$
* **Stale Price Handling:**
  * When current-day market price is missing, carry forward the previous valid closing price with `is_stale = true` and `staleness_days = N`.
  * If `staleness_days > MAX_TOLERANCE` (e.g. 5 business days), generate a high-severity valuation alert.
  * **Never default a missing price to zero.**

---

### 5. Reconciliation & Control Terms

* **Source-to-Target Controls:**
  * Row counts, sum of quantities, and sum of gross amounts matched between `raw` and `curated` schemas.
* **Custodian Position Break:**
  * Mismatch between internal IBOR settled quantity and custodian reported quantity exceeding defined tolerance (e.g., $|\Delta \text{Qty}| > 0.0001$).
* **Break Lifecycle:**
  * `OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED` (or `WRITTEN_OFF`).
  * Resolving financial breaks requires maker-checker dual approval.
