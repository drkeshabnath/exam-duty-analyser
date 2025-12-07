import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import difflib

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

# ----------------- NAME NORMALISATION & MATCHING -----------------

TITLE_TOKENS = {"dr", "mr", "mrs", "ms", "prof", "sir", "smt", "kumari"}

def normalize_name(raw: str) -> str:
    """Lowercase, remove titles and extra spaces to get a comparable form."""
    if not isinstance(raw, str):
        raw = str(raw)
    raw = raw.replace(".", " ")
    tokens = [t for t in raw.lower().split() if t not in TITLE_TOKENS]
    return " ".join(tokens)

# Precompute normalized master names
master_df = pd.DataFrame({"MasterName": full_faculty_list})
master_df["MasterNorm"] = master_df["MasterName"].apply(normalize_name)
master_norm_list = master_df["MasterNorm"].tolist()

def fuzzy_map_name(raw_name: str, cutoff: float = 0.75):
    """
    Map a raw uploaded name to the closest master faculty name.
    Returns (best_name, score, strategy) or (None, 0, 'no_match').
    """
    if not isinstance(raw_name, str):
        raw_name = str(raw_name)
    raw_clean = raw_name.strip()
    if raw_clean == "":
        return None, 0.0, "empty"

    norm = normalize_name(raw_clean)

    # 1. Exact match on raw (case-insensitive)
    for master in full_faculty_list:
        if master.lower().strip() == raw_clean.lower():
            return master, 1.0, "exact_raw"

    # 2. Exact match on normalized
    exact_norm = master_df[master_df["MasterNorm"] == norm]
    if not exact_norm.empty:
        return exact_norm.iloc[0]["MasterName"], 1.0, "exact_norm"

    # 3. Fuzzy match on normalized using difflib
    if master_norm_list:
        best_norm = difflib.get_close_matches(norm, master_norm_list, n=1, cutoff=0.0)
        if best_norm:
            candidate_norm = best_norm[0]
            score = difflib.SequenceMatcher(None, norm, candidate_norm).ratio()
            if score >= cutoff:
                candidate_row = master_df[master_df["MasterNorm"] == candidate_norm].iloc[0]
                return candidate_row["MasterName"], score, "fuzzy"

    # 4. Try last-name-based heuristic if fuzzy score was low
    tokens = norm.split()
    if len(tokens) >= 1:
        last = tokens[-1]
        # candidates where last name appears
        candidates = master_df[master_df["MasterNorm"].str.contains(last)]
        if len(candidates) == 1:
            return candidates.iloc[0]["MasterName"], 0.7, "lastname_unique"

    # 5. No good match
    return None, 0.0, "no_match"

# ----------------- STREAMLIT CONFIG -----------------
st.set_page_config(page_title="Duty Analysis with Fuzzy Name Matching", layout="wide")
st.title("Exam Duty Analysis")
st.caption("Upload one duty file: first column = faculty names (approx), other columns = duty sessions (1 / blank).")

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
possible_name_cols = [
    "Name", "NAME", "Faculty", "Faculty Name",
    "Invigilator", "Invigilator Name"
]

name_col = None
for c in df.columns:
    if str(c).strip() in possible_name_cols:
        name_col = c
        break

if name_col is None:
    name_col = df.columns[0]
    st.info(f"No standard 'Name' column found. Using first column as Name: **{name_col}**")

# Rename to RawName
if name_col != "RawName":
    df = df.rename(columns={name_col: "RawName"})

df["RawName"] = df["RawName"].astype(str).str.strip()

# ----------------- DUTY COLUMNS -----------------
duty_cols = [c for c in df.columns if c != "RawName"]

if not duty_cols:
    st.error("No duty columns found (only name column present). Please add date/session columns.")
    st.stop()

# Convert duty columns to numeric, then >0 => 1 else 0
df[duty_cols] = df[duty_cols].apply(lambda col: pd.to_numeric(col, errors="coerce"))
df[duty_cols] = df[duty_cols].fillna(0)
df[duty_cols] = (df[duty_cols] > 0).astype(int)

st.subheader("Cleaned Duty Matrix (1 = Duty, 0 = No Duty)")
st.dataframe(df)

# ----------------- TOTAL DUTY PER RAW NAME -----------------
df["TotalDuty"] = df[duty_cols].sum(axis=1)
st.success(f"Total faculty rows processed: {len(df)}")

