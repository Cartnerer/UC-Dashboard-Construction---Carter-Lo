import pandas as pd
import streamlit as st

st.set_page_config(page_title="UC Berkeley Admissions Equity Analyzer", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: #f8fafc;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1 {
        color: #0f172a;
        font-weight: 700;
        letter-spacing: -0.04em;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
    }
    .info-card {
        background: #f8fafc;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin: 0.5rem 0 1.2rem 0;
        color: #1f2937;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_DATA_PATH = "data/dashboard_data.csv"

st.title("UC Berkeley Admissions Equity Analyzer")
st.caption("Fall 2025 comparison of Berkeley admissions by Bay Area school poverty level")

st.sidebar.header("Controls")
use_default = st.sidebar.checkbox("Use sample data", value=True)
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if use_default:
    try:
        df = pd.read_csv(DEFAULT_DATA_PATH)
        st.sidebar.success("Sample dataset loaded")
    except FileNotFoundError:
        st.sidebar.warning("Sample dataset not found. Upload a CSV instead.")
        df = None
else:
    df = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

if df is not None:
    required_columns = {"fall_term", "campus", "frpm_pct", "applicants", "admits"}
    missing = sorted(required_columns - set(df.columns))

    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        st.stop()

    campuses = sorted(df["campus"].dropna().unique().tolist())
    years = sorted(df["fall_term"].dropna().astype(int).unique().tolist(), reverse=True)
    default_year = 2025 if 2025 in years else years[0]

    selected_campus = st.sidebar.selectbox("Campus", campuses)
    selected_year = st.sidebar.selectbox("Term", years, index=years.index(default_year))
    low_threshold = st.sidebar.slider("Low-poverty cutoff", 0.0, 0.5, 0.25, step=0.01)
    high_threshold = st.sidebar.slider("High-poverty cutoff", 0.5, 1.0, 0.75, step=0.01)
    show_school_level = st.sidebar.toggle("Show school-by-school view", value=True)

    filtered = df[(df["campus"] == selected_campus) & (df["fall_term"] == selected_year)].copy()

    if filtered.empty:
        st.error(f"No data found for {selected_campus} in fall {selected_year}.")
        st.stop()

    filtered["frpm_pct"] = pd.to_numeric(filtered["frpm_pct"], errors="coerce")
    filtered["applicants"] = pd.to_numeric(filtered["applicants"], errors="coerce").fillna(0)
    filtered["admits"] = pd.to_numeric(filtered["admits"], errors="coerce").fillna(0)

    low_pov = filtered[filtered["frpm_pct"] < low_threshold].copy()
    high_pov = filtered[filtered["frpm_pct"] > high_threshold].copy()

    low_apps = int(low_pov["applicants"].sum())
    low_admits = int(low_pov["admits"].sum())
    high_apps = int(high_pov["applicants"].sum())
    high_admits = int(high_pov["admits"].sum())

    low_rate = (low_admits / low_apps) if low_apps > 0 else 0.0
    high_rate = (high_admits / high_apps) if high_apps > 0 else 0.0
    pct_point_gap = (low_rate - high_rate) * 100

    st.markdown(
        """
        <div class="info-card">
            In the selected slice of data, schools below the low-poverty cutoff are compared against schools above the high-poverty cutoff using aggregate admit rate: total admits divided by total applicants.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Low-poverty schools", f"{low_rate * 100:.2f}%")
        st.caption(f"{low_apps:,} applicants • {low_admits:,} admits")

    with col2:
        st.metric("High-poverty schools", f"{high_rate * 100:.2f}%")
        st.caption(f"{high_apps:,} applicants • {high_admits:,} admits")

    with col3:
        st.metric("Difference", f"{pct_point_gap:.2f} pts")
        st.caption("Positive value means the low-poverty group had the higher admit rate")

    if not low_pov.empty and not high_pov.empty:
        summary_df = pd.DataFrame(
            {
                "group": [f"Low poverty (<{low_threshold:.0%})", f"High poverty (>{high_threshold:.0%})"],
                "applicants": [low_apps, high_apps],
                "admits": [low_admits, high_admits],
                "admit_rate": [low_rate, high_rate],
            }
        )

        chart_col, table_col = st.columns([2, 1])

        with chart_col:
            st.subheader("Comparison chart")
            st.bar_chart(summary_df.set_index("group")["admit_rate"] * 100)

        with table_col:
            st.subheader("Snapshot")
            st.dataframe(summary_df.style.format({"admit_rate": "{:.2%}"}), hide_index=True, use_container_width=True)

        if show_school_level:
            school_col = next(
                (col for col in ["school_name", "school", "high_school", "campus_name"] if col in filtered.columns),
                None,
            )

            if school_col is None:
                school_df = filtered.reset_index(drop=True).copy()
                school_df["School"] = [f"School {i + 1}" for i in range(len(school_df))]
                school_df = school_df[["School", "frpm_pct", "applicants", "admits"]].copy()
            else:
                school_df = filtered[[school_col, "frpm_pct", "applicants", "admits"]].copy()
                school_df = school_df.rename(columns={school_col: "School"})

            school_df["admit_rate"] = school_df.apply(
                lambda row: row["admits"] / row["applicants"] if row["applicants"] > 0 else 0,
                axis=1,
            )
            school_df = school_df[school_df["frpm_pct"].notna()].sort_values("frpm_pct", ascending=True)

            st.subheader("School-level view")
            st.dataframe(
                school_df[["School", "frpm_pct", "applicants", "admits", "admit_rate"]].assign(
                    admit_rate=school_df["admit_rate"].map(lambda x: f"{x:.2%}")
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("What this says")
        st.write(
            f"For the {selected_campus} data in fall {selected_year}, schools under {low_threshold:.0%} FRPM had an aggregate admit rate of {low_rate * 100:.2f}%, while schools above {high_threshold:.0%} FRPM came in at {high_rate * 100:.2f}%. The gap was {pct_point_gap:.2f} percentage points."
        )

        with st.expander("How the calculation works"):
            st.write(
                "Aggregate admit rate = total admits ÷ total applicants for each poverty group. This keeps the comparison focused on the overall applicant pool rather than school-by-school averages."
            )

    else:
        st.warning("There are no schools in one or both poverty bands for the current threshold settings.")

else:
    st.info("Load the sample dataset or upload a CSV to begin the analysis.")
