import io
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# -------------- BASIC CONFIG -----------------
st.set_page_config(
    page_title="Exam Duty Analyser",
    layout="wide"
)

st.title("Exam Invigilation Duty Analyser")
st.caption("Upload duty-list files and get semester-wise analysis, bar charts, and pie charts.")

st.markdown("""
**Instructions**

1. Export each duty list to **Excel (.xlsx) or CSV (.csv)**  
2. Make sure the first columns are: `Sl No`, `Name`, `DEPT` (spelling can be tweaked in the code).  
3. Date columns should contain **✓** (or any non-empty value) when duty is assigned.
""")

# -------------- FILE UPLOAD -----------------
uploaded_files = st.file_uploader(
    "Upload one or more duty-list files",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload at least one file to see the analysis.")
    st.stop()

all_long_dfs = []   # to collect data from all files

st.subheader("Step 1: Map each file to Semester / Exam")

for idx, up_file in enumerate(uploaded_files):
    col1, col2 = st.columns([3, 2])
    with col1:
        st.write(f"**File {idx+1}:** `{up_file.name}`")
    with col2:
        sem_name = st.text_input(
            f"Semester / Exam name for file {idx+1}",
            value=up_file.name.replace(".xlsx", "").replace(".csv", ""),
            key=f"sem_{idx}"
        )

    # -------- Read file into DataFrame --------
    if up_file.name.lower().endswith(".csv"):
        df = pd.read_csv(up_file)
    else:
        df = pd.read_excel(up_file)

    # Show small preview
    st.write("Preview:")
    st.dataframe(df.head())

    # -------- Normalise to long format --------
    # Try to find the ID columns by name (you can tweak these lists)
    possible_slno_cols = ["Sl No", "Sl_No", "Sl", "SlNo"]
    possible_name_cols = ["Name", "NAME"]
    possible_dept_cols = ["DEPT", "Dept", "Department"]

    def find_col(candidates, cols):
        for c in candidates:
            if c in cols:
                return c
        return None

    cols = list(df.columns)
    sl_col = find_col(possible_slno_cols, cols)
    name_col = find_col(possible_name_cols, cols)
    dept_col = find_col(possible_dept_cols, cols)

    if not (name_col and dept_col):
        st.error(
            f"Could not detect Name/Dept columns in `{up_file.name}`. "
            "Please ensure column headers contain 'Name' and 'DEPT' (or adjust the code)."
        )
        st.stop()

    id_cols = [c for c in [sl_col, name_col, dept_col] if c is not None]
    date_cols = [c for c in cols if c not in id_cols]

    # Melt: one row per (Faculty, Date) with duty mark
    long_df = df.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name="Date",
        value_name="DutyMark"
    )

    # Keep only rows where there is some mark (duty assigned)
    long_df["DutyMark"] = long_df["DutyMark"].astype(str).str.strip()
    long_df = long_df[long_df["DutyMark"] != ""]
    long_df["DutyCount"] = 1

    # Add semester / exam name
    long_df["Semester"] = sem_name

    # Normalize column labels
    long_df.rename(columns={name_col: "Name", dept_col: "Dept"}, inplace=True)

    all_long_dfs.append(long_df)

# -------- Combine all semesters --------
master = pd.concat(all_long_dfs, ignore_index=True)

st.success(f"Combined rows after processing all files: **{len(master)}**")

st.subheader("Step 2: Filters")

semesters = sorted(master["Semester"].unique())
selected_semesters = st.multiselect(
    "Select semester(s) to include in analysis",
    options=semesters,
    default=semesters
)

filtered = master[master["Semester"].isin(selected_semesters)]

if filtered.empty:
    st.warning("No data after filtering – please change the selection.")
    st.stop()

# -------- SUMMARY TABLES --------
st.subheader("Summary Tables")

# Faculty-wise duty count
faculty_summary = (
    filtered.groupby(["Semester", "Name", "Dept"])["DutyCount"]
    .sum()
    .reset_index()
    .sort_values(["Semester", "DutyCount"], ascending=[True, False])
)

dept_summary = (
    filtered.groupby(["Semester", "Dept"])["DutyCount"]
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

tabs = st.tabs(["Faculty-wise", "Department-wise", "Date-wise"])

with tabs[0]:
    st.write("**Duty count per faculty**")
    st.dataframe(faculty_summary)

with tabs[1]:
    st.write("**Duty count per department**")
    st.dataframe(dept_summary)

with tabs[2]:
    st.write("**Duty count per date**")
    st.dataframe(date_summary)

# -------- CHARTS --------
st.subheader("Step 3: Visual Analysis")

# Pick single semester for detailed charts
sem_for_plot = st.selectbox(
    "Select a semester/exam for charts",
    options=semesters
)

plot_df = filtered[filtered["Semester"] == sem_for_plot]

col_a, col_b = st.columns(2)

# (A) Bar chart: duty count per faculty
with col_a:
    st.markdown(f"### Bar Chart – Duty Count per Faculty ({sem_for_plot})")

    fac_counts = (
        plot_df.groupby("Name")["DutyCount"]
        .sum()
        .sort_values(ascending=False)
    )

    fig1, ax1 = plt.subplots(figsize=(5, 4))
    fac_counts.plot(kind="bar", ax=ax1)
    ax1.set_ylabel("No. of Duties")
    ax1.set_xlabel("Faculty")
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
    ax1.set_title("Duty Distribution by Faculty")

    st.pyplot(fig1)

# (B) Pie chart: department share of total duty
with col_b:
    st.markdown(f"### Pie Chart – Department Share ({sem_for_plot})")

    dept_counts = (
        plot_df.groupby("Dept")["DutyCount"]
        .sum()
        .sort_values(ascending=False)
    )

    fig2, ax2 = plt.subplots(figsize=(5, 4))
    ax2.pie(dept_counts.values, labels=dept_counts.index, autopct="%1.1f%%")
    ax2.set_title("Share of Duties by Department")

    st.pyplot(fig2)

# -------- OPTIONAL: fairness metrics --------
st.subheader("Step 4: Fairness Check (per Semester)")

fair_summary = (
    faculty_summary.groupby("Semester")["DutyCount"]
    .agg(["min", "max", "mean", "std"])
    .reset_index()
)

st.write("Basic statistics of duty load per semester:")
st.dataframe(fair_summary)
