import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ----------------- MASTER FACULTY LIST -----------------
full_faculty_list = [
    "Mrs. Chandana Das", "Mr. Arindam Talukdar", "Mrs. Namita Choudhury",
    "Dr. Bikul Barman", "Mrs. Archana Khataniar", "Mrs. Ritua Barua",
    "Mr. Kanak Das", "Dr. Arup Bharali", "Mrs. Chitra Rani Deka",
    "Mr. Mukul Patgiri", "Dr. Parag Barman", "Dr. Bhupen Talukdar",
    "Dr. Runima Sarma", "Mr. Monoj Kumar Das", "Dr. Jadav Chandra Basumatary",
    "Dr. Rashmi Devi", "Mr. Anjan Sarma", "Mr. Raju Das",
    "Dr. Arun Kumar Sharma", "Mr. Swapnajyoti Sarma",
    "Dr. Kalpana Pathak Talukdar", "Dr. Pradip Kumar Sarma",
    "Dr. Dipika Kalita", "Dr. Jyotishmay Bora", "Dr. Rupam Patgiri",
    "Mr. Dhanjit Talukdar", "Dr. Manmohan Das", "Mr. Apurba Talukdar",
    "Dr. Bipul Kakati", "Dr. Dipak Baruah", "Dr. Rajib Lochan Sarma",
    "Dr. Akshay Haloi", "Mr. Nabajit Saha", "Dr. Upakul Mahanta",
    "Dr. Dipjyoti Kalita", "Dr. Gitika Kalita", "Dr. Dipen Tayung",
    "Dr. Jitumani Rajbongshi", "Dr. Prasenjit Das", "Dr. Jaba Sharma",
    "Mr. Suren Das", "Mr. Jnanesh Roy Choudhury", "Mrs. Arundhati Gogoi",
    "Dr. Alakesh Barman", "Dr. Banashree Sarkar", "Dr. Bharati Gogoi",
    "Dr. Lonkham Baruah", "Dr. Bishwajit Changmai", "Dr. Kunjalata Baro",
    "Dr. Priyanka Kalita", "Dr. Rupjyoti Gogoi", "Dr. Nijara Rajbongshi",
    "Dr. Ankur Sharmah", "Dr. Purnajoy Mipun", "Dr. Diganta Borgohain",
    "Mrs. Nibedita Mahanta", "Dr. Rinku Moni Kalita",
    "Dr. Amborish Adhyapok", "Dr. Jayashree Deka", "Ms. Barnali Saikia",
    "Dr. Junmoni Hansepi", "Ms. Kasmita Bora", "Dr. Navalakhi Hazarika",
    "Dr. Rajashree Deka", "Dr. Madhumita Boruah", "Dr. Dulumani Deka",
    "Dr. Hirumani Kalita", "Mrs. Mallika Pamsong", "Dr. Nabanita Baruah",
    "Mr. Manish Kiling", "Dr. Sabita Bhagabati", "Dr. Satyananda Mohapatra",
    "Dr. Debajyoti Dutta", "Dr. Keshab Nath", "Dr. Kamal Saharia",
    "Dr. Jagannath Bhuyan", "Dr. Bobby D. Langthasa"
]

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
- Remaining columns: **Exam dates / sessions** (e.g., 04/12/2025, 06/12/2025 M, 06/12/2025 E, etc.)  
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

    # Strip column names
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

# ----------------- COMBINE ALL FILES -----------------
master = pd.concat(all_long_dfs, ignore_index=True)
st.success(f"Combined rows (faculty–date duty assignments) from all files: **{len(master)}**")

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

# ----------------- FAIRNESS SUMMARY -----------------
st.subheader("Step 5: Fairness Summary (per Semester)")

fair_stats = (
    faculty_summary.groupby("Semester")["DutyCount"]
    .agg(["min", "max", "mean", "std"])
    .reset_index()
)

st.write("Basic statistics of duty load per faculty:")
st.dataframe(fair_stats)

# ----------------- ADVANCED ANALYSIS -----------------
st.subheader("Step 6: Advanced Duty Load Analysis (Using Full Faculty List)")

# Total duty per faculty across the selected semesters
faculty_duty_total = (
    filtered.groupby("Name")["DutyCount"]
    .sum()
    .reset_index()
)

# Full roster → DataFrame
faculty_master = pd.DataFrame({"Name": full_faculty_list})

# Merge to include faculty with zero duty
merged = faculty_master.merge(faculty_duty_total, on="Name", how="left")
merged["DutyCount"] = merged["DutyCount"].fillna(0)

# Sort by duty count (ascending)
merged = merged.sort_values("DutyCount", ascending=True).reset_index(drop=True)

# Faculty with zero duty
zero_duty = merged[merged["DutyCount"] == 0]

# Minimum > 0 duty
if (merged["DutyCount"] > 0).any():
    min_duty = merged[merged["DutyCount"] > 0]["DutyCount"].min()
    min_duty_faculty = merged[merged["DutyCount"] == min_duty]
else:
    min_duty = 0
    min_duty_faculty = pd.DataFrame(columns=merged.columns)

# Maximum duty
max_duty = merged["DutyCount"].max()
max_duty_faculty = merged[merged["DutyCount"] == max_duty]

# ----- Display advanced results -----
st.markdown("### 6.1 Faculty Not Assigned Any Duty")
if zero_duty.empty:
    st.success("✅ All faculty in the master list received at least one duty in the selected semesters.")
else:
    st.error("❗ The following faculty received **zero exam duties** in the selected semesters:")
    st.dataframe(zero_duty)

st.markdown("### 6.2 Faculty With Minimum (Non-zero) Duties")
if min_duty == 0 and min_duty_faculty.empty:
    st.info("No faculty with non-zero duties found (check input files).")
else:
    st.info(f"Minimum non-zero duties assigned: **{min_duty}**")
    st.dataframe(min_duty_faculty)

st.markdown("### 6.3 Faculty With Maximum Duties")
st.success(f"Maximum duties assigned to a single faculty: **{max_duty}**")
st.dataframe(max_duty_faculty)

st.markdown("### 6.4 Overall Duty Distribution (All Faculty)")
st.write("Duty count for every faculty in the master list (including those with zero duties):")
st.dataframe(merged)

st.markdown("#### Bar Chart – Duty Distribution for All Faculty (Selected Semesters)")
st.bar_chart(merged.set_index("Name")["DutyCount"])
