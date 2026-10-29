import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="Real Estate Analytics Dashboard",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

sns.set_theme(style="whitegrid")

REQUIRED_COLUMNS = [
    "State", "City", "Locality", "Property_Type", "BHK", "Size_in_SqFt",
    "Price_in_Lakhs", "Year_Built", "Furnished_Status", "Age_of_Property",
    "Nearby_Schools", "Nearby_Hospitals", "Public_Transport_Accessibility",
    "Parking_Space", "Security", "Availability_Status", "Price_per_SqFt_Rs",
    "Amenity_Count", "Has_Parking", "Has_Security", "Is_Ready_To_Move",
    "Floor_Data_Check", "Property_Age_Group", "Size_Category", "Price_Category"
]

NUMERIC_COLUMNS = [
    "BHK", "Size_in_SqFt", "Price_in_Lakhs", "Price_per_SqFt_Rs",
    "Year_Built", "Age_of_Property", "Nearby_Schools", "Nearby_Hospitals",
    "Amenity_Count", "Floor_No", "Total_Floors"
]

@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_csv("output.csv")
    for col in data.columns:
        if col in NUMERIC_COLUMNS:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data

def money_lakhs(value):
    return f"₹{value:,.2f} L"

def chart_empty_message():
    st.info("No data matches the selected filters. Please adjust the filters in the sidebar.")

st.title("🏡 Real Estate Analytics Dashboard")
st.caption("Explore property prices, location patterns, property features, and availability.")

with st.sidebar:
    st.header("Dashboard Controls")
    uploaded = st.file_uploader("Upload a CSV file (optional)", type=["csv"])
    try:
        raw_df = load_data(uploaded)
    except FileNotFoundError:
        st.error("Could not find output.csv. Upload your CSV file using the control above.")
        st.stop()
    except Exception as exc:
        st.error(f"Could not read the CSV: {exc}")
        st.stop()

    if raw_df.empty:
        st.error("The uploaded dataset is empty.")
        st.stop()

    st.markdown("---")
    st.subheader("Filter properties")

    def options_for(col):
        if col not in raw_df.columns:
            return []
        vals = raw_df[col].dropna().astype(str).unique().tolist()
        return sorted(vals)

    states = options_for("State")
    selected_states = st.multiselect("State", states, default=states)

    city_base = raw_df
    if selected_states and "State" in raw_df.columns:
        city_base = raw_df[raw_df["State"].astype(str).isin(selected_states)]
    cities = sorted(city_base["City"].dropna().astype(str).unique()) if "City" in city_base.columns else []
    selected_cities = st.multiselect("City", cities, default=cities)

    property_types = options_for("Property_Type")
    selected_types = st.multiselect("Property type", property_types, default=property_types)

    bhk_vals = sorted(raw_df["BHK"].dropna().unique().tolist()) if "BHK" in raw_df.columns else []
    selected_bhk = st.multiselect("BHK", bhk_vals, default=bhk_vals)

    if "Price_in_Lakhs" in raw_df.columns:
        pmin = float(raw_df["Price_in_Lakhs"].min())
        pmax = float(raw_df["Price_in_Lakhs"].max())
        if pmin == pmax:
            price_range = (pmin, pmax)
        else:
            price_range = st.slider(
                "Price range (₹ lakhs)", min_value=pmin, max_value=pmax,
                value=(pmin, pmax), step=max((pmax-pmin)/200, 0.01), format="%.2f"
            )
    else:
        price_range = None

    size_categories = options_for("Size_Category")
    selected_sizes = st.multiselect("Size category", size_categories, default=size_categories)

    availability = options_for("Availability_Status")
    selected_availability = st.multiselect("Availability", availability, default=availability)

    if st.button("Reset filters", use_container_width=True):
        st.rerun()

df = raw_df.copy()
if selected_states and "State" in df:
    df = df[df["State"].astype(str).isin(selected_states)]
if selected_cities and "City" in df:
    df = df[df["City"].astype(str).isin(selected_cities)]
if selected_types and "Property_Type" in df:
    df = df[df["Property_Type"].astype(str).isin(selected_types)]
if selected_bhk and "BHK" in df:
    df = df[df["BHK"].isin(selected_bhk)]
if price_range and "Price_in_Lakhs" in df:
    df = df[df["Price_in_Lakhs"].between(price_range[0], price_range[1])]
if selected_sizes and "Size_Category" in df:
    df = df[df["Size_Category"].astype(str).isin(selected_sizes)]
if selected_availability and "Availability_Status" in df:
    df = df[df["Availability_Status"].astype(str).isin(selected_availability)]

if df.empty:
    chart_empty_message()
    st.stop()

