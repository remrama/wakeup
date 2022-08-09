"""Run chi2 analysis, export table and plot.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pingouin as pg
import seaborn as sns

import utils

config = utils.load_config()

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--test", type=str, required=True,
    choices=["wakeup", "impact"])
args = parser.parse_args()

test = args.test


# Pick columns/variables for analysis.
if test == "wakeup":
    colA, colB = "Condition", "Wakeup"

# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data.tsv"
export_path_plot = root_dir / "results" / f"chisquared_{test}.png"
export_path_stats = export_path_plot.with_suffix(".tsv")

# Load data.
df, sidecar = utils.load_data_and_sidecar(import_path)

# Drop to final sample.
df = df.query("Completed_part2.eq(True)"
    ).query("Task_completion.eq(3)"
    ).query("Condition.isin(['Clench', 'Visual'])")

# Binarize wakeup success.
df["Wakeup"] = df["Wakeup"].le(2)
# Booleanize the condition.
df["Condition"] = df["Condition"].ne("Clench")

observed, stats = pg.chi2_mcnemar(df, colA, colB)