import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import run_query
from utils.helpers import load_custom_css, render_kpi, apply_chart_theme, render_observation

st.set_page_config(page_title="Warehouse Performance Analytics | OpsIntel", layout="wide")
load_custom_css()

st.title("Warehouse Performance Analytics")
st.markdown("### Fulfillment Operations Throughput, Packing Speed cycles, and Regional Efficiency Modeling")

st.markdown("---")

# Warehouse Performance Metrics Calculation
wh_df = run_query("SELECT * FROM vw_warehouse_perf ORDER BY total_orders DESC")

if wh_df.empty:
    st.warning("No warehouse logistical records located.")
    st.stop()

# Compute derived metrics
wh_df['delivery_rate'] = round((wh_df['delivered'] / wh_df['total_orders']) * 100, 1)
wh_df['breach_rate'] = round((wh_df['sla_breaches'] / wh_df['total_orders']) * 100, 1)

# Weighted Efficiency Score (Enterprise Formula)
# Incorporates: Delivery Rate (30%), SLA Compliance (25%), Customer Rating (25%), Packing Speed (20%)
wh_df['efficiency_score'] = round(
    (wh_df['delivery_rate'] * 0.30) +
    ((100 - wh_df['breach_rate']) * 0.25) +
    (wh_df['avg_csat'] * 20 * 0.25) +
    ((10 - wh_df['avg_packing_hrs'].clip(upper=10)) * 10 * 0.20), 1
)

best_wh = wh_df.loc[wh_df['efficiency_score'].idxmax()]
worst_wh = wh_df.loc[wh_df['efficiency_score'].idxmin()]
avg_packing = round(wh_df['avg_packing_hrs'].mean(), 2)

# Business Observations
st.markdown("## KPI Insights & Warehouse Bottlenecks")

if worst_wh['avg_packing_hrs'] > 6.0:
    render_observation(
        title="Processing Bottleneck Detected in Fulfillment Networks",
        text=f"Fulfillment Center {worst_wh['warehouse']} shows a significant packing latency bottleneck, with operations taking an average of {worst_wh['avg_packing_hrs']} hours per line item.",
        action_plan=f"Audit shift assignments, packing station ergonomics, and sorting queue protocols at {worst_wh['warehouse']}.",
        status="critical"
    )
else:
    render_observation(
        title="Warehouse Dispatch Performance Stabilized",
        text="All primary regional warehouses maintain mean packing lead times under acceptable thresholds.",
        action_plan="Continue tracking peak-hour dispatch delays to prevent future sorting backlogs.",
        status="success"
    )

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi("Top Performing Center", best_wh['warehouse'], f"Efficiency: {best_wh['efficiency_score']}/100", "success")
with col2:
    render_kpi("Underperforming Center", worst_wh['warehouse'], f"Efficiency: {worst_wh['efficiency_score']}/100", "critical")
with col3:
    render_kpi("Network Mean Packing Speed", f"{avg_packing} Hours", "Mean duration inside warehouse gates", "default")
with col4:
    render_kpi("Total Fulfillment Volume", f"{wh_df['total_orders'].sum():,}", "Total units processed", "primary")

st.markdown("---")

# Comparative Dashboard
st.markdown("### Comparative Performance Diagnostics")
col_c1, col_c2 = st.columns(2)

with col_c1:
    fig_eff = px.bar(
        wh_df.sort_values('efficiency_score', ascending=True),
        x='efficiency_score', y='warehouse', orientation='h',
        labels={'efficiency_score': 'Composite Efficiency Index (0-100)', 'warehouse': 'Fulfillment Center'},
        color='efficiency_score', color_continuous_scale='Greens',
        text='efficiency_score'
    )
    fig_eff.update_traces(texttemplate='%{text}', textposition='outside')
    fig_eff = apply_chart_theme(fig_eff, title="Fulfillment Center Efficiency Index Ranking")
    fig_eff.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_eff, use_container_width=True)

with col_c2:
    fig_pack = px.bar(
        wh_df.sort_values('avg_packing_hrs', ascending=False),
        x='avg_packing_hrs', y='warehouse', orientation='h',
        labels={'avg_packing_hrs': 'Mean Packing Speed (Hours)', 'warehouse': 'Fulfillment Center'},
        color='avg_packing_hrs', color_continuous_scale='OrRd',
        text='avg_packing_hrs'
    )
    fig_pack.update_traces(texttemplate='%{text:.2f}h', textposition='outside')
    fig_pack = apply_chart_theme(fig_pack, title="Fulfillment Center Dispatch Latency (Mean Hours)")
    fig_pack.update_layout(yaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig_pack, use_container_width=True)

# Throughput vs CSAT bubble
st.markdown("### Operational Load Density vs. Customer Satisfaction")
fig_bubble = px.scatter(
    wh_df, x='total_orders', y='avg_csat',
    size='sla_breaches', color='region', hover_name='warehouse',
    labels={'total_orders': 'Fulfillment Throughput Volume (Units)', 'avg_csat': 'Customer Satisfaction Index (CSAT)', 'region': 'Operating Region'}
)
fig_bubble = apply_chart_theme(fig_bubble, title="Fulfillment Load Correlation: Throughput vs. CSAT Index (Bubble size = SLA Breaches)")
st.plotly_chart(fig_bubble, use_container_width=True)

# Region Radar
st.markdown("### Regional Operational Radar Profile")
region_df = wh_df.groupby('region').agg({
    'total_orders': 'sum',
    'delivered': 'sum',
    'sla_breaches': 'sum',
    'avg_packing_hrs': 'mean',
    'avg_csat': 'mean',
    'efficiency_score': 'mean'
}).reset_index().round(2)

fig_radar = go.Figure()
for _, row in region_df.iterrows():
    fig_radar.add_trace(go.Scatterpolar(
        r=[
            row['efficiency_score'], 
            row['avg_csat'] * 20, 
            (100 - row['avg_packing_hrs'] * 10),
            (row['delivered'] / row['total_orders']) * 100, 
            100 - (row['sla_breaches'] / row['total_orders']) * 100
        ],
        theta=['Composite Efficiency', 'CSAT Performance', 'Dispatch Acceleration', 'Fulfillment Rate', 'SLA Adherence'],
        fill='toself',
        name=row['region']
    ))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font_family='Inter',
    legend=dict(orientation="h", y=-0.15)
)
st.plotly_chart(fig_radar, use_container_width=True)

# Detailed data Table
st.markdown("### Fulfillment Operations Detail Ledger")
display_df = wh_df[['warehouse', 'region', 'total_orders', 'delivered', 'delivery_rate',
                     'sla_breaches', 'breach_rate', 'avg_packing_hrs', 'avg_csat', 'efficiency_score']]
display_df.columns = ['Fulfillment Center', 'Region Profile', 'Throughput Units', 'Successfully Delivered', 'Fulfillment Rate (%)',
                       'SLA Breach Lines', 'Breach Adherence Deficit (%)', 'Mean Packing Latency (hrs)', 'Mean CSAT Score', 'Composite Efficiency Rating']
st.dataframe(display_df.sort_values('Composite Efficiency Rating', ascending=False), use_container_width=True, hide_index=True)
