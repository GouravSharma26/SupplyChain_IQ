# Testing and Quality Gates

## Unit tests
### Validation
- Required columns present.
- Missing required column rejected with readable message.
- Dates parsed and invalid dates reported.
- Numeric conversion and missing values handled.
- Negative units/inventory/cost values handled according to documented policy.
- Duplicate reporting behaves as documented.
- Empty file and malformed CSV handled safely.

### Analytics
- Total units sold correct on a small fixture.
- Average daily demand denominator correct.
- Inventory value uses the correct snapshot grain.
- Missing optional columns do not crash the app.
- Empty filter returns a safe empty state.

### Forecasting
- Baseline output has correct horizon length.
- Chronological split preserves temporal order.
- Metrics match a hand-calculated fixture.
- Short history triggers fallback.
- Zero-demand series does not cause divide-by-zero errors.
- Models are evaluated on the same test window.

### Inventory
- Reorder point formula correct.
- Replenishment is never negative.
- Inventory at/above target yields zero replenishment.
- Demand multiplier and lead-time scenario change outputs predictably.
- Zero lead time and zero demand are handled.

## Integration and browser checks
1. Launch from a clean environment following README.
2. Load sample data.
3. Upload a valid CSV.
4. Upload invalid CSV and inspect error message.
5. Change filters and confirm charts/KPIs update.
6. Generate forecast and inspect evaluation period/metrics.
7. Change inventory assumptions and confirm recommendation changes.
8. Verify data provenance and limitations are visible.
9. Verify deployed app after cold start/refresh.
10. Inspect hosted logs for exceptions.

## Release gates
- No failing P0 tests.
- No known crash in the main workflow.
- No secrets in source control.
- No fabricated metrics or results.
- Forecast evaluation is chronological and out-of-sample.
- Deployed URL verified by opening it in a browser.
- `RELEASE_REPORT.md` records actual evidence and unresolved limitations.
