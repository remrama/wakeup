"""
Merge the 2 source data files (Initial Survey and Morning Report)
into 1 tsv file. Source files are exported as SPSS from Qualtrics.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import utils


################################################################################
# SETUP
################################################################################


# Load variables from configuration file.
config = utils.load_config()
round1_start = config["round1_start_timestamp"]
round1_end = config["round1_end_timestamp"]
round2_start = config["round2_start_timestamp"]
round2_end = config["round2_end_timestamp"]
root_dir = Path(config["root_directory"])

# Choose export path.
export_path_data = root_dir / "derivatives" / "data.tsv"
export_path_sidecar = export_path_data.with_suffix(".json")

# Load all data and metadata.
initial_df, initial_meta = utils.load_qualtrics_source("initial")
morning_df, morning_meta = utils.load_qualtrics_source("morning")


################################################################################
# PARTICIPANT REMOVAL
################################################################################


# Remove pilot participants and incomplete surveys.
initial_df = utils.standard_qualtrics_clean(initial_df, keep_columns=["StartDate"])
morning_df = utils.standard_qualtrics_clean(morning_df, keep_columns=["StartDate"])
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

# Remove participants who did not consent or are ineligible.
initial_df = (
    initial_df
    .query("Consent.eq(1)")  # Said yes to consent form
    .query("age.gt(1)")  # 18 or older
    .query("Instructions.isin([1, 2])")  # Expressed interest in continuing to second part
)


################################################################################
# MERGE FILES
################################################################################


# Convert participant IDs to integers (to make sure same format).
initial_df["ParticipantID"] = initial_df["ParticipantID"].astype(int)
morning_df["ParticipantID"] = morning_df["ParticipantID"].astype(int)

# Fix participant typos.
morning_id_replacements = {195811: 194811}
morning_df["ParticipantID"] = morning_df["ParticipantID"].replace(morning_id_replacements)
# Remove those who typoed and can't be traced back.
morning_id_removals = [601519]
morning_df = morning_df[~morning_df["ParticipantID"].isin(morning_id_removals)]

# Someone filled out the morning report multiple times. Keep just the first.
morning_df = morning_df.drop_duplicates(subset="ParticipantID", keep="first")

# We expected all Participant IDs to be random, let's check that they were.
# Check if initial assignments were random,
# then if the manually input IDs in part 2 morning survey exist in part 1 initial.
assert initial_df["ParticipantID"].is_unique, "Found overlapping Participant IDs in initial survey."
assert morning_df["ParticipantID"].is_unique, "Found overlapping Participant IDs in morning report."
assert morning_df["ParticipantID"].isin(initial_df["ParticipantID"]).all(), (
    "Found Participant ID(s) in morning report that are not in initial survey."
)

# Merge dataframes.
initial_df = initial_df.set_index("ParticipantID").rename(columns={"StartDate": "StartDate_part1"})
morning_df = morning_df.set_index("ParticipantID").rename(columns={"StartDate": "StartDate_part2"})
df = pd.concat([initial_df, morning_df], axis=1, verify_integrity=True)

# Convert empty strings to NaNs
df = df.replace("", np.nan)

# Add a column denoting which participants completed part 2.
df.insert(0, "Completed_part2", df.index.isin(morning_df.index))
# Sort so those who completed part 2 are on top.
df = df.sort_values("Completed_part2", ascending=False)

# Prepend Participant IDs with letters so they are obviously categorical.
df.index = df.index.map(lambda x: f"sub-{x}")


################################################################################
# LIKERT REMAPPINGS AND SIDECAR INFO
################################################################################

# Generate sidecar based on existing columns
# and
# remap Likert ordering (if options were moved in creation they are in nonsensical order).
# !! Remappings must be applied before deriving aggregate scale scores.

## Start the sidecar with general info but extract the column info from file metadata.
sidecar = {
    "MeasurementToolMetadata": {
        "Description": "Series of custom questionnaires"
    }
}

likert_remappings = {}

for col in df:
    column_info = {}
    probe = None
    levels = None

    # Get probe string (if present).
    if col in initial_meta.column_names_to_labels:
        probe = initial_meta.column_names_to_labels[col]
    elif col in morning_meta.column_names_to_labels:
        probe = morning_meta.column_names_to_labels[col]
    # Get response option strings (if present).
    if col in initial_meta.variable_value_labels:
        levels = initial_meta.variable_value_labels[col]
    elif col in morning_meta.variable_value_labels:
        levels = morning_meta.variable_value_labels[col]
    
    if probe is not None:
        column_info["Probe"] = probe
    if levels is not None:
        # values = list(levels.keys())
        # if ((values[0] != 1)
        #     or values != sorted(values)
        #     or np.any(np.diff(values) != 1)):
        #     new_values = range(1, len(values)+1)
        #     levels = { k: v for k, v in zip(new_values, levels.values()) }
        #     likert_remappings[col] = { x: y for x, y in zip(values, new_values) }
        # levels = { int(k): v for k, v in levels.items() }
        if not col.startswith("Email"):
            if col in initial_meta.column_names_to_labels:
                utils.validate_likert_scales(initial_meta, col)
            else:
                utils.validate_likert_scales(morning_meta, col)
        levels = { int(k): v for k, v in levels.items() }
        column_info["Levels"] = levels

    if column_info:
        sidecar[col] = column_info

# Apply remappings.
for col, remap in likert_remappings.items():
    df[col] = df[col].replace(remap)


################################################################################
# CALCULATE AGGREGATED SURVEY SCORES
################################################################################


def imputed_sum(row, cutoff=0.5):
    """Return imputed sum if proportion of values that are missing are greater than `cutoff`."""
    return np.nan if row.isna().mean() > cutoff else row.fillna(row.mean()).sum()

def imputed_mean(row, cutoff=0.5):
    return np.nan if row.isna().mean() > cutoff else row.fillna(row.mean()).mean()

# Aggregate trait LUSK from initial survey.
lusk_columns = [c for c in df if c.startswith("LUSK")]
df["LUSK"] = df[lusk_columns].apply(imputed_mean, axis=1)

# Aggregate dream-specific state LUSK from morning report.
dream_lusk_columns = [c for c in df if c.startswith("Dream_LUSK")]
df["Dream_LUSK"] = df[dream_lusk_columns].apply(imputed_mean, axis=1)

# Aggregate dream-specific PANAS from morning report.
POS_PANAS = [1, 3, 5, 9, 10, 12, 14, 16, 17, 19]
panas_columns = [c for c in df if c.startswith("PANAS")]
pos_panas_columns = [c for c in panas_columns if int(c.split("_")[-1]) in POS_PANAS]
neg_panas_columns = [c for c in panas_columns if c not in pos_panas_columns]
df["PANAS_pos"] = df[pos_panas_columns].apply(imputed_sum, axis=1)
df["PANAS_neg"] = df[neg_panas_columns].apply(imputed_sum, axis=1)

# Drop unneccessary columns.
drop_columns = ["Email", "Consent", "Instructions"]
drop_columns = drop_columns + lusk_columns + dream_lusk_columns + panas_columns
df = df.drop(columns=drop_columns)
sidecar = {k: v for k, v in sidecar.items() if k in df or k == "MeasurementToolMetadata"}


################################################################################
# EXPORT
################################################################################

df.to_csv(export_path_data, index=True, na_rep="n/a", float_format="%.3f", sep="\t")
with open(export_path_sidecar, "w", encoding="utf-8") as fp:
    json.dump(sidecar, fp, indent=4, sort_keys=False, ensure_ascii=True)
