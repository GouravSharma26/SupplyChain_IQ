# Plan B — Full Project Roadmap

**Start only after Plan A passes its release gate.** This roadmap turns the MVP into a more complete portfolio-grade analytics system.

## Phase 1 — Requirements and data governance
- Review quick-launch release report and known limitations.
- Select a public dataset with documented provenance/license, or keep deterministic synthetic data for reproducibility.
- Define entities, grain, date coverage, business questions, and metric definitions.
- Document data quality rules and schema evolution.
**Exit:** signed-off data contract and reproducible source data.

## Phase 2 — Data engineering and PostgreSQL
- Design tables for products, suppliers, daily demand/sales, inventory snapshots, and purchase/delivery records where data supports them.
- Add migrations, constraints, indexes, and idempotent loading.
- Build raw → staging → curated processing layers.
- Track row counts, rejects, duplicates, and load timestamps.
- Add repeatable ETL and database tests.
**Exit:** a fresh environment can be populated deterministically and reconciled.

## Phase 3 — Exploratory and business analytics
- Analyze demand distributions, trends, seasonality, product mix, lead-time patterns, inventory value, and supplier performance.
- Define inventory turnover only when cost-of-goods-sold and average inventory inputs are available.
- Distinguish measured fields from derived estimates.
- Add exportable summary tables and a business-insights report.
**Exit:** each insight has a metric, time range, comparison, and caveat.

## Phase 4 — Forecasting benchmark
- Establish naïve and seasonal-naïve baselines where appropriate.
- Compare Exponential Smoothing and ARIMA/SARIMA only where history and frequency justify them.
- Use rolling-origin or expanding-window backtesting.
- Report MAE, RMSE, and optionally WAPE; document why MAPE is unsuitable when actual demand is zero or near zero.
- Compare performance by product and aggregate; avoid selecting a single winner based only on one series.
- Produce prediction intervals only where the selected method supports them.
**Exit:** benchmark report with reproducible backtests and model limitations.

## Phase 5 — Regression and supplier-delay risk
- Use regression to estimate continuous outcomes only if meaningful labels exist (for example, delivery duration or demand drivers).
- Use classification for late-delivery risk only if a valid `late_delivery` label and sufficient examples exist.
- Define target leakage exclusions before training.
- Split data by time or supplier/product grouping where appropriate.
- Evaluate regression with MAE/RMSE/R²; classification with precision, recall, PR-AUC, confusion matrix, and threshold analysis as appropriate.
- Compare to a simple baseline and report class imbalance.
**Exit:** models are justified by data availability and have held-out evaluation evidence. If data is insufficient, document this rather than fabricating a model.

## Phase 6 — Inventory optimization and scenario simulation
- Support per-product lead time, demand variability, service-level assumptions, safety stock, reorder point, and target stock.
- Keep deterministic rule-based replenishment distinct from optimization.
- Simulate policy choices across historical demand using explicit assumptions.
- Compare stockout proxy, average inventory, estimated holding cost, and replenishment volume where fields support them.
- Include sensitivity analysis and avoid claiming real savings from simulated results.
**Exit:** scenario outputs are reproducible and clearly labeled estimates.

## Phase 7 — Dashboard and explainability
- Add drill-down by product, category, supplier, and time.
- Add model comparison and forecast diagnostics.
- Show data freshness, quality status, source, model version, and forecast horizon.
- Provide a downloadable CSV/summary report.
- Optional natural-language explanations must be grounded only in computed results, disclose uncertainty, and never execute purchasing actions.
**Exit:** business users can reproduce the metrics and understand recommendation assumptions.

## Phase 8 — Production-readiness and deployment
- Add GitHub Actions for tests and static checks.
- Add Docker Compose for local application and PostgreSQL where useful.
- Add configuration validation, structured logs, and graceful failure.
- Add data/model versioning where justified.
- Verify secrets management, dependency hygiene, and hosted resource constraints.
- Document rollback and re-deployment steps.
**Exit:** clean-clone setup, automated CI, documented deployment, and smoke tests.

## Phase 9 — Research and portfolio polish
- Document research questions, hypotheses, methods, and limitations.
- Add architecture/data-flow diagrams and a short demo video or screenshots.
- Report real metrics only from recorded experiments.
- Add reproducibility instructions and sample output.
- Create a one-page case study: business question → data → method → result → caveat → decision.
**Exit:** a reviewer can understand, run, and verify the project.

## Priority order
P0: reliable analytics and deployed MVP.  
P1: PostgreSQL ETL, robust backtesting, product drill-down, supplier metrics.  
P2: advanced regression/classification, scenario simulation, optional LLM explanation, deeper monitoring.

Do not add a technology simply for keyword coverage. Add it only when it serves a measurable project requirement.
