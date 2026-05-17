import streamlit as st
import pandas as pd
from database.db import run_query

def generate_insights(df_context=None, module="Executive"):
    """
    Simulates an AI-based Business Insights engine.
    In a real system, this could call an LLM with aggregated data context.
    For this demo, we generate rule-based dynamic insights from the DB.
    """
    insights = []
    
    if module == "Executive":
        # Check SLA breaches
        sla_df = run_query("SELECT region, breach_pct FROM vw_sla_summary ORDER BY breach_pct DESC LIMIT 1")
        if not sla_df.empty:
            worst_region = sla_df.iloc[0]['region']
            breach_val = sla_df.iloc[0]['breach_pct']
            if breach_val > 15:
                insights.append(f"⚠️ **SLA Alert:** Region {worst_region} shows a highly elevated SLA breach rate of {breach_val}%. Investigate logistics partners immediately.")
            else:
                insights.append(f"✅ **SLA Status:** All regions maintaining acceptable SLA compliance. {worst_region} has the highest breach rate at {breach_val}%.")
                
        # Check Categories
        cat_df = run_query("SELECT category, SUM(CASE WHEN status='Returned' THEN 1 ELSE 0 END)*100.0/COUNT(*) as ret_rate FROM orders GROUP BY category ORDER BY ret_rate DESC LIMIT 1")
        if not cat_df.empty:
            worst_cat = cat_df.iloc[0]['category']
            ret_rate = cat_df.iloc[0]['ret_rate']
            insights.append(f"📉 **Returns Intelligence:** {worst_cat} category has the highest return rate at {ret_rate:.1f}%. Consider updating product descriptions or quality checks.")
            
        # Overall Revenue
        rev_df = run_query("SELECT SUM(revenue) as total_rev FROM orders")
        if not rev_df.empty:
            rev = rev_df.iloc[0]['total_rev'] / 1000000
            insights.append(f"💰 **Revenue Benchmark:** Platform has generated ₹{rev:.2f}M in total realized revenue over the tracked period.")

    elif module == "SLA":
        wh_df = run_query("SELECT warehouse, avg_packing_hrs FROM vw_warehouse_perf ORDER BY avg_packing_hrs DESC LIMIT 1")
        if not wh_df.empty:
            worst_wh = wh_df.iloc[0]['warehouse']
            hrs = wh_df.iloc[0]['avg_packing_hrs']
            insights.append(f"⏳ **Bottleneck Detected:** Warehouse {worst_wh} contributes significantly to delays with an average packing time of {hrs} hours.")
            
        partner_df = run_query("SELECT shipping_partner, SUM(CASE WHEN sla_breached=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) as breach_rate FROM orders WHERE status='Delivered' GROUP BY shipping_partner ORDER BY breach_rate DESC LIMIT 1")
        if not partner_df.empty:
            worst_partner = partner_df.iloc[0]['shipping_partner']
            brate = partner_df.iloc[0]['breach_rate']
            insights.append(f"🚚 **Logistics Risk:** {worst_partner} has the highest SLA breach rate at {brate:.1f}%. Re-route critical shipments if possible.")

    elif module == "Returns":
        pay_df = run_query("SELECT payment_method, failure_rate_pct, returned_orders FROM vw_payment_analysis ORDER BY failure_rate_pct DESC LIMIT 1")
        if not pay_df.empty:
            worst_pay = pay_df.iloc[0]['payment_method']
            frate = pay_df.iloc[0]['failure_rate_pct']
            insights.append(f"💳 **Transaction Risk:** {worst_pay} orders show higher failure probability ({frate}%).")
            
        cod_df = run_query("SELECT payment_method, returned_orders*100.0/total_txns as ret_rate FROM vw_payment_analysis WHERE payment_method='COD'")
        if not cod_df.empty:
            cod_rate = cod_df.iloc[0]['ret_rate']
            insights.append(f"📦 **COD Behavior:** Cash on Delivery orders have a return rate of {cod_rate:.1f}%. Implement stricter COD verification for high-value items.")

    return insights
