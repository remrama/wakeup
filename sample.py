"""Describe a specific feature of the the final sample.

Choose a feature to export a distribution plot and data file.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt

import utils


# Parse command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument(
    "-f", "--feature", type=str, required=True, choices=["age", "gender", "Condition", "recruitment"]
)
args = parser.parse_args()

feature = args.feature


# Load custom plot settings and grab configuration file.
utils.load_matplotlib_settings()
config = utils.load_config()

# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data_trimmed.tsv"
export_path_data = root_dir / "derivatives" / f"sample_{feature}.tsv".lower()
export_path_plot = export_path_data.with_suffix(".png")

# Load data.
df, sidecar = utils.load_data_and_sidecar(import_path, trim=True)

# # Drop to final sample.
# df = df.query("Completed_part2.eq(True)"
#     ).query("Task_completion.eq(3)")


ser = df[feat].value_counts().rename("count").rename_axis(feature).sort_index()

# Get full text labels.
if feat != "Condition":
    response_legend = { int(k): v.split(" ")[0] for k, v in sidecar[feature]["Levels"].items() }
    ser.index = ser.index.map(response_legend)

# Draw plot.
fig, ax = plt.subplots(figsize=(3.5, 3.5))
bars = ax.bar(
    ser.index, ser.values,
    color="white", edgecolor="black", linewidth=1,
)

# Aesthetics.
ax.set_xlabel(feature.capitalize())
ax.set_ylabel("Count")

# Export.
plt.savefig(export_path_plot)
ser.to_csv(export_path_data, sep="\t")
