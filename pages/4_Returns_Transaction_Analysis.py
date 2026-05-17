import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import run_query
from utils.helpers import load_custom_css, get_base_filters, build_where_clause, render_kpi, format_currency, apply_chart_theme, render_observation

st.set_page_config(page_title="Returns & Transaction Analysis | OpsIntel", layout="wide")
load_custom_css()

st.title("Returns & Transaction Analysis")
st.markdown("### Transaction Attrition, Reverse Logistics, Payment Failures, and Fraud Diagnostics")

# Filters
st.markdown("#### Filter Profile")
sel_region, sel_category, sel_month = get_base_filters()
where_clause = build_where_clause(sel_region, sel_category, sel_month)

# Insights Section
st.markdown("## KPI Insights & Transaction Observations")

payment_fail_worst = run_query("""
    SELECT payment_method, failure_rate_pct, failed_txns
    FROM vw_payment_analysis
    ORDER BY failure_rate_pct DESC
    LIMIT 1
""")

if not payment_fail_worst.empty:
    worst_pay = payment_fail_worst.iloc[0]
    if worst_pay['failure_rate_pct'] > 5:
        render_observation(
            title=f"Elevated Transaction Decline Rate — {worst_pay['payment_method']}",
            text=f"The transaction failure rate for {worst_pay['payment_method']} payment channel is currently elevated at {worst_pay['failure_rate_pct']}%, leading to order drop-offs.",
            action_plan=f"Audit API connections with the primary payment gateway. Configure secondary fallback routing protocols.",
            status="warning"
        )

# Fetch KPIs
txn_kpi = run_query(f"""
    SELECT
        COUNT(*) as total_orders,
        SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_txns,
        SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) as returned_orders,
        SUM(CASE WHEN status = 'Failed' THEN revenue ELSE 0 END) as failed_revenue,
        SUM(CASE WHEN status = 'Returned' THEN revenue ELSE 0 END) as returned_revenue,
        AVG(fraud_risk_score) as avg_fraud_score
    FROM orders {where_clause}
""")

