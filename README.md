# SupplyChain IQ — Intelligent Supply Chain Analytics & Forecasting

**Purpose:** A production-grade, end-to-end supply chain decision support application featuring data contract validation, SQL/pandas analytics, interactive Plotly visualization, chronological holdout demand forecasting, and inventory what-if policy simulation.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/)
[![Tests](https://img.shields.io/badge/pytest-44%20passed-success)](https://github.com/GouravSharma26/SupplyChain_IQ)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![CI](https://github.com/GouravSharma26/SupplyChain_IQ/actions/workflows/ci.yml/badge.svg)](https://github.com/GouravSharma26/SupplyChain_IQ/actions/workflows/ci.yml)

**Live Hosted Application:** [https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/](https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/)

---

## 🎯 Executive Product Overview
SupplyChain IQ empowers operations and supply chain managers to analyze historical demand, benchmark statistical forecasting models against naïve baselines on chronological holdouts, detect stockout risks before they occur, and simulate supplier disruption scenarios.

### Deliverables & Architecture:
1. **Interactive Streamlit Web Dashboard:** Modular 5-tab executive UI with custom typography, KPI cards, and downloadable CSV reports.
2. **Relational Database & Data Engineering Layer (Phase 2):** SQLAlchemy 2.0 multi-entity models (`suppliers`, `products`, `daily_demand`, `inventory_snapshots`, `purchase_orders`) with check constraints and idempotent raw $\rightarrow$ staging $\rightarrow$ curated pipeline. Zero-config SQLite local database (`data/supplychain_iq.db`) with PostgreSQL connection string compatibility via `DATABASE_URL`.
3. **Supplier Fulfillment Scorecard & Working Capital (Phase 3):** Empirical on-time fulfillment rates, delay distributions, SLA risk tiers, Pareto ABC inventory classification, and actionable executive insights with explicit caveats.
4. **Rolling-Origin Forecasting Benchmark (Phase 4):** Expanding-window multi-fold rolling backtesting across sequential cutoffs. Benchmarks Naïve baseline against Seasonal Naïve (7-day lag) and Holt Exponential Smoothing across all SKUs using MAE, RMSE, and WAPE (Weighted Absolute Percentage Error), strictly preserving `None` on undefined zero-demand holdouts.
5. **Machine Learning for Supplier Delay Risk (Phase 5):**
   - Strictly order-time feature extraction to eliminate target leakage.
   - Chronological 75/25 split: Random Forest Classifier vs Majority Class Baseline (Precision, Recall, F1, PR-AUC, Confusion Matrix) and Gradient Boosting Regressor vs Mean Delay Baseline (MAE, RMSE, $R^2$).
   - Interactive PO Simulator Widget: Real-time probability of late delivery and expected delay days for simulated procurement orders.
6. **Multi-Period Policy Trace Simulation (Phase 6):**
   - Day-by-day historical trace simulation tracking stockouts, fill rates, unmet units, and holding capital across Lean JIT (90%), Balanced Standard (95%), and Resilient Buffer (99%) policies, mapped strictly to correct normal Z-scores (1.28, 1.65, 2.33).
   - Lead-time delay sensitivity analysis sweeping disruption friction (+0d to +10d).
7. **Automated Testing Suite:** 44 unit tests covering database schema, idempotent ETL, validation, analytics, forecasting, rolling backtests, machine learning, and simulation logic.

---

## 💻 Local Setup & Execution

### 1. Prerequisites
- Python 3.11 or 3.12
- Git

### 2. Clone and Setup Environment
```bash
git clone https://github.com/GouravSharma26/SupplyChain_IQ.git
cd SupplyChain_IQ

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies and editable package
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Seed the local relational database
python -m supplychain_iq.db.seed
```

### 3. Run Automated Tests
```bash
pytest -v
```
*Expected result:* 44 passed in ~4s.

### 4. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## 🏗️ Architecture & Project Structure

```text
SupplyChainIQ/
├── app.py                      # Main Streamlit web application & tab orchestrator
├── requirements.txt            # Pinned dependency manifest
├── pyproject.toml              # Build & package configuration
├── .env.example                # Sample environment configuration
├── data/
│   └── sample_supply_chain.csv # Bundled 180-day deterministic sample dataset
├── src/
│   └── supplychain_iq/
│       ├── __init__.py         # Package entrypoint
│       ├── data_loader.py      # Dataset loading, bundling & CSV ingestion
│       ├── validation.py       # Strict data contract and quality reporting
│       ├── analytics.py        # Business KPIs, scorecards & Pareto ABC
│       ├── forecasting.py      # Chronological holdout & rolling-origin backtesting
│       ├── inventory.py        # Safety stock, ROP & what-if simulator
│       ├── simulation.py       # Multi-period inventory policy trace simulation
│       ├── db/                 # Relational models, database engine, ETL & seed
│       └── ml/                 # Supplier delay risk classification & regression
├── tests/
│   ├── test_validation.py      # Contract & invalid data handling tests
│   ├── test_analytics.py       # KPI & valuation snapshot tests
│   ├── test_database.py        # SQLAlchemy schema & ETL idempotency tests
│   ├── test_forecasting.py     # Holdout split, rolling backtests & WAPE tests
│   ├── test_inventory.py       # ROP formula & scenario simulation tests
│   ├── test_ml.py              # ML target leakage & model evaluation tests
│   └── test_simulation.py      # Policy trace & sensitivity analysis tests
├── docs/                       # Project specifications, architecture, and phase audit logs
└── README.md                   # Project overview, installation, and deployment instructions
```

---

## 📚 Local Documentation (`docs/`)

Technical design specifications and audit logs are maintained locally in `docs/` (excluded from version control):
- **Architecture & System Design:** `docs/ARCHITECTURE.md`
- **Data Dictionary & KPI Formulas:** `docs/DATA_AND_METRICS.md`
- **Forecasting & ML Methodology:** `docs/FORECASTING_AND_ML.md`
- **Development Checklist & Gates:** `docs/DEVELOPMENT_CHECKLIST.md`
- **Audit Log & Implementation Record:** `docs/PHASE_LOG.md`
- **Release Report & Verification:** `docs/RELEASE_REPORT.md`
- **Deployment Specifications:** `docs/DEPLOYMENT.md`
- **Testing & Quality Assurance:** `docs/TESTING_AND_QUALITY.md`



---

## ☁️ Public Deployment Guide (Streamlit Community Cloud)

1. Ensure all changes are committed and pushed to `main`:
   ```bash
   git push origin main
   ```
2. Navigate to [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account and select repository `GouravSharma26/SupplyChain_IQ`.
4. Set Main file path: `app.py`.
5. Click **Deploy**. No external database or API secrets are required for the quick release.

---

## 📜 Ethical Disclosures & Assumptions
- **Decision Support Notice:** All recommendations, reorder calculations, and scenario projections are decision-support estimates. They do not trigger automated procurement or financial transactions.
- **Sales vs Unconstrained Demand:** Historical demand is measured from observed sales, which may reflect prior stockout constraints.
- **Data Provenance:** The bundled dataset is synthetically generated using a fixed random seed (`seed=42`) for reproducibility and safe public demonstration.
