# ADR-004: Multi-Currency Accounting and FX Quotation Conventions

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Fund Accounting SME, Principal Data Architect, Investment Operations SME
* **Consulted:** Senior Python Engineer, Database Architect
* **Informed:** Core Engineering Team

## Context and Problem Statement

Portfolios frequently hold assets denominated in foreign currencies (e.g., a USD base portfolio holding EUR-denominated equities and GBP cash). Portfolio valuation, risk assessment, and performance reporting require converting all local cash flows and asset values into the portfolio's base currency, while maintaining full traceability of original local amounts and the exact FX rates applied.

## Decision Drivers

* Elimination of currency conversion ambiguities and inverted rate errors.
* Complete multi-currency audit trail for regulatory and accounting inspection.
* Support for ISO 4217 currency standards and direct quotation conventions.

## Considered Options

1. **Option 1: Explicit dual-currency storage on every transaction (`local_amount`, `fx_rate`, `base_amount`) with direct quotation convention**
2. **Option 2: Storing only local amounts and computing base currency dynamically on read**
3. **Option 3: Storing only base currency amounts**

## Decision Outcome

Chosen option: **Option 1: Explicit dual-currency storage on every transaction**.

### Conventions and Standards

* **Base Currency Definition:** Every portfolio has an immutable base reporting currency (`base_currency` in `oltp.portfolios`).
* **Quotation Convention:** Direct quotation: units of local/quote currency per 1 unit of portfolio base currency (or standard interbank quote pair with explicit source mapping).
  $$\text{Amount}_{\text{Base}} = \frac{\text{Amount}_{\text{Local}}}{\text{FX Rate}}$$
  *(Where FX Rate is quoted as Local Currency per 1 Base Currency).*
* **Stored Attributes on Ledger Rows:**
  - `currency_local` (ISO 4217, 3 characters)
  - `gross_amount_local` (`NUMERIC(20, 4)`)
  - `net_amount_local` (`NUMERIC(20, 4)`)
  - `fx_rate_to_base` (`NUMERIC(20, 10)`)
  - `fx_rate_date` (`DATE`)
  - `currency_base` (ISO 4217, 3 characters)
  - `net_amount_base` (`NUMERIC(20, 4)`)

## Oracle / Enterprise Bridge Note

In Oracle core banking schemas, multi-currency tables frequently store `FCY_AMOUNT` (Foreign Currency Amount), `EXCH_RATE`, and `LCY_AMOUNT` (Local/Base Currency Amount). We follow this exact enterprise pattern to ensure reproducible historical valuation without requiring time-consuming historical FX lookups for past settled events.
