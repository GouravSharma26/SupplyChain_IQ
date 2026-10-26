# Architecture and Data Flow

## MVP architecture
```text
Bundled sample CSV / user CSV
          |
          v
  Upload and schema validation
          |
          v
 Cleaning + quality report
          |
          v
 Curated Pandas DataFrame
       /      |       \
      v       v        v
  KPI layer Forecast  Inventory rules
      \       |        /
       \      v       /
        Streamlit dashboard
          |
          v
   Charts, metrics, assumptions,
   warnings, downloadable outputs
```

## Design principles
- Keep calculation logic outside the UI so it can be tested.
- Treat uploaded files as untrusted input.
- Preserve a clear distinction between source fields, cleaned fields, forecasts, and recommendations.
- Make each output traceable to the input data and formula.
- The MVP may process data in memory. PostgreSQL persistence belongs to the full roadmap unless it is already available and can be implemented without threatening the deadline.

## Proposed module responsibilities
- `data_loader.py`: load bundled CSV or uploaded data.
- `validation.py`: normalize columns, validate schema/types, report row-level quality issues.
- `analytics.py`: compute KPIs and aggregated series.
- `forecasting.py`: chronological train/test split, baseline, statistical model, metrics, forecast horizon.
- `inventory.py`: reorder point, safety stock, stock risk, scenario simulation.
- `app.py`: Streamlit UI, navigation, filters, calls to business logic.

## Full architecture
```text
Source files / public dataset
          |
          v
   Raw ingestion + provenance
          |
          v
    Staging + validation -----> Quarantine/reject report
          |
          v
     PostgreSQL curated tables
          |
          +----------+----------------+
          |          |                |
          v          v                v
    SQL analytics  Forecast jobs  Inventory simulation
          |          |                |
          +----------+----------------+
                     |
                     v
              Streamlit dashboard
                     |
                     v
        CSV/report exports and explanations
```

## Failure handling
- Invalid schema: explain missing columns and show expected schema.
- Invalid rows: report row counts and reasons; do not silently drop.
- Empty filtered data: show an empty-state message.
- Short time series: use baseline/fallback and explain limitations.
- Statistical model error: log diagnostic details, show a safe user-facing warning, and preserve baseline results.
- Missing optional fields: hide dependent KPIs or label them unavailable rather than inventing values.
