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
    if not isinstance(name, str): 
        name = str(name)

    raw = name.strip()
    norm = normalize(raw)

    # Exact match
    for m in full_faculty_list:
        if m.lower() == raw.lower():
            return m, 1.0

    # Exact normalized match
    eq = master_df[master_df["Norm"] == norm]
    if not eq.empty:
        return eq.iloc[0]["MasterName"], 1.0

    # Fuzzy match
    best = difflib.get_close_matches(norm, master_df["Norm"].tolist(), n=1)
    if best:
        score = difflib.SequenceMatcher(None, norm, best[0]).ratio()
        if score >= cutoff:
            return master_df[master_df["Norm"] == best[0]].iloc[0]["MasterName"], score

    return None, 0.0


# -------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------
st.set_page_config(page_title="Multi-Semester Duty Analyzer", layout="wide")
st.title("Multi-Semester Exam Duty Analyzer")
st.caption("Automatically merges multiple semester duty files and computes total duty per faculty.")


# -------------------------------------------------
# LOAD ALL DUTY FILES
# -------------------------------------------------
DATA_FOLDER = "duty_files"
files = [f for f in os.listdir(DATA_FOLDER)
         if f.lower().endswith((".xlsx",".xls",".csv"))]

if not files:
    st.error("No files found in duty_files/. Please add duty sheets.")
    st.stop()

st.success(f"Detected {len(files)} files")

summary_all = []


# -------------------------------------------------
# PROCESS EACH FILE
# -------------------------------------------------
for filename in files:
    st.markdown(f"### 📄 Processing File: **{filename}**")

    path = os.path.join(DATA_FOLDER, filename)

    df = pd.read_excel(path) if filename.endswith((".xlsx",".xls")) else pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    name_col = df.columns[0]
    df = df.rename(columns={name_col: "RawName"})
    #df["RawName"] = df["RawName"].astype(str).strip()
    df["RawName"] = df["RawName"].astype(str).str.strip()


    duty_cols = [c for c in df.columns if c != "RawName"]

    df[duty_cols] = df[duty_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    df[duty_cols] = (df[duty_cols] > 0).astype(int)

    # fuzzy map
    df["MappedName"], df["Score"] = zip(*df["RawName"].apply(lambda x: fuzzy_map(x)))

    df["TotalDuty"] = df[duty_cols].sum(axis=1)

    summary = df.groupby("MappedName")["TotalDuty"].sum().reset_index()
    summary["Semester"] = filename

    summary_all.append(summary)


# -------------------------------------------------
# MERGE ALL SEMESTERS
# -------------------------------------------------
final_df = pd.concat(summary_all)

final_total = final_df.groupby("MappedName")["TotalDuty"].sum().reset_index()
final_total = final_total.sort_values("TotalDuty", ascending=False)

st.header("Total Duty Across All Semesters")
st.dataframe(final_total)


# -------------------------------------------------
# BUILD MERGED TABLE FOR ZERO, MIN, MAX
# -------------------------------------------------
merged = pd.DataFrame({"Name": full_faculty_list})
merged = merged.merge(final_total, left_on="Name", right_on="MappedName", how="left")
merged["TotalDuty"] = merged["TotalDuty"].fillna(0).astype(int)
merged = merged.drop(columns=["MappedName"])


# -------------------------------------------------
# HEATMAP
# -------------------------------------------------
st.subheader("Heatmap (Faculty × Semester)")

pivot = final_df.pivot_table(index="MappedName",
                             columns="Semester",
                             values="TotalDuty",
                             aggfunc="sum",
                             fill_value=0)

#fig, ax = plt.subplots(figsize=(14,10))
#sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt="d")
#st.pyplot(fig)

fig, ax = plt.subplots(figsize=(14, 10))
sns.heatmap(
    heatmap_df,
    cmap="YlOrRd",  # Yellow → Orange → Red
    annot=True,
    fmt="d",
    linewidths=0.4,
    linecolor="black",
    cbar_kws={'label': 'Duty Count'},
)
ax.set_title("Duty Heatmap", fontsize=18, fontweight='bold')
st.pyplot(fig)


# -------------------------------------------------
# MINIMUM DUTY
# -------------------------------------------------
st.subheader("Faculty With Minimum Duty")

non_zero = merged[merged["TotalDuty"] > 0]

if non_zero.empty:
    st.info("No faculty assigned duties.")
else:
    min_val = non_zero["TotalDuty"].min()
    st.dataframe(non_zero[non_zero["TotalDuty"] == min_val])


# -------------------------------------------------
# MAXIMUM DUTY
# -------------------------------------------------
st.subheader("Faculty With Maximum Duty")

max_val = merged["TotalDuty"].max()
st.dataframe(merged[merged["TotalDuty"] == max_val])


# -------------------------------------------------
# ZERO DUTY
# -------------------------------------------------
st.subheader("Faculty With ZERO Duties")
st.dataframe(merged[merged["TotalDuty"] == 0])


# -------------------------------------------------
# DISTRIBUTION
# -------------------------------------------------
st.subheader("Full Duty Distribution")
st.dataframe(merged)

st.bar_chart(merged.set_index("Name")["TotalDuty"])
# ----------------- FINAL SUMMARY TABLE -----------------
st.subheader("Overall Duty Assignment Summary")

# Total faculty in master list
total_faculty = len(merged)

# Counts
no_duty_count = (merged["TotalDuty"] == 0).sum()
duty_assigned_count = total_faculty - no_duty_count

# Avoid division-by-zero error
if total_faculty > 0:
    pct_assigned = (duty_assigned_count / total_faculty) * 100
    pct_no_duty = (no_duty_count / total_faculty) * 100
else:
    pct_assigned = pct_no_duty = 0

# Additional statistics
if merged["TotalDuty"].sum() > 0:
    avg_duties = merged["TotalDuty"].mean()
    max_duty = merged["TotalDuty"].max()
    min_non_zero = merged[merged["TotalDuty"] > 0]["TotalDuty"].min() \
                    if (merged["TotalDuty"] > 0).any() else 0
else:
    avg_duties = max_duty = min_non_zero = 0

summary_df = pd.DataFrame({
    "Metric": [
        "Total Faculty in Master List",
        "Faculty Assigned NO Duty",
        "Faculty Assigned SOME Duty",
        "Percentage Assigned Duty",
        "Percentage No Duty",
        "Average Duty Load",
        "Maximum Duty Assigned",
        "Minimum Duty Assigned (Non-zero)"
    ],
    "Value": [
        total_faculty,
        no_duty_count,
        duty_assigned_count,
        f"{pct_assigned:.2f}%",
        f"{pct_no_duty:.2f}%",
        f"{avg_duties:.2f}",
        max_duty,
        min_non_zero
    ]
})

st.dataframe(summary_df, use_container_width=True)

