"""
SupplyChain IQ - Intelligent Demand Forecasting & Inventory Optimization
Executive Decision Support Web Application.
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
    page_title="SupplyChain IQ — Enterprise Demand & Inventory Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enterprise Design System & Modern Iconography CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Executive Hero Header */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px 30px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(90deg, #ffffff 0%, #93c5fd 60%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 6px;
        font-weight: 400;
    }
    .hero-badge {
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38bdf8;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        padding: 6px 14px;
        border-radius: 20px;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Executive KPI Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
    }
    .kpi-accent-blue { border-top: 3px solid #3b82f6; }
    .kpi-accent-indigo { border-top: 3px solid #6366f1; }
    .kpi-accent-emerald { border-top: 3px solid #10b981; }
    .kpi-accent-amber { border-top: 3px solid #f59e0b; }
    .kpi-accent-rose { border-top: 3px solid #f43f5e; }
    .kpi-accent-cyan { border-top: 3px solid #06b6d4; }

    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .kpi-title {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .kpi-symbol {
        font-size: 1rem;
        color: #94a3b8;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .kpi-subtext {
        color: #94a3b8;
        font-size: 0.75rem;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* Polished Pill Badges */
    .pill-healthy {
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .pill-urgent {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        color: #9f1239;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .pill-monitor {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    /* Modern Notice Banners */
    .notice-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 20px;
        color: #1e293b;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    .notice-card strong {
        color: #0f172a;
    }

    /* Tab Label Styling */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 10px 18px !important;
        letter-spacing: -0.01em;
    }

    /* Code styling */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        background: #f1f5f9 !important;
        color: #0f172a !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.82em !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_sidebar():
    """Renders data ingestion options and global filters with modern minimalist design."""
    # Custom Sidebar Brand Badge
    st.sidebar.markdown(
        """
        <div style="padding: 10px 0 16px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="background: linear-gradient(135deg, #2563eb, #38bdf8); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.1rem; box-shadow: 0 2px 8px rgba(37,99,235,0.3);">
                    ◈
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.15rem; color: #0f172a; letter-spacing: -0.02em;">SupplyChain IQ</div>
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">Intelligence Engine</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### ⌖ Data Ingestion Stream")

    data_source_mode = st.sidebar.radio(
        "Ingestion Source:",
        ["Deterministic Benchmark Data (180d)", "Upload Operational CSV"],
        index=0,
        help="Use deterministic pre-bundled supply chain dataset or upload an operational CSV."
    )

    df_clean = pd.DataFrame()
    report = None

    if data_source_mode == "Deterministic Benchmark Data (180d)":
        df_clean, report = load_sample_dataset()
        st.sidebar.success(f"✓ Loaded {len(df_clean)} records across 5 SKUs")
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload Operations CSV",
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
    st.sidebar.markdown("##### ⎈ Operational Scoping")

    # Date Range Filter
    min_date = df_clean["date"].min().date()
    max_date = df_clean["date"].max().date()
    selected_date_range = st.sidebar.date_input(
        "Observation Window:",
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
    selected_product_filter = st.sidebar.selectbox("Catalog Filter (SKU):", product_options, index=0)

    # Category Filter
    selected_categories = None
    if "category" in df_clean.columns:
        cat_options = sorted(df_clean["category"].dropna().unique().tolist())
        selected_categories = st.sidebar.multiselect("Category Segment:", cat_options, default=cat_options)

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
    if df_filtered.empty:
        st.warning("No records found for the selected filter combination.")
        return

    # Precalculate inventory plans to get stockout count
    inv_summary = calculate_inventory_plans(df_filtered)
    kpis = calculate_kpis(df_filtered, stockout_product_count=inv_summary.at_risk_skus_count)

    # Executive Metric Cards Row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-blue">
                <div class="kpi-header">
                    <span class="kpi-title">Units Sold</span>
                    <span class="kpi-symbol">↗</span>
                </div>
                <div class="kpi-value">{kpis.total_units_sold:,}</div>
                <div class="kpi-subtext">Across {kpis.calendar_days} calendar days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-indigo">
                <div class="kpi-header">
                    <span class="kpi-title">Average Daily Velocity</span>
                    <span class="kpi-symbol">⚡</span>
                </div>
                <div class="kpi-value">{kpis.avg_daily_demand:,.1f} <span style="font-size: 0.9rem; font-weight: 500; color: #64748b;">units/d</span></div>
                <div class="kpi-subtext">Total sales / {kpis.calendar_days} calendar days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-emerald">
                <div class="kpi-header">
                    <span class="kpi-title">Latest Stock Valuation</span>
                    <span class="kpi-symbol">◈</span>
                </div>
                <div class="kpi-value">${kpis.total_inventory_value:,.2f}</div>
                <div class="kpi-subtext">{kpis.total_inventory_units:,} units across active SKUs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-cyan">
                <div class="kpi-header">
                    <span class="kpi-title">Avg Supplier Lead Time</span>
                    <span class="kpi-symbol">⏱</span>
                </div>
                <div class="kpi-value">{kpis.avg_lead_time_days:.1f} <span style="font-size: 0.9rem; font-weight: 500; color: #64748b;">days</span></div>
                <div class="kpi-subtext">Sample size: {kpis.lead_time_sample_size} records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Executive Metric Cards Row 2
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        risk_color = "kpi-accent-rose" if kpis.potential_stockout_count > 0 else "kpi-accent-emerald"
        risk_pill = (
            f'<span class="pill-urgent">▲ {kpis.potential_stockout_count} Critical</span>'
            if kpis.potential_stockout_count > 0
            else '<span class="pill-healthy">● Protected</span>'
        )
        st.markdown(
            f"""
            <div class="kpi-card {risk_color}">
                <div class="kpi-header">
                    <span class="kpi-title">Stockout Vulnerability</span>
                    {risk_pill}
                </div>
                <div class="kpi-value">{kpis.potential_stockout_count} <span style="font-size: 1rem; color: #64748b;">/ {kpis.active_products_count} SKUs</span></div>
                <div class="kpi-subtext">On-hand stock below calculated ROP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c6:
        ontime_val = f"{kpis.supplier_on_time_rate:.1f}%" if kpis.supplier_on_time_rate is not None else "N/A"
        ontime_sub = f"Based on {kpis.supplier_sample_size} shipments" if kpis.supplier_on_time_rate is not None else "Shipment logs not provided"
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-amber">
                <div class="kpi-header">
                    <span class="kpi-title">Supplier Fulfillment Rate</span>
                    <span class="kpi-symbol">✓</span>
                </div>
                <div class="kpi-value">{ontime_val}</div>
                <div class="kpi-subtext">{ontime_sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c7:
        turn_val = f"{kpis.inventory_turnover:.2f}x" if kpis.inventory_turnover is not None else "N/A"
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-indigo">
                <div class="kpi-header">
                    <span class="kpi-title">Annualized Turnover</span>
                    <span class="kpi-symbol">↻</span>
                </div>
                <div class="kpi-value">{turn_val}</div>
                <div class="kpi-subtext">{kpis.turnover_note or "Requires >= 30 days"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-blue">
                <div class="kpi-header">
                    <span class="kpi-title">Active SKUs</span>
                    <span class="kpi-symbol">⬡</span>
                </div>
                <div class="kpi-value">{kpis.active_products_count}</div>
                <div class="kpi-subtext">Distinct catalog items in view</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Interactive Trend Charts
    col_chart1, col_chart2 = st.columns([3, 2])
    with col_chart1:
        st.markdown("##### ↗ Demand Trajectory & Velocity")
        daily_trend = get_daily_demand_trend(df_filtered)
        if not daily_trend.empty:
            daily_trend["7d_MA"] = daily_trend["units_sold"].rolling(window=7, min_periods=1).mean()
            fig = px.line(
                daily_trend,
                x="date",
                y="units_sold",
                title="Daily Demand Volume with 7-Day Moving Average",
                labels={"date": "Observation Date", "units_sold": "Units Sold"},
                color_discrete_sequence=["#2563eb"],
            )
            fig.add_scatter(
                x=daily_trend["date"],
                y=daily_trend["7d_MA"],
                mode="lines",
                name="7-Day Moving Avg",
                line=dict(color="#f97316", width=2.5, dash="dot"),
            )
            fig.update_layout(
                hovermode="x unified",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font_family="Plus Jakarta Sans",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        st.markdown("##### ⬡ SKU Volume & Working Capital Share")
        prod_summary = get_product_demand_summary(df_filtered)
        if not prod_summary.empty:
            fig_bar = px.bar(
                prod_summary,
                x="product_name",
                y="total_units_sold",
                color="latest_inventory_value",
                title="Units Sold by SKU (Heatmapped by Stock Valuation)",
                labels={
                    "product_name": "Product SKU",
                    "total_units_sold": "Units Sold",
                    "latest_inventory_value": "Inventory Capital ($)",
                },
                color_continuous_scale="Purples",
            )
            fig_bar.update_layout(
                xaxis_tickangle=-25,
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font_family="Plus Jakarta Sans",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # Inventory Valuation Trend
    st.markdown("##### ◈ Inventory Balance & Working Capital Velocity")
    inv_trend = get_inventory_trend(df_filtered)
    if not inv_trend.empty:
        fig_inv = go.Figure()
        fig_inv.add_trace(
            go.Scatter(
                x=inv_trend["date"],
                y=inv_trend["total_inventory_units"],
                name="Total On-Hand Inventory (Units)",
                mode="lines",
                line=dict(color="#059669", width=2.5),
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
            title="Historical Available Stock Units vs Inventory Capital",
            hovermode="x unified",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font_family="Plus Jakarta Sans",
            yaxis=dict(title="On-Hand Units", showgrid=True, gridcolor="#f1f5f9"),
            yaxis2=dict(title="Valuation ($)", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_inv, use_container_width=True)


def tab_forecasting(df_full: pd.DataFrame, selected_product: str):
    """Renders Demand Forecasting, Naive Baseline Benchmark, and Holdout Evaluation."""
    st.markdown(
        """
        <div class="notice-card">
            <strong>Chronological Integrity Notice:</strong> Evaluation is conducted using a strictly
            <strong>chronological out-of-sample holdout</strong> (zero random shuffling / zero data leakage). Both the statistical model
            and the naïve baseline are evaluated on identical held-out calendar dates using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).
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
            "Target Forecasting SKU:",
            ["ALL"] + products,
            index=default_idx + 1 if selected_product != "All Products" else 0,
            format_func=lambda x: "All Products Aggregated" if x == "ALL" else x,
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
            st.warning(f"⚠ {w}")

    # Holdout benchmark cards
    st.markdown("##### ⎈ Holdout Benchmark & Accuracy Delta")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-blue">
                <div class="kpi-header">
                    <span class="kpi-title">Candidate Model</span>
                    <span class="kpi-symbol">⚡</span>
                </div>
                <div class="kpi-value" style="font-size: 1.25rem;">{result.model_name.split("(")[0].strip()}</div>
                <div class="kpi-subtext">Train: {result.train_start} to {result.train_end}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-amber">
                <div class="kpi-header">
                    <span class="kpi-title">Naïve Baseline</span>
                    <span class="kpi-symbol">◈</span>
                </div>
                <div class="kpi-value" style="font-size: 1.25rem;">Last Value Carried</div>
                <div class="kpi-subtext">Holdout: {result.test_start} to {result.test_end} ({result.test_days}d)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b3:
        if result.mae_model is not None and result.mae_baseline is not None:
            mae_diff = result.mae_baseline - result.mae_model
            mae_pct = (mae_diff / result.mae_baseline * 100) if result.mae_baseline > 0 else 0
            delta_color = "color: #10b981;" if mae_diff >= 0 else "color: #ef4444;"
            mae_val_str = f"{result.mae_model:.2f}"
            mae_sub_str = f"Baseline MAE: {result.mae_baseline:.2f}"
            delta_str = f'<span style="{delta_color} font-size: 0.8rem; font-weight: 700;">{mae_pct:+.1f}% vs Base</span>'
        else:
            mae_val_str = "N/A"
            mae_sub_str = "Unavailable (Insufficient History)"
            delta_str = '<span style="color: #94a3b8; font-size: 0.8rem; font-weight: 600;">Unavailable</span>'

        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-emerald">
                <div class="kpi-header">
                    <span class="kpi-title">Holdout MAE</span>
                    {delta_str}
                </div>
                <div class="kpi-value">{mae_val_str}</div>
                <div class="kpi-subtext">{mae_sub_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b4:
        if result.rmse_model is not None and result.rmse_baseline is not None:
            rmse_diff = result.rmse_baseline - result.rmse_model
            rmse_pct = (rmse_diff / result.rmse_baseline * 100) if result.rmse_baseline > 0 else 0
            rmse_color = "color: #10b981;" if rmse_diff >= 0 else "color: #ef4444;"
            rmse_val_str = f"{result.rmse_model:.2f}"
            rmse_sub_str = f"Baseline RMSE: {result.rmse_baseline:.2f}"
            delta_rmse_str = f'<span style="{rmse_color} font-size: 0.8rem; font-weight: 700;">{rmse_pct:+.1f}% vs Base</span>'
        else:
            rmse_val_str = "N/A"
            rmse_sub_str = "Unavailable (Insufficient History)"
            delta_rmse_str = '<span style="color: #94a3b8; font-size: 0.8rem; font-weight: 600;">Unavailable</span>'

        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-indigo">
                <div class="kpi-header">
                    <span class="kpi-title">Holdout RMSE</span>
                    {delta_rmse_str}
                </div>
                <div class="kpi-value">{rmse_val_str}</div>
                <div class="kpi-subtext">{rmse_sub_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Forecast Plotly Chart
    fig_fc = go.Figure()

    # 1. Historical Actuals
    hist_tail = result.historical_df.tail(60)
    fig_fc.add_trace(
        go.Scatter(
            x=hist_tail["date"],
            y=hist_tail["units_sold"],
            mode="lines+markers",
            name="Historical Actuals",
            line=dict(color="#94a3b8", width=1.5),
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
                name=f"Holt Model Holdout (MAE={result.mae_model})",
                line=dict(color="#2563eb", width=2.5),
            )
        )

    # 3. Future Forecast
    if not result.forecast_df.empty:
        fig_fc.add_trace(
            go.Scatter(
                x=result.forecast_df["date"],
                y=result.forecast_df["forecast"],
                mode="lines+markers",
                name=f"Out-of-Sample Horizon (+{result.forecast_horizon}d)",
                line=dict(color="#10b981", width=3, dash="dot"),
                marker=dict(size=6, symbol="diamond"),
            )
        )

    fig_fc.update_layout(
        title=f"Demand History, Chronological Holdout Benchmark, and Out-of-Sample {result.forecast_horizon}-Day Forecast",
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_family="Plus Jakarta Sans",
        xaxis=dict(title="Calendar Date", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Units Demanded", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # Detailed Holdout Residuals Table
    with st.expander("⌖ View Chronological Holdout Residuals & Observations"):
        if not result.test_df.empty:
            view_test = result.test_df[["date", "actual", "baseline_pred", "model_pred"]].copy()
            view_test["model_abs_error"] = (view_test["actual"] - view_test["model_pred"]).abs()
            view_test["baseline_abs_error"] = (view_test["actual"] - view_test["baseline_pred"]).abs()
            view_test["date"] = view_test["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(view_test, use_container_width=True)


def tab_inventory_planner(df_filtered: pd.DataFrame):
    """Renders Reorder Point Optimization and What-If Scenario Simulator."""
    st.markdown(
        f"""
        <div class="notice-card">
            <strong>Deterministic Reorder Policy:</strong> Reorder Point (ROP) = <code>Lead-Time Demand + Safety Stock</code>.<br>
            Safety stock is calculated as <code>Z × σ(Daily Demand) × √(Lead Time)</code>.<br>
            <em>{ASSUMPTION_DISCLOSURE}</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### ⎈ Scenario Simulation Control Deck")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        demand_mult = st.slider(
            "Demand Surge Multiplier:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Simulate demand surges (e.g., 1.2x = +20% demand) or market contractions."
        )
    with sc2:
        lead_time_jitter = st.slider(
            "Lead Time Delay Jitter (Days):",
            min_value=0,
            max_value=14,
            value=0,
            step=1,
            help="Simulate supply chain friction, freight congestion, or port delays."
        )
    with sc3:
        service_level = st.selectbox(
            "Target Cycle Service Level:",
            list(SERVICE_LEVEL_Z.keys()),
            index=1,
            help="Probability of avoiding a stockout event during lead time."
        )
    with sc4:
        review_days = st.number_input(
            "Replenishment Review Period (Days):",
            min_value=1,
            max_value=30,
            value=7,
            step=1,
            help="Cadence for generating replenishment purchase orders."
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
    st.markdown("##### ◈ Scenario Capital & Exposure Impact")
    i1, i2, i3, i4 = st.columns(4)
    with i1:
        risk_pill = (
            f'<span class="pill-urgent">▲ {plan_summary.at_risk_skus_count} At Risk</span>'
            if plan_summary.at_risk_skus_count > 0
            else '<span class="pill-healthy">● All Protected</span>'
        )
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-rose">
                <div class="kpi-header">
                    <span class="kpi-title">Stockout Vulnerability</span>
                    {risk_pill}
                </div>
                <div class="kpi-value">{plan_summary.at_risk_skus_count} <span style="font-size: 1rem; color: #64748b;">/ {plan_summary.total_skus} SKUs</span></div>
                <div class="kpi-subtext">Current stock below scenario ROP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with i2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-blue">
                <div class="kpi-header">
                    <span class="kpi-title">Replenishment Units</span>
                    <span class="kpi-symbol">↗</span>
                </div>
                <div class="kpi-value">{plan_summary.total_suggested_units:,}</div>
                <div class="kpi-subtext">Units required to attain target stock</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with i3:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-emerald">
                <div class="kpi-header">
                    <span class="kpi-title">Required Working Capital</span>
                    <span class="kpi-symbol">◈</span>
                </div>
                <div class="kpi-value">${plan_summary.total_suggested_cost:,.2f}</div>
                <div class="kpi-subtext">Replenishment units × unit cost</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with i4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-indigo">
                <div class="kpi-header">
                    <span class="kpi-title">Service Level Policy</span>
                    <span class="kpi-symbol">✓</span>
                </div>
                <div class="kpi-value">{service_level.split()[0]}</div>
                <div class="kpi-subtext">Review interval: {review_days} days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 📋 SKU Replenishment Queue & Parameters")

    df_display = plan_summary.to_dataframe()
    if not df_display.empty:
        st.dataframe(df_display, use_container_width=True)

    # Reorder Point Comparison Chart
    if not df_display.empty:
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                x=[p.product_name for p in plan_summary.plans],
                y=[p.current_stock for p in plan_summary.plans],
                name="Current On-Hand Stock",
                marker_color="#2563eb",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                x=[p.product_name for p in plan_summary.plans],
                y=[p.reorder_point for p in plan_summary.plans],
                name="Reorder Point (ROP)",
                marker_color="#f43f5e",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                x=[p.product_name for p in plan_summary.plans],
                y=[p.target_stock for p in plan_summary.plans],
                name="Target Stock Policy",
                marker_color="#10b981",
            )
        )
        fig_bar.update_layout(
            barmode="group",
            title="Current On-Hand Stock vs Calculated ROP vs Target Buffer per SKU",
            hovermode="x unified",
            xaxis_tickangle=-25,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font_family="Plus Jakarta Sans",
            xaxis=dict(showgrid=False),
            yaxis=dict(title="Units", showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def tab_data_quality(report, df_clean: pd.DataFrame):
    """Renders Data Quality Report, Contract Validation, and Provenance."""
    if report is None:
        st.info("No dataset is loaded.")
        return

    # Ingestion Status Card
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-blue">
                <div class="kpi-header"><span class="kpi-title">Raw Ingested Records</span><span class="kpi-symbol">◈</span></div>
                <div class="kpi-value">{report.total_rows:,}</div>
                <div class="kpi-subtext">Total input observations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-emerald">
                <div class="kpi-header"><span class="kpi-title">Clean Records Accepted</span><span class="kpi-symbol">✓</span></div>
                <div class="kpi-value">{report.valid_rows:,}</div>
                <div class="kpi-subtext">Fully contract-compliant rows</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        rej_color = "kpi-accent-rose" if report.rejected_rows > 0 else "kpi-accent-emerald"
        st.markdown(
            f"""
            <div class="kpi-card {rej_color}">
                <div class="kpi-header"><span class="kpi-title">Malformed Records Rejected</span><span class="kpi-symbol">⚠</span></div>
                <div class="kpi-value">{report.rejected_rows:,}</div>
                <div class="kpi-subtext">Explicit contract breaches</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-accent-indigo">
                <div class="kpi-header"><span class="kpi-title">Exact Duplicates Handled</span><span class="kpi-symbol">↻</span></div>
                <div class="kpi-value">{report.duplicate_rows_count:,}</div>
                <div class="kpi-subtext">Sanitized and deduplicated</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown("##### ⌖ Rejection Ledger & Sanitization")
        if report.rejection_reasons:
            reasons_df = pd.DataFrame([
                {"Reason": k, "Rows Rejected": v} for k, v in report.rejection_reasons.items()
            ])
            st.dataframe(reasons_df, use_container_width=True)
        else:
            st.success("✓ Zero rows were rejected. Strict data contract fully satisfied.")

        st.markdown("##### ⚠ Ingestion Warnings & Edge Cases")
        if report.warnings:
            for w in report.warnings:
                st.warning(f"• {w}")
        else:
            st.success("✓ No anomalies or sparsity warnings detected.")

    with col_q2:
        st.markdown("##### ⬡ Missing Values by Column")
        if report.missing_values_by_column:
            missing_df = pd.DataFrame([
                {"Column": k, "Missing Observations": v} for k, v in report.missing_values_by_column.items()
            ])
            st.dataframe(missing_df, use_container_width=True)
        else:
            st.success("✓ Zero missing values across all contract fields.")

        st.markdown("##### ⏱ Ingestion Ledger & Scope")
        st.markdown(
            f"""
            - **Earliest Calendar Date:** `{report.min_date}`
            - **Latest Calendar Date:** `{report.max_date}`
            - **Active Distinct SKUs:** `{report.distinct_products_count}`
            """
        )

    st.markdown("---")
    st.markdown("##### 📜 Contract Schema Specifications")
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
    st.markdown("##### ◈ Data Lineage & Governance Notice")
    st.info(DATA_PROVENANCE_NOTE)
    st.markdown(
        """
        - **Decision Support Notice:** This application provides operational decision support and recommendations. It does not perform automated procurement or financial commitments.
        - **Sales vs Unconstrained Demand:** Units sold represent observed sales, which may be constrained by prior stockouts.
        - **Cost Valuation:** Inventory valuation is calculated from provided unit costs and snapshot quantities, not financial ERP ledger balances.
        """
    )


def main():
    """Main application orchestrator."""
    df_clean, report, df_filtered, selected_product, date_range = render_sidebar()

    # Executive Hero Banner
    st.markdown(
        """
        <div class="hero-banner">
            <div>
                <h1 class="hero-title">
                    <span>SupplyChain IQ</span>
                </h1>
                <div class="hero-subtitle">
                    Intelligent Demand Forecasting, Reorder Optimization & What-If Scenario Simulation
                </div>
            </div>
            <div>
                <span class="hero-badge">
                    <span>●</span> Enterprise Core
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_clean is None or df_filtered is None:
        st.info("⌖ Please load data using the sidebar to begin analysis.")
        return

    # Primary Navigation Tabs with clean modern symbols
    tab1, tab2, tab3, tab4 = st.tabs([
        "◈ Operational Overview",
        "⌖ Demand Forecasting",
        "⚡ Inventory Simulator",
        "✦ Data Quality & Audit",
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
