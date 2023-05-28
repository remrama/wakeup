"""Get some general summary statistics of the whole sample."""
from pathlib import Path

import pandas as pd

import utils


################################################################################
# SETUP
################################################################################

# Load configuration file.
config = utils.load_config()

# Choose filepaths.
root_dir = Path(config["root_directory"])
export_path = root_dir / "derivatives" / "demographics.tsv"
export_path_freq = root_dir / "derivatives" / "demographics_freq.tsv"


################################################################################
# DESCRIPTIVE STATISTICS INCLUDING DREAM RECALL FREQUENCY
################################################################################

# Load trimmed data.
data, meta = utils.load_raw(trim=True)

columns = [
    "age", "gender", "Dream_recall", "Nightmare_recall", "Lucid_recall",
]

desc = data[columns].describe().T
desc.to_csv(export_path, index_label="variable", na_rep="n/a", sep="\t")


################################################################################
# LONG TABLE WITH FREQUENCIES FOR EACH LIKERT RESPONSE OPTION
################################################################################

# Load data.
df, meta = utils.load_raw(trim=False)

# Add a new column that identifies varying levels of study completion.
def participation_level(row):
    level = "pt1_finished"
    if row["Completed_part2"]:
        level = "pt2_finished"
    if row["Task_completion"] == 3:
        level = "pt2_finished_task"
    return level
df["completion"] = df.apply(participation_level, axis=1)

# Pick variables to include in frequency table.
variables = [
    "age", "gender", "Condition", "recruitment",
    "Dream_recall", "Nightmare_recall", "Lucid_recall",
]

# Get full text labels.
for c in variables:
    if c != "Condition":
        response_legend = {int(k): v for k, v in meta[c]["Levels"].items()}
        df[c] = df[c].map(response_legend)

freqs = (df
    .set_index("completion")[variables]
    .stack()
    .groupby(level=[0,1])
    .value_counts()
    .unstack(0)
    .fillna(0)
    .rename_axis(None, axis=1)
    .rename_axis(["response", "probe"])
    .pipe(lambda d: d.assign(total=d.sum(axis=1)))
    .astype(int)
)

freqs.to_csv(export_path_freq, index=True, na_rep="n/a", sep="\t")
