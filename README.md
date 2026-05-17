# 📊 OpsIntel - E-commerce Operations Intelligence System

**OpsIntel** is a business-focused analytics and operations platform designed for Business Analysts, Product Analysts, Operations Analysts, and Data Analysts. It simulates and visualizes how enterprise e-commerce companies monitor operational efficiency, SLA performance, delivery operations, customer experience metrics, and transactional integrity.

Developed using **Python, Streamlit, SQL (SQLite), Pandas, and Plotly**, OpsIntel replicates a Power BI-style dashboard experience to enable data-driven decision-making and operational optimization.

---

## 🚀 Key Features & Modules

### 1. 📈 Executive KPI Dashboard
Provides a premium, C-level overview of core business and operational health:
*   **KPI Cards**: Total Orders, Total Revenue, Order Success Rate, Customer Satisfaction (CSAT), SLA Compliance, Return Rate, Failed Transactions, and Avg Delivery Time.
*   **Trend Visualizations**: Monthly revenue charts and interactive pie charts showing order distributions by region.
*   **Filter Engine**: Slice and dice all KPIs and charts by Region, Category, and Order Month.

### 2. 📦 Order Operations Analytics
Deep dive into order lifecycles and operational trends:
*   **Order Status Split**: Interactive pie charts detailing orders across Delivered, Shipped, Processing, Cancelled, Returned, and Failed states.
*   **Time-Based Analysis**: Hourly order distribution to identify peak demand times.
*   **Cancellation & Return Analysis**: Detailed side-by-side comparison of cancellation and return rates by product category.
*   **Live Processing Queue**: A real-time view of orders currently in "Processing" state for operations managers.

### 3. ⏱️ SLA Monitoring Dashboard
Tracks fulfillment delays, logistics performance, and delivery risks:
*   **Logistics Benchmarking**: Bubble charts analyzing shipping volumes vs. average delivery times across partners (BlueDart, Delhivery, DTDC, FedEx, etc.).
*   **SLA Compliance Heatmap**: A cross-matrix heatmap of SLA breach rates by Region and Category to highlight bottleneck intersections.
*   **Breach Metrics**: Total breached orders, SLA compliance rate, and average delivery times.

### 4. 💳 Returns & Transaction Intelligence
Monitors failed transactions, refund trends, and fraud risk indicators:
*   **Fraud Risk Profiling**: Tracks average fraud risk score across payment methods and user segments.
*   **COD vs Prepaid Analysis**: Side-by-side comparison showing COD return rates vs. Prepaid.
*   **Root Cause Treemaps**: Breakdown of payment failure reasons (e.g., Timeout, CVV Mismatch, OTP Failure).
*   **High-Return Drill-Down**: Interactive Sunburst chart mapping return rates from Product Category down to Region.
*   **Downloadable Reports**: Generate and download a filtered CSV report of recent failures/returns.

### 5. 🏭 Warehouse Performance Analytics
Compares throughput, packing speeds, and operational loads across fulfillment centers:
*   **Composite Efficiency Score**: Calculates a custom, multi-weighted efficiency score (0-100) for each center based on delivery speed, CSAT, packing time, and SLA breaches.
*   **Fulfillment Speed Charts**: Shows average packing times (hours) across warehouses.
*   **Regional Radar Charts**: Polar charts visualising how regions perform against key indicators (Efficiency, CSAT, Packing Speed, Delivery Rate, SLA Compliance).

### 🧠 AI Business Insights Engine
An automated, rule-based diagnostic engine providing C-level intelligence:
*   Dynamically identifies which warehouse drives the most SLA breaches (e.g., *“Warehouse W4 contributes to 32% of SLA breaches”*).
*   Highlights systemic issues (e.g., *“COD orders show higher return probability”*, *“Region South shows rising fulfillment delays”*).
*   Provides actionable operational recommendations for each diagnostic alert.

---

## 🛠️ Tech Stack & Database Architecture
*   **Frontend**: Streamlit (with corporate dark-mode/glassmorphic custom CSS styling)
*   **Data Science**: Pandas, NumPy
*   **Visualization**: Plotly Express, Plotly Graph Objects
*   **Database**: SQLite with structured SQL Views:
    *   `vw_sla_summary`: Computes regional delivery and packing statistics.
    *   `vw_revenue_summary`: Monthly aggregated financials by category.
    *   `vw_warehouse_perf`: Warehouse throughput, CSAT, and breach statistics.
    *   `vw_payment_analysis`: Payment method failure and fraud-risk profiling.

---

## 📂 Project Structure
```directory
├── app.py                     # Main application landing page
├── requirements.txt           # Project dependencies
├── components/
│   └── insights_engine.py     # AI Business Insights logic
├── data/
│   ├── generate_data.py       # Realistic 55,000+ orders generator
│   ├── orders.csv             # Generated CSV dataset
│   └── opsIntel.db            # SQLite database file
├── database/
│   └── db.py                  # SQLite configuration & SQL views
├── pages/                     # Multi-page dashboards
│   ├── 1_Executive_KPI_Dashboard.py
│   ├── 2_Order_Operations_Analytics.py
│   ├── 3_SLA_Monitoring_Dashboard.py
│   ├── 4_Returns_Transaction_Intelligence.py
│   ├── 5_Warehouse_Performance.py
│   └── 6_AI_Business_Insights.py
└── utils/
    └── helpers.py             # Shared UI widgets and filters
```

---

## 🚀 How to Run locally

### 1. Set Up Virtual Environment (Recommended)
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Data & Initialize Database (Completed)
The startup process pre-generates **55,000 orders** and sets up the SQLite views.
```bash
python -c "import sys; sys.path.append('.'); from data.generate_data import generate_data; from database.db import init_db; df = generate_data(); init_db(df)"
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.
