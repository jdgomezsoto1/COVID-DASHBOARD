import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------
# PAGE CONFIG
# --------------------------------

st.set_page_config(
    page_title="COVID-19 Mortality Patterns and Potential Reporting Anomalies",
    layout="wide"
)

# --------------------------------
# TITLE
# --------------------------------

st.title("🌍 COVID-19 Mortality Inequality Dashboard")

st.markdown("""
### WHO Public Health Analysis

This dashboard analyzes COVID-19 mortality trends across regions,
income levels, and age groups to understand how the pandemic
affected populations differently around the world.
""")

# --------------------------------
# LOAD DATA
# --------------------------------
df = pd.read_csv("covid.csv")
# --------------------------------
# POPULATION DATA (2023)
# --------------------------------

pop = pd.read_csv("population.csv")

population_df = pop[
    ["Country Code", "2023"]
].copy()

population_df.columns = [
    "Country_code",
    "Population"
]

population_df["Population"] = pd.to_numeric(
    population_df["Population"],
    errors="coerce"
)

# Merge population into covid data
df = df.merge(
    population_df,
    on="Country_code",
    how="left"
)

# --------------------------------
# CLEAN DATA
# --------------------------------

# Convert deaths column
df["Deaths"] = pd.to_numeric(df["Deaths"], errors="coerce")

# Remove missing values
df = df.dropna(subset=["Deaths"])

# Create date column
df["Date"] = pd.to_datetime(
    df["Year"].astype(str) + "-" + df["Month"].astype(str)
)

# --------------------------------
# SIDEBAR FILTERS
# --------------------------------

st.sidebar.header("Filters")

# WHO REGION

all_regions = sorted(df["Who_region"].dropna().unique())

select_all_regions = st.sidebar.checkbox(
    "Select All Regions",
    value=True
)

if select_all_regions:
    selected_region = all_regions
else:
    selected_region = st.sidebar.multiselect(
        "Select WHO Region",
        options=all_regions
    )

# INCOME LEVEL

all_income = sorted(df["Wb_income"].dropna().unique())

select_all_income = st.sidebar.checkbox(
    "Select All Income Levels",
    value=True
)

if select_all_income:
    selected_income = all_income
else:
    selected_income = st.sidebar.multiselect(
        "Select Income Level",
        options=all_income
    )

# COUNTRY

all_countries = sorted(df["Country"].dropna().unique())

select_all_countries = st.sidebar.checkbox(
    "Select All Countries",
    value=True
)

if select_all_countries:
    selected_country = all_countries
else:
    selected_country = st.sidebar.multiselect(
        "Select Country",
        options=all_countries
    )

# FILTER DATAFRAME

filtered_df = df[
    (df["Who_region"].isin(selected_region)) &
    (df["Wb_income"].isin(selected_income)) &
    (df["Country"].isin(selected_country))
]

# Filter dataframe

filtered_df = df[
    (df["Who_region"].isin(selected_region)) &
    (df["Wb_income"].isin(selected_income))
]

if selected_country:
    filtered_df = filtered_df[
        filtered_df["Country"].isin(selected_country)
    ]

# --------------------------------
# KPI METRICS
# --------------------------------

total_deaths = int(filtered_df["Deaths"].sum())
total_countries = filtered_df["Country"].nunique()
avg_deaths = round(filtered_df["Deaths"].mean(), 2)

col1, col2, col3 = st.columns(3)

col1.metric("Total Deaths", f"{total_deaths:,}")
col2.metric("Countries Included", total_countries)
col3.metric("Average Deaths", avg_deaths)

# --------------------------------
# LINE CHART
# --------------------------------

timeline_df = (
    filtered_df.groupby(["Date", "Who_region"])["Deaths"]
    .sum()
    .reset_index()
)

fig1 = px.line(
    timeline_df,
    x="Date",
    y="Deaths",
    color="Who_region",
    title="COVID-19 Death Trends by WHO Region",
    markers=True
)

fig1.update_layout(
    template="plotly_dark",
    height=600
)

st.plotly_chart(fig1, use_container_width=True)

# --------------------------------
# BAR CHART
# --------------------------------

income_df = (
    filtered_df.groupby("Wb_income")["Deaths"]
    .sum()
    .reset_index()
)

