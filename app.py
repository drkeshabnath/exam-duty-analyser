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


# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="Single File Duty Analysis", layout="wide")
st.title("Exam Duty Analysis (Single File Version)")
st.caption("Upload one duty file (Name + date/session columns).")


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

df.columns = [c.strip() for c in df.columns]
df["Name"] = df["Name"].astype(str).strip()

st.subheader("Uploaded File Preview")
st.dataframe(df.head())


# ----------------- TRANSFORM INTO LONG FORMAT -----------------
date_cols = [c for c in df.columns if c != "Name"]

long_df = df.melt(
    id_vars=["Name"],
    value_vars=date_cols,
    var_name="Date",
    value_name="DutyMark"
)

long_df["DutyMark"] = long_df["DutyMark"].astype(str).str.strip()
long_df = long_df[long_df["DutyMark"] != ""]
long_df["DutyCount"] = 1

st.success(f"Total duty assignments found: {len(long_df)}")


# ----------------- SUMMARY -----------------
st.subheader("Faculty-wise Duty Summary")

faculty_summary = (
    long_df.groupby("Name")["DutyCount"]
    .sum()
    .reset_index()
    .sort_values("DutyCount", ascending=False)
)

st.dataframe(faculty_summary)


# ----------------- CHARTS -----------------
st.subheader("Graphical Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Bar Chart – Duty per Faculty")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    faculty_summary.set_index("Name")["DutyCount"].plot(kind="bar", ax=ax1)
    ax1.set_title("Duty Distribution")
    ax1.set_ylabel("Duties")
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
    st.pyplot(fig1)

with col2:
    st.markdown("### Pie Chart – Duty Share")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie(
        faculty_summary["DutyCount"],
        labels=faculty_summary["Name"],
        autopct="%1.1f%%"
    )
    ax2.set_title("Percentage Share of Duties")
    st.pyplot(fig2)


# ----------------- ADVANCED ANALYSIS -----------------
st.subheader("Advanced Analysis (Using Master Faculty List)")

# Merge with master list
roster_df = pd.DataFrame({"Name": full_faculty_list})
merged = roster_df.merge(faculty_summary, on="Name", how="left")
merged["DutyCount"] = merged["DutyCount"].fillna(0)
merged = merged.sort_values("DutyCount")


# Zero-Duty
zero_duty = merged[merged["DutyCount"] == 0]
st.markdown("### Faculty with **Zero** Duties")
if zero_duty.empty:
    st.success("All faculty received at least one duty.")
else:
    st.error("These faculty received ZERO duties:")
    st.dataframe(zero_duty)


# Minimum duty (non-zero)
non_zero = merged[merged["DutyCount"] > 0]
if not non_zero.empty:
    min_duty = non_zero["DutyCount"].min()
    min_list = merged[merged["DutyCount"] == min_duty]
    st.markdown("### Faculty with Minimum Duties")
    st.info(f"Minimum duties: **{min_duty}**")
    st.dataframe(min_list)
else:
    st.info("No faculty had non-zero duties.")


# Maximum duty
max_duty = merged["DutyCount"].max()
max_list = merged[merged["DutyCount"] == max_duty]
st.markdown("### Faculty with Maximum Duties")
st.success(f"Maximum duties: **{max_duty}**")
st.dataframe(max_list)


# Full Distribution
st.markdown("### Full Duty Distribution (Master List)")
st.dataframe(merged)

st.markdown("### Distribution Bar Chart")
st.bar_chart(merged.set_index("Name")["DutyCount"])
