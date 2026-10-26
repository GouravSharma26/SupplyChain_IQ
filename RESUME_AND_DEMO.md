# Demo Script and Resume Guidance

## 3-minute demo
1. **Problem (20 sec):** Explain that supply-chain teams need to balance demand, available inventory, and replenishment lead times.
2. **Data quality (30 sec):** Load sample data or upload a CSV; show validation counts and warnings.
3. **Business analytics (40 sec):** Filter products/dates and explain units sold, demand trend, inventory value, and stock-risk flags.
4. **Forecasting (40 sec):** Compare baseline and statistical forecast, point out the held-out test window, and explain MAE/RMSE.
5. **Decision support (35 sec):** Change demand multiplier or lead time and show how the reorder recommendation changes.
6. **Engineering and limitations (15 sec):** Mention tests, reproducible setup, data provenance, and that recommendations are estimates rather than purchase orders.

## Resume wording rules
Use only after the features are implemented and verified. Replace bracketed metrics with actual results from logs/tests; omit any metric not measured.

**Potential project entry after verification**
**SupplyChain IQ | Python, Pandas, SQL/PostgreSQL (if implemented), Streamlit, Plotly, Time-Series Forecasting**
- Built an interactive supply-chain analytics dashboard to preprocess order/inventory data, report data-quality issues, and visualize demand and inventory KPIs.
- Compared a naïve demand baseline with [verified model] using chronological holdout evaluation and [verified metrics].
- Implemented transparent reorder-point and inventory scenario calculations to support stockout-risk analysis.

Do not claim SQL/PostgreSQL, XGBoost, Power BI, deployment, or specific model performance unless that capability is present and verified in the project.
