# ADR-005: Trade Date (IBOR) vs. Settlement Date (ABOR/Cash) and Holiday Calendars

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Investment Operations SME, Fund Accounting SME, Principal Data Architect
* **Consulted:** QA Lead, Database Architect
* **Informed:** Core Engineering Team

## Context and Problem Statement

When an equity trade occurs, the economic commitment happens on the **Trade Date ($T$)**, but the physical exchange of cash and delivery of securities occurs on the **Settlement Date ($T+n$)**. Portfolio managers require real-time knowledge of economic exposure on $T$ (the IBOR view), whereas custodians, bank accounts, and accountants recognize cash movements only on $T+n$ (the ABOR view). Conflating these two dates causes severe cash reconciliation breaks.

## Decision Drivers

* Clear separation of IBOR and ABOR operational views.
* Accurate modeling of settlement cycles (e.g. US SEC and European $T+1$ settlement regimes).
* Proper handling of business days, weekends, and exchange holidays.

## Considered Options

1. **Option 1: Explicit bitemporal dates on every ledger transaction (`trade_date` vs `settlement_date`) with a business-day calendar service**
2. **Option 2: Single date field driving both positions and cash**
3. **Option 3: Separate ledger tables for trades vs cash movements**

## Decision Outcome

Chosen option: **Option 1: Explicit dual dates on a unified ledger + business-day calendar**.

### Rules & Invariants

1. **Date Ownership:**
   - **IBOR Holdings / Position View:** Driven strictly by `trade_date`.
   - **ABOR Cash Ledger / Bank View:** Driven strictly by `settlement_date`.
   - Between `trade_date` and `settlement_date`, cash is tracked in an `UNSETTLED_CASH_RECEIVABLE` or `UNSETTLED_CASH_PAYABLE` accrual state.
2. **Settlement Cycle:**
   - Default equity settlement cycle is configured to **$T+1$ business days**.
   - Weekends (Saturday, Sunday) are skipped.
   - Business calendar calculates:
     $$\text{settlement\_date} = \text{business\_days\_add}(\text{trade\_date}, 1)$$

## Oracle / Enterprise Bridge Note

In Oracle packages, bank calendars are typically modeled using table `HOLIDAY_CALENDAR` with functions like `GET_SETTLEMENT_DATE(p_trade_date, p_market, p_offset)`. We adopt this pattern by providing a database-backed business calendar table in `oltp` with a fast in-memory Python calendar utility.
