import streamlit as st
import pandas as pd
import os
from database.db import run_query

def load_custom_css():
    st.markdown("""
        <style>
            /* Enterprise Business Intelligence Styling (Power BI & SAP Analytics Cloud Inspired) */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                background-color: #F8FAFC;
                color: #1E293B;
            }
            .main {
                background-color: #F8FAFC;
                padding: 1.5rem;
            }
            h1 {
                font-size: 1.85rem !important;
                font-weight: 700 !important;
                color: #0F172A !important;
                border-bottom: 2px solid #E2E8F0;
                padding-bottom: 0.5rem;
                margin-bottom: 1.5rem !important;
            }
            h2 {
                font-size: 1.4rem !important;
                font-weight: 600 !important;
                color: #1E293B !important;
                margin-top: 1.5rem !important;
                margin-bottom: 1rem !important;
            }
            h3 {
                font-size: 1.1rem !important;
                font-weight: 600 !important;
                color: #334155 !important;
            }
            
            /* Professional Metric Card Design */
            .kpi-container {
                display: flex;
                flex-direction: column;
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 1.25rem;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
                margin-bottom: 1rem;
                position: relative;
                overflow: hidden;
            }
            .kpi-container::before {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background-color: #475569; /* Default neutral Slate */
            }
            .kpi-container.primary::before { background-color: #1E3A8A; } /* Navy */
            .kpi-container.success::before { background-color: #16A34A; } /* Success Green */
            .kpi-container.warning::before { background-color: #D97706; } /* Warning Amber */
            .kpi-container.critical::before { background-color: #DC2626; } /* Critical Red */
            
            .kpi-label {
                color: #64748B;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.25rem;
            }
            .kpi-value {
                color: #0F172A;
                font-size: 1.75rem;
                font-weight: 700;
                line-height: 1.1;
            }
            .kpi-subtext {
                color: #94A3B8;
                font-size: 0.7rem;
                margin-top: 0.25rem;
            }
            
            /* Business Observation Boards */
            .observation-card {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #3B82F6;
                padding: 1.25rem;
                border-radius: 6px;
                margin-bottom: 1rem;
            }
            .observation-card.critical { border-left-color: #DC2626; background-color: #FEF2F2; }
            .observation-card.warning { border-left-color: #D97706; background-color: #FFFBEB; }
            .observation-card.success { border-left-color: #16A34A; background-color: #F0FDF4; }
            
            .observation-title {
                font-weight: 600;
                font-size: 0.95rem;
                color: #0F172A;
                margin-bottom: 0.25rem;
            }
            .observation-text {
                font-size: 0.85rem;
                color: #334155;
                line-height: 1.5;
            }
            .observation-action {
                font-size: 0.8rem;
                color: #475569;
                margin-top: 0.5rem;
                border-top: 1px solid #F1F5F9;
                padding-top: 0.4rem;
                font-style: italic;
            }
            
            /* Corporate Table Styling */
            .dataframe {
                border-collapse: collapse;
                width: 100%;
                font-size: 0.85rem;
            }
            .dataframe th {
                background-color: #F1F5F9 !important;
                color: #1E293B !important;
                font-weight: 600 !important;
                text-align: left;
                padding: 10px !important;
            }
            .dataframe td {
                padding: 10px !important;
                border-bottom: 1px solid #E2E8F0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

def render_kpi(label, value, subtext="", status_class="default"):
    """
    Renders an enterprise SAP/PowerBI style metric card.
    status_class options: 'default', 'primary', 'success', 'warning', 'critical'
    """
    st.markdown(f"""
        <div class="kpi-container {status_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtext">{subtext}</div>
        </div>
    """, unsafe_allow_html=True)

def render_observation(title, text, action_plan=None, status="info"):
    """
    Renders professional Business Observations / Operational Highlights.
    """
    status_class = ""
    if status == "critical":
        status_class = "critical"
    elif status == "warning":
        status_class = "warning"
    elif status == "success":
        status_class = "success"
        
    action_html = f'<div class="observation-action"><strong>Recommended Action:</strong> {action_plan}</div>' if action_plan else ""
    
    st.markdown(f"""
        <div class="observation-card {status_class}">
            <div class="observation-title">{title}</div>
            <div class="observation-text">{text}</div>
            {action_html}
        </div>
    """, unsafe_allow_html=True)

def format_currency(val):
    if val >= 1_000_000_000:
        return f"INR {val/1_000_000_000:.2f} B"
    elif val >= 1_000_000:
        return f"INR {val/1_000_000:.2f} M"
    elif val >= 1_000:
        return f"INR {val/1_000:.1f} K"
    return f"INR {val:,.2f}"

def get_base_filters():
    col1, col2, col3 = st.columns(3)
    
    regions = run_query("SELECT DISTINCT region FROM orders")['region'].tolist()
    categories = run_query("SELECT DISTINCT category FROM orders")['category'].tolist()
    months = run_query("SELECT DISTINCT order_month FROM orders ORDER BY order_month DESC")['order_month'].tolist()
    
    with col1:
        sel_region = st.multiselect("Region Profile", sorted(regions), default=[])
    with col2:
        sel_category = st.multiselect("Product Category", sorted(categories), default=[])
    with col3:
        sel_month = st.multiselect("Reporting Month", sorted(months), default=[])
        
    return sel_region, sel_category, sel_month

def build_where_clause(regions, categories, months):
    clauses = []
    if regions:
        regions_str = "','".join(regions)
        clauses.append(f"region IN ('{regions_str}')")
    if categories:
        categories_str = "','".join(categories)
        clauses.append(f"category IN ('{categories_str}')")
    if months:
        months_str = "','".join(months)
        clauses.append(f"order_month IN ('{months_str}')")
        
    if clauses:
        return "WHERE " + " AND ".join(clauses)
    return ""

def apply_chart_theme(fig, title=None, height=350):
    fig.update_layout(
        title={
            'text': title,
            'y': 0.95,
            'x': 0.05,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'size': 14, 'color': '#0F172A', 'weight': 'bold'}
        } if title else None,
        height=height,
        margin=dict(l=30, r=20, t=50, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Inter',
        font_color='#475569',
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='#CBD5E1',
            linewidth=1,
            ticks='outside',
            tickfont=dict(size=10, color='#64748B'),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#E2E8F0',
            gridwidth=1,
            showline=False,
            showticklabels=True,
            tickfont=dict(size=10, color='#64748B'),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color='#475569')
        )
    )
    return fig
