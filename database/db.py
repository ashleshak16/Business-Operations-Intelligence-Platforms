"""
OpsIntel - Database Layer
SQLite-backed analytics store with pre-built SQL views.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "opsIntel.db")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db(df: pd.DataFrame):
    """Load DataFrame into SQLite and create analytical views."""
    conn = get_connection()
    df.to_sql("orders", conn, if_exists="replace", index=False)

    conn.executescript("""
        -- SLA Summary View
        CREATE VIEW IF NOT EXISTS vw_sla_summary AS
        SELECT
            region,
            warehouse,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) AS breached_orders,
            ROUND(SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS breach_pct,
            ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
            ROUND(AVG(packing_time_hrs), 2) AS avg_packing_hrs
        FROM orders
        WHERE status = 'Delivered'
        GROUP BY region, warehouse;

        -- Revenue Summary View
        CREATE VIEW IF NOT EXISTS vw_revenue_summary AS
        SELECT
            order_month,
            region,
            category,
            SUM(revenue) AS total_revenue,
            COUNT(*) AS total_orders,
            AVG(revenue) AS avg_order_value,
            SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) AS returns,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_txns
        FROM orders
        GROUP BY order_month, region, category;

        -- Warehouse Performance View
        CREATE VIEW IF NOT EXISTS vw_warehouse_perf AS
        SELECT
            warehouse,
            region,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS delivered,
            SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) AS sla_breaches,
            ROUND(AVG(packing_time_hrs), 2) AS avg_packing_hrs,
            ROUND(AVG(csat_score), 2) AS avg_csat,
            ROUND(AVG(delivery_days), 2) AS avg_delivery_days
        FROM orders
        GROUP BY warehouse, region;

        -- Payment & Failure View
        CREATE VIEW IF NOT EXISTS vw_payment_analysis AS
        SELECT
            payment_method,
            COUNT(*) AS total_txns,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_txns,
            ROUND(SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct,
            SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders,
            ROUND(AVG(fraud_risk_score), 1) AS avg_fraud_risk,
            SUM(revenue) AS total_revenue
        FROM orders
        GROUP BY payment_method;
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized with analytical views.")

def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df
