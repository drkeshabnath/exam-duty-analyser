import os
import difflib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


# -------------------------------------------------
# MASTER FACULTY LIST
# -------------------------------------------------
full_faculty_list = [
    "Mrs. Chandana Das","Mr. Arindam Talukdar","Mrs. Namita Choudhury",
    "Dr. Bikul Barman","Mrs. Archana Khataniar","Mrs. Ritua Barua",
    "Mr. Kanak Das","Dr. Arup Bharali","Mrs. Chitra Rani Deka",
    "Mr. Mukul Patgiri","Dr. Parag Barman","Dr. Bhupen Talukdar",
    "Dr. Runima Sarma","Mr. Monoj Kumar Das","Dr. Jadav Chandra Basumatary",
    "Dr. Rashmi Devi","Mr. Anjan Sarma","Mr. Raju Das",
    "Dr. Arun Kumar Sharma","Mr. Swapnajyoti Sarma",
    "Dr. Kalpana Pathak Talukdar","Dr. Pradip Kumar Sarma",
    "Dr. Dipika Kalita","Dr. Jyotishmay Bora","Dr. Rupam Patgiri",
    "Mr. Dhanjit Talukdar","Dr. Manmohan Das","Mr. Apurba Talukdar",
    "Dr. Bipul Kakati","Dr. Dipak Baruah","Dr. Rajib Lochan Sarma",
    "Dr. Akshay Haloi","Mr. Nabajit Saha","Dr. Upakul Mahanta",
    "Dr. Dipjyoti Kalita","Dr. Gitika Kalita","Dr. Dipen Tayung",
    "Dr. Jitumani Rajbongshi","Dr. Prasenjit Das","Dr. Jaba Sharma",
    "Mr. Suren Das","Mr. Jnanesh Roy Choudhury","Mrs. Arundhati Gogoi",
    "Dr. Alakesh Barman","Dr. Banashree Sarkar","Dr. Bharati Gogoi",
    "Dr. Lonkham Baruah","Dr. Bishwajit Changmai","Dr. Kunjalata Baro",
    "Dr. Priyanka Kalita","Dr. Rupjyoti Gogoi","Dr. Nijara Rajbongshi",
    "Dr. Ankur Sharmah","Dr. Purnajoy Mipun","Dr. Diganta Borgohain",
    "Mrs. Nibedita Mahanta","Dr. Rinku Moni Kalita",
    "Dr. Amborish Adhyapok","Dr. Jayashree Deka","Ms. Barnali Saikia",
    "Dr. Junmoni Hansepi","Ms. Kasmita Bora","Dr. Navalakhi Hazarika",
    "Dr. Rajashree Deka","Dr. Madhumita Boruah","Dr. Dulumani Deka",
    "Dr. Hirumani Kalita","Mrs. Mallika Pamsong","Dr. Nabanita Baruah",
    "Mr. Manish Kiling","Dr. Sabita Bhagabati","Dr. Satyananda Mohapatra",
    "Dr. Debajyoti Dutta","Dr. Keshab Nath","Dr. Kamal Saharia",
    "Dr. Jagannath Bhuyan","Dr. Bobby D. Langthasa"
]
full_faculty_list = [n.strip() for n in full_faculty_list]


# -------------------------------------------------
# NAME NORMALIZATION + FUZZY MATCH
# -------------------------------------------------
TITLE_TOKENS = {"dr","mr","mrs","ms","prof","sir","smt","kumari"}

def normalize(n):
    n = str(n).lower().replace("."," ")
    parts = [p for p in n.split() if p not in TITLE_TOKENS]
    return " ".join(parts)

master_df = pd.DataFrame({"MasterName": full_faculty_list})
master_df["Norm"] = master_df["MasterName"].apply(normalize)


def fuzzy_map(name, cutoff=0.70):
    if not isinstance(name, str): name=str(name)
    raw = name.strip()
    norm = normalize(raw)

    # Exact
    for m in full_faculty_list:
        if m.lower() == raw.lower():
            return m, 1.0

    # norm exact
    eq = master_df[master_df["Norm"] == norm]
    if not eq.empty:
        return eq.iloc[0]["MasterName"], 1.0

    # fuzzy
    best = difflib.get_close_matches(norm, master_df["Norm"].tolist(), n=1)
    if best:
        score = difflib.SequenceMatcher(None, norm, best[0]).ratio()
        if score >= cutoff:
            return master_df[master_df["Norm"]==best[0]].iloc[0]["MasterName"], score

    return None, 0.0


# -------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------
st.set_page_config(page_title="Multi-Semester Duty Analyzer", layout="wide")
st.title("📚 Multi-Semester Exam Duty Analyzer")
st.caption("This tool merges duty data from multiple semesters to compute **total faculty duty load**.")


