"""
SupplyChain IQ - Intelligent Demand Forecasting & Inventory Optimization
MVP Web Application built with Streamlit and Plotly.
"""

from pathlib import Path
import sys
import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure src is on Python path
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from supplychain_iq.data_loader import (
    load_sample_dataset,
    load_csv_data,
    DATA_PROVENANCE_NOTE,
    SAMPLE_DATA_PATH,
)
from supplychain_iq.validation import REQUIRED_COLUMNS, OPTIONAL_COLUMNS
from supplychain_iq.analytics import (
    calculate_kpis,
    filter_dataset,
    get_daily_demand_trend,
    get_product_demand_summary,
    get_inventory_trend,
)
from supplychain_iq.forecasting import generate_demand_forecast, MIN_HISTORY_FOR_MODEL
from supplychain_iq.inventory import (
    calculate_inventory_plans,
    SERVICE_LEVEL_Z,
    ASSUMPTION_DISCLOSURE,
)

# Page configuration
st.set_page_config(
    page_title="SupplyChain IQ | Demand Intelligence & Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for executive polish
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-subtitle {
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .status-badge-healthy {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-badge-urgent {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-badge-monitor {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .callout-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #1e3a8a;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_sidebar():
    """Renders data ingestion options and global filters."""
    st.sidebar.title("📦 SupplyChain IQ")
    st.sidebar.caption("Executive Decision Support & Forecasting")
    st.sidebar.markdown("---")

    st.sidebar.subheader("1. Data Source")
    data_source_mode = st.sidebar.radio(
        "Select Data Ingestion Mode:",
        ["Bundled Sample Data (180 Days)", "Upload Custom CSV"],
        index=0,
        help="Use deterministic pre-bundled supply chain dataset or upload an operational CSV."
    )

    df_clean = pd.DataFrame()
    report = None

    if data_source_mode == "Bundled Sample Data (180 Days)":
        df_clean, report = load_sample_dataset()
        st.sidebar.success(f"✓ Loaded {len(df_clean)} observations (5 SKUs)")
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload Operational CSV",
            type=["csv"],
            help="CSV must contain date, product_id, units_sold, inventory_on_hand, unit_cost, lead_time_days."
        )
        if uploaded_file is not None:
            df_clean, report = load_csv_data(uploaded_file)
            if report.is_valid:
                st.sidebar.success(f"✓ Validated {report.valid_rows} rows")
            else:
                st.sidebar.error(f"Validation failed: {report.error_message}")
        else:
            st.sidebar.info("Upload a CSV file to evaluate custom operations.")
            return None, None, None, None, None

    if df_clean.empty or not report.is_valid:
        return df_clean, report, None, None, None

    st.sidebar.markdown("---")
    st.sidebar.subheader("2. Operational Filters")

    # Date Range Filter
    min_date = df_clean["date"].min().date()
    max_date = df_clean["date"].max().date()
    selected_date_range = st.sidebar.date_input(
        "Analysis Window:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_filter, end_filter = selected_date_range
    else:
        start_filter, end_filter = min_date, max_date

    # Product Filter
    product_options = ["All Products"] + sorted(df_clean["product_id"].unique().tolist())
    selected_product_filter = st.sidebar.selectbox("Filter SKU / Product:", product_options, index=0)

    # Category Filter
    selected_categories = None
    if "category" in df_clean.columns:
        cat_options = sorted(df_clean["category"].dropna().unique().tolist())
        selected_categories = st.sidebar.multiselect("Filter Category:", cat_options, default=cat_options)

    # Apply filters
    filtered_pids = None if selected_product_filter == "All Products" else [selected_product_filter]
    filtered_df = filter_dataset(
        df_clean,
        start_date=pd.Timestamp(start_filter),
        end_date=pd.Timestamp(end_filter),
        product_ids=filtered_pids,
        categories=selected_categories,
    )

    return df_clean, report, filtered_df, selected_product_filter, (start_filter, end_filter)


def tab_overview(df_filtered: pd.DataFrame, df_full: pd.DataFrame):
    """Renders Executive KPI dashboard and demand/inventory trends."""
    st.subheader("Operational Health & Overview")

    if df_filtered.empty:
        st.warning("No records found for the selected filter combination.")
        return

    # Precalculate inventory plans to get stockout count
    inv_summary = calculate_inventory_plans(df_filtered)
    kpis = calculate_kpis(df_filtered, stockout_product_count=inv_summary.at_risk_skus_count)

    # Metric Cards Row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Units Sold", f"{kpis.total_units_sold:,}")
        st.caption(f"Across {kpis.calendar_days} calendar days")
    with c2:
        st.metric("Average Daily Demand", f"{kpis.avg_daily_demand:,.1f} units/day")
        st.caption(f"Total sales / {kpis.calendar_days} days")
    with c3:
        st.metric("Latest Inventory Value", f"${kpis.total_inventory_value:,.2f}")
        st.caption(f"{kpis.total_inventory_units:,} units across active SKUs")
    with c4:
        st.metric("Avg Supplier Lead Time", f"{kpis.avg_lead_time_days:.1f} days")
        st.caption(f"Sample size: {kpis.lead_time_sample_size} records")

    # Metric Cards Row 2
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric(
            "SKUs at Stockout Risk",
            f"{kpis.potential_stockout_count} / {kpis.active_products_count}",
            delta="- Immediate Action" if kpis.potential_stockout_count > 0 else "Optimal",
            delta_color="inverse" if kpis.potential_stockout_count > 0 else "normal",
        )
        st.caption("On-hand stock below calculated reorder point")
    with c6:
        if kpis.supplier_on_time_rate is not None:
            st.metric("Supplier On-Time Rate", f"{kpis.supplier_on_time_rate:.1f}%")
            st.caption(f"Based on {kpis.supplier_sample_size} delivery logs")
        else:
            st.metric("Supplier On-Time Rate", "N/A")
            st.caption("Delivery delay tracking not provided")
    with c7:
        if kpis.inventory_turnover is not None:
            st.metric("Annualized Inventory Turnover", f"{kpis.inventory_turnover:.2f}x")
            st.caption(kpis.turnover_note)
        else:
            st.metric("Inventory Turnover", "N/A")
            st.caption(kpis.turnover_note or "Requires >= 30 days history")
    with c8:
        st.metric("Active Catalog SKUs", str(kpis.active_products_count))
        st.caption("Distinct products in selected window")

    st.markdown("---")

    # Interactive Trend Charts
    col_chart1, col_chart2 = st.columns([3, 2])
    with col_chart1:
        st.markdown("##### 📈 Daily Demand Trend")
        daily_trend = get_daily_demand_trend(df_filtered)
        if not daily_trend.empty:
            daily_trend["7d_MA"] = daily_trend["units_sold"].rolling(window=7, min_periods=1).mean()
            fig = px.line(
                daily_trend,
                x="date",
                y="units_sold",
                title="Daily Volume Sold with 7-Day Moving Average",
                labels={"date": "Observation Date", "units_sold": "Units Sold"},
                color_discrete_sequence=["#3b82f6"],
            )
            fig.add_scatter(
                x=daily_trend["date"],
                y=daily_trend["7d_MA"],
                mode="lines",
                name="7-Day Moving Avg",
                line=dict(color="#f97316", width=2, dash="dot"),
            )
            fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        st.markdown("##### 🏆 Product Volume & Stock Breakdown")
        prod_summary = get_product_demand_summary(df_filtered)
        if not prod_summary.empty:
            fig_bar = px.bar(
                prod_summary,
                x="product_name",
                y="total_units_sold",
                color="latest_inventory_value",
                title="Total Units Sold by Product (Colored by Stock Value)",
                labels={
                    "product_name": "Product",
                    "total_units_sold": "Units Sold",
                    "latest_inventory_value": "Stock Value ($)",
                },
                color_continuous_scale="Blues",
            )
            fig_bar.update_layout(xaxis_tickangle=-25)
            st.plotly_chart(fig_bar, use_container_width=True)

    # Inventory Valuation Trend
    st.markdown("##### 📦 Inventory Units and Valuation Over Time")
    inv_trend = get_inventory_trend(df_filtered)
    if not inv_trend.empty:
        fig_inv = go.Figure()
        fig_inv.add_trace(
            go.Scatter(
                x=inv_trend["date"],
                y=inv_trend["total_inventory_units"],
                name="Total On-Hand Units",
                mode="lines",
                line=dict(color="#059669", width=2),
                yaxis="y1",
            )
        )
        fig_inv.add_trace(
            go.Scatter(
                x=inv_trend["date"],
                y=inv_trend["total_inventory_value"],
                name="Estimated Valuation ($)",
                mode="lines",
                line=dict(color="#6366f1", width=2, dash="dash"),
                yaxis="y2",
            )
        )
        fig_inv.update_layout(
            title="Daily Available Inventory Units vs Valuation",
            hovermode="x unified",
            yaxis=dict(title="On-Hand Units"),
            yaxis2=dict(title="Valuation ($)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_inv, use_container_width=True)


def tab_forecasting(df_full: pd.DataFrame, selected_product: str):
    """Renders Demand Forecasting, Naive Baseline Benchmark, and Holdout Evaluation."""
    st.subheader("Demand Forecasting & Model Evaluation Benchmark")
    st.markdown(
        """
        <div class="callout-box">
        <strong>Methodological Integrity Notice:</strong> Evaluation is conducted using a strictly
        <strong>chronological out-of-sample holdout</strong> (no random shuffling). Both the statistical model
        and the naïve baseline are scored on identical held-out dates using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Product selector for forecasting
    products = sorted(df_full["product_id"].unique().tolist())
    default_idx = 0
    if selected_product in products:
        default_idx = products.index(selected_product)
    
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        f_product = st.selectbox(
            "Select Product for Demand Forecast:",
            ["ALL"] + products,
            index=default_idx + 1 if selected_product != "All Products" else 0,
            format_func=lambda x: "All Products Combined" if x == "ALL" else x,
        )
    with col_ctrl2:
        f_horizon = st.slider("Forecast Horizon (Days):", min_value=7, max_value=30, value=14, step=7)
    with col_ctrl3:
        f_test_days = st.slider("Holdout Test Window (Days):", min_value=7, max_value=28, value=14, step=7)

    # Run forecast engine
    result = generate_demand_forecast(
        df_full,
        product_id=f_product,
        horizon_days=f_horizon,
        test_days=f_test_days,
    )

    if result.warnings:
        for w in result.warnings:
            st.warning(f"⚠️ {w}")

    # Holdout benchmark cards
    st.markdown("##### ⚖️ Out-of-Sample Holdout Model Comparison")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.metric("Evaluated Model", result.model_name.split("(")[0].strip())
        st.caption(f"Train: {result.train_start} to {result.train_end}")
    with b2:
        st.metric("Benchmark Baseline", "Naïve (Last Value)")
        st.caption(f"Holdout: {result.test_start} to {result.test_end} ({result.test_days}d)")
    with b3:
        # Comparison delta
        mae_diff = result.mae_baseline - result.mae_model
        mae_pct = (mae_diff / result.mae_baseline * 100) if result.mae_baseline > 0 else 0
        st.metric(
            "Holdout MAE",
            f"{result.mae_model:.2f}",
            delta=f"{mae_pct:+.1f}% vs Baseline" if not result.fallback_used else "Fallback Baseline",
            delta_color="normal" if mae_diff >= 0 else "inverse",
        )
        st.caption(f"Baseline MAE: {result.mae_baseline:.2f}")
    with b4:
        rmse_diff = result.rmse_baseline - result.rmse_model
        rmse_pct = (rmse_diff / result.rmse_baseline * 100) if result.rmse_baseline > 0 else 0
        st.metric(
            "Holdout RMSE",
            f"{result.rmse_model:.2f}",
            delta=f"{rmse_pct:+.1f}% vs Baseline" if not result.fallback_used else "Fallback Baseline",
            delta_color="normal" if rmse_diff >= 0 else "inverse",
        )
        st.caption(f"Baseline RMSE: {result.rmse_baseline:.2f}")

    # Forecast Plotly Chart
    fig_fc = go.Figure()

    # 1. Historical Actuals
    hist_tail = result.historical_df.tail(60)
    fig_fc.add_trace(
        go.Scatter(
            x=hist_tail["date"],
            y=hist_tail["units_sold"],
            mode="lines+markers",
            name="Historical Actual Demand",
            line=dict(color="#64748b", width=1.5),
            marker=dict(size=4),
        )
    )

    # 2. Holdout Test Actuals
    if not result.test_df.empty:
        fig_fc.add_trace(
            go.Scatter(
                x=result.test_df["date"],
                y=result.test_df["actual"],
                mode="lines+markers",
                name="Holdout Actuals",
                line=dict(color="#0f172a", width=2.5),
                marker=dict(size=6),
            )
        )
        fig_fc.add_trace(
            go.Scatter(
                x=result.test_df["date"],
                y=result.test_df["baseline_pred"],
                mode="lines",
                name=f"Naïve Baseline (MAE={result.mae_baseline})",
                line=dict(color="#f59e0b", width=2, dash="dash"),
            )
        )
        fig_fc.add_trace(
            go.Scatter(
                x=result.test_df["date"],
                y=result.test_df["model_pred"],
                mode="lines",
                name=f"Model Holdout Pred (MAE={result.mae_model})",
                line=dict(color="#3b82f6", width=2.5),
            )
        )

    # 3. Future Forecast
    if not result.forecast_df.empty:
        fig_fc.add_trace(
            go.Scatter(
                x=result.forecast_df["date"],
                y=result.forecast_df["forecast"],
                mode="lines+markers",
                name=f"Future Forecast (+{result.forecast_horizon} Days)",
                line=dict(color="#10b981", width=3, dash="dot"),
                marker=dict(size=6, symbol="diamond"),
            )
        )

    fig_fc.update_layout(
        title=f"Demand History, Chronological Holdout Benchmark, and {result.forecast_horizon}-Day Out-of-Sample Forecast",
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Units Demanded",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # Detailed Holdout Residuals Table
    with st.expander("🔍 View Chronological Holdout Actuals vs Forecast Data"):
        if not result.test_df.empty:
            view_test = result.test_df[["date", "actual", "baseline_pred", "model_pred"]].copy()
            view_test["model_abs_error"] = (view_test["actual"] - view_test["model_pred"]).abs()
            view_test["baseline_abs_error"] = (view_test["actual"] - view_test["baseline_pred"]).abs()
            view_test["date"] = view_test["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(view_test, use_container_width=True)


def tab_inventory_planner(df_filtered: pd.DataFrame):
    """Renders Reorder Point Optimization and What-If Scenario Simulator."""
    st.subheader("Inventory Policy & What-If Scenario Planner")

    st.markdown(
        f"""
        <div class="callout-box">
        <strong>Operational Framework:</strong> Reorder Point (ROP) = Lead-Time Demand + Safety Stock.<br>
        Safety stock is computed as <code>Z × σ(Daily Demand) × √(Lead Time)</code>.<br>
        <em>{ASSUMPTION_DISCLOSURE}</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### 🎛️ What-If Scenario Parameters")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        demand_mult = st.slider(
            "Demand Surge Multiplier:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Simulate market surges (e.g., 1.2x = +20% demand) or recessions."
        )
    with sc2:
        lead_time_jitter = st.slider(
            "Lead Time Delay (Days):",
            min_value=0,
            max_value=14,
            value=0,
            step=1,
            help="Simulate supply disruption or shipping port congestion."
        )
    with sc3:
        service_level = st.selectbox(
            "Target Cycle Service Level:",
            list(SERVICE_LEVEL_Z.keys()),
            index=1,
            help="Probability of not stocking out during lead time."
        )
    with sc4:
        review_days = st.number_input(
            "Review Period (Days):",
            min_value=1,
            max_value=30,
            value=7,
            step=1,
            help="Frequency of placing replenishment purchase batches."
        )

    # Compute inventory plan under chosen scenario
    plan_summary = calculate_inventory_plans(
        df_filtered,
        service_level_label=service_level,
        review_period_days=review_days,
        demand_multiplier=demand_mult,
        lead_time_delta_days=lead_time_jitter,
    )

    # Executive Impact Metrics
    st.markdown("##### 📊 Scenario Impact Summary")
    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.metric(
            "Total SKUs at Stockout Risk",
            f"{plan_summary.at_risk_skus_count} / {plan_summary.total_skus}",
            delta="- At Risk" if plan_summary.at_risk_skus_count > 0 else "Protected",
            delta_color="inverse" if plan_summary.at_risk_skus_count > 0 else "normal",
        )
    with i2:
        st.metric("Total Replenishment Units", f"{plan_summary.total_suggested_units:,}")
        st.caption("Units needed to reach target stock")
    with i3:
        st.metric("Est. Capital Required ($)", f"${plan_summary.total_suggested_cost:,.2f}")
        st.caption("Replenishment units × unit cost")
    with i4:
        st.metric("Active Service Level", service_level.split()[0])
        st.caption(f"Review period: {review_days} days")

    st.markdown("---")
    st.markdown("##### 📋 SKU Replenishment Recommendations")

    df_display = plan_summary.to_dataframe()
    if not df_display.empty:
        # Style dataframe rows based on stockout risk
        st.dataframe(df_display, use_container_width=True)

    # Reorder Point Comparison Chart
    if not df_display.empty:
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                x=[p.product_name for p in plan_summary.plans],
                y=[p.current_stock for p in plan_summary.plans],
                name="Current On-Hand Stock",
                marker_color="#3b82f6",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                x=[p.product_name for p in plan_summary.plans],
                y=[p.reorder_point for p in plan_summary.plans],
                name="Calculated Reorder Point (ROP)",
                marker_color="#ef4444",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                x=[p.product_name for p in plan_summary.plans],
                y=[p.target_stock for p in plan_summary.plans],
                name="Target Stock Level",
                marker_color="#10b981",
            )
        )
        fig_bar.update_layout(
            barmode="group",
            title="Current Stock vs Reorder Point vs Target Stock per SKU",
            hovermode="x unified",
            xaxis_tickangle=-25,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def tab_data_quality(report, df_clean: pd.DataFrame):
    """Renders Data Quality Report, Contract Validation, and Provenance."""
    st.subheader("Data Contract Ingestion & Quality Audit")

    if report is None:
        st.info("No dataset is loaded.")
        return

    # Ingestion Status Card
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Raw Rows Ingested", f"{report.total_rows:,}")
    with c2:
        st.metric("Valid Rows Accepted", f"{report.valid_rows:,}")
    with c3:
        st.metric("Rows Rejected", f"{report.rejected_rows:,}")
    with c4:
        st.metric("Exact Duplicates Filtered", f"{report.duplicate_rows_count:,}")

    st.markdown("---")

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown("##### 🛑 Rejection Reasons & Sanitization")
        if report.rejection_reasons:
            reasons_df = pd.DataFrame([
                {"Reason": k, "Rows Rejected": v} for k, v in report.rejection_reasons.items()
            ])
            st.dataframe(reasons_df, use_container_width=True)
        else:
            st.success("✓ Zero rows were rejected. Strict data contract fully satisfied.")

        st.markdown("##### ⚠️ Ingestion Warnings & Edge Cases")
        if report.warnings:
            for w in report.warnings:
                st.warning(f"• {w}")
        else:
            st.success("✓ No anomalies or sparsity warnings detected.")

    with col_q2:
        st.markdown("##### 📊 Missing Values by Column")
        if report.missing_values_by_column:
            missing_df = pd.DataFrame([
                {"Column": k, "Missing Observations": v} for k, v in report.missing_values_by_column.items()
            ])
            st.dataframe(missing_df, use_container_width=True)
        else:
            st.success("✓ Zero missing values across all contract fields.")

        st.markdown("##### 📅 Dataset Metadata")
        st.write(f"- **Earliest Date:** `{report.min_date}`")
        st.write(f"- **Latest Date:** `{report.max_date}`")
        st.write(f"- **Distinct SKUs:** `{report.distinct_products_count}`")

    st.markdown("---")
    st.markdown("##### 📜 Data Contract & Schema Specifications")
    spec_rows = [
        {"Column": "date", "Required": "Yes", "Type": "Date / Datetime", "Description": "Observation date (YYYY-MM-DD)"},
        {"Column": "product_id", "Required": "Yes", "Type": "String", "Description": "Unique SKU identifier"},
        {"Column": "product_name", "Required": "No (Fallback)", "Type": "String", "Description": "Display name (falls back to product_id)"},
        {"Column": "units_sold", "Required": "Yes", "Type": "Numeric >= 0", "Description": "Daily units demanded/sold"},
        {"Column": "inventory_on_hand", "Required": "Yes", "Type": "Numeric >= 0", "Description": "On-hand inventory available at observation"},
        {"Column": "unit_cost", "Required": "Yes", "Type": "Numeric >= 0", "Description": "Unit acquisition cost ($)"},
        {"Column": "lead_time_days", "Required": "Yes", "Type": "Numeric >= 0", "Description": "Supplier replenishment lead time in days"},
        {"Column": "category", "Required": "Optional", "Type": "String", "Description": "Merchandising category"},
        {"Column": "supplier_id", "Required": "Optional", "Type": "String", "Description": "Supplier key identifier"},
        {"Column": "supplier_name", "Required": "Optional", "Type": "String", "Description": "Supplier commercial name"},
        {"Column": "delivery_delay_days", "Required": "Optional", "Type": "Numeric", "Description": "Shipment arrival delay in days"},
        {"Column": "selling_price", "Required": "Optional", "Type": "Numeric >= 0", "Description": "Customer retail price ($)"},
    ]
    st.dataframe(pd.DataFrame(spec_rows), use_container_width=True)

    st.markdown("---")
    st.markdown("##### 🏷️ Data Provenance & Methodological Limitations")
    st.info(DATA_PROVENANCE_NOTE)
    st.markdown(
        """
        - **Decision Support Only:** This application provides operational decision support and recommendations. It does not perform automated procurement or financial commitments.
        - **Sales vs Unconstrained Demand:** Units sold represent observed sales, which may be constrained by prior stockouts.
        - **Cost Valuation:** Inventory valuation is calculated from provided unit costs and snapshot quantities, not financial ERP ledger balances.
        """
    )


def main():
    """Main application orchestrator."""
    df_clean, report, df_filtered, selected_product, date_range = render_sidebar()

    st.title("SupplyChain IQ — Intelligent Demand & Inventory Analytics")

    if df_clean is None or df_filtered is None:
        st.info("👈 Please load data using the sidebar to begin analysis.")
        return

    # Primary Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Overview",
        "🔮 Demand Forecasting",
        "📦 Inventory Planner & Simulator",
        "🛡️ Data Quality & Audit",
    ])

    with tab1:
        tab_overview(df_filtered, df_clean)

    with tab2:
        tab_forecasting(df_clean, selected_product)

    with tab3:
        tab_inventory_planner(df_filtered)

    with tab4:
        tab_data_quality(report, df_clean)


if __name__ == "__main__":
    main()
