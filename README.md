# Investment Data Engineering & Portfolio Intelligence Platform

An enterprise-grade, bitemporal investment data engineering platform designed to process, reconcile, and analyze multi-currency equity and cash portfolios using modern data architecture principles.

---

## 1. Architecture Overview

The platform implements a layered data lakehouse and relational warehouse architecture powered by PostgreSQL 16, Python 3.12, Polars, and FastAPI:

```
[ Synthetic Market & Custodian Feeds ]
                  │
                  ▼
         [ raw ] Schema (Immutable Payload & Ingestion Manifests with SHA-256)
                  │
                  ▼
      [ staging ] Schema (Typed, Cleaned In-flight Payloads)
            │                  │
   (Valid)  ▼         (Invalid)▼
 [ curated ] Schema     [ quarantine ] Schema (Reason codes & Audit Trail)
      │      ▲
      │      └────────── [ oltp ] Transaction Ledger (Append-Only Bitemporal IBOR)
      ▼
   [ dw ] Dimensional Warehouse (SCD Type 2 Dimensions, Daily Fact Snapshots, P&L, NAV)
      │
      ▼
[ FastAPI Services & Operational Analytics Dashboard ]
```

---

## 2. Core Investment Domain Capabilities

- **Immutable Bitemporal Ledger:** Separate valid time (`trade_date`, `settlement_date`) from transaction system time (`recorded_at_utc`). Amend and cancel handled strictly via counterbalancing reversal entries.
- **IBOR vs. ABOR Views:** Trade-date driven position and exposure calculations for portfolio management; settlement-date driven cash and custody reconciliations.
- **Reconciliation & Break Management:** Position and cash reconciliation against simulated custodian feeds with configurable break thresholds and resolution workflows.
- **Data Quality & Lineage:** BCBS 239 compliant source-to-target row controls, checksum validations, and automated quarantine routing.
- **Deterministic Scalability:** Synthetic data generation capable of producing test datasets ranging from thousands to millions of rows for reproducible benchmarking.

---

## 3. Technology Stack

- **Backend & Core:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Polars, psycopg 3
- **Database:** PostgreSQL 16 (strict schema separation: `oltp`, `raw`, `staging`, `quarantine`, `curated`, `dw`, `audit`)
- **Testing & Quality:** pytest, Hypothesis, ruff, mypy (strict), pre-commit
- **Infrastructure & CI:** Docker, Docker Compose, GitHub Actions CI

---

## 4. Repository Layout

```text
├── .github/workflows/       # Continuous integration pipelines
├── backend/                 # Python backend services, domain logic, and tests
│   ├── pyproject.toml       # Pinned dependencies & tool configurations
│   ├── ruff.toml            # Linter & code formatting rules
│   ├── mypy.ini             # Strict type checking configuration
│   └── tests/               # Unit, integration, and property tests
├── docs/                    # Architecture, ADRs, runbooks, and domain specs
│   └── architecture/
│       ├── adr/             # Architecture Decision Records
│       ├── domain_glossary.md
│       └── assumptions.md
├── infrastructure/          # Containerization and orchestration
│   └── docker/              # Docker Compose and service definitions
├── .env.example             # Environment configuration template
├── .gitattributes           # Cross-platform LF line ending enforcement
└── LICENSE                  # Apache-2.0 with Educational Project Disclaimer
```

---

## 5. Getting Started

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/imsatheeshmn/banking-portfolio-agent.git
   cd banking-portfolio-agent
   ```

2. **Run Tests:**
   ```bash
   cd backend
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

3. **Start Database (Docker Compose):**
   ```bash
   docker compose -f infrastructure/docker/docker-compose.yml up -d
   ```

---

## 6. Project Roadmap

- [x] **Milestone 0: Foundations** (Repo layout, tooling, CI, ADR template, domain glossary, assumptions)
- [ ] **Milestone 1a: Database** (Schemas, entities, constraints, Alembic migrations, audit model)
- [ ] **Milestone 1b: Domain Logic** (Transaction validation, lifecycle, positions from ledger)
- [ ] **Milestone 1c: API** (FastAPI endpoints, error contracts, API integration tests)
- [ ] **Milestone 1d: UI & Packaging** (Functional operations screens, one-command startup)
- [ ] **Milestone 2: Ingestion Framework** (Raw storage, manifests, quarantine, idempotency)
- [ ] **Milestone 3: Portfolio Processing** (Market prices, FX, holdings, valuation, NAV)
- [ ] **Milestone 4: Reconciliation & Controls** (Custodian recon, break workflow, DQ rules)
- [ ] **Milestone 5: Data Warehouse** (Dimensional model, SCD Type 2, dbt models)
- [ ] **Milestone 6: Orchestration & Lineage** (Airflow DAGs, scheduling, OpenLineage)
- [ ] **Milestone 7: Scale Benchmark** (Synthetic generator, performance evaluation)
- [ ] **Milestone 10: Enterprise Readiness** (Security, RBAC, backup/restore runbooks)

---

## 7. Educational Disclaimer

*This project is built strictly for educational, portfolio demonstration, and research purposes. It uses 100% synthetic data and does not constitute financial, investment, accounting, or legal advice.*
