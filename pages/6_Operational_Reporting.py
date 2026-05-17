import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import run_query
from utils.helpers import load_custom_css, format_currency, render_observation, apply_chart_theme

st.set_page_config(page_title="Operational Reporting | OpsIntel", layout="wide")
load_custom_css()

st.title("Operational Reporting")
st.markdown("### Executive Summary, Analytical Ledger Builder, and Recommended Action Plans")

st.markdown("---")

# ─── EXECUTIVE SUMMARY ───────────────────────────────────────────
st.markdown("## Executive Summary")

# Compile professional findings dynamically from database
findings = []

# Finding 1: SLA and Warehouse performance
sla_wh = run_query("""
    SELECT warehouse, region, 
        SUM(CASE WHEN sla_breached=1 THEN 1 ELSE 0 END) as breaches,
        COUNT(*) as total,
        ROUND(SUM(CASE WHEN sla_breached=1 THEN 1 ELSE 0 END)*100.0/COUNT(*), 1) as breach_rate
    FROM orders WHERE status='Delivered'
    GROUP BY warehouse, region
    ORDER BY breach_rate DESC
""")
if not sla_wh.empty:
    worst_wh = sla_wh.iloc[0]
    total_breaches = sla_wh['breaches'].sum()
    pct_contrib = round((worst_wh['breaches'] / total_breaches) * 100, 1) if total_breaches > 0 else 0
    findings.append({
        "title": "Fulfillment Network Friction (Critical Delivery Latency)",
        "summary": f"Audit checks indicate fulfillment center {worst_wh['warehouse']} ({worst_wh['region']}) accounts for {pct_contrib}% of the total logistics SLA breaches across active supply lines. The facility's local breach rate stands at {worst_wh['breach_rate']}%.",
        "action": f"Deploy a dispatch audit team to {worst_wh['warehouse']} to inspect layout capacity, pick-to-pack workflows, and carrier handoffs.",
        "status": "critical"
    })

# Finding 2: Payment and checkout failure rates
pay_fail = run_query("""
    SELECT payment_method,
        COUNT(*) as total,
        SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) as failures,
        ROUND(SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as fail_rate,
        ROUND(SUM(CASE WHEN status='Failed' THEN revenue ELSE 0 END), 0) as lost_rev
    FROM orders GROUP BY payment_method ORDER BY fail_rate DESC
    LIMIT 1
""")
if not pay_fail.empty:
    worst_pay = pay_fail.iloc[0]
    findings.append({
        "title": "Gateway Processing Degradation (Financial Leakage)",
        "summary": f"Transaction audit records indicate that the {worst_pay['payment_method']} payment route experienced a high failure capture rate of {worst_pay['fail_rate']}%. This operational bottleneck resulted in gross revenue drop-offs totaling {format_currency(worst_pay['lost_rev'])} during the reporting period.",
        "action": f"Re-evaluate api connection parameters with payment gateway providers and check for timeout thresholds on {worst_pay['payment_method']} pipelines.",
        "status": "critical"
    })

# Finding 3: Return behaviors (COD vs Prepaid)
cod_ret = run_query("""
    SELECT 
        CASE WHEN payment_method='COD' THEN 'COD' ELSE 'Prepaid' END as settlement_type,
        COUNT(*) as total,
        SUM(CASE WHEN status='Returned' THEN 1 ELSE 0 END) as returns,
        ROUND(SUM(CASE WHEN status='Returned' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as return_rate
    FROM orders GROUP BY settlement_type
""")
if not cod_ret.empty and len(cod_ret) == 2:
    cod_rate = cod_ret[cod_ret['settlement_type']=='COD']['return_rate'].values[0]
    pre_rate = cod_ret[cod_ret['settlement_type']=='Prepaid']['return_rate'].values[0]
    variance = round(cod_rate - pre_rate, 2)
    findings.append({
        "title": "Cash-on-Delivery (COD) Reverse Logistics Exposure",
        "summary": f"Reconciliation audits reveal a significant variance of {variance}% in returns between settlement methodologies (COD Return Rate: {cod_rate}% vs Prepaid Return Rate: {pre_rate}%). COD orders represent a higher logistical return exposure.",
        "action": "Implement a mandatory interactive voice response (IVR) or SMS-based buyer confirmation protocol for COD orders exceeding INR 5,000.",
        "status": "warning"
    })

# Render Observations in Corporate style
for f in findings:
    render_observation(
        title=f['title'],
        text=f['summary'],
        action_plan=f['action'],
        status=f['status']
    )

st.markdown("---")

# ─── CUSTOM REPORT BUILDER ─────────────────────────────────────────
st.markdown("## Operational Custom Report Builder")
st.markdown("Filter, configure, and compile custom transactional reports for export to ERP or SAP modules.")

# Sidebar/Local reporting config columns
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    report_type = st.selectbox(
        "Focus Operational Ledger",
        ["All Operational Log Entries", "Service Level Agreement (SLA) Breaches", "Transaction Deficits & Gateway Failures", "Reverse Logistics (Customer Returns)"]
    )

with col_b2:
    target_region = st.multiselect(
        "Fulfillment Region Profile",
        ["North", "South", "East", "West", "Central"],
        default=[]
    )

with col_b3:
    export_columns = st.multiselect(
        "Select Fields to Include",
        ["order_id", "order_date", "region", "city", "warehouse", "shipping_partner", "category", "payment_method", "status", "revenue", "delivery_days", "sla_breached", "csat_score", "fraud_risk_score"],
        default=["order_id", "order_date", "warehouse", "shipping_partner", "status", "revenue", "sla_breached"]
    )

# Build custom SQL Query based on selections
base_query = "SELECT * FROM orders"
clauses = []

if report_type == "Service Level Agreement (SLA) Breaches":
    clauses.append("sla_breached = 1")
elif report_type == "Transaction Deficits & Gateway Failures":
    clauses.append("status = 'Failed'")
elif report_type == "Reverse Logistics (Customer Returns)":
    clauses.append("status = 'Returned'")

if target_region:
    reg_str = "','".join(target_region)
    clauses.append(f"region IN ('{reg_str}')")

if clauses:
    base_query += " WHERE " + " AND ".join(clauses)

base_query += " ORDER BY order_date DESC LIMIT 10000"

# Fetch custom report
report_df = run_query(base_query)

if not report_df.empty:
    # Filter columns to only what the user selected
    if export_columns:
        # Keep only the valid columns that exist in the dataframe
        valid_cols = [c for c in export_columns if c in report_df.columns]
        display_df = report_df[valid_cols]
    else:
        display_df = report_df
        
    st.markdown(f"**Compiled Report Size:** {len(display_df):,} entries (Displaying top 100 entries below)")
    st.dataframe(display_df.head(100), use_container_width=True, hide_index=True)
    
    # Download Button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download Operational Ledger Extract (CSV)",
        data=csv,
        file_name="operational_reporting_ledger.csv",
        mime="text/csv"
    )
else:
    st.warning("No records matched your exact reporting parameters.")
