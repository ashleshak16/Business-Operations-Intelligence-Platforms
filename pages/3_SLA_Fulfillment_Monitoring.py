import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import run_query
from utils.helpers import load_custom_css, get_base_filters, build_where_clause, render_kpi, apply_chart_theme, render_observation

st.set_page_config(page_title="SLA & Fulfillment Monitoring | OpsIntel", layout="wide")
load_custom_css()

st.title("SLA & Fulfillment Monitoring")
st.markdown("### Service Level Agreement Audit, Dispatch Diagnostics, and Logistics Performance")

# Filters
st.markdown("#### Filter Profile")
sel_region, sel_category, sel_month = get_base_filters()
where_clause = build_where_clause(sel_region, sel_category, sel_month)

# Business Observations / KPI Insights
st.markdown("## KPI Insights & SLA Performance Observations")

# Fetch worst logistics metrics dynamically
partner_worst = run_query("""
    SELECT shipping_partner,
        COUNT(*) as total_deliveries,
        SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) as breaches,
        ROUND(SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*), 1) as breach_rate
    FROM orders 
    WHERE status = 'Delivered'
    GROUP BY shipping_partner
    ORDER BY breach_rate DESC
    LIMIT 1
""")

if not partner_worst.empty:
    worst_p = partner_worst.iloc[0]
    if worst_p['breach_rate'] > 20:
        render_observation(
            title=f"Logistics Performance Deficit — {worst_p['shipping_partner']}",
            text=f"Shipping partner {worst_p['shipping_partner']} exhibits an elevated SLA breach rate of {worst_p['breach_rate']}%. Average turnaround cycle times are systematically delayed.",
            action_plan=f"Request diagnostic routing audits from {worst_p['shipping_partner']}; restrict allocation of critical high-value lines.",
            status="critical"
        )

# Metrics
sla_metrics = run_query(f"""
    SELECT 
        COUNT(*) as total_delivered,
        SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) as breached,
        AVG(delivery_days) as avg_days
    FROM orders 
    WHERE status = 'Delivered'
""")

if not sla_metrics.empty:
    m = sla_metrics.iloc[0]
    total_del = m['total_delivered']
    breaches = m['breached'] or 0
    breach_rate = (breaches / total_del * 100) if total_del else 0
    avg_days = m['avg_days'] or 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi("Fulfillment SLA Breach Rate", f"{breach_rate:.1f}%", "Fraction of delayed order lines", "critical" if breach_rate > 20 else "default")
    with col2:
        render_kpi("Audit Failure Volume", f"{breaches:,}", "Total lines breaching transit target", "critical" if breaches > 1000 else "default")
    with col3:
        render_kpi("Mean Logistics Turnaround", f"{avg_days:.1f} Days", "Average duration of shipping cycle", "default")

st.markdown("---")

# Partner Benchmarking
st.markdown("### Logistics Partner Audit")
partner_df = run_query(f"""
    SELECT 
        shipping_partner,
        COUNT(*) as total_deliveries,
        SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) as breaches,
        ROUND(AVG(delivery_days), 1) as avg_delivery_time
    FROM orders 
    WHERE status = 'Delivered'
    GROUP BY shipping_partner
    ORDER BY total_deliveries DESC
""")

if not partner_df.empty:
    partner_df['Breach Rate %'] = round((partner_df['breaches'] / partner_df['total_deliveries']) * 100, 1)
    
    col1, col2 = st.columns(2)
    with col1:
        fig_partner = px.bar(
            partner_df, x='shipping_partner', y='Breach Rate %', 
            labels={'shipping_partner': 'Shipping Partner', 'Breach Rate %': 'SLA Breach Rate (%)'},
            color='Breach Rate %', color_continuous_scale='Reds'
        )
        fig_partner = apply_chart_theme(fig_partner, title="SLA Breach Incidence Rate by Logistics Partner")
        st.plotly_chart(fig_partner, use_container_width=True)
        
    with col2:
        fig_time = px.scatter(
            partner_df, x='total_deliveries', y='avg_delivery_time', 
            size='breaches', color='shipping_partner', hover_name='shipping_partner',
            labels={'total_deliveries': 'Delivered Volume (Units)', 'avg_delivery_time': 'Mean Transit Cycle (Days)'}
        )
        fig_time = apply_chart_theme(fig_time, title="Carrier Volume Capacity vs. Lead Time Performance")
        st.plotly_chart(fig_time, use_container_width=True)

# Heatmap Matrix
st.markdown("### Regional SLA Heatmap Matrix")
heat_df = run_query(f"""
    SELECT region, category, SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*) as breach_rate
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY region, category
""")
if not heat_df.empty:
    heat_pivot = heat_df.pivot(index='region', columns='category', values='breach_rate').fillna(0)
    fig_heat = px.imshow(
        heat_pivot, text_auto=".1f", aspect="auto", color_continuous_scale="Reds",
        labels=dict(x="Product Category", y="Operational Region", color="Breach %")
    )
    fig_heat = apply_chart_theme(fig_heat, title="Cross-Segment SLA Failure Risk Intensity (%)")
    st.plotly_chart(fig_heat, use_container_width=True)