# ----------------- FUZZY MAP UPLOADED NAMES TO MASTER LIST -----------------
st.subheader("Name Matching to Master Faculty List")

mapped_names = []
match_scores = []
strategies = []

for raw in df["RawName"]:
    best_name, score, strat = fuzzy_map_name(raw)
    mapped_names.append(best_name)
    match_scores.append(score)
    strategies.append(strat)

df["MappedName"] = mapped_names
df["MatchScore"] = match_scores
df["MatchStrategy"] = strategies

st.markdown("#### Sample of Name Mapping")
st.dataframe(df[["RawName", "MappedName", "MatchScore", "MatchStrategy", "TotalDuty"]].head(15))

# Rows where no good match found
unmatched = df[df["MappedName"].isna()]
if not unmatched.empty:
    st.warning("Some names could not be confidently matched to the master faculty list:")
    st.dataframe(unmatched[["RawName", "TotalDuty", "MatchScore", "MatchStrategy"]])

# ----------------- FACULTY-WISE SUMMARY (BY RAW NAME) -----------------
st.subheader("Faculty-wise Duty Summary")
faculty_summary_raw = (
    df.groupby(["RawName"])["TotalDuty"]
    .sum()
    .reset_index()
    .sort_values("TotalDuty", ascending=False)
)
st.dataframe(faculty_summary_raw)

# ----------------- CANONICAL SUMMARY (BY MAPPED MASTER NAME) -----------------
st.subheader("Canonical Duty Summary")

# Only keep rows that got mapped to a master name
mapped_df = df[~df["MappedName"].isna()].copy()
canonical_summary = (
    mapped_df.groupby("MappedName")["TotalDuty"]
    .sum()
    .reset_index()
    .sort_values("TotalDuty", ascending=False)
    .rename(columns={"MappedName": "Name"})
)

st.dataframe(canonical_summary)

# ----------------- CHARTS (CANONICAL) -----------------
st.subheader("Graphical Analysis")
total_duty_sum = canonical_summary["TotalDuty"].sum()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Duty Count per Faculty (Canonical)")
    if total_duty_sum == 0:
        st.info("All TotalDuty values are 0 – no duties assigned (after mapping).")
    else:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        canonical_summary.set_index("Name")["TotalDuty"].plot(kind="bar", ax=ax1)
        ax1.set_ylabel("Duty Count")
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
        ax1.set_title("Duty Distribution (Canonical Names)")
        fig1.tight_layout()
        st.pyplot(fig1)

with col2:
    st.markdown("### Duty Share (Canonical)")
    if total_duty_sum == 0:
        st.info("Cannot draw pie chart – all TotalDuty values are 0.")
    else:
        fig2, ax2 = plt.subplots(figsize=(6, 4))

ax2.pie(
    canonical_summary["TotalDuty"],
    labels=None,                # remove labels from pie itself
    autopct="%1.1f%%",
    pctdistance=0.85,           # move % slightly outward
)

# Add labels as legend (NO OVERLAP)
ax2.legend(
    canonical_summary["Name"],
    title="Faculty",
    loc="center left",
    bbox_to_anchor=(1, 0.5),
    fontsize=8
)

ax2.set_title("Duty Share (%) – Canonical")
st.pyplot(fig2)



        
       # fig2, ax2 = plt.subplots(figsize=(6, 4))
       # ax2.pie(
        #    canonical_summary["TotalDuty"],
        #    labels=canonical_summary["Name"],
         #   autopct="%1.1f%%"
        #)
        #ax2.set_title("Duty Share (%) – Canonical")
        #fig2.tight_layout()
        #st.pyplot(fig2)

# ----------------- ADVANCED ANALYSIS WITH MASTER LIST -----------------
st.subheader("Advanced Analysis")

roster_df = pd.DataFrame({"Name": full_faculty_list})
roster_df["Name"] = roster_df["Name"].astype(str).str.strip()

# Merge master list with canonical duty summary
merged = roster_df.merge(canonical_summary, on="Name", how="left")
merged["TotalDuty"] = merged["TotalDuty"].fillna(0).astype(int)
merged = merged.sort_values("TotalDuty")

# 1. Faculty with zero duties
st.markdown("### Faculty with ZERO Duties")
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
