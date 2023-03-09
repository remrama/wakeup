"""
Run correlation analysis asking if dream control influenced emotion.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pingouin as pg

import utils


################################################################################
# SETUP
################################################################################

control_col = "Dream_LUSK"
emotion_col = "PANAS_neg"

control_limits = [1, 5]  # LUSK total min, max values
emotion_limits = [10, 50]  # PANAS total min and max values
control_limits[0] -= 0.5
control_limits[1] += 0.5
emotion_limits[0] -= 5
emotion_limits[1] += 5

# Load custom plotting settings.
utils.load_matplotlib_settings()

# Choose filepaths.
config = utils.load_config()
root_dir = Path(config["root_directory"])
export_path_plot = root_dir / "derivatives" / "control_emotion-plot.png"
export_path_desc = root_dir / "derivatives" / "control_emotion-desc.tsv"
export_path_stat = root_dir / "derivatives" / "control_emotion-stat.tsv"

# Load data.
df, meta = utils.load_raw(trim=True)

# Reduce to only wakeup task conditions.
df = df.query("Condition != 'Clench'")
# Ensure values are floats.
df[control_col] = df[control_col].astype(float)
df[emotion_col] = df[emotion_col].astype(float)


################################################################################
# STATISTICS
################################################################################

# Get descriptives.
desc = df[[control_col, emotion_col]].describe().T.rename_axis("variable")

# Run correlation.
x = df[control_col].to_numpy()
y = df[emotion_col].to_numpy()
stat = pg.corr(x, y, method="kendall")


################################################################################
# PLOTTING
################################################################################

# Get regression line predictor.
coef = np.polyfit(x, y, 1)
poly1d_func = np.poly1d(coef) 

# Open figure.
fig, ax = plt.subplots(figsize=(2, 2))

# Draw dots and regression line.
ax.plot(x, y, "ko", ms=5, alpha=0.2)
ax.plot(x, poly1d_func(x), "-k")

# Aesthetics.
ax.set_xlabel(control_col)
ax.set_ylabel(emotion_col)
ax.set_xlim(*control_limits)
ax.set_ylim(*emotion_limits)
ax.xaxis.set_major_locator(plt.MultipleLocator(1))
ax.yaxis.set_major_locator(plt.MultipleLocator(10))
ax.grid(True, axis="both")
# ax.margins(0.1)


################################################################################
# EXPORT
################################################################################

desc.to_csv(export_path_desc, na_rep="n/a", sep="\t")
stat.to_csv(export_path_desc, index_label="method", na_rep="n/a", sep="\t")
plt.savefig(export_path_plot)
plt.savefig(export_path_plot.with_suffix(".pdf"))
plt.savefig(export_path_plot.with_suffix(".svg"))
