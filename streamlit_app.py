import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Competitor Team Dashboard", layout="wide")
st.title("🏢 Competitor Team Analysis Dashboard")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Sidebar filters
    st.sidebar.header("Filters")
    firms = st.sidebar.multiselect("Select Firms", df["Firm Name"].unique())
    offices = st.sidebar.multiselect("Select Offices", df["Current Office"].dropna().unique())
    year_range = st.sidebar.slider(
        "Year Joined Range", 
        int(df["Year Joined"].min()), 
        int(df["Year Joined"].max()),
        (int(df["Year Joined"].min()), int(df["Year Joined"].max()))
    )

    filtered_df = df.copy()
    if firms:
        filtered_df = filtered_df[filtered_df["Firm Name"].isin(firms)]
    if offices:
        filtered_df = filtered_df[filtered_df["Current Office"].isin(offices)]
    filtered_df = filtered_df[
        (filtered_df["Year Joined"] >= year_range[0]) & 
        (filtered_df["Year Joined"] <= year_range[1])
    ]

    # KPI Cards
    total_team = len(filtered_df["Name"])
    avg_year = filtered_df["Year Joined"].mean()
    num_offices = filtered_df["Current Office"].nunique()
    unique_titles = filtered_df["Harmonized title"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Team Members", total_team)
    col2.metric("Avg. Year Joined", f"{avg_year:.1f}")
    col3.metric("No. of Offices", num_offices)
    col4.metric("Unique Titles", unique_titles)

    # Tabs for charts
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "👥 Composition", "🌍 Geography & Education"])

    with tab1:
        col1, col2 = st.columns(2)
        fig1 = px.bar(filtered_df.groupby("Firm Name")["Name"].count().reset_index(),
                      x="Firm Name", y="Name", title="Team Size by Firm", color="Firm Name")
        col1.plotly_chart(fig1, use_container_width=True)

        seniority_counts = filtered_df.groupby(["Firm Name", "Harmonized title"])["Name"].count().reset_index()
        fig2 = px.funnel(seniority_counts, x="Name", y="Harmonized title",
                         color="Firm Name", title="Seniority Pyramid")
        col2.plotly_chart(fig2, use_container_width=True)

        fig3 = px.line(filtered_df.groupby(["Year Joined", "Firm Name"])["Name"].count().reset_index(),
                       x="Year Joined", y="Name", color="Firm Name", markers=True,
                       title="Hiring Trends Over Time")
        st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        fig4 = px.histogram(filtered_df, x="Harmonized title", color="Firm Name", barmode="group",
                            title="Title Distribution")
        col1.plotly_chart(fig4, use_container_width=True)

        fig5 = px.histogram(filtered_df, x="Harmonized team", color="Firm Name", barmode="group",
                            title="Team Distribution")
        col2.plotly_chart(fig5, use_container_width=True)

        fig6 = px.histogram(filtered_df, x="Harmonized sub-team", color="Firm Name", barmode="group",
                            title="Sub-team Distribution")
        st.plotly_chart(fig6, use_container_width=True)

    with tab3:
        fig7 = px.histogram(filtered_df, x="Current Office", color="Firm Name", barmode="group",
                            title="Office Location Distribution")
        st.plotly_chart(fig7, use_container_width=True)

        edu_df = pd.melt(filtered_df, id_vars=["Firm Name"], 
                         value_vars=["Masters Degree", "Undergraduate"],
                         var_name="Degree Type", value_name="Degree")
        fig8 = px.histogram(edu_df, x="Degree", color="Firm Name", facet_col="Degree Type",
                            barmode="group", title="Education Background Comparison")
        st.plotly_chart(fig8, use_container_width=True)

        fig9 = px.histogram(filtered_df, x="Committee memberships", color="Firm Name",
                            barmode="group", title="Committee Membership Counts")
        st.plotly_chart(fig9, use_container_width=True)
else:
    st.info("Please upload a CSV file to begin.")
