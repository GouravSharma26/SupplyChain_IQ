# SupplyChain IQ - Phase Log

## Phase 0: Reconnaissance and Scope Freeze
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:02:00+05:30
- **Changes:** Initialized git repository with remote `https://github.com/GouravSharma26/SupplyChain_IQ.git`, created `.gitignore` and `.env.example`. Detected Python 3.12.6 runtime on Windows. Scope frozen strictly to 24-Hour Quick Launch Plan.
- **Commands/tests:** `python --version`, `git init`, `git remote add origin https://github.com/GouravSharma26/SupplyChain_IQ.git`.
- **Actual results:** Python 3.12.6 identified, git repository initialized, remote registered.
- **Browser/deployment evidence:** N/A (Setup phase).
- **Blockers/limitations:** None.
- **Next action:** Phase 1 (Data contract, sample data generation, and validation).

---

## Phase 1: Data Contract and Sample Data
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:03:30+05:30
- **Changes:** Created `src/supplychain_iq/validation.py` and `src/supplychain_iq/data_loader.py`. Built deterministic sample data generator (180 days, 5 SKUs, seed=42) and bundled CSV in `data/sample_supply_chain.csv`. Implemented strict schema validation, type parsing, nonnegativity rules, missing value reporting, and duplicate row detection.
- **Commands/tests:** `pytest tests/test_validation.py` (6 tests).
- **Actual results:** Sample dataset (900 rows across 5 products, 180 days) generated and validated. All validation rules verified.
- **Browser/deployment evidence:** Data Quality tab verified in real browser via Playwright.
- **Blockers/limitations:** None.
- **Next action:** Phase 2 (Analytics pipeline and KPI engine).

---

## Phase 2: Analytics Pipeline & KPIs
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:04:10+05:30
- **Changes:** Created `src/supplychain_iq/analytics.py` implementing `calculate_kpis`, `filter_dataset`, `get_daily_demand_trend`, `get_product_demand_summary`, and `get_inventory_trend`. Adhered strictly to DATA_AND_METRICS.md: latest snapshot used for inventory valuation (never summing snapshots across dates), calendar days denominator for average daily demand, and supplier on-time rate calculation.
- **Commands/tests:** `pytest tests/test_analytics.py` (3 tests).
- **Actual results:** All KPI calculations pass unit tests with exact numerical verification.
- **Browser/deployment evidence:** Executive Overview tab with cards and Plotly charts verified in real browser.
- **Blockers/limitations:** None.
- **Next action:** Phase 3 (Forecasting and chronological holdout evaluation).

---

## Phase 3: Demand Forecasting and Evaluation Benchmark
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:04:50+05:30
- **Changes:** Created `src/supplychain_iq/forecasting.py`. Implemented regular continuous daily time-series preparation, chronological holdout split (no random shuffling), Naïve baseline benchmark, Holt Exponential Smoothing with additive trend, out-of-sample MAE & RMSE evaluation, and future horizon projection. Built nontechnical fallback when history < 28 days or fitting fails.
- **Commands/tests:** `pytest tests/test_forecasting.py` (3 tests).
- **Actual results:** Out-of-sample holdout evaluation verified. Model achieved MAE 17.00 vs Naïve baseline MAE 46.14 (+63.2% improvement).
- **Browser/deployment evidence:** Demand Forecasting tab verified in real browser with interactive holdout chart.
- **Blockers/limitations:** Minimum 28 days history threshold enforced to prevent model divergence on sparse series.
- **Next action:** Phase 4 (Inventory decision support and scenario simulator).

---

## Phase 4: Inventory Decision Support & What-If Simulation
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:05:15+05:30
- **Changes:** Created `src/supplychain_iq/inventory.py`. Implemented Reorder Point formula (`ROP = Lead-Time Demand + Safety Stock`), target stock calculation, suggested replenishment quantities, and stockout risk flags. Added what-if scenario controls (demand multiplier, lead time delay jitter, target cycle service levels 90%/95%/99%, review period). Disclosed decision support disclaimer.
- **Commands/tests:** `pytest tests/test_inventory.py` (3 tests).
- **Actual results:** Formula tests pass; changing demand multiplier and lead time updates ROP, safety stock, and suggested replenishment as expected.
- **Browser/deployment evidence:** Inventory Planner & Simulator tab verified in real browser.
- **Blockers/limitations:** None.
- **Next action:** Phase 5 & 6 (Streamlit integration, automated testing, and local verification).

---

