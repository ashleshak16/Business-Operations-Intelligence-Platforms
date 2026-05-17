import streamlit as st
import os

st.set_page_config(
    page_title="OpsIntel | Business Operations Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.helpers import load_custom_css
load_custom_css()

st.title("Business Operations Intelligence Platform")

st.markdown("""
### Enterprise Decision Support & Analytics

Welcome to **OpsIntel**, the centralized enterprise operations reporting platform. This decision-support system provides Product Analysts, Business Analysts, and SAP Support teams with robust data visualizations, SLA monitoring, and transaction reconciliations to drive operational efficiency.

### System Modules
Use the sidebar navigation to access specialized reporting dashboards:

1. **Executive Overview**: A unified executive summary of corporate key performance indicators, regional distributions, and high-level health.
2. **Order Operations Analytics**: Deep-dive reporting on order lifecycle volumes, peak transaction hours, and category cancellation rates.
3. **SLA & Fulfillment Monitoring**: Rigorous auditing of service level agreement compliance, shipping partner performance, and transit cycle bottlenecks.
4. **Returns & Transaction Analysis**: Reconciliation of transaction failure pathways, refund behavior patterns, and customer segment risk profiling.
5. **Warehouse Performance Analytics**: Comparative throughput auditing and composite efficiency modeling across regional fulfillment centers.
6. **Operational Reporting**: Custom query builders, exportable operational findings, and recommended corporate action plans.

---
*Classification: Internal Operations | Decision Support Systems | Enterprise Analytics*
""")

# Setup DB if not exists
db_path = os.path.join(os.path.dirname(__file__), "data", "opsIntel.db")
csv_path = os.path.join(os.path.dirname(__file__), "data", "orders.csv")

if not os.path.exists(db_path):
    st.warning("Operations database not initialized. Conducting master data ingestion... Please stand by.")
    with st.spinner("Processing master data logs (55,000+ transaction lines)..."):
        import sys
        sys.path.append(os.path.dirname(__file__))
        from data.generate_data import generate_data
        from database.db import init_db
        
        df = generate_data()
        init_db(df)
        st.success("Master database populated. Re-initiating interface.")
        st.rerun()
