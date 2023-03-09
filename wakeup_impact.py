"""Run chi2 analysis on subjective reporting of task causing awakening, export table and plot.
"""
from pathlib import Path

import colorcet as cc
import matplotlib.pyplot as plt
import pingouin as pg
from statsmodels.graphics.mosaicplot import mosaic

import utils


################################################################################
# SETUP
################################################################################

# Load custom plotting settings.
utils.load_matplotlib_settings()

# Choose filepaths.
config = utils.load_config()
root_dir = Path(config["root_directory"])
export_path_plot = root_dir / "derivatives" / "wakeup_impact-plot.png"
export_path_freq = root_dir / "derivatives" / "wakeup_impact-freq.tsv"
export_path_stat = root_dir / "derivatives" / "wakeup_impact-stat.json"

# Load data.
df, meta = utils.load_raw(trim=True)

# Reduce to Clench and Visual conditions.
df = df.query("Condition.isin(['Clench', 'Visual'])")
# Make sure variables are binarized.
df["Condition"] = df["Condition"].ne("Clench")
df["Wakeup_impact"] = df["Wakeup_impact"].eq(2)

COLUMN_A = "Condition"
COLUMN_B = "Wakeup_impact"


################################################################################
# STATISTICS
################################################################################

# Remove correction to get integers/counts in `observed` contingency table output.
expected, observed, stats = pg.chi2_independence(df, COLUMN_A, COLUMN_B, correction=False)
# Reformat contingency table for exporting.
observed = observed.stack().rename("count")


################################################################################
# PLOTTING
################################################################################

LABELS = {
    COLUMN_A: {False: "Clench", True: "Visual"},
    COLUMN_B: {False: "No", True: "Yes"},
}
LEGEND_TITLE = "Task woke me up"

# Reformat contingency data for plotting with mosaic.
observed = observed.reset_index().replace(LABELS).set_index([COLUMN_A, COLUMN_B]).squeeze("columns")

# Get stats values.
chi2val, pval = stats.set_index("test").loc["pearson", ["chi2", "pval"]]

# Plotting variables.
FIGSIZE = (2.4, 1.8)
w2h_ratio = FIGSIZE[0] / FIGSIZE[1]
AX_LEFT = 0.26
AX_WIDTH = 0.42
AX_TOP = 0.75
ax_height = AX_WIDTH * w2h_ratio
GRIDSPEC_KW = dict(left=AX_LEFT, right=AX_LEFT + AX_WIDTH, top=AX_TOP, bottom=AX_TOP - ax_height)
SIG_XLOC = 1.05
SIG_YLOC = 0.5

cmap = cc.cm.cwr
palette = {
    LABELS[COLUMN_B][0]: cmap(1.),
    LABELS[COLUMN_B][1]: cmap(0.),
}

props = lambda key: {  # ("True", "True") strings(?) tuple in key_order
    "color": palette[str(key[1])],
    "alpha": 1,
}

# Open figure.
fig, ax = plt.subplots(figsize=FIGSIZE, gridspec_kw=GRIDSPEC_KW)

# Draw boxes.
_, rects = mosaic(
    data=observed,
    properties=props,
    labelizer=lambda x: None,
    # horizontal=True,
    # axes_label=True,
    gap=0.05,
    ax=ax,
)

# Aesthetics.
ax.set_xlabel("Dream task")
ax.set_ylabel("Relative frequency")
ax.yaxis.set(
    major_locator=plt.MultipleLocator(0.5),
    minor_locator=plt.MultipleLocator(0.1),
    major_formatter=plt.matplotlib.ticker.PercentFormatter(xmax=1),
)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_position(("outward", 5))
ax.spines["bottom"].set_position(("outward", 5))

ax2 = ax.twiny()
ax2.spines["top"].set_position(("outward", 5))
ax2.set_xlabel("Relative frequency", labelpad=6)
ax2.xaxis.set(major_locator=plt.MultipleLocator(0.5),
    minor_locator=plt.MultipleLocator(0.1),
    major_formatter=plt.matplotlib.ticker.PercentFormatter(xmax=1))

ax.tick_params(which="both", direction="out")
ax2.tick_params(which="both", direction="out")

# Legend.
handles = [
    plt.matplotlib.patches.Patch(edgecolor="none", label=l, facecolor=c) for l, c in palette.items()
]
legend = ax.legend(
    handles=handles[::-1],
    title=LEGEND_TITLE,
    loc="upper left",
    bbox_to_anchor=(1, 1),
    borderaxespad=0,
    frameon=False,
    labelspacing=0.1,
    handletextpad=0.2,
)
# legend._legend_box.sep = 2 # brings title up farther on top of handles/labels
legend._legend_box.align = "left"

# Add significance text.
sigchars = "*" * sum([pval < cutoff for cutoff in (0.05, 0.01, 0.001)])
ptxt = r"p<0.001" if pval < .001 else fr"$p={pval:.3f}$"
ptxt = ptxt.replace("0.", ".", 1)
chi2txt = fr"$\chi^2={chi2val:.1f}$"
stats_txt = chi2txt + "\n" + ptxt + sigchars
ax.text(
    SIG_XLOC, SIG_YLOC, stats_txt, transform=ax.transAxes, ha="left", va="top", linespacing=1
)

# Export.
observed.to_csv(export_path_freq, index=True, na_rep="n/a", sep="\t")
stats.to_csv(export_path_stat, index=False, na_rep="n/a", sep="\t")
plt.savefig(export_path_plot)
plt.savefig(export_path_plot.with_suffix(".pdf"))
plt.savefig(export_path_plot.with_suffix(".svg"))