# KPI row
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Properties", f"{len(df):,}")
c2.metric("Average price", money_lakhs(df["Price_in_Lakhs"].mean()) if "Price_in_Lakhs" in df else "N/A")
c3.metric("Median price", money_lakhs(df["Price_in_Lakhs"].median()) if "Price_in_Lakhs" in df else "N/A")
c4.metric("Median price / sq ft", f"₹{df['Price_per_SqFt_Rs'].median():,.0f}" if "Price_per_SqFt_Rs" in df else "N/A")
ready_pct = (pd.to_numeric(df["Is_Ready_To_Move"], errors="coerce").mean() * 100) if "Is_Ready_To_Move" in df else np.nan
c5.metric("Ready to move", f"{ready_pct:.1f}%" if pd.notna(ready_pct) else "N/A")

st.markdown("---")
tab_overview, tab_prices, tab_location, tab_features, tab_data = st.tabs(
    ["Overview", "Price Analysis", "Location Insights", "Property Features", "Data Explorer"]
)

def show_fig(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

with tab_overview:
    left, right = st.columns(2)
    with left:
        st.subheader("Property price distribution")
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(df["Price_in_Lakhs"].dropna(), bins=35, kde=True, ax=ax)
        ax.set_xlabel("Price (₹ lakhs)")
        ax.set_ylabel("Number of properties")
        show_fig(fig)
    with right:
        st.subheader("Listings by property type")
        if "Property_Type" in df:
            counts = df["Property_Type"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            counts.plot(kind="bar", ax=ax)
            ax.set_xlabel("")
            ax.set_ylabel("Number of properties")
            ax.tick_params(axis="x", rotation=25)
            show_fig(fig)
    left, right = st.columns(2)
    with left:
        st.subheader("Availability status")
        if "Availability_Status" in df:
            counts = df["Availability_Status"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            counts.plot(kind="bar", ax=ax)
            ax.set_xlabel("")
            ax.set_ylabel("Number of properties")
            ax.tick_params(axis="x", rotation=20)
            show_fig(fig)
    with right:
        st.subheader("Furnishing status")
        if "Furnished_Status" in df:
            counts = df["Furnished_Status"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            counts.plot(kind="pie", autopct="%1.1f%%", ax=ax, ylabel="")
            show_fig(fig)

with tab_prices:
    st.subheader("Price analysis")
    left, right = st.columns(2)
    with left:
        st.markdown("**Price by BHK (box plot)**")
        if {"BHK", "Price_in_Lakhs"}.issubset(df.columns):
            plot_df = df[["BHK", "Price_in_Lakhs"]].dropna()
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.boxplot(data=plot_df, x="BHK", y="Price_in_Lakhs", ax=ax)
            ax.set_xlabel("Bedrooms (BHK)")
            ax.set_ylabel("Price (₹ lakhs)")
            show_fig(fig)
    with right:
        st.markdown("**Property size vs price**")
        if {"Size_in_SqFt", "Price_in_Lakhs"}.issubset(df.columns):
            plot_df = df[["Size_in_SqFt", "Price_in_Lakhs", "Property_Type"]].dropna()
            if len(plot_df) > 4000:
                plot_df = plot_df.sample(4000, random_state=42)
            fig, ax = plt.subplots(figsize=(7, 4))
            if "Property_Type" in plot_df:
                sns.scatterplot(data=plot_df, x="Size_in_SqFt", y="Price_in_Lakhs",
                                hue="Property_Type", alpha=0.55, ax=ax, legend=False)
            else:
                sns.scatterplot(data=plot_df, x="Size_in_SqFt", y="Price_in_Lakhs", alpha=0.55, ax=ax)
            ax.set_xlabel("Size (sq ft)")
            ax.set_ylabel("Price (₹ lakhs)")
            show_fig(fig)
    left, right = st.columns(2)
    with left:
        st.markdown("**Median price per sq ft by city**")
        if {"City", "Price_per_SqFt_Rs"}.issubset(df.columns):
            city_prices = df.groupby("City")["Price_per_SqFt_Rs"].median().sort_values(ascending=False).head(12).sort_values()
            fig, ax = plt.subplots(figsize=(7, 4))
            city_prices.plot(kind="barh", ax=ax)
            ax.set_xlabel("Median price per sq ft (₹)")
            show_fig(fig)
    with right:
        st.markdown("**Average price by property type**")
        if {"Property_Type", "Price_in_Lakhs"}.issubset(df.columns):
            avg = df.groupby("Property_Type")["Price_in_Lakhs"].mean().sort_values()
            fig, ax = plt.subplots(figsize=(7, 4))
            avg.plot(kind="barh", ax=ax)
            ax.set_xlabel("Average price (₹ lakhs)")
            show_fig(fig)

with tab_location:
    st.subheader("Location insights")
    left, right = st.columns(2)
    with left:
        st.markdown("**Top cities by listing count**")
        if "City" in df:
            city_counts = df["City"].value_counts().head(15).sort_values()
            fig, ax = plt.subplots(figsize=(7, 5))
            city_counts.plot(kind="barh", ax=ax)
            ax.set_xlabel("Number of listings")
            show_fig(fig)
    with right:
        st.markdown("**Median price by state**")
        if {"State", "Price_in_Lakhs"}.issubset(df.columns):
            state_prices = df.groupby("State")["Price_in_Lakhs"].median().sort_values()
            fig, ax = plt.subplots(figsize=(7, 5))
            state_prices.plot(kind="barh", ax=ax)
            ax.set_xlabel("Median price (₹ lakhs)")
            show_fig(fig)
    st.markdown("**City comparison table**")
    if {"City", "Price_in_Lakhs", "Price_per_SqFt_Rs"}.issubset(df.columns):
        city_summary = df.groupby("City").agg(
            Listings=("Price_in_Lakhs", "size"),
            Average_Price_Lakhs=("Price_in_Lakhs", "mean"),
            Median_Price_Lakhs=("Price_in_Lakhs", "median"),
            Median_Price_per_SqFt=("Price_per_SqFt_Rs", "median")
        ).sort_values("Listings", ascending=False).reset_index()
        st.dataframe(city_summary, use_container_width=True, hide_index=True)

with tab_features:
    st.subheader("Property features")
    left, right = st.columns(2)
    with left:
        st.markdown("**Correlation heatmap**")
        corr_cols = [c for c in [
            "BHK", "Size_in_SqFt", "Price_in_Lakhs", "Price_per_SqFt_Rs",
            "Age_of_Property", "Nearby_Schools", "Nearby_Hospitals", "Amenity_Count"
        ] if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if len(corr_cols) >= 2:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(df[corr_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
            show_fig(fig)
    with right:
        st.markdown("**Average price by transport accessibility**")
        if {"Public_Transport_Accessibility", "Price_in_Lakhs"}.issubset(df.columns):
            transport = df.groupby("Public_Transport_Accessibility")["Price_in_Lakhs"].mean().sort_values()
            fig, ax = plt.subplots(figsize=(7, 5))
            transport.plot(kind="bar", ax=ax)
            ax.set_xlabel("Transport accessibility")
            ax.set_ylabel("Average price (₹ lakhs)")
            ax.tick_params(axis="x", rotation=20)
            show_fig(fig)
    left, right = st.columns(2)
    with left:
        st.markdown("**Nearby schools vs hospitals**")
        if {"Nearby_Schools", "Nearby_Hospitals", "Price_in_Lakhs"}.issubset(df.columns):
            plot_df = df[["Nearby_Schools", "Nearby_Hospitals", "Price_in_Lakhs"]].dropna()
            if len(plot_df) > 2500:
                plot_df = plot_df.sample(2500, random_state=42)
            fig, ax = plt.subplots(figsize=(7, 4))
            sizes = plot_df["Price_in_Lakhs"].clip(lower=1)
            sizes = 15 + 100 * sizes / max(sizes.quantile(0.95), 1)
            ax.scatter(plot_df["Nearby_Schools"], plot_df["Nearby_Hospitals"], s=sizes, alpha=0.3)
            ax.set_xlabel("Nearby schools")
            ax.set_ylabel("Nearby hospitals")
            show_fig(fig)
    with right:
        st.markdown("**Amenity count distribution**")
        if "Amenity_Count" in df:
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.countplot(data=df, x="Amenity_Count", ax=ax)
            ax.set_xlabel("Number of amenities")
            ax.set_ylabel("Properties")
            show_fig(fig)
    st.caption("Charts describe associations in the dataset; they do not prove that a feature causes higher prices or guarantees future returns.")

with tab_data:
    st.subheader("Explore filtered property records")
    st.write(f"Showing {len(df):,} records after applying the sidebar filters.")
    visible_cols = [c for c in [
        "State", "City", "Locality", "Property_Type", "BHK", "Size_in_SqFt",
        "Price_in_Lakhs", "Price_per_SqFt_Rs", "Furnished_Status",
        "Availability_Status", "Public_Transport_Accessibility", "Amenity_Count"
    ] if c in df.columns]
    st.dataframe(df[visible_cols], use_container_width=True, hide_index=True)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_real_estate_data.csv",
        mime="text/csv",
    )
    with st.expander("Data quality checks"):
        if "Floor_Data_Check" in df:
            st.write("Floor data check categories")
            st.dataframe(df["Floor_Data_Check"].value_counts(dropna=False).rename_axis("Status").reset_index(name="Records"))
        missing = df.isna().sum().sort_values(ascending=False)
        missing = missing[missing > 0]
        if len(missing):
            st.write("Missing values by column")
            st.dataframe(missing.rename_axis("Column").reset_index(name="Missing values"), use_container_width=True, hide_index=True)
        else:
            st.success("No missing values in the filtered data.")

st.markdown("---")
st.caption("Built with Streamlit, Pandas, Matplotlib, and Seaborn. Currency and price labels follow the source dataset.")
