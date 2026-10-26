# Project Requirements and Acceptance Criteria

## 1. Problem
Retail and distribution teams need a clear way to inspect demand patterns, stock levels, replenishment needs, and forecast quality. SupplyChain IQ provides an educational, transparent decision-support dashboard using public or synthetic data.

## 2. Target users
- Supply-chain analyst
- Inventory planner
- Operations manager
- Data science interviewer reviewing a portfolio project

## 3. Quick-launch functional requirements (P0)
### Data ingestion and quality
- Load a bundled sample dataset on first launch.
- Allow CSV upload.
- Required fields: `date`, `product_id`, `product_name`, `units_sold`, `inventory_on_hand`, `unit_cost`, `lead_time_days`.
- Optional fields: `supplier_id`, `supplier_name`, `delivery_delay_days`, `category`, `region`, `selling_price`.
- Parse dates, normalize column names, validate required columns, and coerce numeric columns safely.
- Report input rows, valid rows, rejected rows, missing values, duplicates, and validation warnings.
- Never expose a traceback as the normal user-facing error.

### Analytics
- Filters for date range, product, and category when fields exist.
- KPI cards: total units sold, average daily demand, inventory value, estimated stockout-risk products, and average lead time.
- Charts: demand over time, demand by product/category, inventory on hand, and inventory value.
- Include explanatory captions and units.

### Forecasting
- Aggregate demand to a consistent daily or weekly frequency.
- Show naïve forecast as a baseline.
- Use Exponential Smoothing where enough observations exist; otherwise use a clearly labeled fallback.
- Use a chronological holdout. No random split.
- Report MAE and RMSE for each model on the same test window.
- Display forecast horizon and date range.
- Show warnings for sparse or irregular history.

### Inventory decision support
- Compute average demand per day and a configurable lead-time demand estimate.
- Reorder point = average daily demand × lead time + safety stock.
- Safety stock can be a transparent configurable value in the quick launch; do not present it as statistically optimized unless it is.
- Suggested reorder quantity = max(0, target stock − current stock), with target stock and assumptions shown.
- Flag potential stockout if on-hand stock is below reorder point.
- Include a what-if control for lead time, safety stock, or demand multiplier.

### Usability and deployment
- Responsive dashboard with clear section labels and loading/error states.
- Provide a sample dataset and one-click reset/reload.
- Include setup instructions and a public deployment URL in release notes after successful deployment.
- Automated tests for data validation, KPI calculations, forecast evaluation, and inventory formulas.

## 4. Full-roadmap requirements (P1/P2)
- PostgreSQL persistence and schema migrations.
- Supplier delivery performance analysis and delay-risk model if labels/data support it.
- Product-level forecast model comparison, seasonality handling, and backtesting.
- Inventory policy simulation across multiple products.
- Explainability, confidence intervals where methodologically supported, and scenario comparison.
- Optional Power BI export or BI-ready reporting tables.
- Optional natural-language explanation layer with explicit caveats and no unsupported claims.
- CI workflow, containerized local setup, data/model version tracking, and stronger monitoring.

## 5. Non-functional requirements
- Reproducible setup.
- Deterministic tests.
- No secrets committed.
- Graceful handling of invalid input.
- Reasonable performance on a laptop and hosted free tier.
- Clear data provenance, metric definitions, model limitations, and responsible interpretation.

## 6. Quick-launch definition of done
All P0 requirements are implemented or deviations are explicitly recorded; tests pass; local app starts; core flows pass browser checks; deployment URL is reachable; README includes setup and limitations; release report contains evidence. A feature is not done merely because a placeholder exists.