fig2 = px.bar(
    income_df,
    x="Wb_income",
    y="Deaths",
    color="Wb_income",
    title="Total Deaths by Income Level"
)

fig2.update_layout(
    template="plotly_dark",
    height=500
)

st.plotly_chart(fig2, use_container_width=True)

# --------------------------------
# AGE GROUP ANALYSIS
# --------------------------------

age_df = (
    filtered_df.groupby("Agegroup")["Deaths"]
    .sum()
    .reset_index()
)

fig3 = px.pie(
    age_df,
    names="Agegroup",
    values="Deaths",
    title="Death Distribution by Age Group"
)

fig3.update_layout(
    template="plotly_dark",
    height=500
)

st.plotly_chart(fig3, use_container_width=True)

# --------------------------------
# INSIGHTS
# --------------------------------

st.markdown("""
# Key Findings

### Global Inequality

COVID-19 mortality was distributed unevenly across WHO regions,
income levels, and age groups.

### Regional Differences

Certain regions experienced significantly larger mortality waves,
suggesting differences in exposure, healthcare capacity, and policy response.

### Age Impact

Older age groups accounted for a disproportionately large share
of reported deaths.

### Potential Reporting Anomalies

Several countries reported mortality figures substantially lower
than the average for countries within the same WHO region.

While these differences do not prove underreporting, they raise
questions about reporting practices, testing capacity, data quality,
and transparency during the pandemic.
""")


st.subheader("Top 10 Countries by Deaths")

top_countries = (
    filtered_df.groupby("Country")["Deaths"]
    .sum()
    .reset_index()
    .sort_values("Deaths", ascending=False)
    .head(10)
)

fig4 = px.bar(
    top_countries,
    x="Deaths",
    y="Country",
    orientation="h",
    title="Top 10 Countries with Highest COVID Deaths"
)

fig4.update_layout(
    template="plotly_dark",
    height=600
)

st.plotly_chart(fig4, use_container_width=True)

st.subheader("Dataset Preview")

st.dataframe(
    filtered_df,
    use_container_width=True
)

map_df = (
    filtered_df.groupby("Country_code")["Deaths"]
    .sum()
    .reset_index()
)

fig5 = px.choropleth(
    map_df,
    locations="Country_code",
    color="Deaths",
    color_continuous_scale="Reds",
    title="Global COVID Deaths Map"
)

st.plotly_chart(fig5, use_container_width=True)

# --------------------------------
# POTENTIAL REPORTING ANOMALIES
# --------------------------------

st.header("🚨 Potential Reporting Anomalies")

country_stats = (
    filtered_df.groupby(
        ["Country", "Who_region"]
    )
    .agg(
        Deaths=("Deaths", "sum"),
        Population=("Population", "first")
    )
    .reset_index()
)

country_stats["Deaths_per_100k"] = (
    country_stats["Deaths"] /
    country_stats["Population"]
) * 100000


regional_avg = (
    country_stats.groupby("Who_region")["Deaths_per_100k"]
    .mean()
    .reset_index()
)

regional_avg.columns = [
    "Who_region",
    "Regional_Average"
]

country_stats = country_stats.merge(
    regional_avg,
    on="Who_region",
    how="left"
)
country_stats["Anomaly_Index"] = (
    country_stats["Regional_Average"]
    /
    (country_stats["Deaths_per_100k"] + 1)
)

country_stats = country_stats[
    country_stats["Deaths"] > 1000
]

anomaly_df = (
    country_stats
    .sort_values("Anomaly_Index", ascending=False)
    .head(15)
)


st.markdown("""
Countries with unusually low reported mortality compared to the average
country in their WHO region receive a higher anomaly score.

**Important:** This does NOT prove underreporting. It simply highlights
countries whose reported mortality appears unusually low relative to
regional peers.
""")

fig = px.bar(
    anomaly_df,
    x="Anomaly_Index",
    y="Country",
    orientation="h",
    color="Who_region",
    title="Countries With The Most Unusual Mortality Reporting Patterns"
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

fig.update_layout(
    template="plotly_dark",
    height=700
)

st.plotly_chart(
    fig,
    use_container_width=True
)