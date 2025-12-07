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
full_faculty_list = [n.strip() for n in full_faculty_list]

# ----------------- STREAMLIT CONFIG -----------------
st.set_page_config(page_title="Duty Analysis (1 / blank)", layout="wide")
st.title("Exam Duty Analysis (1 = Duty, Blank = No Duty)")
st.caption("Upload one duty file: first column = faculty names, remaining columns = 1 or blank.")

uploaded_file = st.file_uploader(
    "Upload duty file (Excel/CSV)",
    type=["xlsx", "xls", "csv"]
)

if not uploaded_file:
    st.stop()

# ----------------- READ FILE -----------------
if uploaded_file.name.lower().endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# Ensure column names are strings and trimmed
df.columns = [str(c).strip() for c in df.columns]

st.subheader("Raw Uploaded File (First 5 rows)")
st.dataframe(df.head())

# ----------------- DETECT NAME COLUMN -----------------
possible_name_cols = ["Name", "NAME", "Faculty", "Faculty Name",
                      "Invigilator", "Invigilator Name"]

name_col = None
for c in df.columns:
    if str(c).strip() in possible_name_cols:
        name_col = c
        break

# If no obvious name column found, assume first column
if name_col is None:
    name_col = df.columns[0]
    st.info(f"No explicit 'Name' column found. Using first column as Name: **{name_col}**")

# Rename to standard "Name"
if name_col != "Name":
    df = df.rename(columns={name_col: "Name"})

# Clean Name values
df["Name"] = df["Name"].astype(str).str.strip()

# ----------------- DUTY COLUMNS -----------------
duty_cols = [c for c in df.columns if c != "Name"]

if not duty_cols:
    st.error("No duty columns found (only 'Name' present). Please add date/session columns.")
    st.stop()

# Convert duty columns: "1" -> 1, others (blank, 0, NaN, text) -> 0
def duty_value(x):
    s = str(x).strip()
    return 1 if s == "1" else 0

df[duty_cols] = df[duty_cols].applymap(duty_value)

st.subheader("Cleaned Duty Matrix (1 = Duty, 0 = No Duty)")
st.dataframe(df)

# ----------------- TOTAL DUTY CALC -----------------
df["TotalDuty"] = df[duty_cols].sum(axis=1)

st.success(f"Total faculty rows processed: {len(df)}")

# ----------------- BASIC SUMMARY -----------------
st.subheader("Faculty-wise Duty Summary")
faculty_summary = df[["Name", "TotalDuty"]].sort_values("TotalDuty", ascending=False)
st.dataframe(faculty_summary)

# ----------------- CHARTS -----------------
st.subheader("Graphical Analysis")
total_duty_sum = faculty_summary["TotalDuty"].sum()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Bar Chart – Duty Count per Faculty")
    if total_duty_sum == 0:
        st.info("All TotalDuty values are 0 – no duties assigned in this file.")
    else:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        faculty_summary.set_index("Name")["TotalDuty"].plot(kind="bar", ax=ax1)
        ax1.set_ylabel("Duty Count")
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
        ax1.set_title("Duty Distribution")
        fig1.tight_layout()
        st.pyplot(fig1)

with col2:
    st.markdown("### Pie Chart – Duty Share")
    if total_duty_sum == 0:
        st.info("Cannot draw pie chart – all TotalDuty values are 0.")
    else:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.pie(
            faculty_summary["TotalDuty"],
            labels=faculty_summary["Name"],
            autopct="%1.1f%%"
        )
        ax2.set_title("Duty Share (%)")
        fig2.tight_layout()
        st.pyplot(fig2)

# ----------------- ADVANCED ANALYSIS WITH MASTER LIST -----------------
st.subheader("Advanced Analysis (Using Master Faculty List)")

roster_df = pd.DataFrame({"Name": full_faculty_list})
roster_df["Name"] = roster_df["Name"].astype(str).str.strip()

merged = roster_df.merge(faculty_summary, on="Name", how="left")
merged["TotalDuty"] = merged["TotalDuty"].fillna(0).astype(int)
merged = merged.sort_values("TotalDuty")

# 1. Faculty with zero duties
st.markdown("### Faculty with ZERO Duties (From Master List)")
zero_duty = merged[merged["TotalDuty"] == 0]
st.dataframe(zero_duty)

# 2. Minimum non-zero duty
non_zero = merged[merged["TotalDuty"] > 0]
st.markdown("### Faculty with MINIMUM Non-zero Duties")
if non_zero.empty:
    st.info("No faculty has non-zero duties.")
else:
    min_duty = non_zero["TotalDuty"].min()
    st.info(f"Minimum non-zero duties: **{min_duty}**")
    st.dataframe(merged[merged["TotalDuty"] == min_duty])

# 3. Maximum duty
st.markdown("### Faculty with MAXIMUM Duties")
max_duty = merged["TotalDuty"].max()
st.success(f"Maximum duties: **{max_duty}**")
st.dataframe(merged[merged["TotalDuty"] == max_duty])

# 4. Full distribution
st.markdown("### Full Duty Distribution (Master List)")
st.dataframe(merged)

st.markdown("### Overall Duty Distribution – Bar Chart (Master List)")
st.bar_chart(merged.set_index("Name")["TotalDuty"])
