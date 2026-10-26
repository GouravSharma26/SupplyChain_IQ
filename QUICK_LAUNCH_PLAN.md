# Plan A — 24-Hour Quick Launch

**Goal:** Deliver and deploy a functioning SupplyChain IQ MVP within 24 hours. This plan takes precedence over all other plans.

## Scope lock
### Must ship
1. Streamlit application.
2. Bundled sample data plus CSV upload.
3. Data cleaning/validation report.
4. KPI cards and interactive charts.
5. Naïve baseline and one statistical demand forecast where data permits.
6. MAE/RMSE evaluation on chronological holdout.
7. Reorder-point and stockout-risk calculations.
8. One inventory what-if simulation.
9. Tests, README, and public deployment.
10. Browser verification and release report.

### Explicitly deferred
- User accounts and roles
- Live ERP, SAP, Azure, or supplier integrations
- LLM assistant
- Sophisticated deep learning
- Production-grade multi-tenant PostgreSQL
- Advanced supplier delay classification
- Kubernetes/microservices
- Complex UI polish that delays a working release

## Time-boxed execution (24 hours total)
These are elapsed-time budgets, not permission to skip release verification.

### Phase 0 — Reconnaissance and freeze (0:00–0:45)
- Inspect repository and environment.
- Confirm Python version, Git status, hosting account/access, and available dataset.
- Create the documentation files, checklist, and phase log.
- Decide the fastest reliable deployment target.
- Choose a bundled synthetic dataset with clear labeling unless a suitable licensed dataset is already ready.
**Gate:** repository is runnable or a minimal project skeleton exists; scope is frozen.

### Phase 1 — Data contract and sample data (0:45–2:30)
- Implement sample-data generation or include a deterministic CSV.
- Create schema/column validation and normalization.
- Handle invalid dates, nonnumeric values, negative units, duplicates, and missing required fields.
- Report rejected rows and warnings.
**Gate:** valid sample data loads; malformed CSV produces a readable message; tests cover key validation rules.

### Phase 2 — Analytics pipeline (2:30–5:00)
- Implement reusable preprocessing functions in a separate module.
- Calculate KPI functions independent of Streamlit.
- Build charts for demand trend, product demand, inventory, and inventory value.
- Add date/product/category filters where available.
**Gate:** KPI calculations are unit-tested and dashboard filters work.

### Phase 3 — Forecasting and evaluation (5:00–8:30)
- Aggregate demand by date and product.
- Implement naïve baseline forecast.
- Implement Exponential Smoothing with a documented minimum-history threshold and exception fallback.
- Use a chronological holdout (for example, last 20% or last 7 periods, with a minimum test window appropriate to data).
- Calculate MAE and RMSE on the same held-out dates for both methods.
- Show model, test window, horizon, and metric definitions.
**Gate:** forecast output and metrics are reproducible; no random split or training-set score is used.

### Phase 4 — Inventory decision support (8:30–10:30)
- Implement reorder point = average daily demand × lead time + safety stock.
- Implement stockout/reorder flags and suggested replenishment quantity.
- Add scenario controls for demand multiplier and lead-time days.
- Show all assumptions and label outputs as estimates.
**Gate:** formula tests pass and changing scenario controls changes the result as expected.

### Phase 5 — Streamlit integration and usability (10:30–14:00)
- Assemble pages/tabs: Overview, Demand Forecast, Inventory Planner, Data Quality / About.
- Add clear metric definitions, source labels, warnings, and empty states.
- Ensure the sample dataset works without secrets or external API calls.
- Make the app readable on typical laptop and mobile browser widths.
**Gate:** the complete user journey works locally from first launch through recommendation.

### Phase 6 — Test, debug, and polish (14:00–17:00)
- Run formatter/linter if configured, pytest, and a production-like local launch.
- Fix all P0 defects.
- Test missing columns, empty data, one-product data, short history, and zero demand.
- Check logs for exceptions.
**Gate:** tests pass; no known blocker in primary workflow.

### Phase 7 — Deployment (17:00–20:00)
- Push source to GitHub.
- Configure the chosen hosting platform using repository instructions.
- Add only necessary non-secret configuration.
- Wait for build completion and inspect build logs.
- Open the deployed URL and verify that it loads sample data and renders charts.
**Gate:** public deployment is reachable and core workflows function on the hosted instance.

### Phase 8 — Browser acceptance and release evidence (20:00–22:00)
Manually verify:
1. First load with sample data.
2. KPI and chart rendering.
3. Date/product filter behavior.
4. Valid CSV upload.
5. Invalid CSV error handling.
6. Forecast chart and evaluation metrics.
7. Inventory recommendation and scenario changes.
8. About/data provenance/limitations content.
9. Refresh and cold-start behavior on deployment.
10. Mobile-ish narrow viewport if browser tools permit.
Record screenshots or concise evidence, actual test counts, commit SHA, and deployed URL.
**Gate:** all critical browser checks pass or are listed as known issues.

### Phase 9 — Documentation and contingency (22:00–24:00)
- Update README with exact local setup and deployed URL.
- Complete `RELEASE_REPORT.md`.
- Update checklist and phase log with actual status.
- Fix remaining P0 defects only; do not start P1 features.
- If deployment fails, provide reproducible local run instructions and record the exact blocker; do not claim deployment success.
**Final gate:** all quick-launch acceptance criteria pass, or the remaining gaps are explicitly documented.

## Minimum recommended repository structure
```text
supplychain-iq/
├── app.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── data/
│   └── sample_supply_chain.csv
├── src/
│   └── supplychain_iq/
│       ├── __init__.py
│       ├── data_loader.py
│       ├── validation.py
│       ├── analytics.py
│       ├── forecasting.py
│       └── inventory.py
├── tests/
│   ├── test_validation.py
│   ├── test_analytics.py
│   ├── test_forecasting.py
│   └── test_inventory.py
└── docs/
    └── (project documentation)
```

## Dependency guidance
Use a small dependency set and pin compatible versions after testing. Typical packages: `streamlit`, `pandas`, `numpy`, `plotly`, `statsmodels`, `scikit-learn`, `pytest`. Avoid adding PostgreSQL drivers unless the MVP actually uses PostgreSQL.

## Deployment decision
Choose one target based on access and reliability. Streamlit Community Cloud is a natural option for a Streamlit portfolio app if account access and repository requirements are satisfied. Otherwise choose a platform already available to the developer. Do not promise deployment before testing. Never put secrets in Git.

## Emergency prioritization if behind schedule
1. Preserve ingestion + validation + KPI dashboard + baseline forecast + inventory formulas.
2. Keep a statistical model only if it can be evaluated correctly.
3. Simplify styling and chart count.
4. Defer optional database and supplier model.
5. Never remove tests, misrepresent metrics, or claim an unverified deployment.
