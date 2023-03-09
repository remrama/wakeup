"""Run regression analysis asking if dream task influenced reported wakeup time.
"""
from math import ceil
from pathlib import Path

import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg

import utils


################################################################################
# SETUP
################################################################################

task_mapping = {"Clench": 0, "Visual": 1}
task_col = "Condition"
wakeup_col = "Wakeup"

# Load custom plotting settings.
utils.load_matplotlib_settings()

# Choose filepaths.
config = utils.load_config()
root_dir = Path(config["root_directory"])
export_path_plot = root_dir / "derivatives" / "wakeup_timing-plot.png"
export_path_freq = root_dir / "derivatives" / "wakeup_timing-freq.tsv"
export_path_stat = root_dir / "derivatives" / "wakeup_timing-stat.tsv"

# Load data.
df, meta = utils.load_raw(trim=True)

# Reduce to Clench and Visual conditions.
df = df.query(f"{task_col}.isin(['Clench', 'Visual'])")
# Make sure columns are integers.
df[task_col] = df[task_col].map(task_mapping).astype(int)
df[wakeup_col] = df[wakeup_col].astype(int)


################################################################################
# STATISTICS
################################################################################

# Run regression.
stat = pg.linear_regression(X=df[wakeup_col], y=df[task_col], add_intercept=True)

# Get descriptive counts.
inverted_mapping = {v: k for k, v in task_mapping.items()}
freq = (df
    .groupby(task_col)[wakeup_col]
    .value_counts(sort=False, dropna=False)
    .rename("frequency")
    .reset_index(drop=False)
    .replace({task_col: inverted_mapping})
    .rename(columns={task_col: "Task"})
)

# Export frequencies and stats.
freq.to_csv(export_path_freq, index=False, na_rep="n/a", sep="\t")
stat.to_csv(export_path_stat, index=False, na_rep="n/a", sep="\t")


################################################################################
# PLOTTING
################################################################################

figsize = (3, 3)
barwidth = 0.8
xtick_labels = ["Clench", "Visual"]
n_tasks = len(xtick_labels)
xticks = range(n_tasks)
y_labels = ["during", "0-5 seconds", "6-30 seconds", "31-120 seconds", ">120 seconds"]
cmap = cc.cm.diverging_linear_protanopic_deuteranopic_bjy_57_89_c34
cmap = cc.cm.gwv
cmap = cc.cm.linear_protanopic_deuteranopic_kbw_5_95_c34
cmap = cc.cm.linear_tritanopic_kcw_5_95_c22

# Make sure wakeup responses are categorical.
cats, cat_labels = zip(*meta[wakeup_col]["Levels"].items())
cats = list(map(int, cats))
# FLIP order of values, so HIGHER is EARLIER awakening.
df[wakeup_col] = df[wakeup_col].rsub(max(cats))
df[wakeup_col] = pd.Categorical(df[wakeup_col], cats, ordered=True)

n_categories = len(cats)
midpoint = ceil((cats[0] + cats[-1]) / 2)


# Get relative percents.
pcts = (df
    .groupby(task_col)[wakeup_col]
    .value_counts(sort=False, dropna=False, normalize=True)
    .multiply(100)
    .unstack(0)
)
pcts.columns = pcts.columns.map(inverted_mapping)
ss
# pcts = pcts.shift(fill_value=0)
# pcts = pcts.cumsum().shift(fill_value=0)
left_adjust = pcts.loc[:midpoint-1].sum(axis=0)
# ser = ser[ser!=0]
pcts = pcts.cumsum().shift(fill_value=0).sub(left_adjust)
# pcts = pcts.cumsum().shift(fill_value=0).sub(left_adjust)

# Open figure.
fig, ax = plt.subplots(figsize=figsize)

# Draw bars.
data = pcts[xtick_labels].to_numpy()
bottom = np.zeros(n_tasks)
for i, row in enumerate(data):
    color = cmap(i / n_categories)
    label = y_labels[i]
    p = ax.bar(xticks, row, bottom=bottom, color=color, label=label, width=barwidth, edgecolor="white")
    ax.bar_label(p, label_type="center", fmt="%.0f")
    bottom += row

# Aesthetics.
ax.axhline(0, color="black", linewidth=0.5, zorder=0)
ax.set_xlim(-1, n_tasks)
ax.margins(y=0)
ss
# xticks_minor = range(-100, 101, 10)
# xticks = range(-100, 101, 50)
# xticklabels = [f"{abs(x)}%" for x in xticks]


# Loop over eack task.
for i, (task, ser) in enumerate(pcts.groupby(task_col)):
    ser = ser.droplevel(task_col)
    left_adjust = ser.loc[:midpoint-1].sum()
    ser = ser[ser!=0]
    xlocs = ser.cumsum().shift(fill_value=0).sub(left_adjust).to_numpy()
    xwidths = ser.to_numpy()
    x = [(x, w) for x, w in zip(xlocs, xwidths)]
    c = [cmap(i/n_categories) for i in ser.index]
    y = (i - bar_height / 2, bar_height)
    bars = ax.broken_barh(x, y, color=c, linewidth=linewidth, edgecolor="white")
    yticks.append(i)
    yticklabels.append(task)
n_conditions = df[task_col].nunique()
ax.axvline(0, color="black", linewidth=linewidth, zorder=0)
xticks_minor = range(-100, 101, 10)
xticks = range(-100, 101, 50)
xticklabels = [f"{abs(x)}%" for x in xticks]
ax.margins(x=0)
ax.set_xticks(xticks)
ax.set_xticks(xticks_minor, minor=True)
ax.set_xticklabels(xticklabels)
ax.set_ylim(-1, n_conditions)
# ax.tick_params(bottom=False, labelbottom=False)
ax.set_xlabel("Relative percentage")
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_position(("outward", 5))

