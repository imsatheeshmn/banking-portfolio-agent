# ADR-001: Numeric Precision, Scale, and Financial Rounding Conventions

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Principal Data Architect, Fund Accounting SME, Database Architect, Senior Python Engineer
* **Consulted:** QA Lead, Investment Operations SME
* **Informed:** Core Engineering Team

## Context and Problem Statement

Financial and investment portfolio calculations involve monetary values, asset quantities, and multi-currency exchange rates. Using binary floating-point arithmetic (e.g. standard IEEE 754 `float` in Python or `FLOAT`/`DOUBLE PRECISION` in SQL) introduces catastrophic precision drift due to binary representation limits (for example, `0.1 + 0.2 != 0.3`). In addition, inconsistent rounding across pipeline stages leads to un-reconciled breaks in valuation and Net Asset Value (NAV).

## Decision Drivers

* Strict compliance with investment accounting standards: zero tolerance for rounding leakage in cash balances and holdings.
* Consistency across the Python domain logic, data engineering pipelines (Polars), and PostgreSQL storage.
* Explicit alignment with BCBS 239 principle of accuracy and auditability.

## Considered Options

1. **Option 1: PostgreSQL `NUMERIC` + Python `decimal.Decimal` with explicit `ROUND_HALF_UP`**
2. **Option 2: Integer representation (storing minor currency units / cents and micro-shares)**
3. **Option 3: IEEE 754 Floating-point (`DOUBLE PRECISION` / Python `float`) with post-hoc rounding**

## Decision Outcome

Chosen option: **Option 1: PostgreSQL `NUMERIC` + Python `decimal.Decimal`**.

### Exact Precision & Scale Specifications

| Domain Field | PostgreSQL Type | Python Representation | Rationale |
|---|---|---|---|
| **Quantity (Shares / Units)** | `NUMERIC(24, 8)` | `Decimal` (quantized to 8 decimal places) | Supports fractional shares, stock split ratios, and large institutional equity quantities up to $10^{16}$. |
| **Market Unit Price** | `NUMERIC(20, 10)` | `Decimal` (quantized to 10 decimal places) | Accommodates high-precision quotation for low-par securities and penny stocks. |
| **Cash & Valuation Amounts** | `NUMERIC(20, 4)` | `Decimal` (quantized to 4 decimal places) | Preserves sub-cent intermediate values (e.g. dividend withholdings, fee accruals) with final 2-decimal reporting quantization. |
| **FX Conversion Rates** | `NUMERIC(20, 10)` | `Decimal` (quantized to 10 decimal places) | Conforms to interbank market standard quotation (e.g. EUR/USD, JPY pairs). |

### Rounding Policy

* **Algorithm:** Standard financial half-up rounding (`decimal.ROUND_HALF_UP` in Python). Values equidistant from both bounds round away from zero (e.g. 2.555 -> 2.56, -2.555 -> -2.56).
* **Application Boundary:** Rounding is applied strictly at transaction boundary outputs and reporting aggregates. Intermediate calculations retain full precision.
* **Prohibition:** Python `float` is strictly forbidden across all domain models, schemas, and API contracts.

## Oracle / Enterprise Bridge Note

In Oracle databases, `NUMBER(p, s)` is used universally. PostgreSQL's `NUMERIC(p, s)` (and its alias `DECIMAL(p, s)`) is exact and identical in semantic behavior to Oracle's `NUMBER(p, s)`. In PL/SQL, `PLS_INTEGER` or `BINARY_FLOAT` is sometimes used for raw algorithmic performance, but core banking packages strictly mandate `NUMBER`. In Python, `decimal.Decimal` functions as the exact equivalent of Oracle's exact `NUMBER`.
