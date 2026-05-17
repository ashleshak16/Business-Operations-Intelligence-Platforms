import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import run_query
from utils.helpers import load_custom_css, get_base_filters, build_where_clause, apply_chart_theme

st.set_page_config(page_title="Order Operations Analytics | OpsIntel", layout="wide")
load_custom_css()

st.title("Order Operations Analytics")
st.markdown("### Operational Lifecycles, Processing Cycles, and Cancellation Analytics")

# Filters
st.markdown("#### Filter Profile")
sel_region, sel_category, sel_month = get_base_filters()
where_clause = build_where_clause(sel_region, sel_category, sel_month)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Lifecycle Status Split")
    status_df = run_query(f"SELECT status, COUNT(*) as count FROM orders {where_clause} GROUP BY status")
    if not status_df.empty:
        fig_status = px.pie(
            status_df, names='status', values='count', hole=0.5,
            color='status',
            color_discrete_map={
                'Delivered': '#16A34A',
                'Cancelled': '#DC2626',
                'Returned': '#D97706',
                'Processing': '#2563EB',
                'Shipped': '#7C3AED',
                'Failed': '#475569'
            }
        )
        fig_status = apply_chart_theme(fig_status)
        st.plotly_chart(fig_status, use_container_width=True)

with col2:
    st.markdown("### Hourly Transaction Density")
    hour_df = run_query(f"SELECT order_hour, COUNT(*) as count FROM orders {where_clause} GROUP BY order_hour ORDER BY order_hour")
    if not hour_df.empty:
        fig_hour = px.bar(
            hour_df, x='order_hour', y='count',
            labels={'order_hour': 'Hour of Day (24-Hour Clock)', 'count': 'Transaction Count'},
            color_discrete_sequence=['#3B82F6']
        )
        fig_hour = apply_chart_theme(fig_hour)
        st.plotly_chart(fig_hour, use_container_width=True)

st.markdown("### Operational Attrition Rates (Cancellation & Return Split)")
cat_df = run_query(f"""
    SELECT 
        category, 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
        SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) as returned
    FROM orders {where_clause}
    GROUP BY category
    ORDER BY total DESC
""")
if not cat_df.empty:
    cat_df['Cancellation %'] = round((cat_df['cancelled'] / cat_df['total']) * 100, 2)
    cat_df['Return %'] = round((cat_df['returned'] / cat_df['total']) * 100, 2)
    
    fig_cat = px.bar(
        cat_df, x='category', y=['Cancellation %', 'Return %'], 
        barmode='group', 
        labels={'value': 'Percentage (%)', 'category': 'Product Category', 'variable': 'Operational State'},
        color_discrete_map={'Cancellation %': '#DC2626', 'Return %': '#D97706'}
    )
    fig_cat = apply_chart_theme(fig_cat)
    st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("### Live Operations Queue (In-Fulfillment Status)")
processing_df = run_query(f"""
    SELECT order_id AS [Order Reference], 
           order_date AS [Entry Date], 
           region AS [Target Region], 
           warehouse AS [Fulfillment Center], 
           category AS [Product Class], 
           total_amount AS [Value (INR)] 
    FROM orders 
    WHERE status = 'Processing' 
    LIMIT 10
""")
st.dataframe(processing_df, use_container_width=True, hide_index=True)
