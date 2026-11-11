# ADR-003: Long-Only Portfolio Position Policy

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Product Owner, Investment Operations SME, Security & Risk Analyst
* **Consulted:** Principal Data Architect, QA Lead
* **Informed:** Core Engineering Team

## Context and Problem Statement

In institutional asset management, long-only mandates forbid portfolios from holding negative security positions (short selling). If an operations desk or data feed attempts to process a `SELL` trade where the sell quantity exceeds the settled/trade-date position available in the portfolio, allowing negative balances introduces severe reconciliation breaks, pricing errors, and custody borrowing compliance failures.

## Decision Drivers

* Strict fidelity to Phase A long-only investment mandate scope.
* Fail-fast operational risk prevention: corrupt feeds must not pollute curated holdings.
* Clear quarantine and break triage workflow.

## Considered Options

1. **Option 1: Strict rejection and quarantine of any sell exceeding currently held quantity**
2. **Option 2: Allow short positions with an overdraft/borrowing interest accrual mechanism**
3. **Option 3: Silent clipping / truncation of sell quantity to available holdings**

## Decision Outcome

Chosen option: **Option 1: Strict rejection and quarantine**.

### Invariant Rules

* At trade validation time, for any transaction where `transaction_type = 'SELL'`, the engine evaluates:
  $$\text{Cumulative Buys} - \text{Cumulative Sells} \ge \text{Proposed Sell Quantity}$$
* If this condition is violated:
  1. The transaction status is marked `REJECTED`.
  2. The record is routed to the `quarantine` schema with error code `ERR_INSUFFICIENT_HOLDINGS`.
  3. No ledger record is posted to the active portfolio view.
  4. An operational alert is logged in the `audit` schema.

## Oracle / Enterprise Bridge Note

In Oracle databases, this was traditionally enforced via compound table triggers (`BEFORE INSERT ON trade_table FOR EACH ROW`) or stored procedure APIs wrapping trade booking. In our architecture, the Python validation service enforces this business rule prior to posting to the database, while the warehouse fact generation pipeline enforces a non-negative quantity constraint (`CHECK (quantity >= 0)`) in the `dw` schema.