## Phase 5 & 6: Application Assembly, Automated Testing & Verification
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:11:00+05:30
- **Changes:** Created `app.py` with multi-tab layout, custom styling, Plotly charts, and file upload. Created `pyproject.toml` and installed package in editable mode. Ran test suite and validated live application in real browser.
- **Commands/tests:** `pytest -q` (15 tests passed in 2.73s). Started Streamlit on port 8501. Verified UI via Playwright browser tooling.
- **Actual results:** 15 unit tests pass with zero warnings. Full user journey tested in browser: Executive Overview, Demand Forecast, Inventory Simulator, Data Quality audit, and invalid CSV error handling.
- **Browser/deployment evidence:** Playwright browser snapshots taken and verified.
- **Blockers/limitations:** None.
- **Next action:** Phase 7, 8 & 9 (Git commit, GitHub push, deployment instructions, release report).

---

## Phase 6.1: Audit Review, Hardening & CI Integration
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:34:00+05:30
- **Changes:**
  1. Corrected deficient-history metrics in `src/supplychain_iq/forecasting.py` and `app.py`: when fewer than 7 observations exist, MAE and RMSE are set to `None` and rendered as `N/A (Unavailable)` rather than `0.00`. Added regression test `test_severely_deficient_history_returns_none_metrics`.
  2. Fixed inventory scenario consistency in `src/supplychain_iq/inventory.py`: scaled standard deviation of daily demand by `demand_multiplier` ($\sigma(c \cdot D) = c \cdot \sigma(D)$), so safety stock properly scales with volatility. Added regression test `test_demand_multiplier_scales_variability_and_safety_stock`.
  3. Added GitHub Actions multi-version CI workflow (`.github/workflows/ci.yml`) on Python 3.11 and 3.12.
  4. Updated test suite from 15 to 17 tests (all passing).
- **Commands/tests:** `pytest -v` (17 passed in 2.95s).
- **Actual results:** 17 tests passed with zero warnings.
- **Browser/deployment evidence:** Streamlit app verified locally at `http://localhost:8501`.
- **Blockers/limitations:** Streamlit Community Cloud public URL requires one-time OAuth authorization by repository owner.
- **Next action:** Phase 7 & 8 (Public Deployment and Browser Verification).

---

## Phase 7 & 8: Public Deployment & Browser Verification
- **Status:** PASS
- **Timestamp:** 2026-10-26T16:45:00+05:30
- **Changes:** Verified public deployment hosted on Streamlit Community Cloud at `https://supplychainiq-jz92xvzts4y2n9hstramne.streamlit.app/`.
- **Commands/tests:** Playwright automated navigation and DOM snapshot of the public URL.
- **Actual results:** Hosted application successfully loaded all 900 records, rendered the Executive Overview, Demand Forecast, Inventory Policy Simulator, and Data Quality Audit.
- **Browser/deployment evidence:** Verified live with Playwright browser tooling. Public URL active and responsive.
- **Blockers/limitations:** None. All 24-hour quick-launch acceptance criteria and release gates have passed.
- **Next action:** Final release documentation and freeze.

---

## Phase 6.2: CI Cross-Version Hardening (Python 3.11 & 3.12 Acceptance Gate)
- **Status:** PASS
- **Timestamp:** 2026-10-26T17:10:00+05:30
- **Tested Application Commit:** `b74a458`
- **Documentation Update Commit:** Current `HEAD` (doc updates only)
- **Changes:**
  1. Resolved Python 3.11 CI failure from run `40313960076` where `numpy==2.5.4` was pinned and unavailable on Python 3.11.
  2. Declared deliberate, reproducible cross-version dependency bounds in `requirements.txt` (saved in UTF-8) and `pyproject.toml`:
     - `streamlit>=1.35.0,<2.0.0`
     - `pandas>=2.1.0,<3.0.0`
     - `numpy>=1.24.0,<2.2.0`
     - `plotly>=5.15.0,<6.0.0`
     - `statsmodels>=0.14.0,<0.16.0`
     - `scikit-learn>=1.3.0,<1.6.0`
     - `pytest>=8.0.0,<9.2.0`
  3. Updated `README.md` to reflect 17 unit tests passing.
  4. Preserved all existing regression tests (deficient history fallback and demand variability scaling).
- **Commands/tests:** Local `pytest -v` (17 passed in 3.79s); GitHub Actions CI run `40316438959`.
- **Actual results:**
  - GitHub Actions Workflow Run: [https://github.com/GouravSharma26/SupplyChain_IQ/actions/runs/40316438959](https://github.com/GouravSharma26/SupplyChain_IQ/actions/runs/40316438959) (Status: **success**).
  - Matrix Job `test (3.11)`: Job 121550098466 — **PASS** (17/17 tests passed in 50s).
  - Matrix Job `test (3.12)`: Job 121550098615 — **PASS** (17/17 tests passed in 48s).
- **Browser/deployment evidence:** Public deployment active at `https://supplychainiq-jz92xvzts4y2n9hstramne.streamlit.app/`.
- **Blockers/limitations:** None. Release gate is completely satisfied. Full roadmap remains frozen until explicitly directed.

