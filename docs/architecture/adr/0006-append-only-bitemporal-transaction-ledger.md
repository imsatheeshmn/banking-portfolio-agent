# ADR-006: Append-Only Bitemporal Transaction Ledger and Reversal Modeling

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Principal Data Architect, Security & Compliance Lead, Database Architect
* **Consulted:** Investment Operations SME, Senior Python Engineer
* **Informed:** Core Engineering Team

## Context and Problem Statement

Financial regulations (including BCBS 239, Sarbanes-Oxley, and MiFID II) require complete auditability of all financial records. In traditional transactional databases, updating a posted trade row in-place destroys historical truth: the system can no longer answer what it believed its risk or NAV was at a previous point in time. If a trade was entered with an erroneous price or cancelled by a broker, updating or deleting the row makes retroactive audit reconstruction impossible.

## Decision Drivers

* Complete immutability of posted financial transactions.
* Support for retroactive corrections without mutating historical snapshots.
* Support for bitemporal queries along both valid time and transaction time.

## Considered Options

1. **Option 1: Append-only ledger with explicit cancelling reversal records and replacement entries**
2. **Option 2: In-place `UPDATE` with an audit trigger table copying before-images**
3. **Option 3: Soft deletes with `is_deleted` flags on the main table**

## Decision Outcome

Chosen option: **Option 1: Append-only ledger with explicit reversing entries**.

### Ledger Modeling Specifications

* **Schema:** `oltp.transaction_ledger`
* **Permissions:** Application role is granted `INSERT` and `SELECT` only; `UPDATE` and `DELETE` privileges are explicitly revoked.
* **Bitemporal Dimensions:**
  - **Valid Time:** `trade_date`, `settlement_date` (real-world business dates).
  - **System Time:** `recorded_at_utc` (`TIMESTAMPTZ`, when the platform committed the row).
* **Correction & Amendment Workflow:**
  1. A posted transaction $T_1$ is never modified.
  2. To cancel $T_1$, an exact inverted entry $T_2$ is inserted with `original_transaction_id = T_1.id`, `status = 'CANCELLED'`, negated quantity, and negated gross/net amounts.
  3. To amend $T_1$, two records are posted in a single atomic transaction:
     - Cancelling entry $T_2$ negating $T_1$.
     - New active replacement entry $T_3$ with corrected attributes and `original_transaction_id = T_1.id`.

## Oracle / Enterprise Bridge Note

In Oracle accounting systems, this is the foundational double-entry bookkeeping and general ledger principle ("storno" accounting). Modifying a posted voucher directly in table `GL_JE_LINES` is illegal under audit standards. All corrections must be posted as counterbalancing reversal vouchers. In PostgreSQL, we enforce this structurally by granting only `INSERT` and `SELECT` to the operational runtime role.
