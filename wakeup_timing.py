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
    .unstack(0, fill_value=0)
    .rename(columns=inverted_mapping)
    .rename_axis(None, axis=1)
)


################################################################################
# PLOTTING
################################################################################

probe = "How soon after performing the task did you wake up?"
probe_labels = ["during", "0-5 seconds", "6-30 seconds", "31-120 seconds", ">120 seconds"]

figsize = (5.5, 1.5)
bar_height = 0.8
linewidth = 0.5
edgecolor = "black"

n_tasks = df[task_col].nunique()
# cmap = cc.cm.diverging_linear_protanopic_deuteranopic_bjy_57_89_c34
# cmap = cc.cm.gwv
cmap = cc.cm.linear_protanopic_deuteranopic_kbw_5_95_c34_r
# cmap = cc.cm.linear_tritanopic_kcw_5_95_c22

# Make sure wakeup responses are categorical.
cats, cat_labels = zip(*meta[wakeup_col]["Levels"].items())
cats = list(map(int, cats))
df[wakeup_col] = pd.Categorical(df[wakeup_col], cats, ordered=True)

n_categories = len(cats)
midpoint = ceil((cats[0] + cats[-1]) / 2)

# Get relative percents.
pcts = (df
    .groupby(task_col)[wakeup_col]
    .value_counts(sort=False, dropna=False, normalize=True)
    .multiply(100)
    # .unstack(0)
)
# pcts.columns = pcts.columns.map(inverted_mapping)
# pcts = pcts.cumsum().shift(fill_value=0).sub(left_adjust)

# Open figure.
fig, ax = plt.subplots(figsize=figsize)

# Build ticks on the fly to ensure order is correct.
yticks = []
yticklabels = []

# Loop over eack task.
for i, (task, ser) in enumerate(pcts.groupby(task_col)):
    ## NOTE, this is overcomplicated since there are no gaps in the bars. Should just use barh.
    ser = ser.droplevel(task_col)
    left_adjust = ser.loc[:midpoint-1].sum()
    ser = ser[ser!=0]
    xlocs = ser.cumsum().shift(fill_value=0).sub(left_adjust).to_numpy()
    xwidths = ser.to_numpy()
    x = [(x, w) for x, w in zip(xlocs, xwidths)]
    c = [cmap((j-1) / (n_categories-1)) for j in ser.index]
    y = (i - bar_height / 2, bar_height)
    bars = ax.broken_barh(x, y, color=c, linewidth=linewidth, edgecolor=edgecolor)
    # broken_barh doesn't return BarCollections for ax.bar_label so set manually
    for k in x:
        x_ = np.cumsum(k).mean()
        s = f"{k[1]:.0f}%"
        c_ = "white" if x_ > 0 else "black"
        ax.text(x_, i, s, color=c_, ha="center", va="center")
    # Save yticks on the fly.
    yticks.append(i)
    yticklabels.append(inverted_mapping[task])

# Write stats results.
beta, pval = stat.loc[1, ["coef", "pval"]]
utils.vertical_sigbar(ax, y1=yticks[0], y2=yticks[1], x=1.04, p=pval, width=0.02, caplength=None, linewidth=1)
# sigchars = "*" * sum([pval < cutoff for cutoff in (0.05, 0.01, 0.001)])
# ptxt = r"p<0.001" if pval < .001 else fr"$p={pval:.3f}$"
# ptxt = ptxt.replace("0.", ".", 1)
# btxt = fr"$\beta={beta:.2f}$"
# stats_txt = btxt + "\n" + ptxt + sigchars
# ax.text(1, 1, stats_txt, transform=ax.transAxes, ha="right", va="top", linespacing=1)

# Aesthetics.
ax.axvline(0, color="black", linewidth=linewidth, zorder=0)
ax.margins(x=0, y=0.1)
xticks_minor = range(-100, 101, 10)
xticks = range(-100, 101, 50)
xticklabels = [f"{abs(x)}%" for x in xticks]
ax.set_xticks(xticks)
ax.set_xticks(xticks_minor, minor=True)
ax.set_xticklabels(xticklabels)
# ax.set_ylim(-1, n_tasks)
# ax.set_xlabel("Relative percentage")
ax.set_ylabel("Dream task")
ax.set_yticks(yticks)
ytick_longlabels = {
    "Clench": "Clench fist",
    "Visual": "Close eyes\nand wakeup",
}
yticklabels = [ytick_longlabels[k] for k in yticklabels]
ax.set_yticklabels(yticklabels)
ax.tick_params(which="both", axis="both", direction="out", top=False, right=False)
ax.tick_params(which="both", left=False, bottom=False, labelbottom=False)
ax.spines[["top", "right", "bottom", "left"]].set_visible(False)

# Legend.
handles = [
    plt.matplotlib.patches.Patch(
        facecolor=cmap((i-1) / (n_categories-1)), label=l, edgecolor=edgecolor, linewidth=linewidth
    ) for i, l in zip(cats, probe_labels)
]
legend = ax.legend(handles=handles,
    title=probe,
    loc="lower center", bbox_to_anchor=(0.5, 1),
    borderaxespad=0.2, frameon=False,
    labelspacing=0.2,  # rowspacing, vertical space between the legend entries
    handletextpad=0.2,  # space between legend marker and label
    # fontsize=8,
    ncol=n_categories,
)
legend._legend_box.sep = 5


################################################################################
# EXPORT
################################################################################

freq.to_csv(export_path_freq, index=False, na_rep="n/a", sep="\t")
stat.to_csv(export_path_stat, index=False, na_rep="n/a", sep="\t")
plt.savefig(export_path_plot)
plt.savefig(export_path_plot.with_suffix(".pdf"))
plt.savefig(export_path_plot.with_suffix(".svg"))
