import os
import streamlit as st
import pandas as pd

# =============================================================================
# PAGE SETUP
# =============================================================================
st.set_page_config(
    page_title="AI-Powered Mobile Sales Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean, professional CSS (light-touch, safe)
st.markdown(
    """
    <style>
      .main-title {font-size: 2rem; font-weight: 800; color:#173b5a; margin-bottom: 0.2rem;}
      .sub-title {font-size: 0.95rem; color:#5b6b7a; margin-bottom: 1.2rem;}
      .block-title {font-size: 1.2rem; font-weight: 700; color:#243746; margin-top: 1.2rem; margin-bottom: 0.6rem;}
      [data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# DATA LOADING + CLEANING
# =============================================================================

EXPECTED_COLS = [
    "Year",
    "Quarter",
    "Product Model",
    "5G Capability",
    "Units Sold",
    "Revenue ($)",
    "Market Share (%)",
    "Regional 5G Coverage (%)",
    "5G Subscribers (millions)",
    "Avg 5G Speed (Mbps)",
    "Preference for 5G (%)",
    "Region",
]

NUMERIC_COLS = [
    "Units Sold",
    "Revenue ($)",
    "Market Share (%)",
    "Regional 5G Coverage (%)",
    "5G Subscribers (millions)",
    "Avg 5G Speed (Mbps)",
    "Preference for 5G (%)",
]

QUARTER_ORDER = ["Q1", "Q2", "Q3", "Q4"]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip spaces, unify common name mismatches."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.replace("\ufeff", "", regex=False).str.strip()

    col_map = {
        "ProductModel": "Product Model",
        "Product_Model": "Product Model",
        "Units_Sold": "Units Sold",
        "Revenue": "Revenue ($)",
        "Revenue ($ )": "Revenue ($)",
        "Revenue $": "Revenue ($)",
        "Market Share %": "Market Share (%)",
        "Market Share": "Market Share (%)",
        "Regional 5G Coverage %": "Regional 5G Coverage (%)",
        "Regional 5G Coverage": "Regional 5G Coverage (%)",
        "Preference for 5G %": "Preference for 5G (%)",
        "5G Preference %": "Preference for 5G (%)",
        "Preference for 5G": "Preference for 5G (%)",
        "5G Subscribers": "5G Subscribers (millions)",
        "5G Subscribers (Millions)": "5G Subscribers (millions)",
        "5G Subscribers (million)": "5G Subscribers (millions)",
        "Avg 5G Speed": "Avg 5G Speed (Mbps)",
        "Average 5G Speed (Mbps)": "Avg 5G Speed (Mbps)",
        "Avg 5G Speed Mbps": "Avg 5G Speed (Mbps)",
    }
    df.rename(columns={c: col_map.get(c, c) for c in df.columns}, inplace=True)
    return df


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns safely even if they contain commas or symbols."""
    df = df.copy()
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = (
                df[c]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    return df


def _clean_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure quarters look like Q1/Q2/Q3/Q4 and sort correctly."""
    df = df.copy()
    if "Quarter" in df.columns:
        df["Quarter"] = df["Quarter"].astype(str).str.strip().str.upper()
        df["Quarter"] = df["Quarter"].replace(
            {"1": "Q1", "2": "Q2", "3": "Q3", "4": "Q4",
             "QUARTER 1": "Q1", "QUARTER 2": "Q2", "QUARTER 3": "Q3", "QUARTER 4": "Q4"}
        )
        df["Quarter"] = pd.Categorical(df["Quarter"], categories=QUARTER_ORDER, ordered=True)
    return df


def _apply_data_quality_rules(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Rules:
    - Market Share (%) < 0  => set to NaN (excluded from calculations)
    - Regional 5G Coverage (%) > 100 => set to NaN (excluded from calculations)
    Returns:
    - cleaned df
    - issues_df (rows that had problems)
    """
    df = df.copy()

    bad_ms = pd.Series(False, index=df.index)
    bad_cov = pd.Series(False, index=df.index)

    if "Market Share (%)" in df.columns:
        bad_ms = df["Market Share (%)"].notna() & (df["Market Share (%)"] < 0)
        df.loc[bad_ms, "Market Share (%)"] = pd.NA

    if "Regional 5G Coverage (%)" in df.columns:
        bad_cov = df["Regional 5G Coverage (%)"].notna() & (df["Regional 5G Coverage (%)"] > 100)
        df.loc[bad_cov, "Regional 5G Coverage (%)"] = pd.NA

    issues_mask = bad_ms | bad_cov
    issues_df = df.loc[issues_mask].copy()

    if not issues_df.empty:
        issues_df["Bad Market Share (<0)"] = bad_ms.loc[issues_df.index]
        issues_df["Bad Coverage (>100)"] = bad_cov.loc[issues_df.index]

        keep_cols = [c for c in [
            "Year", "Quarter", "Product Model", "Region",
            "Market Share (%)", "Regional 5G Coverage (%)",
            "Units Sold", "Revenue ($)",
            "Bad Market Share (<0)", "Bad Coverage (>100)"
        ] if c in issues_df.columns]
        issues_df = issues_df[keep_cols]

    return df, issues_df


@st.cache_data
def load_data(csv_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and prepare data for dashboard. Returns (df, issues_df)."""
    df = pd.read_csv(csv_path)
    df = _normalize_columns(df)

    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        st.error(f"Missing columns in {csv_path}: {missing}")
        st.stop()

    df = _coerce_numeric(df)
    df = _clean_quarter(df)

    df = df.dropna(subset=["Year", "Quarter", "Product Model", "Region"])

    for c in ["Product Model", "Region", "5G Capability"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # Apply your quality rules
    df, issues_df = _apply_data_quality_rules(df)

    return df, issues_df


# =============================================================================
# LOAD
# =============================================================================
CSV_PATH = "data/Expanded_Dataset.csv"
if not os.path.exists(CSV_PATH):
    st.error(f"{CSV_PATH} not found. Put it in the same folder as app.py.")
    st.stop()

df, issues_df_all = load_data(CSV_PATH)

# =============================================================================
# AUTO FILTERS (AUTO-CATEGORIZE COLUMNS)
# =============================================================================
st.sidebar.markdown("## 🔎 Auto Filters")
st.sidebar.caption("Filters generated automatically from your dataset.")

numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = [c for c in df.columns if c not in numeric_cols]

filters = {}
for col in categorical_cols:
    nunique = df[col].nunique(dropna=True)
    if nunique <= 50:
        options = ["All"] + sorted(df[col].dropna().astype(str).unique().tolist())
        filters[col] = st.sidebar.selectbox(f"Select {col}", options)

filtered = df.copy()
for col, val in filters.items():
    if val != "All":
        filtered = filtered[filtered[col].astype(str) == val]

# Filter issues table in the same way (so it matches current view)
issues_filtered = issues_df_all.copy()
for col, val in filters.items():
    if val != "All" and col in issues_filtered.columns:
        issues_filtered = issues_filtered[issues_filtered[col].astype(str) == val]

# =============================================================================
# HEADER
# =============================================================================
st.markdown('<div class="main-title">📱 AI-Powered Mobile Sales Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Auto-filtered metrics, trends, 5G insights, data quality checks, and next-quarter forecast.</div>',
    unsafe_allow_html=True,
)

# =============================================================================
# METRICS
# =============================================================================
st.markdown('<div class="block-title">Key Metrics</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

total_units = int(filtered["Units Sold"].sum(skipna=True))
total_revenue = float(filtered["Revenue ($)"].sum(skipna=True))
avg_market_share = float(filtered["Market Share (%)"].mean(skipna=True))
avg_speed = float(filtered["Avg 5G Speed (Mbps)"].mean(skipna=True))
avg_subs = float(filtered["5G Subscribers (millions)"].mean(skipna=True))

c1.metric("📦 Total Units Sold", f"{total_units:,}")
c2.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
c3.metric("📈 Avg Market Share", f"{avg_market_share:.2f}%")
c4.metric("⚡ Avg 5G Speed", f"{avg_speed:.1f} Mbps")
c5.metric("📶 Avg 5G Subscribers", f"{avg_subs:.2f} M")

# =============================================================================
# TRENDS (GROUP BY QUARTER)
# =============================================================================
st.markdown('<div class="block-title">Trends by Quarter</div>', unsafe_allow_html=True)

trend = (
    filtered.groupby("Quarter", as_index=False)
    .agg({"Units Sold": "sum", "Revenue ($)": "sum"})
    .sort_values("Quarter")
)

left, right = st.columns(2)

with left:
    st.caption("Units Sold (Quarterly)")
    if len(trend) > 0:
        st.line_chart(trend.set_index("Quarter")["Units Sold"], use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

with right:
    st.caption("Revenue ($) (Quarterly)")
    if len(trend) > 0:
        st.bar_chart(trend.set_index("Quarter")["Revenue ($)"], use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

# =============================================================================
# NEXT QUARTER SALES FORECAST (Units Sold)
# =============================================================================
st.markdown('<div class="block-title">📊 Next Quarter Sales Forecast</div>', unsafe_allow_html=True)

try:
    from sklearn.linear_model import LinearRegression
    import numpy as np

    forecast_df = (
        filtered.groupby("Quarter", as_index=False)
        .agg({"Units Sold": "sum"})
        .sort_values("Quarter")
    )

    # Need at least 2 points to fit a line
    if len(forecast_df) >= 2:
        forecast_df["Quarter_Num"] = forecast_df["Quarter"].astype(str).str.replace("Q", "", regex=False).astype(int)

        X = forecast_df[["Quarter_Num"]]
        y = forecast_df["Units Sold"].values

        model = LinearRegression()
        model.fit(X, y)

        # next quarter number (wrap after 4)
        last_q = int(forecast_df["Quarter_Num"].max())
        next_q = last_q + 1 if last_q < 4 else 1

        predicted_units = float(model.predict([[next_q]])[0])

        st.metric("📈 Predicted Units Sold (Next Quarter)", f"{int(predicted_units):,}")

        # Plot with predicted point appended
        next_label = f"Q{next_q}"
        forecast_plot = pd.concat(
            [
                forecast_df[["Quarter", "Units Sold"]],
                pd.DataFrame({"Quarter": [next_label], "Units Sold": [predicted_units]}),
            ],
            ignore_index=True,
        )
        # Keep order Q1..Q4 (prediction might wrap)
        forecast_plot["Quarter"] = pd.Categorical(forecast_plot["Quarter"], categories=QUARTER_ORDER, ordered=True)
        forecast_plot = forecast_plot.sort_values("Quarter")

        st.line_chart(forecast_plot.set_index("Quarter")["Units Sold"], use_container_width=True)
    else:
        st.info("Not enough data to forecast (need at least 2 quarters after filtering).")

except Exception:
    st.warning("Forecast needs scikit-learn. Install with: pip install scikit-learn")

# =============================================================================
# 5G INSIGHTS
# =============================================================================
st.markdown('<div class="block-title">5G Insights</div>', unsafe_allow_html=True)
i1, i2, i3 = st.columns(3)

avg_cov = float(filtered["Regional 5G Coverage (%)"].mean(skipna=True))
avg_pref = float(filtered["Preference for 5G (%)"].mean(skipna=True))
avg_cap = filtered["5G Capability"].value_counts(dropna=True)

i1.metric("📡 Avg Regional 5G Coverage", f"{avg_cov:.2f}%")
i2.metric("👍 Avg Preference for 5G", f"{avg_pref:.2f}%")
i3.write("**5G Capability Split**")
i3.dataframe(avg_cap.rename_axis("5G Capability").to_frame("Count"), use_container_width=True, height=160)

# =============================================================================
# DATA QUALITY ISSUES (corner + full width)
# =============================================================================
st.markdown('<div class="block-title">🧹 Data Quality Issues</div>', unsafe_allow_html=True)

left_q, right_q = st.columns([2, 1])

with right_q:
    st.caption("⚠️ Rows with invalid values")
    if not issues_filtered.empty:
        st.dataframe(issues_filtered.head(8), use_container_width=True, height=240)
        st.write(f"Total issue rows: **{len(issues_filtered)}**")
    else:
        st.success("No invalid values found for current filters.")

st.markdown("### Full list of issue rows")
if not issues_filtered.empty:
    st.dataframe(issues_filtered, use_container_width=True, height=260)
else:
    st.write("No issue rows to display.")

# =============================================================================
# FILTERED TABLE + DOWNLOAD
# =============================================================================
st.markdown('<div class="block-title">Filtered Data Table</div>', unsafe_allow_html=True)
st.dataframe(filtered, use_container_width=True, height=330)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered Data (CSV)",
    data=csv_bytes,
    file_name="filtered_sales_data.csv",
    mime="text/csv",
)

st.sidebar.markdown("---")
st.sidebar.caption("Mobile Sales & 5G Analytics • Streamlit Dashboard")