# Platform Architecture Assumptions & Scope Boundaries

---

### 1. Instrument Scope Boundaries

* **Phase A (Active Scope):**
  * **Cash Balances:** Multi-currency cash accounts (USD, EUR, GBP, JPY, CAD, CHF, AUD, SGD).
  * **Listed Equities:** Common and preferred equities traded on recognized exchanges.
  * **Corporate Actions:** Cash dividends and stock splits only.
* **Phase B (Deferred until post-M5):**
  * Government fixed-income bonds (accrued interest, day-count conventions e.g. Actual/Actual, 30/360).
* **Explicitly Out of Scope:**
  * OTC Derivatives (Swaps, Options, Forwards, Futures).
  * Funds of funds / Private Equity capital calls.
  * Real-time FIX market data feeds / Direct broker connectivity.
  * Live tax withholding regimes.

---

### 2. Architectural Boundaries & Principles

* **Synthetic Data Exclusively:**
  * 100% generated via deterministic, reproducible seeding.
  * No confidential, employer, or live customer data is permitted in any environment.
* **Precision & Invariant Standards:**
  * Python `float` is banned for financial quantities, prices, FX, and cash amounts. `decimal.Decimal` is enforced across all domain entities.
  * PostgreSQL `NUMERIC` types are used exclusively in database definitions.
* **Separation of Concerns:**
  * Database enforces referential integrity, column types, and state domain checks.
  * Python services execute business workflows and state transition machines.
* **BCBS 239 Alignment:**
  * End-to-end data lineage from `raw` ingestion hashes through `curated` and `dw` mart facts.
  * Immutable run IDs (`run_id`) and correlation IDs stamped on every batch operation.
