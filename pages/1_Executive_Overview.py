import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import run_query
from utils.helpers import load_custom_css, render_kpi, format_currency, get_base_filters, build_where_clause, apply_chart_theme, render_observation

st.set_page_config(page_title="Executive Overview | OpsIntel", layout="wide")
load_custom_css()

st.title("Executive Overview")
st.markdown("### Operational Highlights & Corporate Key Performance Indicators")

# Base Filter System
st.markdown("#### Filter Profile")
sel_region, sel_category, sel_month = get_base_filters()
where_clause = build_where_clause(sel_region, sel_category, sel_month)

# Data Fetching
kpi_query = f"""
    SELECT 
        COUNT(*) as total_orders,
        SUM(revenue) as total_revenue,
        SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_txns,
        SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) as returned_orders,
        SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) as delivered_orders,
        SUM(CASE WHEN status NOT IN ('Failed', 'Cancelled') THEN 1 ELSE 0 END) as successful_orders,
        SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) as sla_breaches,
        AVG(delivery_days) as avg_delivery,
        AVG(csat_score) as avg_csat
    FROM orders {where_clause}
"""
kpi_data = run_query(kpi_query).iloc[0]

total_orders = int(kpi_data['total_orders'])
if total_orders == 0:
    st.warning("No transactional records found matching specified parameters.")
    st.stop()

total_revenue_val = kpi_data['total_revenue'] or 0
total_revenue = format_currency(total_revenue_val)
failed_txns = int(kpi_data['failed_txns'] or 0)
return_rate = (kpi_data['returned_orders'] / total_orders) * 100 if total_orders else 0
order_success_rate = (kpi_data['successful_orders'] / total_orders) * 100 if total_orders else 0
delivered_orders = int(kpi_data['delivered_orders'] or 0)
sla_compliance = 100 - ((kpi_data['sla_breaches'] / delivered_orders) * 100 if delivered_orders else 0)
avg_delivery = round(kpi_data['avg_delivery'] or 0, 1)
avg_csat = round(kpi_data['avg_csat'] or 0, 1)

# Business Observations & Executive Summary Section
st.markdown("## Business Observations")

# Dynamically populate high-quality executive observations
if sla_compliance < 70:
    render_observation(
        title="Service Level Agreement Deficit Detected",
        text=f"Fulfillment SLA compliance is currently underperforming at {sla_compliance:.1f}%, indicating systemic supply chain friction or transit delays.",
        action_plan="Initiate a root-cause investigation into regional carrier metrics and warehouse processing throughput.",
        status="critical"
    )
else:
    render_observation(
        title="Fulfillment Operations Stabilized",
        text=f"Supply chain throughput maintains acceptable SLA compliance of {sla_compliance:.1f}% across active shipping partners.",
        action_plan="Continue monitoring warehouse-specific packing cycles to prevent regional delivery backlogs.",
        status="success"
    )

if return_rate > 5:
    render_observation(
        title="Elevated Product Return Trend",
        text=f"Corporate return rate has spiked to {return_rate:.1f}%, leading to high logistical reverse-cycle overhead costs.",
        action_plan="Cross-reference returns with vendor product specifications and inspect packaging standards.",
        status="warning"
    )

# KPI Matrix Rows
st.markdown("## Corporate KPI Dashboard")

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi("Total Order Volume", f"{total_orders:,}", "Total corporate order line entries", "primary")
with col2:
    render_kpi("Gross Realized Revenue", total_revenue, "Net revenue after deductions", "success")
with col3:
    render_kpi("Fulfillment Success Rate", f"{order_success_rate:.1f}%", "Ratio of successful transactions", "success" if order_success_rate > 90 else "warning")
with col4:
    render_kpi("Customer Experience Index", f"{avg_csat} / 5.0", "Mean corporate CSAT score", "success" if avg_csat > 4.0 else "warning")

col5, col6, col7, col8 = st.columns(4)
with col5:
    render_kpi("SLA Compliance Rate", f"{sla_compliance:.1f}%", "Percentage of orders within SLA target", "success" if sla_compliance > 75 else "critical")
with col6:
    render_kpi("Operational Return Rate", f"{return_rate:.1f}%", "Fraction of delivered orders returned", "warning" if return_rate > 5 else "success")
with col7:
    render_kpi("Failed Transactions", f"{failed_txns:,}", "Transactions blocked at gateway level", "critical" if failed_txns > total_orders * 0.05 else "default")
with col8:
    render_kpi("Avg Logistic Lead Time", f"{avg_delivery} Days", "Average time from dispatch to delivery", "default")

# Trend Analysis
st.markdown("## Trend Analysis")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    trend_data = run_query(f"SELECT order_month, SUM(revenue) as revenue FROM orders {where_clause} GROUP BY order_month ORDER BY order_month")
    if not trend_data.empty:
        fig_trend = px.line(
            trend_data, x='order_month', y='revenue', 
            labels={'order_month': 'Reporting Month', 'revenue': 'Revenue (INR)'},
            color_discrete_sequence=['#1E3A8A']
        )
        fig_trend = apply_chart_theme(fig_trend, title="Monthly Revenue Realization Trend (INR)")
        st.plotly_chart(fig_trend, use_container_width=True)

with chart_col2:
    reg_data = run_query(f"SELECT region, COUNT(*) as orders FROM orders {where_clause} GROUP BY region")
    if not reg_data.empty:
        fig_reg = px.pie(
            reg_data, names='region', values='orders', 
            hole=0.5,
            color_discrete_sequence=['#1E3A8A', '#3B82F6', '#475569', '#0D9488', '#F59E0B']
        )
        fig_reg = apply_chart_theme(fig_reg, title="Regional Operational Contribution Split")
        st.plotly_chart(fig_reg, use_container_width=True)
