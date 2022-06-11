"""Merge 2 surveys into a single file.

Takes the 2 Qualtrics outputs in SPSS format and merges to a tsv.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

import utils



config = utils.load_config()
round1_start = config["round1_start_timestamp"]
round1_end = config["round1_end_timestamp"]
round2_start = config["round2_start_timestamp"]
round2_end = config["round2_end_timestamp"]

# Choose export path.
root_dir = Path(config["root_directory"])
export_path_data = root_dir / "derivatives" / "data.tsv"
export_path_sidecar = export_path_data.with_suffix(".json")

# Load all data and metadata.
initial_df, initial_meta = utils.load_qualtrics_source("initial")
morning_df, morning_meta = utils.load_qualtrics_source("morning")

# Remove most pilot participants and incomplete surveys.
initial_df = utils.standard_qualtrics_clean(initial_df, keep_columns=["StartDate"])
morning_df = utils.standard_qualtrics_clean(morning_df, keep_columns=["StartDate"])

# Remove some more pilot data.
# Reduce entries to those only within the 2 data collection windows.
initial_df = initial_df[
    initial_df["StartDate"].between(round1_start, round1_end)
    |
    initial_df["StartDate"].between(round2_start, round2_end)
]
morning_df = morning_df[
    morning_df["StartDate"].between(round1_start, round1_end)
    |
    morning_df["StartDate"].between(round2_start, round2_end)
]


#################################################################
# Remove ineligible or non-consenting participants
#################################################################

initial_df = (initial_df
    .query("Consent.eq(1)") # Said yes to consent form
    .query("age.gt(1)") # 18 or older
    .query("Instructions.isin([1, 2])") # Expressed interest in continuing to second part
)

# text_response_values = initial_meta.variable_value_labels


# Convert participant IDs to integers (to make sure same format).
initial_df["ParticipantID"] = initial_df["ParticipantID"].astype(int)
morning_df["ParticipantID"] = morning_df["ParticipantID"].astype(int)


# # ########### Convert text responses to ordinal variables.
# # for column in df:
# #     if meta.variable_measure[column] == "scale":
# #         df[column] = pd.Categorical(df[column], ordered=True)


### Calculate aggregate survey scores

# Regular LUSK from initial survey
lusk_columns = [ c for c in initial_df if c.startswith("LUSK") ]
initial_df["LUSK"] = initial_df[lusk_columns].mean(axis=1)

# Dream-specific LUSK from morning report
dream_lusk_columns = [ c for c in morning_df if c.startswith("Dream_LUSK") ]
morning_df["Dream_LUSK"] = morning_df[dream_lusk_columns].mean(axis=1)

# Dream-specific PANAS from morning report
POS_PANAS = [1, 3, 5, 9, 10, 12, 14, 16, 17, 19]
panas_columns = [ c for c in morning_df if c.startswith("PANAS") ]
pos_panas_columns = [ c for c in panas_columns if int(c.split("_")[-1]) in POS_PANAS ]
neg_panas_columns = [ c for c in panas_columns if c not in pos_panas_columns ]
morning_df["PANAS_pos"] = morning_df[pos_panas_columns].sum(axis=1)
morning_df["PANAS_neg"] = morning_df[neg_panas_columns].sum(axis=1)
print("not accounting for NaNs in agg survey scores")



####### Merge the two on participant ID

# Fix participant typos.
morning_id_replacements = {
    195811: 194811,
}
# Remove those who typoed and can't be traced back.
morning_id_removals = [
    601519, # verbal condition but otherwise the ID seems random
]
morning_df["ParticipantID"] = morning_df["ParticipantID"].replace(morning_id_replacements)
morning_df = morning_df[~morning_df["ParticipantID"].isin(morning_id_removals)]

# Someone filled out the morning report multiple times. Keep just the first.
morning_df = morning_df.drop_duplicates(subset="ParticipantID", keep="first")

# We expected all Participant IDs to be random, let's check that they were.
# Check if initial assignments were random,
# then if the manually input IDs in part 2 morning survey exist in part 1 initial.
assert initial_df["ParticipantID"].is_unique, "Overlapping Participant IDs in initial survey"
assert morning_df["ParticipantID"].is_unique, "Overlapping Participant IDs in morning report"
assert morning_df["ParticipantID"].isin(initial_df["ParticipantID"]).all(), "Morning report Participant ID(s) that are not in initial survey"


initial_df = initial_df.set_index("ParticipantID")
morning_df = morning_df.set_index("ParticipantID")
initial_df = initial_df.rename(columns={"StartDate": "StartDate_part1"})
morning_df = morning_df.rename(columns={"StartDate": "StartDate_part2"})
df = pd.concat([initial_df, morning_df], axis=1, verify_integrity=True)

# Convert empty strings to NaNS
df = df.replace("", np.nan)

# Sort so those who completed the second task are on top.
df.insert(0, "Completed_part2", df.index.isin(morning_df.index))
df = df.sort_values("Completed_part2", ascending=False)

# Prepend Participant IDs with letters so it's obviously categorical.
df.index = df.index.map(lambda x: f"sub-{x}")
# # Convert participant ID to letters so it's obviously categorical.
# df.index = df.index.astype(int).astype(str
#     ).map(lambda x: [ string.ascii_uppercase[int(c)] for c in x ]
#     ).str.join("")


# No longer need Consent and Instructions columns.
# Some columns are now worthless.
DROP_COLUMNS = ["Email", "Consent", "Instructions"]
df = df.drop(columns=DROP_COLUMNS)
df = df.drop(columns=lusk_columns+dream_lusk_columns+panas_columns)


############# Generate sidecar based on existing columns

## Start the sidecar with general info but extract the column info from file metadata.
sidecar = {
    "MeasurementToolMetadata": {
        "Description": "Series of custom questionnaires"
    }
}

for col in df:
    column_info = {}
    # Get probe string (if present).
    if col in initial_meta.column_names_to_labels:
        column_info["Probe"] = initial_meta.column_names_to_labels[col]
    elif col in morning_meta.column_names_to_labels:
        column_info["Probe"] = morning_meta.column_names_to_labels[col]
    # Get response option strings (if present).
    if col in initial_meta.variable_value_labels:
        column_info["Levels"] = initial_meta.variable_value_labels[col]
    elif col in morning_meta.variable_value_labels:
        column_info["Levels"] = morning_meta.variable_value_labels[col]
    
    if column_info:
        sidecar[col] = column_info

# Export.
df.to_csv(export_path_data, sep="\t",
    index=True, na_rep="n/a", float_format="%.1f")
with open(export_path_sidecar, "w", encoding="utf-8") as fp:
    json.dump(sidecar, fp, indent=4, sort_keys=False, ensure_ascii=True)
