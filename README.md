# SupplyChain IQ — Intelligent Supply Chain Analytics & Forecasting

**Purpose:** A production-grade, end-to-end supply chain decision support application featuring data contract validation, SQL/pandas analytics, interactive Plotly visualization, chronological holdout demand forecasting, and inventory what-if policy simulation.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/)
[![Tests](https://img.shields.io/badge/pytest-24%20passed-success)](https://github.com/GouravSharma26/SupplyChain_IQ)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![CI](https://github.com/GouravSharma26/SupplyChain_IQ/actions/workflows/ci.yml/badge.svg)](https://github.com/GouravSharma26/SupplyChain_IQ/actions/workflows/ci.yml)

**Live Hosted Application:** [https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/](https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/)

---

## 🎯 Executive Product Overview
SupplyChain IQ empowers operations and supply chain managers to analyze historical demand, benchmark statistical forecasting models against naïve baselines on chronological holdouts, detect stockout risks before they occur, and simulate supplier disruption scenarios.

### Deliverables & Architecture:
1. **Interactive Streamlit Web Dashboard:** Modular multi-tab executive UI with custom typography and modern KPI styling.
2. **Relational Database & Data Engineering Layer (Phase 2):** SQLAlchemy 2.0 multi-entity models (`suppliers`, `products`, `daily_demand`, `inventory_snapshots`, `purchase_orders`) with check constraints and idempotent raw $\rightarrow$ staging $\rightarrow$ curated pipeline. Zero-config SQLite local database (`data/supplychain_iq.db`) with PostgreSQL connection string compatibility via `DATABASE_URL`.
3. **Data Ingestion Stream:** Support for Relational Database queries, deterministic benchmark dataset (180 calendar days, 5 SKUs, seed=42), or custom CSV file uploads.
4. **Data Quality & Contract Audit:** Rejection reporting, nonnegativity enforcement, unparseable date handling, and duplicate resolution.
5. **Core KPI Engine:** Units sold, average daily demand, latest snapshot inventory valuation, average lead time, and supplier on-time delivery rates.
6. **Demand Forecasting Benchmark:** Holt Exponential Smoothing with additive trend evaluated against a Naïve baseline strictly on out-of-sample chronological holdouts (MAE & RMSE). Minimum 28-day history threshold with automatic fallback.
7. **Inventory Decision Support:** Safety stock ($Z \times \sigma \times \sqrt{L}$), Reorder Point ($ROP$), target stock, and replenishment capital estimation.
8. **Interactive What-If Simulation:** Real-time adjustments for demand surge (0.5x–2.0x), supplier delay jitter (+0 to +14 days), and cycle service levels (90%, 95%, 99%).
9. **Automated Testing Suite:** 24 unit tests covering schema constraints, entity relationships, idempotent ETL, validation, analytics, forecasting, and inventory logic.

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
*Expected result:* 24 passed in ~3s.

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
│       ├── analytics.py        # Business KPIs and chart aggregation
│       ├── forecasting.py      # Chronological holdout evaluation & Holt model
│       └── inventory.py        # Safety stock, ROP & what-if simulator
├── tests/
│   ├── test_validation.py      # Contract & invalid data handling tests
│   ├── test_analytics.py       # KPI & valuation snapshot tests
│   ├── test_forecasting.py     # Holdout split, MAE/RMSE & fallback tests
│   └── test_inventory.py       # ROP formula & scenario simulation tests
├── PHASE_LOG.md                # Phase-by-phase execution audit log
├── DEVELOPMENT_CHECKLIST.md    # Gate verification checklist
└── RELEASE_REPORT.md           # Formal quick-launch release report
```

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
