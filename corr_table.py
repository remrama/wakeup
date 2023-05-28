"""Big exploratory correlation table."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pingouin as pg

import utils


plt.rcParams["savefig.dpi"] = 600
plt.rcParams["figure.constrained_layout.use"] = True
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 8
plt.rcParams["axes.titlesize"] = 8
plt.rcParams["axes.labelsize"] = 8
plt.rcParams["axes.labelsize"] = 8
plt.rcParams["xtick.labelsize"] = 8
plt.rcParams["ytick.labelsize"] = 8
plt.rcParams["axes.linewidth"] = 0.8

config = utils.load_config()

# Pick columns to plot.
columns = [
    # from initial
    "Dream_recall",
    "Nightmare_recall",
    "Lucid_recall",
    "LUSK",
    # from morning
    "Multiple_attempts",
    "Wakeup",
    "Wakeup_impact",
    "Lucidity",
    "Nightmare",
    "Sleep_paralysis",
    "Dream_LUSK",
    "PANAS_pos",
    "PANAS_neg",
]

# Choose filepaths.
root_dir = Path(config["root_directory"])
export_path_plot = root_dir / "derivatives" / "corr_table.png"

# Load data.
df, meta = utils.load_raw(trim=True)

# Draw.
n_vars = len(columns)
figsize = (0.9*n_vars, 0.9*n_vars)
fig, axes = plt.subplots(nrows=n_vars, ncols=n_vars, figsize=figsize, sharex="col", sharey=False)

def get_bins(var):
    if "LUSK" in var:
        levels = [1, 2, 3, 4, 5]
    elif "PANAS" in var:
        levels = range(10, 51)
    else:
        levels = [int(k) for k in meta[var]["Levels"]]
    low_lim = min(levels) - 0.5
    high_lim = max(levels) + 0.5
    return np.linspace(low_lim, high_lim, len(levels) + 1)

hist1d_kwargs = dict(color="white", edgecolor="black", linewidth=1, clip_on=False)
hist2d_kwargs = dict(cmap="Blues", clip_on=False)

for c in range(n_vars):
    xvar = columns[c]
    xbins = get_bins(xvar)
    xvals = df[xvar].values
    for r in range(n_vars):
        yvar = columns[r]
        ybins = get_bins(yvar)
        yvals = df[yvar].values

        ax = axes[r, c]
        ax.set_aspect("auto")

        if c > r:
            ax.axis("off")
            continue
        
        if c == r:
            ax.hist(xvals, bins=xbins, **hist1d_kwargs)
        else:
            stats = pg.corr(xvals, yvals, method="kendall")
            r, p = stats.loc["kendall", ["r", "p-val"]]

            ax.hist2d(xvals, yvals, bins=(xbins, ybins), **hist2d_kwargs)
            ax.set_ylim(ybins.min(), ybins.max())
            if yvar.endswith("_recall"):
                ax.invert_yaxis()
            if ax.get_subplotspec().is_first_col():
                ax.set_ylabel(yvar.replace("_", "\n"))

        ax.set_xlim(xbins.min(), xbins.max())
        if xvar.endswith("_recall"):
            ax.invert_xaxis()
        if ax.get_subplotspec().is_last_row():
            ax.set_xlabel(xvar.replace("_", "\n"))
            x_minorlocator = plt.matplotlib.ticker.MultipleLocator(1)
            x_majorlocator = plt.matplotlib.ticker.FixedLocator(
                [xbins[:2].mean(), xbins[-2:].mean()])
            ax.xaxis.set_minor_locator(x_minorlocator)
            ax.xaxis.set_major_locator(x_majorlocator)

        if r == c:
            ax.spines[["left", "top", "right"]].set_visible(False)
        if ax.get_subplotspec().is_first_row() or not ax.get_subplotspec().is_first_col():
            ax.yaxis.set_major_formatter(plt.matplotlib.ticker.NullFormatter())
            ax.tick_params(left=False)
        else:
            y_minorlocator = plt.matplotlib.ticker.MultipleLocator(1)
            y_majorlocator = plt.matplotlib.ticker.FixedLocator(
                [ybins[:2].mean(), ybins[-2:].mean()])
            ax.yaxis.set_minor_locator(y_minorlocator)
            ax.yaxis.set_major_locator(y_majorlocator)

        if r != c:
            text = f"r = {r:.2f}\np = {p:.3f}".replace("0.", ".")
            color = "black" if p < .1 else "gainsboro"
            ax.text(0.95, 0.05, text, color=color, va="bottom", ha="right", transform=ax.transAxes)

fig.align_labels()

# Export.
plt.savefig(export_path_plot)
