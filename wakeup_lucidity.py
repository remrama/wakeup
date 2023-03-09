"""
Run correlation analysis asking if lucidity during the dream task influenced reported wakeup time.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pingouin as pg

import utils


################################################################################
# SETUP
################################################################################

wakeup_col = "Wakeup"
lucidity_col = "Task_lucid"

# Load custom plotting settings.
utils.load_matplotlib_settings()

# Choose filepaths.
config = utils.load_config()
root_dir = Path(config["root_directory"])
export_path_plot = root_dir / "derivatives" / "wakeup_lucidity-plot.png"
export_path_desc = root_dir / "derivatives" / "wakeup_lucidity-desc.tsv"
export_path_stat = root_dir / "derivatives" / "wakeup_lucidity-stat.tsv"

# Load data.
df, meta = utils.load_raw(trim=True)

# Reduce to only wakeup task conditions.
df = df.query("Condition != 'Clench'")
# Ensure values are floats.
df[wakeup_col] = df[wakeup_col].astype(float)
df[lucidity_col] = df[lucidity_col].astype(float)


################################################################################
# STATISTICS
################################################################################

# Get descriptives.
desc = df[[wakeup_col, lucidity_col]].describe().T.rename_axis("variable")

# Run correlation.
x = df[lucidity_col].to_numpy()
y = df[wakeup_col].to_numpy()
stat = pg.corr(x, y, method="kendall")


################################################################################
# PLOTTING
################################################################################

# Get regression line predictor.
coef = np.polyfit(x, y, 1)
poly1d_func = np.poly1d(coef)

# Grab ticks and labels from the sidecar file.
xticks, xticklabels = zip(*meta[wakeup_col]["Levels"].items())
xticks = list(map(int, xticks))
yticks, yticklabels = zip(*meta[lucidity_col]["Levels"].items())
yticks = list(map(int, yticks))

# Open figure.
fig, ax = plt.subplots(figsize=(2, 2))

# Draw dots and regression line.
ax.plot(x, y, "ko", ms=5, alpha=0.2)
ax.plot(x, poly1d_func(x), "-k")

# Aesthetics.
ax.set_xticks(xticks)
ax.set_yticks(yticks)
ax.set_xlabel(lucidity_col)
ax.set_ylabel(wakeup_col)
ax.grid(True, axis="both")
ax.set_aspect("equal")
ax.margins(0.1)
ax.tick_params(direction="out", axis="both", which="both", top=False, right=False)


################################################################################
# EXPORT
################################################################################

desc.to_csv(export_path_desc, na_rep="n/a", sep="\t")
stat.to_csv(export_path_stat, index_label="method", na_rep="n/a", sep="\t")
plt.savefig(export_path_plot)
plt.savefig(export_path_plot.with_suffix(".pdf"))
plt.savefig(export_path_plot.with_suffix(".svg"))
