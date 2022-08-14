"""Describe a specific feature of the the final sample.
Choose a feature to export a distribution plot and data file.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt

import utils

config = utils.load_config()


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--feature", type=str, required=True,
    choices=["age", "gender", "Condition", "recruitment"])
args = parser.parse_args()

feat = args.feature

# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data_trimmed.tsv"
export_path_data = root_dir / "results" / f"sample_{feat}.tsv".lower()
export_path_plot = export_path_data.with_suffix(".png")

# Load data.
df, sidecar = utils.load_data_and_sidecar(import_path)

# # Drop to final sample.
# df = df.query("Completed_part2.eq(True)"
#     ).query("Task_completion.eq(3)")

# if feat == "recruitment":
#     # recruitment_5_TEXT is for "Other" write-in
#     # recruitment_7_TEXT is for "Online dream forum" write-in
#     # recruitment_8_TEXT is for "Email list" write-in
#     # (Don't line up with response options because of the reordering.)
#     df["recruitment_TEXT"] = df["recruitment_5_TEXT"].fillna(df["recruitment_7_TEXT"]).fillna(df["recruitment_8_TEXT"])
#     # These aren't really interesting so I'm ditching them.


ser = df[feat].value_counts().rename("count").rename_axis(feat).sort_index()

# Get full text labels.
if feat != "Condition":
    response_legend = { int(k): v.split(" ")[0] for k, v in sidecar[feat]["Levels"].items() }
    ser.index = ser.index.map(response_legend)

# Draw plot.
fig, ax = plt.subplots(figsize=(3.5, 3.5), constrained_layout=True)
bars = ax.bar(
    ser.index, ser.values,
    color="white", edgecolor="black", linewidth=1,
)

# Aesthetics.
ax.set_xlabel(feat.capitalize())
ax.set_ylabel("Count")

# Export.
plt.savefig(export_path_plot, dpi=300)
ser.to_csv(export_path_data, sep="\t")