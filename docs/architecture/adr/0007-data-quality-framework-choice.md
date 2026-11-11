# ADR-007: In-Flight Pipeline Validation vs. Post-Load dbt Quality Framework

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Principal Data Architect, Data Engineer, Recon & Data Quality Analyst
* **Consulted:** QA Lead, Senior Python Engineer
* **Informed:** Core Engineering Team

## Context and Problem Statement

Data quality failures in investment platforms (e.g. malformed identifiers, null prices, mismatched row counts, inverted FX rates) can propagate into downstream valuation and regulatory reports. We need a clear, unbloated data quality architecture that catches invalid records at the gate while validating warehouse dimensional marts post-load.

## Decision Drivers

* Fast-fail rejection of corrupted records before landing in curated tables.
* Automated routing of bad records to a dedicated `quarantine` schema with actionable reason codes.
* Robust, testable warehouse assertion framework without heavy, unneeded infrastructure overhead.

## Considered Options

1. **Option 1: Two-Tier DQ — In-flight Python/Pydantic/Polars validation + Post-load dbt tests in `dw`**
2. **Option 2: Heavyweight external framework (Great Expectations / Soda Core) across all layers**
3. **Option 3: Pure database triggers and check constraints only**

## Decision Outcome

Chosen option: **Option 1: Two-Tier DQ architecture**.

### Tier 1: In-Flight Gatekeeper (Ingestion & Curated Pipelines)
- Implemented using Python domain validators (Pydantic v2 schemas and Polars vectorized assertions).
- Records that fail schema validation, referential checks, or domain bounds are diverted directly to `quarantine` tables with error codes, payload snapshots, and timestamp.
- Valid records proceed into `staging` and `curated`.

### Tier 2: Post-Load Warehouse Governance (dbt Marts in `dw`)
- dbt generic tests (`unique`, `not_null`, `relationships`, `accepted_values`) run on all dimensions and facts.
- Singular custom SQL tests verify investment invariants:
  - Total portfolio asset value + cash matches NAV aggregate.
  - Zero orphan transactions in fact tables.
  - Source-to-target row count and amount reconciliation controls.

## Oracle / Enterprise Bridge Note

In Oracle data warehouses, ETL routines commonly used PL/SQL exception blocks (`EXCEPTION WHEN OTHERS THEN INSERT INTO err_log`) or Oracle SQL Loader bad files (`.bad` files) to trap malformed records. Our two-tier approach mirrors this enterprise pattern cleanly: Python/Polars acts as the intelligent error-trapping staging engine routing to `quarantine`, while dbt provides declarative assertions over the warehouse layer.