# -------------------------------------------------
# LOAD ALL DUTY FILES
# -------------------------------------------------
DATA_FOLDER = "duty_files"
files = [f for f in os.listdir(DATA_FOLDER)
         if f.lower().endswith((".xlsx",".xls",".csv"))]

if not files:
    st.error("No files inside duty_files/. Please add files.")
    st.stop()

st.success(f"Detected {len(files)} duty files")

combined_all = []   # store per-file final tables
summary_all = []    # store per-file summaries


# -------------------------------------------------
# PROCESS EACH FILE
# -------------------------------------------------
for filename in files:
    st.markdown(f"### 📄 Processing File: **{filename}**")

    path = os.path.join(DATA_FOLDER, filename)

    if filename.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    df.columns = [str(c).strip() for c in df.columns]
    name_col = df.columns[0]
    df = df.rename(columns={name_col:"RawName"})
    df["RawName"] = df["RawName"].astype(str).str.strip()

    duty_cols = [c for c in df.columns if c!="RawName"]

    # convert to duty = 1/0
    df[duty_cols] = df[duty_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    df[duty_cols] = (df[duty_cols] > 0).astype(int)

    # fuzzy map names
    df["MappedName"], df["Score"] = zip(*df["RawName"].apply(lambda x: fuzzy_map(x)))

    # per-file summary
    df["TotalDuty"] = df[duty_cols].sum(axis=1)
    file_summary = df.groupby("MappedName")["TotalDuty"].sum().reset_index()
    file_summary["Semester"] = filename

    summary_all.append(file_summary)
    combined_all.append(df)


# -------------------------------------------------
# MERGE ALL SEMESTER SUMMARIES
# -------------------------------------------------
final_df = pd.concat(summary_all)
final_total = final_df.groupby("MappedName")["TotalDuty"].sum().reset_index()
final_total = final_total.sort_values("TotalDuty", ascending=False)

st.header("📊 Total Duty Across All Semesters")
st.dataframe(final_total)


# -------------------------------------------------
# HEATMAP ACROSS ALL FILES
# -------------------------------------------------
st.subheader("🔥 Combined Duty Heatmap (All Semesters)")

pivot = final_df.pivot_table(index="MappedName",
                             columns="Semester",
                             values="TotalDuty",
                             aggfunc="sum",
                             fill_value=0)

fig, ax = plt.subplots(figsize=(14, 10))
sns.heatmap(pivot,
            cmap="YlGnBu",
            annot=True,
            fmt="d",
            linewidths=0.5,
            linecolor="gray",
            cbar_kws={'label':'Duty Count'})
ax.set_title("Combined Duty Heatmap (Faculty × Semester)", fontsize=16)
st.pyplot(fig)


# -------------------------------------------------
# BAR CHART
# -------------------------------------------------
st.subheader("📌 Bar Chart – Total Duty Across All Semesters")

fig2, ax2 = plt.subplots(figsize=(12, 6))
ax2.bar(final_total["MappedName"], final_total["TotalDuty"], color="teal")
ax2.set_xticklabels(final_total["MappedName"], rotation=90)
ax2.set_ylabel("Duty Count")
ax2.set_title("Total Duty Load Across All Semesters")
st.pyplot(fig2)


# -------------------------------------------------
# PEOPLE WITH ZERO DUTY
# -------------------------------------------------
st.subheader("🚫 Faculty With Zero Duties")

final_total_full = pd.DataFrame({"Name": full_faculty_list})
final_total_full = final_total_full.merge(final_total,
                                          left_on="Name",
                                          right_on="MappedName",
                                          how="left")

final_total_full["TotalDuty"] = final_total_full["TotalDuty"].fillna(0)
zero = final_total_full[final_total_full["TotalDuty"] == 0]
st.dataframe(zero)
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
st.markdown("### Full Duty Distribution")
st.dataframe(merged)

st.markdown("### Overall Duty Distribution")
st.bar_chart(merged.set_index("Name")["TotalDuty"])

# ----------------- FINAL SUMMARY TABLE -----------------
st.subheader("Overall Duty Assignment Summary")

total_faculty = len(merged)
no_duty_count = (merged["TotalDuty"] == 0).sum()
duty_assigned_count = total_faculty - no_duty_count

summary_df = pd.DataFrame({
    "Metric": [
        "Total Faculty",
        "Faculty Assigned No Duty",
        "Faculty Assigned Duty",
        "Percentage Assigned Duty",
        "Percentage No Duty"
    ],
    "Value": [
        total_faculty,
        no_duty_count,
        duty_assigned_count,
        f"{(duty_assigned_count / total_faculty) * 100:.2f}%",
        f"{(no_duty_count / total_faculty) * 100:.2f}%"
    ]
})

st.dataframe(summary_df)

