"""
RzKala Dashboard - Streamlit
Retail analytics dashboard for non-technical users
Supports single and multi-file upload with smart merge
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Project path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.core.mapper import load_and_map
from src.core.analyzer import run_all_analyses
from src.core.merger import merge_from_dataframes
from src.components.kpi_cards import get_kpi_cards
from src.components.funnel_chart import get_funnel_data

# Page config
st.set_page_config(
    page_title="RzKala Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("RzKala - Sales Analytics Dashboard")

# ============================================================
# Sidebar - File Upload (Single or Multiple)
# ============================================================
st.sidebar.header("Upload Sales Data")

upload_mode = st.sidebar.radio(
    "Upload Mode",
    ["Single File", "Multiple Files (Merge)"],
    help="Single: one CSV/Excel file. Multiple: merge several files into one dataset."
)

uploaded_files = []

if upload_mode == "Single File":
    uploaded_file = st.sidebar.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="WooCommerce export, POS data, or any sales file"
    )
    if uploaded_file:
        uploaded_files = [uploaded_file]
else:
    uploaded_file = st.sidebar.file_uploader(
        "Choose multiple files to merge",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help="Upload multiple files - columns will be auto-detected and merged"
    )
    if uploaded_file:
        uploaded_files = uploaded_file

# ============================================================
# Load data
# ============================================================
@st.cache_data
def load_single_file(file):
    temp_path = os.path.join(BASE_DIR, 'data', 'user_uploads', file.name)
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, 'wb') as f:
        f.write(file.getbuffer())
    return load_and_map(file_path=temp_path)


@st.cache_data
def load_and_merge_files(files):
    # Save and load all files using mapper
    all_dfs = []
    file_names = []

    for file in files:
        temp_path = os.path.join(BASE_DIR, 'data', 'user_uploads', file.name)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, 'wb') as f:
            f.write(file.getbuffer())

        # Use mapper to standardize
        data = load_and_map(file_path=temp_path)
        df = data['orders']
        df['source_file'] = file.name
        all_dfs.append(df)
        file_names.append(file.name)

    # Simple concat - all dataframes already standardized by mapper
    if len(all_dfs) == 1:
        return all_dfs[0], ["Single file loaded - no merge needed."], {}

    # Find all columns across all dataframes
    all_columns = []
    for df in all_dfs:
        all_columns.extend(df.columns.tolist())
    all_columns = list(set(all_columns))

    # Align - add missing columns as NaN
    aligned = []
    for df in all_dfs:
        for col in all_columns:
            if col not in df.columns:
                df[col] = pd.NA
        aligned.append(df[all_columns])

    # Concat
    merged = pd.concat(aligned, ignore_index=True)

    # Report
    missing_report = {}
    for std_col in ['order_date', 'total_price', 'customer_phone', 'order_id', 'product_name', 'quantity', 'unit_cost',
                    'discount_pct', 'category', 'profit']:
        if std_col not in all_columns:
            missing_report[std_col] = "not available in any file"

    log = [
        f"Merged {len(file_names)} files: {file_names}",
        f"Total columns: {len(all_columns)}",
        f"Columns: {all_columns}",
        f"Missing: {list(missing_report.keys()) if missing_report else 'None'}"
    ]

    return merged, log, missing_report
# Process uploaded files
data = None
merge_log = None

if uploaded_files:
    if upload_mode == "Single File":
        data = load_single_file(uploaded_files[0])
    else:
        if len(uploaded_files) > 1:
            merged_df, merge_log, missing_report = load_and_merge_files(uploaded_files)

            # Save merged file temporarily and load with mapper
            merged_path = os.path.join(BASE_DIR, 'data', 'user_uploads', '_merged_temp.csv')
            os.makedirs(os.path.dirname(merged_path), exist_ok=True)
            merged_df.to_csv(merged_path, index=False)
            data = load_and_map(file_path=merged_path)
        elif len(uploaded_files) == 1:
            data = load_single_file(uploaded_files[0])
else:
    data = load_and_map()

orders = data['orders']
traffic = data.get('traffic')
ad_spend = data.get('ad_spend')

# ============================================================
# Run analysis
# ============================================================
results = run_all_analyses(
    orders_df=orders,
    traffic_df=traffic,
    ad_spend_df=ad_spend
)

kpi = get_kpi_cards(orders)
funnel = get_funnel_data(orders, traffic)

# ============================================================
# Status messages
# ============================================================
if upload_mode == "Multiple Files" and len(uploaded_files) > 1:
    st.success(f"Merged {len(uploaded_files)} files successfully.")
    if merge_log:
        with st.expander("Merge Details"):
            for log in merge_log:
                st.text(log)
            if missing_report:
                st.subheader("Missing Columns")
                for col, status in missing_report.items():
                    if "not available" in status:
                        st.warning(f"Column not in dataset: {col}")
                    else:
                        st.info(f"{col}: {status}")

st.markdown("---")

# ============================================================
# Row 1 - KPI Cards
# ============================================================
st.subheader("Performance Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"{kpi['total_revenue']:,.0f} Rials")
with col2:
    st.metric("Net Profit", f"{kpi['total_profit']:,.0f} Rials")
with col3:
    st.metric("Total Orders", f"{kpi['total_orders']:,}")
with col4:
    st.metric("Unique Customers", f"{kpi['unique_customers']:,}")

col5, col6, col7 = st.columns(3)
with col5:
    st.metric("Avg Order Value", f"{kpi['avg_order_value']:,.0f} Rials")
with col6:
    st.metric("Profit Margin", f"{kpi['profit_margin_pct']}%")
with col7:
    st.metric("Cancellation Rate", f"{kpi['cancellation_rate']}%")

st.markdown("---")

# ============================================================
# Row 2 - Sales Trend
# ============================================================
st.subheader("Sales Trend")

if 'trend' in results and len(results['trend']) > 0:
    col_trend1, col_trend2 = st.columns(2)

    with col_trend1:
        fig_trend = px.line(
            results['trend'],
            x='date',
            y='revenue',
            title='Daily Revenue',
            labels={'date': 'Date', 'revenue': 'Revenue (Rials)'}
        )
        st.plotly_chart(fig_trend, width='stretch')

    with col_trend2:
        if 'trend_weekly' in results and len(results['trend_weekly']) > 0:
            fig_weekly = px.bar(
                results['trend_weekly'],
                x='week',
                y='revenue',
                title='Weekly Revenue',
                labels={'week': 'Week', 'revenue': 'Revenue (Rials)'}
            )
            st.plotly_chart(fig_weekly, width='stretch')

st.markdown("---")

# ============================================================
# Row 3 - Pareto + RFM
# ============================================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 20 Products by Profit")
    if 'profitability' in results and len(results['profitability']) > 0:
        top_products = results['profitability'].head(20)
        fig_pareto = px.bar(
            top_products,
            x='product_name',
            y='profit',
            title='Product Profitability',
            labels={'product_name': 'Product', 'profit': 'Profit (Rials)'}
        )
        fig_pareto.update_xaxes(tickangle=45)
        st.plotly_chart(fig_pareto, width='stretch')

with col_right:
    st.subheader("Customer Segmentation (RFM)")
    if 'rfm' in results and len(results['rfm']) > 0:
        fig_rfm = px.pie(
            results['rfm'],
            names='segment',
            values='customer_count',
            title='Customer Distribution',
            hole=0.4
        )
        st.plotly_chart(fig_rfm, width='stretch')

st.markdown("---")

# ============================================================
# Row 4 - Funnel + Repeat Rate
# ============================================================
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Sales Funnel")
    if len(funnel) > 1:
        fig_funnel = px.funnel(
            funnel,
            x='count',
            y='stage',
            title='Conversion Funnel'
        )
        st.plotly_chart(fig_funnel, width='stretch')
    else:
        st.info("Traffic data not available. Funnel cannot be displayed.")

with col_right2:
    st.subheader("Customer Repeat Rate")
    if 'repeat_rate' in results and len(results['repeat_rate']) > 0:
        fig_repeat = px.pie(
            results['repeat_rate'],
            names='customer_type',
            values='customer_count',
            title='How many times customers buy?',
            hole=0.4
        )
        st.plotly_chart(fig_repeat, width='stretch')

st.markdown("---")

# ============================================================
# Row 5 - TreeMap + Scatter
# ============================================================
col_left3, col_right3 = st.columns(2)

with col_left3:
    st.subheader("Product TreeMap")
    if 'treemap_data' in results and len(results['treemap_data']) > 0:
        treemap_df = results['treemap_data'].head(30)

        # Add source info if available
        if 'source_file' in orders.columns:
            path = ['source_file', 'product_name']
        else:
            path = ['product_name']

        fig_treemap = px.treemap(
            treemap_df,
            path=path,
            values='revenue',
            title='Revenue by Product'
        )
        st.plotly_chart(fig_treemap, width='stretch')

with col_right3:
    st.subheader("Revenue vs Profit")
    if 'scatter_data' in results and len(results['scatter_data']) > 0:
        fig_scatter = px.scatter(
            results['scatter_data'],
            x='total_revenue',
            y='total_profit',
            size='units_sold',
            hover_name='product_name',
            title='Revenue vs Profit Correlation',
            labels={
                'total_revenue': 'Revenue',
                'total_profit': 'Profit',
                'units_sold': 'Units Sold'
            }
        )
        st.plotly_chart(fig_scatter, width='stretch')

st.markdown("---")

# ============================================================
# Row 6 - ROAS (if available)
# ============================================================
if 'roas' in results and len(results['roas']) > 0:
    st.subheader("Return on Ad Spend (ROAS)")
    fig_roas = px.bar(
        results['roas'],
        x='campaign',
        y='roas',
        title='ROAS by Campaign',
        labels={'campaign': 'Campaign', 'roas': 'ROAS (x)'},
        text='roas'
    )
    st.plotly_chart(fig_roas, width='stretch')
    st.markdown("---")

# ============================================================
# Row 7 - Discount Impact (if available)
# ============================================================
if 'discount_impact' in results and len(results['discount_impact']) > 0:
    st.subheader("Discount Impact on Profit")
    fig_discount = px.bar(
        results['discount_impact'],
        x='discount_range',
        y='profit',
        title='Profit by Discount Range',
        labels={'discount_range': 'Discount %', 'profit': 'Profit (Rials)'}
    )
    st.plotly_chart(fig_discount, width='stretch')
    st.markdown("---")

# ============================================================
# Download section
# ============================================================
st.subheader("Download Reports")

col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    if 'trend' in results:
        csv = results['trend'].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "Download Sales Trend (CSV)",
            data=csv,
            file_name="rzkala_trend.csv",
            mime="text/csv"
        )

with col_dl2:
    if 'profitability' in results:
        csv = results['profitability'].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "Download Profitability (CSV)",
            data=csv,
            file_name="rzkala_profitability.csv",
            mime="text/csv"
        )

with col_dl3:
    if 'rfm' in results:
        csv = results['rfm'].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "Download RFM Segments (CSV)",
            data=csv,
            file_name="rzkala_rfm.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.caption("Built with Python | RzKala Dashboard v1.1 | Multi-file merge supported")