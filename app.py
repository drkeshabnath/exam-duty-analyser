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

# ----------------- STREAMLIT -----------------
st.set_page_config(page_title="Duty Analysis (Blank = No Duty)", layout="wide")
st.title("Exam Duty Analysis (1 = Duty, Blank = No Duty)")
st.caption("Upload one duty file: Name column + columns with 1 or blank entries.")

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

df.columns = [str(c).strip() for c in df.columns]

if "Name" not in df.columns:
    st.error("File must contain a 'Name' column.")
    st.stop()

df["Name"] = df["Name"].astype(str).str.strip()

# ----------------- CONVERT BLANKS TO 0, '1' TO 1 -----------------
date_cols = [c for c in df.columns if c != "Name"]

df[date_cols] = df[date_cols].applymap(lambda x:
    1 if str(x).strip() == "1" else 0
)

st.subheader("Cleaned Duty File")
st.dataframe(df)

# ----------------- COMPUTE TOTAL DUTY -----------------
df["TotalDuty"] = df[date_cols].sum(axis=1)

st.success(f"Total faculty entries processed: {len(df)}")

# ----------------- SUMMARY TABLE -----------------
st.subheader("Faculty Duty Summary")
faculty_summary = df[["Name", "TotalDuty"]].sort_values("TotalDuty", ascending=False)
st.dataframe(faculty_summary)

# ----------------- CHARTS -----------------
st.subheader("Graphical Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Bar Chart – Duty Count")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    faculty_summary.set_index("Name")["TotalDuty"].plot(kind="bar", ax=ax1)
    ax1.set_ylabel("Duty Count")
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
    fig1.tight_layout()
    st.pyplot(fig1)

with col2:
    st.markdown("### Pie Chart – Duty Share")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie(
        faculty_summary["TotalDuty"],
        labels=faculty_summary["Name"],
        autopct="%1.1f%%"
    )
    ax2.set_title("Duty Share %")
    st.pyplot(fig2)

# ----------------- ADVANCED ANALYSIS -----------------
st.subheader("Advanced Analysis (Using Master Faculty List)")

roster_df = pd.DataFrame({"Name": full_faculty_list})

merged = roster_df.merge(faculty_summary, on="Name", how="left")
merged["TotalDuty"] = merged["TotalDuty"].fillna(0)

merged = merged.sort_values("TotalDuty")

# Zero-duty list
zero_duty = merged[merged["TotalDuty"] == 0]
st.markdown("### Faculty with ZERO Duties")
st.dataframe(zero_duty)

# Min duties
non_zero = merged[merged["TotalDuty"] > 0]
if not non_zero.empty:
    min_duty = non_zero["TotalDuty"].min()
    st.info(f"Minimum duties assigned: {min_duty}")
    st.dataframe(merged[merged["TotalDuty"] == min_duty])
else:
    st.info("No faculty has non-zero duties.")

# Max duties
max_duty = merged["TotalDuty"].max()
st.success(f"Maximum duties assigned: {max_duty}")
st.dataframe(merged[merged["TotalDuty"] == max_duty])

# Full distribution
st.markdown("### Full Duty Distribution")
st.dataframe(merged)

# Distribution bar chart
st.markdown("### Duty Count Distribution (All Faculty)")
st.bar_chart(merged.set_index("Name")["TotalDuty"])
