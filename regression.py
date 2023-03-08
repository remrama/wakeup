from pathlib import Path

import colorcet as cc
import matplotlib.pyplot as plt
import pingouin as pg

import utils


# # Load custom plotting settings.
# utils.load_matplotlib_settings()

# Choose filepaths.
config = utils.load_config()
root_dir = Path(config["root_directory"])
export_path_plot = root_dir / "derivatives" / "chisquared.png"
export_path_ctab = export_path_plot.with_suffix(".tsv")
export_path_stats = export_path_plot.with_suffix(".json")

# Load data.
df, meta = utils.load_data_and_sidecar(trim=True)

df = df.query("Condition.isin(['Clench', 'Visual'])")

# ctab = df[[colA, colB]].groupby([colA, colB]).size().unstack().fillna(0)

# Binarize variables used.
# df["Wakeup"] = df["Wakeup"].le(2)
# df["Condition"] = df["Condition"].ne("Clench")
# df["Wakeup_impact"] = df["Wakeup_impact"].eq(2)

import pandas as pd

condition_col = "Condition"
probe_col = "Wakeup_impact"
df = df[[condition_col, probe_col]].copy()
cats, cat_labels = zip(*meta[probe_col]["Levels"].items())
cats = list(map(int, cats))
df[probe_col] = pd.Categorical(df[probe_col], cats, ordered=True)

pcts = df.groupby(condition_col)[probe_col].value_counts(sort=False, dropna=False, normalize=True).multiply(100)
# pcts_cum = pcts.groupby(condition_col).cumsum()
from math import ceil
midpoint = ceil((cats[0] + cats[-1]) / 2)

cmap = cc.cm.diverging_linear_protanopic_deuteranopic_bjy_57_89_c34
cmap = cc.cm.gwv
cmap = cc.cm.linear_protanopic_deuteranopic_kbw_5_95_c34
cmap = cc.cm.linear_tritanopic_kcw_5_95_c22
n_categories = len(cats)
bar_height = 0.8
linewidth = 0.5

fig, ax = plt.subplots()
yticks = []
yticklabels = []
for i, (cond, ser) in enumerate(pcts.groupby(condition_col)):
    ser = ser.droplevel(condition_col)
    left_adjust = ser.loc[:midpoint-1].sum()
    ser = ser[ser!=0]
    xlocs = ser.cumsum().shift(fill_value=0).sub(left_adjust).to_numpy()
    xwidths = ser.to_numpy()
    x = [ (x, w) for x, w in zip(xlocs, xwidths) ]
    c = [ cmap(i/n_categories) for i in ser.index ]
    y = (i - bar_height / 2, bar_height)
    bars = ax.broken_barh(x, y, color=c, linewidth=linewidth, edgecolor="white")
    yticks.append(i)
    yticklabels.append(cond)
n_conditions = df[condition_col].nunique()
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

