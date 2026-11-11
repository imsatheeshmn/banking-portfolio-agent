# ADR-002: Weighted Average Cost Basis for Phase A Portfolio Positions

* **Status:** Accepted
* **Date:** 2026-11-11
* **Deciders:** Fund Accounting SME, Investment Operations SME, Principal Data Architect
* **Consulted:** QA Lead, Senior Python Engineer
* **Informed:** Core Engineering Team

## Context and Problem Statement

When a portfolio disposes of (sells) an asset acquired across multiple transaction lots at varying prices, the platform must determine the cost basis of the disposed shares to calculate:
1. Remaining position book value (cost).
2. Realized Profit and Loss (Realized P&L).
3. Unrealized Profit and Loss on remaining inventory.

Different accounting conventions exist across investment jurisdictions, primarily Weighted Average Cost (WAC) and First-In, First-Out (FIFO) tax lot tracking.

## Decision Drivers

* Simplicity and deterministic mathematical reproducibility for Phase A IBOR positions.
* Elimination of stateful tax-lot exhaustion logic in early milestone iterations.
* Compatibility with standard institutional fund accounting (ABOR) baseline methodologies.

## Considered Options

1. **Option 1: Weighted Average Cost (WAC) dynamically calculated from the ledger**
2. **Option 2: Explicit FIFO Tax Lot Accounting (lot tracking with lot exhaustion tracking tables)**
3. **Option 3: Specific Lot Identification**

## Decision Outcome

Chosen option: **Option 1: Weighted Average Cost (WAC) for Phase A**.

### Algorithm Specification

1. **Acquisition (BUY):**
   $$\text{New Quantity} = \text{Old Quantity} + \text{Bought Quantity}$$
   $$\text{New Total Cost} = \text{Old Total Cost} + \text{Trade Gross Amount}$$
   $$\text{New Unit Cost} = \frac{\text{New Total Cost}}{\text{New Quantity}}$$

2. **Disposal (SELL):**
   $$\text{Cost of Sold Shares} = \text{Sold Quantity} \times \text{Current Unit Cost}$$
   $$\text{Realized P&L} = \text{Trade Net Proceeds} - \text{Cost of Sold Shares}$$
   $$\text{New Total Cost} = \text{Old Total Cost} - \text{Cost of Sold Shares}$$
   $$\text{New Quantity} = \text{Old Quantity} - \text{Sold Quantity}$$
   *(Note: Selling shares reduces total cost proportionally; the unit cost basis remains unchanged after a sale).*

### Extension Path

FIFO tax lot accounting is recorded as an approved extension for post-Milestone 5, which will introduce an explicit `tax_lot` allocation table for tax-optimized jurisdictions.

## Oracle / Enterprise Bridge Note

In legacy SimCorp Dimension or Oracle-based core banking systems (e.g., Flexcube or Olympic), position tables often store cached average cost columns updated by transactional package triggers (`AFTER INSERT ON trade`). In our modern layered architecture, positions and average costs are pure derived projections calculated deterministically from the immutable bitemporal transaction ledger.
