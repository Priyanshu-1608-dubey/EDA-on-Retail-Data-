import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ===========================
# 1. APP CONFIGURATION (PREMIUM UI)
# ===========================
st.set_page_config(
    page_title="Sales Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to hide default headers and make it look like a native app
st.markdown("""
    <style>
    .main {
        background-color: #FFFFFF;
    }
    .block-container {
        padding-top: 2rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #0068C9;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Enterprise Sales Dashboard")
st.markdown("### Real-time Data Analysis & Insights")
st.markdown("---")

# ===========================
# 2. LOAD DATA (MEMORY-EFFICIENT CHUNKED APPROACH)
# ===========================

@st.cache_data
def load_support_data():
    """Load product and city lookup tables once (small, cacheable)."""
    try:
        products = pd.read_csv("product_hierarchy.csv")
        cities = pd.read_csv("store_cities.csv")
        return products, cities
    except FileNotFoundError as e:
        st.error(f"❌ File not found: {e}. Please ensure 'product_hierarchy.csv' and 'store_cities.csv' are in the folder.")
        st.stop()

def load_sales_chunked(chunksize=100000):
    """Load sales data in chunks without caching (to avoid MemoryError).
    
    Returns aggregated stats and a sample of merged rows for display.
    Shows progress bar during loading.
    """
    try:
        products, cities = load_support_data()
        products_dict = dict(zip(products["product_id"], products.get("product_name", products.columns[1])))
        cities_dict = dict(zip(cities["store_id"], cities.get("city", cities.columns[1])))
        
        # Progress bar and status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Accumulate aggregates and sample rows
        agg_data = {
            "total_revenue": 0,
            "total_transactions": 0,
            "min_date": None,
            "max_date": None,
            "product_revenue": {},
            "city_revenue": {},
            "dates": []
        }
        sample_rows = []
        chunk_count = 0
        
        for chunk in pd.read_csv("sales.csv", chunksize=chunksize, low_memory=False):
            chunk_count += 1
            status_text.text(f"⏳ Processing chunk {chunk_count}... ({len(chunk)} rows)")
            progress_bar.progress(min(chunk_count * 0.1, 0.9))  # Cap at 90% until done
            
            # Clean chunk
            chunk.drop_duplicates(inplace=True)
            chunk.fillna(0, inplace=True)
            
            if "date" in chunk.columns:
                chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
                agg_data["dates"].extend(chunk["date"].dropna().tolist())
            
            if "revenue" in chunk.columns:
                agg_data["total_revenue"] += chunk["revenue"].sum()
            
            agg_data["total_transactions"] += len(chunk)
            
            # Aggregate by product
            if "product_id" in chunk.columns and "revenue" in chunk.columns:
                for pid, rev in chunk.groupby("product_id")["revenue"].sum().items():
                    prod_name = products_dict.get(pid, f"Product {pid}")
                    agg_data["product_revenue"][prod_name] = agg_data["product_revenue"].get(prod_name, 0) + rev
            
            # Aggregate by city
            if "store_id" in chunk.columns and "revenue" in chunk.columns:
                for sid, rev in chunk.groupby("store_id")["revenue"].sum().items():
                    city_name = cities_dict.get(sid, f"Store {sid}")
                    agg_data["city_revenue"][city_name] = agg_data["city_revenue"].get(city_name, 0) + rev
            
            # Keep a sample for raw data display (only first few chunks)
            if len(sample_rows) < 3:  # Reduced: 3 chunks × 100k = up to 300k rows
                chunk_merge = chunk.copy()
                if "product_id" in chunk_merge.columns:
                    chunk_merge["product_name"] = chunk_merge["product_id"].map(products_dict)
                if "store_id" in chunk_merge.columns:
                    chunk_merge["city"] = chunk_merge["store_id"].map(cities_dict)
                sample_rows.append(chunk_merge)
        
        if not sample_rows:
            st.error("❌ No data found in sales.csv")
            st.stop()
        
        sample_df = pd.concat(sample_rows, ignore_index=True).iloc[:50000]  # Cap sample at 50k rows
        del sample_rows  # Free memory
        
        # Compute date range
        if agg_data["dates"]:
            agg_data["min_date"] = min(agg_data["dates"])
            agg_data["max_date"] = max(agg_data["dates"])
            agg_data["dates"] = []  # Clear to save memory
        
        progress_bar.progress(1.0)
        status_text.text("✅ Data loaded successfully!")
        
        return agg_data, sample_df, products, cities
        
    except FileNotFoundError as e:
        st.error(f"❌ File not found: {e}. Please ensure 'sales.csv' is in the folder.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.stop()

# Load the data
agg_data, sample_data, products_raw, cities_raw = load_sales_chunked()
total_revenue = agg_data["total_revenue"]
total_sales_count = agg_data["total_transactions"]
avg_ticket = total_revenue / total_sales_count if total_sales_count > 0 else 0
top_product = max(agg_data["product_revenue"].items(), key=lambda x: x[1])[0] if agg_data["product_revenue"] else "N/A"
min_date = agg_data.get("min_date")
max_date = agg_data.get("max_date")

# Mock filtered_data for later use (sidebar filtering will work on sample)
filtered_data = sample_data
if min_date and max_date and "date" in filtered_data.columns:
    filtered_data["date"] = pd.to_datetime(filtered_data["date"], errors="coerce")
else:
    st.warning("Date column not found or could not be parsed.")

# ===========================
# 3. SIDEBAR CONTROLS
# ===========================

with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    
    st.info(f"📊 Showing sample of **{len(filtered_data)}** rows from {total_sales_count:,} total transactions.")
    
    # Date Filter
    if min_date and max_date and "date" in filtered_data.columns:
        start_date, end_date = st.date_input(
            "Select Date Range",
            value=(min_date.date() if hasattr(min_date, 'date') else min_date, 
                   max_date.date() if hasattr(max_date, 'date') else max_date),
            min_value=min_date.date() if hasattr(min_date, 'date') else min_date,
            max_value=max_date.date() if hasattr(max_date, 'date') else max_date
        )
        
        # Apply Filter to sample
        filtered_data = sample_data[
            (sample_data["date"].dt.date >= start_date) & 
            (sample_data["date"].dt.date <= end_date)
        ].copy()
    else:
        st.warning("Date column not found or could not be parsed. Showing all sample rows.")

# ===========================
# 4. KEY PERFORMANCE INDICATORS (KPIs)
# ===========================

# Display aggregated metrics from full dataset
col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
col2.metric("🧾 Total Transactions", f"{total_sales_count:,}")
col3.metric("📉 Avg. Ticket Size", f"${avg_ticket:,.2f}")
col4.metric("🏆 Top Product", str(top_product))

st.markdown("---")

# ===========================
# 5. VISUALIZATION TABS
# ===========================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Sales Trends", 
    "📦 Product Analysis", 
    "🌍 Regional Performance", 
    "🔍 Data Explorer",
    "💡 Recommendations"
])

# --- TAB 1: TIME SERIES ---
with tab1:
    st.subheader("Revenue Timeline (from Full Dataset)")
    if "date" in filtered_data.columns and len(filtered_data) > 0:
        daily_sales = filtered_data.groupby(filtered_data["date"].dt.date)["revenue"].sum()
        st.line_chart(daily_sales, color="#0068C9")
    else:
        st.write("No date data available.")

# --- TAB 2: PRODUCTS ---
with tab2:
    st.subheader("Top 10 Best Selling Products (Full Dataset)")
    
    if agg_data["product_revenue"]:
        top_products_series = pd.Series(agg_data["product_revenue"]).nlargest(10)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=top_products_series.values, y=top_products_series.index, palette="viridis", ax=ax)
        ax.set_xlabel("Revenue")
        ax.set_ylabel("")
        st.pyplot(fig)
    else:
        st.write("No product data available.")

# --- TAB 3: CITIES ---
with tab3:
    st.subheader("City-wise Revenue Distribution (Full Dataset)")
    
    if agg_data["city_revenue"]:
        city_sales = pd.Series(agg_data["city_revenue"]).sort_values(ascending=False)
        
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        sns.barplot(x=city_sales.index, y=city_sales.values, palette="magma", ax=ax2)
        plt.xticks(rotation=45)
        ax2.set_ylabel("Revenue")
        ax2.set_xlabel("City")
        st.pyplot(fig2)
    else:
        st.write("No city data available.")

# --- TAB 4: DATA EXPLORER (HEATMAP + RAW DATA) ---
with tab4:
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        st.subheader("Correlation Matrix (Sample)")
        # Filter only numeric columns for correlation
        if len(filtered_data) > 0:
            numeric_df = filtered_data.select_dtypes(include=[np.number])
            if not numeric_df.empty and numeric_df.shape[1] > 1:
                fig3, ax3 = plt.subplots(figsize=(6, 5))
                sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax3, fmt=".2f")
                st.pyplot(fig3)
            else:
                st.write("Not enough numeric columns for correlation.")
        else:
            st.write("No data available.")
        
    with col_d2:
        st.subheader("Sample Data Preview")
        if len(filtered_data) > 0:
            st.dataframe(filtered_data.head(100), height=400)
            
            with st.expander("View Basic Statistics"):
                st.write(filtered_data.describe())
        else:
            st.write("No data to display.")

# --- TAB 5: RECOMMENDATIONS ---
with tab5:
    st.subheader("🤖 Automated Business Insights")
    
    st.markdown(f"""
    Based on the analysis of **{len(filtered_data)}** transactions:
    
    1.  **Inventory Management:** Ensure high stock levels for **{top_product}**, as it is the primary revenue driver.
    2.  **Regional Strategy:** Focus marketing budget on top performing cities visible in the Regional tab.
    3.  **Performance Review:** Identify products with near-zero revenue in the raw data and consider liquidation.
    4.  **Seasonal Planning:** Use the Sales Trends tab to identify peak dates and prepare logicstics in advance.
    """)