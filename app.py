import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ----------------- BASIC CONFIG -----------------
st.set_page_config(
    page_title="Exam Duty Analyser",
    layout="wide"
)

st.title("Exam Invigilation Duty Analyser")
st.caption("Upload duty-list files (Name + date/session columns) and get semester-wise analysis.")

st.markdown("""
**Expected format for each file**

- First column: **Name**  
- Remaining columns: **Exam dates / sessions**  
- Any non-empty value (✓, tick, text, etc.) means **duty assigned**.
""")

# ----------------- FILE UPLOAD -----------------
uploaded_files = st.file_uploader(
    "Upload one or more duty-list files (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least one duty-list file to begin.")
    st.stop()

all_long_dfs = []

st.subheader("Step 1: Map each file to a Semester / Exam")

for idx, up_file in enumerate(uploaded_files):
    col1, col2 = st.columns([3, 2])

    with col1:
        st.write(f"**File {idx + 1}:** `{up_file.name}`")
    with col2:
        sem_name = st.text_input(
            f"Semester / Exam name for file {idx + 1}",
            value=up_file.name.replace(".xlsx", "").replace(".csv", ""),
            key=f"sem_{idx}"
        )

    # ---- Read file ----
    if up_file.name.lower().endswith(".csv"):
        df = pd.read_csv(up_file)
    else:
        df = pd.read_excel(up_file)

    # Normalise column names a bit
    df.columns = [str(c).strip() for c in df.columns]

    if "Name" not in df.columns:
        st.error(
            f"`Name` column not found in `{up_file.name}`. "
            "Please ensure the first column header is exactly 'Name'."
        )
        st.stop()

    st.write("Preview:")
    st.dataframe(df.head())

    # ---- Reshape to long format ----
    date_cols = [c for c in df.columns if c != "Name"]

    long_df = df.melt(
        id_vars=["Name"],
        value_vars=date_cols,
        var_name="Date",
        value_name="DutyMark"
    )

    long_df["DutyMark"] = long_df["DutyMark"].astype(str).str.strip()
    long_df = long_df[long_df["DutyMark"] != ""]   # only rows with duty
    long_df["DutyCount"] = 1
    long_df["Semester"] = sem_name

    all_long_dfs.append(long_df)

# Combine all semesters
master = pd.concat(all_long_dfs, ignore_index=True)
st.success(f"Combined rows (faculty-date duty assignments) from all files: **{len(master)}**")

# ----------------- FILTERS -----------------
st.subheader("Step 2: Filters")

semesters = sorted(master["Semester"].unique())
selected_semesters = st.multiselect(
    "Select semester(s) to include in analysis",
    options=semesters,
    default=semesters
)

filtered = master[master["Semester"].isin(selected_semesters)]

if filtered.empty:
    st.warning("No data after filtering. Please change the selection.")
    st.stop()

# ----------------- SUMMARY TABLES -----------------
st.subheader("Step 3: Summary Tables")

faculty_summary = (
    filtered.groupby(["Semester", "Name"])["DutyCount"]
    .sum()
    .reset_index()
    .sort_values(["Semester", "DutyCount"], ascending=[True, False])
)

date_summary = (
    filtered.groupby(["Semester", "Date"])["DutyCount"]
    .sum()
    .reset_index()
    .sort_values(["Semester", "Date"])
)

t1, t2 = st.tabs(["Faculty-wise duties", "Date/session-wise duties"])

with t1:
    st.write("Total duties per faculty (per semester):")
    st.dataframe(faculty_summary)

with t2:
    st.write("Total duties per date/session (per semester):")
    st.dataframe(date_summary)

# ----------------- CHARTS -----------------
st.subheader("Step 4: Visual Analysis")

sem_for_plot = st.selectbox(
    "Select a single semester/exam for charts",
    options=semesters
)

plot_df = filtered[filtered["Semester"] == sem_for_plot]

col_a, col_b = st.columns(2)

# (A) Bar chart: duties per faculty
with col_a:
    st.markdown(f"### Bar chart – Duties per Faculty ({sem_for_plot})")
    fac_counts = (
        plot_df.groupby("Name")["DutyCount"]
        .sum()
        .sort_values(ascending=False)
    )

    fig1, ax1 = plt.subplots(figsize=(6, 4))
    fac_counts.plot(kind="bar", ax=ax1)
    ax1.set_ylabel("No. of Duties")
    ax1.set_xlabel("Faculty")
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
    ax1.set_title("Duty Distribution by Faculty")
    fig1.tight_layout()
    st.pyplot(fig1)

# (B) Pie chart: share of duty by faculty
with col_b:
    st.markdown(f"### Pie chart – Share of Duties ({sem_for_plot})")
    fac_counts = (
        plot_df.groupby("Name")["DutyCount"]
        .sum()
        .sort_values(ascending=False)
    )

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie(
        fac_counts.values,
        labels=fac_counts.index,
        autopct="%1.1f%%"
    )
    ax2.set_title("Share of Total Duties by Faculty")
    fig2.tight_layout()
    st.pyplot(fig2)

# ----------------- SIMPLE FAIRNESS STATS -----------------
st.subheader("Step 5: Fairness Summary (per Semester)")

fair_stats = (
    faculty_summary.groupby("Semester")["DutyCount"]
    .agg(["min", "max", "mean", "std"])
    .reset_index()
)

st.write("Basic statistics of duty load per faculty:")
st.dataframe(fair_stats)
