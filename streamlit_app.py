# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title="Competitor Team Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🏢 Competitor Team Analysis Dashboard")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
if not uploaded_file:
    st.info("Please upload a CSV file to begin.")
    st.stop()

# Load
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

# Expected columns and safe defaults if missing
expected_cols_defaults = {
    "Firm Name": "Unknown Firm",
    "Name": "Unknown Name",
    "Title": "",
    "Harmonized title": "Other",
    "Year Joined": pd.NA,
    "Current Office": "Unknown Office",
    "Team Associated": "",
    "Harmonized team": "Other",
    "Investment sub-team / Area of focus": "",
    "Harmonized sub-team": "Other",
    "Prior Experience": "",
    "Masters Degree": "",
    "Undergraduate": "",
    "Committee memberships": ""
}

# Add missing cols with defaults
for col, default in expected_cols_defaults.items():
    if col not in df.columns:
        df[col] = default

# Convert Year Joined to numeric (coerce errors -> NaN)
df["Year Joined"] = pd.to_numeric(df["Year Joined"], errors="coerce")

# Helper to get unique sorted options or a fallback
def unique_options(series, fallback=None):
    vals = series.dropna().unique().tolist()
    vals = [v for v in vals if str(v).strip() != ""]
    if not vals:
        return [fallback] if fallback is not None else []
    return sorted(vals)

# Sidebar filters
st.sidebar.header("Filters")
firms_options = unique_options(df["Firm Name"], fallback="Unknown Firm")
selected_firms = st.sidebar.multiselect("Select Firms", options=firms_options, default=firms_options[:2])

offices_options = unique_options(df["Current Office"], fallback=None)
selected_offices = st.sidebar.multiselect("Select Offices", options=offices_options, default=offices_options if len(offices_options)<=5 else offices_options[:3])

# Year Joined filter only shown if meaningful year data exists
years_nonnull = df["Year Joined"].dropna()
has_years = not years_nonnull.empty
if has_years:
    min_year = int(years_nonnull.min())
    max_year = int(years_nonnull.max())
    if min_year == max_year:
        year_range = st.sidebar.slider("Year Joined (single year available)", min_year, max_year, (min_year, max_year))
    else:
        year_range = st.sidebar.slider("Year Joined range", min_year, max_year, (min_year, max_year))
else:
    st.sidebar.info("No valid 'Year Joined' data found — year filter disabled.")
    year_range = None

# Apply filters
filtered_df = df.copy()
if selected_firms:
    filtered_df = filtered_df[filtered_df["Firm Name"].isin(selected_firms)]
if selected_offices:
    filtered_df = filtered_df[filtered_df["Current Office"].isin(selected_offices)]
if has_years and year_range is not None:
    # keep rows with Year Joined in range (rows with NaN year will be excluded unless you want to include them)
    filtered_df = filtered_df[
        (filtered_df["Year Joined"].notna()) &
        (filtered_df["Year Joined"].between(year_range[0], year_range[1]))
    ]

if filtered_df.empty:
    st.warning("No rows after applying filters. Try changing filters or upload a different file.")
    st.stop()

# KPI Cards (safe calculations)
total_team = int(filtered_df["Name"].nunique()) if "Name" in filtered_df.columns else int(len(filtered_df))
avg_year_val = filtered_df["Year Joined"].dropna().mean()
avg_year = f"{int(avg_year_val)}" if not np.isnan(avg_year_val) else "N/A"
num_offices = int(filtered_df["Current Office"].nunique())
unique_titles = int(filtered_df["Harmonized title"].nunique())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Team Members", total_team)
col2.metric("Avg. Year Joined", avg_year)
col3.metric("No. of Offices", num_offices)
col4.metric("Unique Titles", unique_titles)

# Safe plotting helpers
def can_plot_column(df_, col):
    return (col in df_.columns) and (not df_[col].dropna().empty) and (df_[col].astype(str).str.strip().ne("").any())

def safe_histogram(df_, x, color, title, barmode="group"):
    if not can_plot_column(df_, x):
        st.info(f"Skipping '{title}': no data for column '{x}'.")
        return
    try:
        fig = px.histogram(df_, x=x, color=color if color in df_.columns else None, barmode=barmode, title=title)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render {title}: {e}")

# Dashboard Tabs and layout
tab1, tab2, tab3 = st.tabs(["📊 Overview", "👥 Composition", "🌍 Geography & Education"])

with tab1:
    r1c1 = st.columns(1)
    # Team Size by Firm
    if can_plot_column(filtered_df, "Firm Name"):
        team_size = filtered_df.groupby("Firm Name")["Name"].count().reset_index().rename(columns={"Name":"Count"})
        fig1 = px.bar(team_size, x="Firm Name", y="Count", title="Team Size by Firm", text="Count", color="Firm Name")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No 'Firm Name' data to show Team Size.")
    

    # Hiring trends (if Year Joined exists)
    if has_years:
        yt = filtered_df.groupby(["Year Joined", "Firm Name"])["Name"].count().reset_index().rename(columns={"Name":"Count"})
        yt = yt.dropna(subset=["Year Joined"])
        if not yt.empty:
            fig3 = px.line(yt, x="Year Joined", y="Count", color="Firm Name", markers=True, title="Hiring Trends Over Time")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Year data exists but no valid points after filtering.")
    else:
        st.info("No 'Year Joined' data available for Hiring Trends.")

with tab2:
    c1, c2 = st.columns(2)
    safe_histogram(filtered_df, x="Harmonized title", color="Firm Name", title="Harmonized Title Distribution")
    safe_histogram(filtered_df, x="Harmonized team", color="Firm Name", title="Harmonized Team Distribution")
    safe_histogram(filtered_df, x="Harmonized sub-team", color="Firm Name", title="Harmonized Sub-team Distribution")

with tab3:
    # Office distribution
    safe_histogram(filtered_df, x="Current Office", color="Firm Name", title="Office Location Distribution")
    # Education breakdown (if any)
    edu_cols = [c for c in ["Masters Degree", "Undergraduate"] if can_plot_column(filtered_df, c)]
    if edu_cols:
        # melt only existing edu columns
        edu_df = filtered_df.melt(id_vars=["Firm Name"], value_vars=edu_cols, var_name="Degree Type", value_name="Degree")
        if not edu_df.empty and can_plot_column(edu_df, "Degree"):
            try:
                fig_edu = px.histogram(edu_df, x="Degree", color="Firm Name", facet_col="Degree Type", barmode="group", title="Education Background Comparison")
                st.plotly_chart(fig_edu, use_container_width=True)
            except Exception as e:
                st.error(f"Could not render Education chart: {e}")
        else:
            st.info("No education data available to plot.")
    else:
        st.info("No 'Masters Degree' or 'Undergraduate' data available.")

    # Committee memberships
    safe_histogram(filtered_df, x="Committee memberships", color="Firm Name", title="Committee Membership Counts")

# Optional: show filtered table and allow download
with st.expander("Show filtered data (first 200 rows)"):
    st.dataframe(filtered_df.head(200), use_container_width=True)

# Download button
try:
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", csv, "filtered_competitors.csv", "text/csv")
except Exception:
    st.info("Download not available for this dataset.")
