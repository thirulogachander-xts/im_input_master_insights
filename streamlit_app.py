import streamlit as st
import pandas as pd
import plotly.express as px
from database import engine, SessionLocal, Base
from models import InputMaster
from data_loader import load_data
import os

# Initialize database
Base.metadata.create_all(bind=engine)

# Page Config
st.set_page_config(page_title="IM Insights Dashboard", layout="wide", page_icon="📈")

# Custom CSS for light green theme
st.markdown("""
    <style>
    .main {
        background-color: #F0FDF4;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        color: #22C55E;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to get data as DataFrame
def get_data_df():
    db = SessionLocal()
    try:
        query = db.query(InputMaster)
        df = pd.read_sql(query.statement, engine)
        return df
    finally:
        db.close()

# Initial Data Load
df = get_data_df()
if df.empty:
    with st.spinner("Initializing database from CSV..."):
        success, msg = load_data()
        if success:
            df = get_data_df()
        else:
            st.error(msg)

# Sidebar - Filters
st.sidebar.header("🔍 Filters")

search_query = st.sidebar.text_input("Search Nickname / Agent", "")

# Get unique values for filters
def get_unique(col):
    return sorted(df[col].dropna().unique().tolist())

sourcing_approaches = ["All"] + get_unique('sourcingapproach')
active_flags = ["All"] + get_unique('activeflg')
entry_statuses = ["All"] + get_unique('entrystatus')
country_codes = ["All"] + get_unique('countrycode')
business_templates = ["All"] + get_unique('btname')

sel_sourcing = st.sidebar.selectbox("Sourcing Approach", sourcing_approaches)
sel_active = st.sidebar.selectbox("Active Status", active_flags)
sel_entry = st.sidebar.selectbox("Entry Status", entry_statuses)
sel_country = st.sidebar.selectbox("Country Code", country_codes)
sel_template = st.sidebar.selectbox("Business Template", business_templates)

if st.sidebar.button("🔄 Refresh Data"):
    success, msg = load_data()
    if success:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)

# Filter Logic
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df['nickname'].str.contains(search_query, case=False, na=False) |
        filtered_df['agentname'].str.contains(search_query, case=False, na=False)
    ]

if sel_sourcing != "All":
    filtered_df = filtered_df[filtered_df['sourcingapproach'] == sel_sourcing]
if sel_active != "All":
    filtered_df = filtered_df[filtered_df['activeflg'] == sel_active]
if sel_entry != "All":
    filtered_df = filtered_df[filtered_df['entrystatus'] == sel_entry]
if sel_country != "All":
    filtered_df = filtered_df[filtered_df['countrycode'] == sel_country]
if sel_template != "All":
    filtered_df = filtered_df[filtered_df['btname'] == sel_template]

# Dashboard Header
st.title("IM Insights Dashboard")
st.markdown("Insights on the Input Master table")

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Entities", len(filtered_df))
m2.metric("Active Entities", len(filtered_df[filtered_df['activeflg'] == 'true']))
m3.metric("Countries", len(filtered_df['countrycode'].unique()))
m4.metric("Templates", len(filtered_df['btname'].unique()))

st.divider()

# Widgets Row
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 Input Bucket Details")
    bucket_counts = filtered_df['inputBucketDetails'].value_counts().reset_index()
    bucket_counts.columns = ['Bucket', 'Count']
    fig1 = px.bar(bucket_counts, x='Bucket', y='Count', color_discrete_sequence=['#22C55E'])
    fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("⭐ Interest & Rating")
    
    # Prep data for stacked bar
    ri = filtered_df['ratinginterest'].value_counts().get('true', 0)
    rated = filtered_df['rated'].apply(lambda x: str(x).lower() in ['true', 'y', 'yes']).sum()
    ci = filtered_df['clientinterest'].value_counts().get('true', 0)
    
    interest_df = pd.DataFrame({
        'Category': ['Rating Interest', 'Rated', 'Client Interest'],
        'True': [ri, rated, ci],
        'Total': [len(filtered_df)] * 3
    })
    interest_df['False'] = interest_df['Total'] - interest_df['True']
    
    fig2 = px.bar(interest_df, x='Category', y=['True', 'False'], 
                 color_discrete_map={'True': '#22C55E', 'False': '#DCFCE7'},
                 barmode='stack')
    fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    st.subheader("🛠️ Sourcing Strategy")
    sourcing_counts = filtered_df['sourcingapproach'].value_counts().reset_index()
    sourcing_counts.columns = ['Approach', 'Count']
    fig3 = px.bar(sourcing_counts, x='Approach', y='Count', color_discrete_sequence=['#4ADE80'])
    fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig3, use_container_width=True)

# Landing Page Details below Sourcing
with col3:
    st.markdown("**Landing Page Stats**")
    st.write(filtered_df['landingpageurltype'].value_counts().head(3))

# Data Table
st.divider()
st.subheader("📋 Detailed Data")
st.dataframe(
    filtered_df[['nickname', 'agentname', 'countrycode', 'entrystatus', 'activeflg', 'sourcingapproach']],
    use_container_width=True
)

# Footer
st.markdown("---")
st.caption("Data is updated periodically. Use the sidebar to refresh manually.")
