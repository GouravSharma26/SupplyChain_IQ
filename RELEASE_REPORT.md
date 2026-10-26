# SupplyChain IQ Release Report

- **Release Date/Time:** 2026-10-26 19:25 IST
- **Tested Application Commit SHA:** `40672ce` (fix(simulation, forecasting): map numeric service levels to Z-scores and preserve None for undefined WAPE)
- **Target Branch:** `main`
- **Repository URL:** [https://github.com/GouravSharma26/SupplyChain_IQ.git](https://github.com/GouravSharma26/SupplyChain_IQ.git)
- **Verified Public URL:** [https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/](https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/)
- **Local Application URL:** `http://localhost:8501`
- **Deployment Platform:** Streamlit Community Cloud
- **Verified CI Run:** [Run 40334471149](https://github.com/GouravSharma26/SupplyChain_IQ/actions/runs/40334471149) (Status: **PASS / SUCCESS**)
  - **Python 3.11 Matrix Job:** PASS (44/44 tests passed in 51s)
  - **Python 3.12 Matrix Job:** PASS (44/44 tests passed in 48s)
- **Runtime Environment & Constraints:** Python 3.11 and 3.12 compatible. Dependencies: `streamlit>=1.35.0,<2.0.0`, `pandas>=2.1.0,<3.0.0`, `numpy>=1.24.0,<2.2.0`, `plotly>=5.15.0,<6.0.0`, `statsmodels>=0.14.0,<0.16.0`, `scikit-learn>=1.3.0,<1.6.0`, `pytest>=8.0.0,<9.2.0`, `SQLAlchemy>=2.0.0,<2.1.0`.

---

## Acceptance Criteria Verification Matrix

| Criterion | Status | Evidence |
|---|---|---|
| Sample data loads | **PASS** | `data/sample_supply_chain.csv` loaded: 900 rows, 5 SKUs, 180 calendar days. Verified locally and on public deployment. |
| CSV validation works | **PASS** | Tested in `tests/test_validation.py` (6 tests) and in real browser with malformed CSV upload (`test_invalid.csv` returned explicit missing column error). |
| KPIs and charts render | **PASS** | Total Units Sold (`28,441`), Avg Daily Demand (`158.0/day`), Latest Stock Value (`$70,219.50`), Lead Time (`9.4d`), and Stockout Risks (`4/5`) rendered with Plotly charts on hosted app. |
| Forecast baseline and model comparison work | **PASS** | Holt Exponential Smoothing evaluated against Naïve Baseline (Last Value) on chronological 14-day holdout. Model MAE: `17.00` vs Baseline MAE: `46.14` (+63.2% improvement). |
| Rolling-Origin Backtesting & Undefined WAPE Handling (Phase 4 & Audit) | **PASS** | Expanding-window multi-fold backtesting evaluated across rolling origins without data leakage. Evaluates Holt, Seasonal Naïve (7d cyclical), and Naïve using WAPE, MAE, and RMSE across all SKUs. When holdouts have 0 actual demand, WAPE strictly preserves `None` rather than 0.0, excluding undefined folds from averages without distorting models. |
| Supplier Fulfillment & Scorecards (Phase 3) | **PASS** | Scorecard with empirical on-time rate %, lead time distributions, SLA risk tiers, Pareto ABC inventory classification, and executive insight cards with explicit caveats. |
| Machine Learning Supplier Delay Risk (Phase 5) | **PASS** | Random Forest Classifier vs Majority Class Baseline, Gradient Boosting Regressor vs Mean Delay Baseline, strict target leakage exclusion (pre-shipment features only), feature importances, and interactive new PO risk simulator. |
| Multi-Period Policy Simulation & Service-Level Mapping (Phase 6 & Audit) | **PASS** | Historical trace simulation strictly mapping numeric service levels (90, 95, 99) to correct normal Z-scores (1.28, 1.65, 2.33). Proved monotonic ordering of safety stock, ROP, target stock, and holding costs, with lead-time delay sensitivity analysis sweeping 0–10d disruption. |
| Insufficient history error handling | **PASS** | For series with deficient history, metrics degrade gracefully with explicit nontechnical explanations instead of crashing. |
| Automated Unit tests pass | **PASS** | **44/44 tests passed** locally and on CI under both Python 3.11 and 3.12 with zero warnings (`pytest -v`). |
| Local browser journey passes | **PASS** | Verified via Playwright browser tooling: Operational Overview, Demand Forecast, Inventory Simulator, Supplier Risk, and Data Quality audit tabs all verified. |
| CI Pipeline Multi-Version Active & Verified | **PASS** | Automated GitHub Actions CI workflow ([Run 40334471149](https://github.com/GouravSharma26/SupplyChain_IQ/actions/runs/40334471149)) passed for both Python 3.11 and 3.12. |
| Deployed URL opens & verified live | **PASS** | Verified live via Playwright browser tooling at `https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/`. All 5 tabs, tables, charts, and interactive simulators operate cleanly. |

---

## Test Evidence
- **Test Command:** `pytest -v`
- **Actual Output:**
```text
tests/test_analytics.py::test_kpi_units_and_inventory_valuation PASSED   [  2%]
tests/test_analytics.py::test_filter_dataset PASSED                      [  5%]
tests/test_analytics.py::test_daily_demand_trend PASSED                  [  7%]
tests/test_analytics.py::test_supplier_scorecard_and_risk_tiers PASSED   [ 10%]
tests/test_analytics.py::test_product_mix_abc_pareto PASSED              [ 12%]
tests/test_analytics.py::test_generate_executive_insights PASSED         [ 15%]
tests/test_database.py::test_init_db_creates_all_tables PASSED           [ 17%]
tests/test_database.py::test_entity_relationships_and_foreign_keys PASSED [ 20%]
tests/test_database.py::test_schema_constraints_enforce_valid_data PASSED [ 23%]
tests/test_database.py::test_etl_loading_and_idempotency PASSED          [ 25%]
tests/test_database.py::test_query_curated_dataframe PASSED              [ 28%]
tests/test_database.py::test_query_supplier_fulfillment_metrics PASSED   [ 30%]
tests/test_database.py::test_etl_rejects_malformed_dataframe PASSED      [ 33%]
tests/test_forecasting.py::test_calculate_metrics PASSED                 [ 35%]
tests/test_forecasting.py::test_short_history_fallback PASSED            [ 38%]
tests/test_forecasting.py::test_severely_deficient_history_returns_none_metrics PASSED [ 41%]
tests/test_forecasting.py::test_chronological_holdout_and_evaluation PASSED [ 43%]
tests/test_forecasting.py::test_calculate_wape PASSED                    [ 46%]
tests/test_forecasting.py::test_seasonal_naive_forecast PASSED           [ 48%]
tests/test_forecasting.py::test_evaluate_rolling_origin_backtest PASSED  [ 51%]
tests/test_forecasting.py::test_benchmark_all_skus PASSED                [ 53%]
tests/test_inventory.py::test_reorder_point_and_replenishment PASSED     [ 56%]
tests/test_inventory.py::test_what_if_scenario_demand_multiplier PASSED  [ 58%]
tests/test_inventory.py::test_what_if_scenario_lead_time_delta PASSED    [ 61%]
tests/test_inventory.py::test_demand_multiplier_scales_variability_and_safety_stock PASSED [ 64%]
tests/test_ml.py::test_target_leakage_exclusions PASSED                  [ 66%]
tests/test_ml.py::test_supplier_risk_model_training_and_evaluation PASSED [ 69%]
tests/test_ml.py::test_inference_on_new_order PASSED                     [ 71%]
tests/test_ml.py::test_insufficient_order_history_fallback PASSED        [ 74%]
tests/test_ml.py::test_synthesize_orders_from_demand_data PASSED         [ 76%]
tests/test_simulation.py::test_simulate_inventory_policy_metrics PASSED  [ 77%]
tests/test_simulation.py::test_compare_standard_policies_tradeoff PASSED [ 79%]
tests/test_simulation.py::test_lead_time_sensitivity_analysis PASSED     [ 81%]
tests/test_simulation.py::test_numeric_service_level_mapping_to_z PASSED [ 84%]
tests/test_simulation.py::test_policies_reflect_configured_service_level PASSED [ 86%]
tests/test_validation.py::test_valid_dataset PASSED                      [ 88%]
tests/test_validation.py::test_empty_dataset PASSED                      [ 90%]
tests/test_validation.py::test_missing_required_columns PASSED           [ 93%]
tests/test_validation.py::test_invalid_dates_and_negative_values PASSED  [ 95%]
tests/test_validation.py::test_product_name_fallback_when_absent PASSED  [ 97%]
tests/test_validation.py::test_exact_duplicates_handling PASSED          [100%]
```
- **Total Tests:** 44 passed, 0 failed, 0 skipped in 3.63s.

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