if not txn_kpi.empty:
    m = txn_kpi.iloc[0]
    total = int(m['total_orders'])
    failed = int(m['failed_txns'] or 0)
    returned = int(m['returned_orders'] or 0)
    fail_rate = (failed / total * 100) if total else 0
    ret_rate = (returned / total * 100) if total else 0
    failed_rev = m['failed_revenue'] or 0
    returned_rev = m['returned_revenue'] or 0
    avg_fraud = round(m['avg_fraud_score'] or 0, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi("Declined Order Lines", f"{failed:,}", "Total transaction capture errors", "critical" if fail_rate > 5 else "default")
    with c2:
        render_kpi("Gateway Decline Rate", f"{fail_rate:.1f}%", "Ratio of payment failure incidents", "critical" if fail_rate > 5 else "default")
    with c3:
        render_kpi("Returned Order Lines", f"{returned:,}", "Total volume of customer returns", "warning" if ret_rate > 8 else "default")
    with c4:
        render_kpi("Decline Revenue Leakage", format_currency(failed_rev), "Estimated value of failed checkouts", "critical")
    with c5:
        render_kpi("Average Risk Index", f"{avg_fraud} / 100", "Mean transactional risk index", "warning" if avg_fraud > 40 else "default")

st.markdown("---")

# Payment Analysis Graphs
col1, col2 = st.columns(2)
pay_df = run_query("SELECT * FROM vw_payment_analysis ORDER BY failure_rate_pct DESC")

if not pay_df.empty:
    with col1:
        fig_fail = px.bar(
            pay_df, x='payment_method', y='failure_rate_pct',
            labels={'payment_method': 'Payment Protocol', 'failure_rate_pct': 'Failure Rate (%)'},
            color_discrete_sequence=['#DC2626']
        )
        fig_fail = apply_chart_theme(fig_fail, title="Transaction Capture Failure Rate (%) by Payment Protocol")
        st.plotly_chart(fig_fail, use_container_width=True)

    with col2:
        fig_fraud = px.bar(
            pay_df, x='payment_method', y='avg_fraud_risk',
            labels={'payment_method': 'Payment Protocol', 'avg_fraud_risk': 'Mean Transactional Risk Index'},
            color_discrete_sequence=['#475569']
        )
        fig_fraud = apply_chart_theme(fig_fraud, title="Mean Transactional Risk Index Profile")
        st.plotly_chart(fig_fraud, use_container_width=True)

# COD vs Prepaid Analysis
st.markdown("### Reverse Logistics Analysis (COD vs. Prepaid Return Patterns)")
cod_df = run_query(f"""
    SELECT 
        CASE WHEN payment_method = 'COD' THEN 'Cash on Delivery (COD)' ELSE 'Prepaid' END as payment_type,
        COUNT(*) as total,
        SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) as returned,
        ROUND(SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as return_rate
    FROM orders {where_clause}
    GROUP BY payment_type
""")

if not cod_df.empty:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_cod = px.bar(
            cod_df, x='payment_type', y='return_rate',
            color='payment_type',
            labels={'payment_type': 'Settlement Type', 'return_rate': 'Return Incidence Rate (%)'},
            color_discrete_map={'Cash on Delivery (COD)': '#DC2626', 'Prepaid': '#16A34A'}
        )
        fig_cod = apply_chart_theme(fig_cod, title="Operational Return Incidence by Transaction Settlement Type")
        st.plotly_chart(fig_cod, use_container_width=True)

    with col_c2:
        fig_vol = px.pie(
            cod_df, names='payment_type', values='total',
            color_discrete_sequence=['#475569', '#CBD5E1'],
            hole=0.5
        )
        fig_vol = apply_chart_theme(fig_vol, title="Transaction Settlement Contribution Split")
        st.plotly_chart(fig_vol, use_container_width=True)

# Return Reasons and Failure Treemaps
col_r1, col_r2 = st.columns(2)

with col_r1:
    reason_df = run_query(f"""
        SELECT return_reason, COUNT(*) as count 
        SELECT return_reason, COUNT(*) as count 
        FROM orders 
        WHERE status = 'Returned' AND return_reason IS NOT NULL
        GROUP BY return_reason 
        ORDER BY count DESC
    """)
    # Fix potential SQLite/SQL grammar error in multiline
    reason_df = run_query(f"SELECT return_reason, COUNT(*) as count FROM orders WHERE status = 'Returned' AND return_reason IS NOT NULL GROUP BY return_reason ORDER BY count DESC")
    if not reason_df.empty:
        fig_reason = px.bar(
            reason_df, x='count', y='return_reason', orientation='h',
            labels={'count': 'Return Order Volume', 'return_reason': 'Stated Return Rationale'},
            color_discrete_sequence=['#D97706']
        )
        fig_reason = apply_chart_theme(fig_reason, title="Systemic Return Rationale Audit")
        fig_reason.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_reason, use_container_width=True)

with col_r2:
    fail_reason_df = run_query(f"SELECT failure_reason, COUNT(*) as count FROM orders WHERE status = 'Failed' AND failure_reason IS NOT NULL GROUP BY failure_reason ORDER BY count DESC")
    if not fail_reason_df.empty:
        fig_fail_reason = px.treemap(
            fail_reason_df, path=['failure_reason'], values='count',
            color_discrete_sequence=['#EF4444']
        )
        fig_fail_reason = apply_chart_theme(fig_fail_reason, title="Payment Capture Failure Root Causes")
        st.plotly_chart(fig_fail_reason, use_container_width=True)

# High Return drilldown
st.markdown("### High-Return Drill-down Analysis")
hi_ret_df = run_query(f"""
    SELECT category, region,
        COUNT(*) as total,
        SUM(CASE WHEN status='Returned' THEN 1 ELSE 0 END) as returns,
        ROUND(SUM(CASE WHEN status='Returned' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as return_rate
    FROM orders {where_clause}
    GROUP BY category, region
    ORDER BY return_rate DESC
""")
if not hi_ret_df.empty:
    fig_sunburst = px.sunburst(
        hi_ret_df, path=['category', 'region'], values='returns',
        color='return_rate', color_continuous_scale='YlOrRd',
        labels={'return_rate': 'Return Incidence Rate (%)'}
    )
    fig_sunburst = apply_chart_theme(fig_sunburst, title="Returns Contribution Matrix (Category to Region Segment)")
    st.plotly_chart(fig_sunburst, use_container_width=True)
