# SupplyChain IQ Release Report

- **Release Date/Time:** 2026-10-26 16:47 IST
- **Commit SHA:** `400eddd`
- **Target Branch:** `main`
- **Repository URL:** [https://github.com/GouravSharma26/SupplyChain_IQ.git](https://github.com/GouravSharma26/SupplyChain_IQ.git)
- **Verified Public URL:** [https://supplychainiq-jz92xvzts4y2n9hstramne.streamlit.app/](https://supplychainiq-jz92xvzts4y2n9hstramne.streamlit.app/)
- **Local Application URL:** `http://localhost:8501`
- **Deployment Platform:** Streamlit Community Cloud
- **CI Status:** GitHub Actions workflow active (`.github/workflows/ci.yml`) on Python 3.11 & 3.12.
- **Runtime Environment:** Python 3.12.6, Streamlit 1.66.1, Pandas 3.1.0, NumPy 2.5.4, Plotly 7.1.0, Statsmodels 0.15.0, Scikit-learn 1.9.1, Pytest 9.1.1.

---

## Acceptance Criteria Verification Matrix

| Criterion | Status | Evidence |
|---|---|---|
| Sample data loads | **PASS** | `data/sample_supply_chain.csv` loaded: 900 rows, 5 SKUs, 180 calendar days. Verified locally and on public deployment. |
| CSV validation works | **PASS** | Tested in `tests/test_validation.py` (6 tests) and in real browser with malformed CSV upload (`test_invalid.csv` returned explicit missing column error). |
| KPIs and charts render | **PASS** | Total Units Sold (`28,441`), Avg Daily Demand (`158.0/day`), Latest Stock Value (`$70,219.50`), Lead Time (`9.4d`), and Stockout Risks (`4/5`) rendered with Plotly charts on hosted app. |
| Forecast baseline and model comparison work | **PASS** | Holt Exponential Smoothing evaluated against Naïve Baseline (Last Value) on chronological 14-day holdout. Model MAE: `17.00` vs Baseline MAE: `46.14` (+63.2% improvement). |
| Chronological holdout and metrics verified | **PASS** | Strictly sequential split (Train: 2026-05-01 to 2026-10-13, Holdout: 2026-10-14 to 2026-10-27). Verified in `tests/test_forecasting.py`. |
| Insufficient history error handling | **PASS** | For series with < 7 observations, MAE and RMSE are set to `None` and rendered as `N/A` with explicit warning, preventing misinterpretation as 0.0 / "perfect accuracy". Verified in unit test. |
| Inventory calculations & scenario consistency verified | **PASS** | Safety stock ($Z \times \sigma \times \sqrt{L}$), Reorder Point ($ROP$), target stock, suggested replenishment. What-if demand multiplier scales both daily demand and standard deviation ($\sigma(c \cdot D) = c \cdot \sigma(D)$), scaling safety stock consistently. |
| Unit tests pass | **PASS** | **17/17 tests passed** in 2.95s with zero warnings (`pytest -v`). |
| Local browser journey passes | **PASS** | Verified via Playwright browser tooling: Operational Overview, Demand Forecast, Inventory Simulator, and Data Quality audit tabs all verified. |
| CI Pipeline Active | **PASS** | Automated GitHub Actions CI workflow active (`.github/workflows/ci.yml`) covering Python 3.11 and 3.12. |
| Deployed URL opens | **PASS** | Verified live in browser at `https://supplychainiq-jz92xvzts4y2n9hstramne.streamlit.app/`. |
| Hosted primary workflow passes | **PASS** | Full user journey and all 4 tabs verified live on the hosted Streamlit Community Cloud instance. |

---

## Test Evidence
- **Test Command:** `pytest -v`
- **Actual Output:**
```text
tests/test_analytics.py::test_kpi_units_and_inventory_valuation PASSED   [  5%]
tests/test_analytics.py::test_filter_dataset PASSED                      [ 11%]
tests/test_analytics.py::test_daily_demand_trend PASSED                  [ 17%]
tests/test_forecasting.py::test_calculate_metrics PASSED                 [ 23%]
tests/test_forecasting.py::test_short_history_fallback PASSED            [ 29%]
tests/test_forecasting.py::test_severely_deficient_history_returns_none_metrics PASSED [ 35%]
tests/test_forecasting.py::test_chronological_holdout_and_evaluation PASSED [ 41%]
tests/test_inventory.py::test_reorder_point_and_replenishment PASSED     [ 47%]
tests/test_inventory.py::test_what_if_scenario_demand_multiplier PASSED  [ 52%]
tests/test_inventory.py::test_what_if_scenario_lead_time_delta PASSED    [ 58%]
tests/test_inventory.py::test_demand_multiplier_scales_variability_and_safety_stock PASSED [ 64%]
tests/test_validation.py::test_valid_dataset PASSED                      [ 70%]
tests/test_validation.py::test_empty_dataset PASSED                      [ 76%]
tests/test_validation.py::test_missing_required_columns PASSED           [ 82%]
tests/test_validation.py::test_invalid_dates_and_negative_values PASSED  [ 88%]
tests/test_validation.py::test_product_name_fallback_when_absent PASSED  [ 94%]
tests/test_validation.py::test_exact_duplicates_handling PASSED          [100%]
============================== 17 passed in 2.95s ==============================
```
- **Total Tests:** 17 passed, 0 failed, 0 skipped.

---

## Known Limitations
1. **Decision Support Only:** Inventory recommendations are calculated estimates and do not trigger automated procurement or financial purchases.
2. **Sales vs Unconstrained Demand:** Observed sales figures serve as a proxy for demand, which may be constrained by historical stockouts.
3. **Turnover Metric:** Annualized inventory turnover requires at least 30 calendar days of cost and stock observation history.
4. **Statistical Model Minimum History:** Exponential Smoothing requires at least 28 days of history; series with fewer observations gracefully fall back to the Naïve Baseline. Series with fewer than 7 days report metrics as unavailable (`N/A`).

---

## Deferred Full-Roadmap Tasks
- PostgreSQL relational layer and Alembic migrations.
- Multi-origin backtesting (expanding window evaluation across rolling cutoffs).
- Automated email/Slack alerts for critical stockout thresholds.
- Supplier delay classification model (pending delivery tracking labels).
- Optional LLM operational assistant for natural language explanations.

---

## Final Decision
- [x] **Quick-Launch MVP Verification Complete** — Core engine, data validation, forecasting holdout, inventory simulation, and CI pipeline fully verified.
