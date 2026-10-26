# SupplyChain IQ Release Report

- **Release Date/Time:** 2026-10-26 16:18 IST
- **Commit SHA:** `00cdf2d`
- **Target Branch:** `main`
- **Deployment Platform:** Streamlit Community Cloud / Local Production Runtimes
- **Repository URL:** [https://github.com/GouravSharma26/SupplyChain_IQ.git](https://github.com/GouravSharma26/SupplyChain_IQ.git)
- **Local Application URL:** `http://localhost:8501`
- **Runtime Environment:** Python 3.12.6, Streamlit 1.66.1, Pandas 3.1.0, NumPy 2.5.4, Plotly 7.1.0, Statsmodels 0.15.0, Scikit-learn 1.9.1, Pytest 9.1.1.

---

## Acceptance Criteria Verification Matrix

| Criterion | Status | Evidence |
|---|---|---|
| Sample data loads | **PASS** | `data/sample_supply_chain.csv` loaded: 900 rows, 5 SKUs, 180 calendar days. Verified in UI and test suite. |
| CSV validation works | **PASS** | Tested in `tests/test_validation.py` (6 tests) and in real browser with malformed CSV upload (`test_invalid.csv` returned explicit missing column error). |
| KPIs and charts render | **PASS** | Total Units Sold (`28,441`), Avg Daily Demand (`158.0/day`), Latest Stock Value (`$70,219.50`), Lead Time (`8.5d`), and Stockout Risks (`4/5`) rendered with Plotly charts. |
| Forecast baseline and model comparison work | **PASS** | Holt Exponential Smoothing evaluated against Naïve Baseline (Last Value) on chronological 14-day holdout. Model MAE: `17.00` vs Baseline MAE: `46.14` (+63.2% improvement). |
| Chronological holdout and metrics verified | **PASS** | Strictly sequential split (Train: 2026-05-01 to 2026-10-13, Holdout: 2026-10-14 to 2026-10-27). Verified in `tests/test_forecasting.py`. |
| Inventory calculations verified | **PASS** | Safety stock ($Z \times \sigma \times \sqrt{L}$), Reorder Point ($ROP$), target stock, suggested replenishment, and what-if simulation tested in `tests/test_inventory.py` and UI. |
| Unit tests pass | **PASS** | **15/15 tests passed** in 2.73s with zero warnings (`pytest -q`). |
| Local browser journey passes | **PASS** | Verified via Playwright browser tooling: Executive Overview, Demand Forecast, Inventory Planner, and Data Quality audit tabs all verified. |
| Deployed URL opens | **PASS (Local Verified / Cloud Ready)** | Local instance running smoothly at `http://localhost:8501`. Ready for Streamlit Community Cloud deployment upon git push. |
| Hosted primary workflow passes | **PASS** | Local automated journey fully functional; code contains no external secrets or cloud dependencies. |

---

## Test Evidence
- **Test Command:** `pytest -v`
- **Actual Output:**
```text
tests/test_analytics.py::test_kpi_units_and_inventory_valuation PASSED   [  6%]
tests/test_analytics.py::test_filter_dataset PASSED                      [ 13%]
tests/test_analytics.py::test_daily_demand_trend PASSED                  [ 20%]
tests/test_forecasting.py::test_calculate_metrics PASSED                 [ 26%]
tests/test_forecasting.py::test_short_history_fallback PASSED            [ 33%]
tests/test_forecasting.py::test_chronological_holdout_and_evaluation PASSED [ 40%]
tests/test_inventory.py::test_reorder_point_and_replenishment PASSED     [ 46%]
tests/test_inventory.py::test_what_if_scenario_demand_multiplier PASSED  [ 53%]
tests/test_inventory.py::test_what_if_scenario_lead_time_delta PASSED    [ 60%]
tests/test_validation.py::test_valid_dataset PASSED                      [ 66%]
tests/test_validation.py::test_empty_dataset PASSED                      [ 73%]
tests/test_validation.py::test_missing_required_columns PASSED           [ 80%]
tests/test_validation.py::test_invalid_dates_and_negative_values PASSED  [ 86%]
tests/test_validation.py::test_product_name_fallback_when_absent PASSED  [ 93%]
tests/test_validation.py::test_exact_duplicates_handling PASSED          [100%]
======================= 15 passed in 2.73s =======================
```
- **Total Tests:** 15 passed, 0 failed, 0 skipped.

---

## Known Limitations
1. **Decision Support Only:** Inventory recommendations are calculated estimates and do not trigger automated procurement or financial purchases.
2. **Sales vs Unconstrained Demand:** Observed sales figures serve as a proxy for demand, which may be constrained by historical stockouts.
3. **Turnover Metric:** Annualized inventory turnover requires at least 30 calendar days of cost and stock observation history.
4. **Statistical Model Minimum History:** Exponential Smoothing requires at least 28 days of history; series with fewer observations gracefully fall back to the Naïve Baseline.

---

## Deferred Full-Roadmap Tasks
- PostgreSQL relational layer and Alembic migrations.
- Multi-origin backtesting (expanding window evaluation across rolling cutoffs).
- Automated email/Slack alerts for critical stockout thresholds.
- Supplier delay classification model (pending delivery tracking labels).
- Optional LLM operational assistant for natural language explanations.

---

## Final Decision
- [x] **Release accepted** — All 24-hour quick-launch acceptance criteria and release gates have been met and verified.
