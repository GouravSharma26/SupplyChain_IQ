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
- [x] Deploy application (verified live at https://supplychainiq-jz92xvzts4y2n9hstramne.streamlit.app/)
- [x] Verify hosted URL in browser (verified with Playwright)
- [x] Test valid/invalid uploads (verified in browser)
- [x] Test filters, forecast, and inventory scenario (verified in browser)
- [x] Update README with exact setup and deployment URL
- [x] Create `RELEASE_REPORT.md` with evidence
- [x] Record known limitations and deferred features

## Full roadmap — do not start before quick-launch gate
- [ ] Dataset provenance/license review
- [ ] PostgreSQL schema and migrations
- [ ] Idempotent ingestion and reconciliation
- [ ] Raw/staging/curated data layers
- [ ] Supplier performance analytics
- [ ] Forecast rolling-origin backtesting
- [ ] Seasonal baseline and additional models where justified
- [ ] Regression/delay prediction only if labels support it
- [ ] Inventory policy simulation and sensitivity analysis
- [ ] CSV/report export
- [ ] Optional grounded AI explanations
- [ ] CI workflow and dependency checks
- [ ] Containerized local environment if useful
- [ ] Architecture and data-flow diagrams
- [ ] Final reproducibility audit
