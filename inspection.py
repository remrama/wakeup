"""Inspect responses to either survey.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

import utils

config = utils.load_config()

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--survey", type=str, required=True,
    choices=["initial", "morning"])
args = parser.parse_args()

survey = args.survey


# Pick columns to plot.
if survey == "initial":
    columns = [
        "Dream_recall", "Nightmare_recall",
        "Lucid_recall", "LUSK",
    ]
elif survey == "morning":
    columns = [
        "Multiple_attempts",
        "Wakeup", "Wakeup_impact",
        "Lucidity", "Nightmare", "Sleep_paralysis",
        "Dream_LUSK", "PANAS_pos", "PANAS_neg",
    ]

# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data.tsv"
export_path_plot = root_dir / "results" / f"inspection_{survey}.png"

# Load data.
df, sidecar = utils.load_data_and_sidecar(import_path)

# Drop to final sample.
df = df.query("Completed_part2.eq(True)"
    ).query("Task_completion.eq(3)")

# Draw.
g = sns.pairplot(df,
    vars=columns,
    kind="hist", corner=True,
    plot_kws=dict(cmap="binary"),
    diag_kws=dict(fill=False, color="black"),
)

# Aesthetics.
# [ ax.invert_xaxis() for ax in g.axes.flat if isinstance(ax, plt.Axes) ]
g.fig.align_labels()

# Export.
plt.savefig(export_path_plot, dpi=300)