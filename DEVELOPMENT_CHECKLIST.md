# Development Checklist

## Quick launch — mandatory
- [x] Inspect repository/runtime and record constraints
- [x] Freeze MVP scope
- [x] Create deterministic, labeled sample dataset
- [x] Implement CSV loading and schema validation
- [x] Implement data quality report
- [x] Implement analytics/KPI functions
- [x] Implement dashboard charts and filters
- [x] Implement naïve baseline forecast
- [x] Implement statistical forecast with fallback
- [x] Implement chronological holdout evaluation
- [x] Implement MAE/RMSE
- [x] Implement reorder point and replenishment formulas
- [x] Implement scenario simulation controls
- [x] Add unit tests for validation
- [x] Add unit tests for analytics
- [x] Add unit tests for forecasting
- [x] Add unit tests for inventory
- [x] Run tests and record actual output (17 passed)
- [x] Launch locally and check logs
- [x] Push repository to GitHub (pushed to origin/main)
- [x] Deploy application (verified live at https://supplychainiq-bzrenpttfjbwqmxailamdd.streamlit.app/)
- [x] Verify hosted URL in browser (verified with Playwright)
- [x] Test valid/invalid uploads (verified in browser)
- [x] Test filters, forecast, and inventory scenario (verified in browser)
- [x] Update README with exact setup and deployment URL
- [x] Create `RELEASE_REPORT.md` with evidence
- [x] Record known limitations and deferred features

## Full roadmap — Plan B Implementation
- [x] Dataset provenance/license review (deterministic 180-day 5-SKU benchmark + multi-supplier generation)
- [x] PostgreSQL/relational schema and models (SQLAlchemy 2.0 multi-entity models: `suppliers`, `products`, `daily_demand`, `inventory_snapshots`, `purchase_orders`)
- [x] Idempotent ingestion and reconciliation (`python -m supplychain_iq.db.seed`, verified 0 duplicates on repeated runs)
- [x] Raw/staging/curated data layers (validation gate, staging normalization, curated upserts)
- [x] Supplier performance analytics (scorecard, on-time delivery rates, delay duration, risk tier classification)
- [x] Forecast rolling-origin backtesting (expanding-window multi-fold evaluation across rolling cutoffs)
- [x] Seasonal baseline and additional models where justified (Seasonal Naïve 7-day lag vs Holt Exponential Smoothing vs Naïve, evaluated via WAPE, MAE, RMSE)
- [x] Regression/delay prediction only if labels support it (Random Forest classification & Gradient Boosting regression with strict target leakage exclusions)
- [x] Inventory policy simulation and sensitivity analysis (Multi-period policy trace comparison & lead-time delay sensitivity sweep)
- [x] CSV/report export (downloadable CSVs for Supplier Scorecard, ABC Product Mix, and Holdout Residuals)
- [ ] Optional grounded AI explanations
- [x] CI workflow and dependency checks (GitHub Actions matrix for Python 3.11 & 3.12)
- [ ] Containerized local environment if useful
- [ ] Architecture and data-flow diagrams
- [ ] Final reproducibility audit

