# Data Contract, KPIs, and Formula Definitions

## Data contract
Minimum columns:
| Column | Type | Meaning | Rule |
|---|---|---|---|
| `date` | date/datetime | Observation date | Must parse; invalid rows reported |
| `product_id` | string | Stable product key | Non-empty |
| `product_name` | string | Display name | May fall back to product_id |
| `units_sold` | numeric | Units sold in period | Must be nonnegative |
| `inventory_on_hand` | numeric | Available units at observation | Must be nonnegative |
| `unit_cost` | numeric | Cost per unit | Must be nonnegative |
| `lead_time_days` | numeric | Supplier replenishment lead time | Must be nonnegative |

Optional columns: `supplier_id`, `supplier_name`, `delivery_delay_days`, `category`, `region`, `selling_price`.

For a dataset without all required fields, either map its fields explicitly or use the sample data. Do not silently invent source columns.

## Data quality report
Report:
- Input row count and valid row count.
- Rejected row count with reasons.
- Missing values by column.
- Duplicate row count.
- Date coverage and distinct product count.
- Warnings for sparse history, negative values, constant series, or absent optional fields.

Document whether duplicates are dropped, aggregated, or retained. Do not treat rows as duplicates based on a subset of fields without an explicit rule.

## KPIs and formulas
1. **Total units sold:** sum of `units_sold` over the selected period.
2. **Average daily demand:** total units sold divided by the number of calendar days in the selected date span, unless a different denominator is explicitly displayed.
3. **Inventory value estimate:** sum of `inventory_on_hand × unit_cost` at the selected snapshot grain. If the data has multiple daily snapshots, do not sum all snapshots as if they were separate stock at one time; use the latest snapshot per product or clearly label period aggregation.
4. **Average lead time:** mean of available `lead_time_days`; show sample size and note that this is a simple average.
5. **Potential stockout risk:** count of products with current on-hand inventory below the calculated reorder point. This is a rule-based risk flag, not a prediction of certain stockout.
6. **Inventory turnover:** only calculate when a valid COGS measure and average inventory valuation are available; otherwise mark unavailable.
7. **Supplier on-time rate:** only calculate if shipment due/actual dates or an equivalent valid label exist.

## Inventory formulas
- Average daily demand = units sold over demand window / calendar days in that window.
- Lead-time demand = average daily demand × lead time days.
- Reorder point = lead-time demand + safety stock.
- Suggested replenishment = max(0, target stock − current stock).
- Target stock may be calculated as reorder point + demand over a configurable review period, but the dashboard must disclose this assumption.
- Scenario demand = baseline demand × demand multiplier.
- Scenario lead-time demand = scenario average daily demand × scenario lead time.
- Scenario estimates are not purchase orders and do not trigger actions.

## Assumptions and caveats
- If the dataset is synthetic, label it prominently.
- If inventory is a snapshot rather than a time series, do not infer historical stock movements.
- A missing supplier field means supplier-level analysis is unavailable.
- If sales are used as a proxy for demand, mention that observed sales can be constrained by stockouts.
- Costs and stock values are estimates based on provided input fields, not accounting records.
