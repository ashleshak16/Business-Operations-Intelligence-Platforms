"""
OpsIntel - Enterprise Data Generator
Generates realistic 50,000+ order dataset simulating real e-commerce operations.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
NUM_ORDERS = 55000
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2025, 3, 31)

REGIONS = ["North", "South", "East", "West", "Central"]

WAREHOUSES = {
    "North":   ["W1-Delhi", "W2-Chandigarh"],
    "South":   ["W3-Bangalore", "W4-Chennai"],
    "East":    ["W5-Kolkata", "W6-Bhubaneswar"],
    "West":    ["W7-Mumbai", "W8-Ahmedabad"],
    "Central": ["W9-Hyderabad", "W10-Nagpur"],
}

SHIPPING_PARTNERS = ["BlueDart", "Delhivery", "DTDC", "FedEx", "Ecom Express", "XpressBees", "Amazon Logistics"]

CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Books", "Sports", "Beauty", "Grocery", "Toys", "Automotive", "Health"]

PAYMENT_METHODS = ["COD", "Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet", "EMI"]

ORDER_STATUSES = ["Delivered", "Cancelled", "Returned", "Processing", "Shipped", "Failed"]

RETURN_REASONS = ["Wrong Product", "Defective Item", "Not as Described", "Changed Mind", "Better Price Found", "Damaged in Transit", "Duplicate Order"]

FAILURE_REASONS = ["Payment Gateway Timeout", "Insufficient Funds", "Card Declined", "Bank Server Error", "CVV Mismatch", "Expired Card", "OTP Failure", "Network Error"]

CUSTOMER_SEGMENTS = ["Premium", "Standard", "New", "Loyal", "At-Risk", "Dormant"]

CITY_BY_REGION = {
    "North":   ["Delhi", "Jaipur", "Lucknow", "Agra", "Amritsar", "Chandigarh", "Meerut"],
    "South":   ["Bangalore", "Chennai", "Hyderabad", "Kochi", "Mysore", "Coimbatore", "Vizag"],
    "East":    ["Kolkata", "Bhubaneswar", "Patna", "Guwahati", "Ranchi", "Cuttack"],
    "West":    ["Mumbai", "Pune", "Ahmedabad", "Surat", "Vadodara", "Nashik", "Rajkot"],
    "Central": ["Nagpur", "Bhopal", "Indore", "Raipur", "Jabalpur", "Gwalior"],
}

# ─────────────────────────────────────────────
#  WEIGHT CONFIGS for realistic distributions
# ─────────────────────────────────────────────
STATUS_WEIGHTS = [0.72, 0.08, 0.07, 0.05, 0.05, 0.03]  # Delivered dominates

CATEGORY_WEIGHTS = [0.18, 0.20, 0.12, 0.06, 0.07, 0.08, 0.10, 0.05, 0.06, 0.08]

PAYMENT_WEIGHTS = [0.25, 0.15, 0.14, 0.28, 0.07, 0.07, 0.04]

SEGMENT_WEIGHTS = [0.12, 0.35, 0.20, 0.18, 0.10, 0.05]

PARTNER_WEIGHTS = [0.14, 0.22, 0.10, 0.09, 0.15, 0.16, 0.14]

# ─────────────────────────────────────────────
#  PRICE RANGES per category
# ─────────────────────────────────────────────
PRICE_RANGES = {
    "Electronics":    (2000, 85000),
    "Fashion":        (299,  5999),
    "Home & Kitchen": (399,  12000),
    "Books":          (99,   999),
    "Sports":         (499,  15000),
    "Beauty":         (199,  3999),
    "Grocery":        (49,   2999),
    "Toys":           (199,  4999),
    "Automotive":     (299,  25000),
    "Health":         (149,  8999),
}

# ─────────────────────────────────────────────
#  SLA THRESHOLDS (days by region + partner)
# ─────────────────────────────────────────────
SLA_STANDARD = {
    "North": 3, "South": 4, "East": 5, "West": 3, "Central": 4
}

def random_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def generate_order_id(i):
    return f"ORD-{2024100000 + i}"

def generate_customer_id(i):
    return f"CUST-{random.randint(100000, 999999)}"

def get_delivery_days(region, status, partner):
    base = SLA_STANDARD.get(region, 4)
    if status == "Delivered":
        # 20% chance of SLA breach
        if random.random() < 0.20:
            return base + random.randint(1, 6)
        return max(1, base + random.randint(-1, 1))
    elif status == "Shipped":
        return base + random.randint(0, 3)
    else:
        return None

def get_packing_time(warehouse, status):
    # W4-Chennai and W8-Ahmedabad underperform
    if warehouse in ["W4-Chennai", "W8-Ahmedabad", "W10-Nagpur"]:
        return round(random.uniform(3.5, 9.0), 2)
    return round(random.uniform(0.5, 4.0), 2)

def generate_data():
    print(f"🚀 Generating {NUM_ORDERS:,} orders...")

    orders = []

    for i in range(NUM_ORDERS):
        region    = random.choices(REGIONS, weights=[0.22, 0.20, 0.15, 0.25, 0.18])[0]
        warehouse = random.choice(WAREHOUSES[region])
        city      = random.choice(CITY_BY_REGION[region])
        partner   = random.choices(SHIPPING_PARTNERS, weights=PARTNER_WEIGHTS)[0]
        category  = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
        payment   = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]
        status    = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS)[0]
        segment   = random.choices(CUSTOMER_SEGMENTS, weights=SEGMENT_WEIGHTS)[0]

        order_date = random_date(START_DATE, END_DATE)

        price_min, price_max = PRICE_RANGES[category]
        unit_price = round(random.uniform(price_min, price_max), 2)
        qty        = random.choices([1, 2, 3, 4, 5], weights=[0.55, 0.25, 0.10, 0.06, 0.04])[0]
        discount   = round(random.uniform(0, 0.35) * unit_price, 2)
        revenue    = round((unit_price * qty) - discount, 2)
        tax        = round(revenue * 0.18, 2)
        total_amount = round(revenue + tax, 2)

        delivery_days = get_delivery_days(region, status, partner)
        dispatch_date = order_date + timedelta(hours=random.randint(1, 24)) if status != "Failed" else None
        delivery_date = (order_date + timedelta(days=delivery_days)) if delivery_days and status == "Delivered" else None

        sla_days = SLA_STANDARD.get(region, 4)
        sla_breached = (delivery_days > sla_days) if delivery_days else False

        packing_time = get_packing_time(warehouse, status) if status not in ["Failed", "Cancelled"] else None

        return_reason    = random.choice(RETURN_REASONS) if status == "Returned" else None
        failure_reason   = random.choice(FAILURE_REASONS) if status == "Failed" else None

        # Customer satisfaction: lower for breached SLA, returns, fails
        if status == "Delivered" and not sla_breached:
            csat = round(random.uniform(3.5, 5.0), 1)
        elif sla_breached or status == "Returned":
            csat = round(random.uniform(1.5, 3.2), 1)
        elif status in ["Cancelled", "Failed"]:
            csat = round(random.uniform(1.0, 2.5), 1)
        else:
            csat = round(random.uniform(2.8, 4.2), 1)

        # Fraud risk score (higher for COD + high value + new segment)
        fraud_score = 0
        if payment == "COD": fraud_score += 30
        if total_amount > 20000: fraud_score += 25
        if segment == "New": fraud_score += 20
        if status == "Failed": fraud_score += 15
        fraud_score = min(100, fraud_score + random.randint(0, 10))

        orders.append({
            "order_id":         generate_order_id(i),
            "customer_id":      generate_customer_id(i),
            "order_date":       order_date.strftime("%Y-%m-%d"),
            "order_month":      order_date.strftime("%Y-%m"),
            "order_hour":       order_date.hour,
            "order_day_of_week": order_date.strftime("%A"),
            "region":           region,
            "city":             city,
            "warehouse":        warehouse,
            "shipping_partner": partner,
            "category":         category,
            "payment_method":   payment,
            "customer_segment": segment,
            "status":           status,
            "unit_price":       unit_price,
            "quantity":         qty,
            "discount":         discount,
            "revenue":          revenue,
            "tax":              tax,
            "total_amount":     total_amount,
            "delivery_days":    delivery_days,
            "sla_threshold_days": sla_days,
            "sla_breached":     sla_breached,
            "packing_time_hrs": packing_time,
            "dispatch_date":    dispatch_date.strftime("%Y-%m-%d") if dispatch_date else None,
            "delivery_date":    delivery_date.strftime("%Y-%m-%d") if delivery_date else None,
            "return_reason":    return_reason,
            "failure_reason":   failure_reason,
            "csat_score":       csat,
            "fraud_risk_score": fraud_score,
        })

        if (i + 1) % 10000 == 0:
            print(f"  ✅ {i+1:,} orders generated...")

    df = pd.DataFrame(orders)

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "orders.csv")
    df.to_csv(out_path, index=False)
    print(f"\n✅ Dataset saved → {out_path}")
    print(f"   Shape: {df.shape}")
    print(f"   Date range: {df['order_date'].min()} → {df['order_date'].max()}")
    print(f"   Total Revenue: ₹{df['revenue'].sum():,.0f}")
    print(f"   SLA Breach Rate: {df['sla_breached'].mean()*100:.1f}%")
    print(f"   Return Rate: {(df['status']=='Returned').mean()*100:.1f}%")
    return df

if __name__ == "__main__":
    generate_data()
