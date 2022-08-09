"""Run chi2 analysis, export table and plot.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pingouin as pg
import seaborn as sns
from statsmodels.graphics.mosaicplot import mosaic

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
    label_legend = {
        "Condition": {0: "clench", 1: "visual"},
        "Wakeup": {0: "Kept dreaming", 1: "Wokeup"},
    }
# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data.tsv"
export_path_plot = root_dir / "results" / f"chisquared_{test}.png"
export_path_ctab = export_path_plot.with_suffix(".tsv")
export_path_stats = export_path_plot.with_suffix(".json")

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

# Reformat contingency table for exporting.
observed = observed.stack().rename("count")


#####################################################
# Visualization
#####################################################

# Reformat contingency data for plotting with mosaic.
observed = observed.reset_index().replace(label_legend
    ).set_index([colA, colB]).squeeze("columns")

# Get stats values.
chi2val, pval = stats.loc["mcnemar", ["chi2", "p-exact"]]

# Plotting variables.
FIGSIZE = (2.2, 1.8)
w2h_ratio = FIGSIZE[0] / FIGSIZE[1]
AX_LEFT = .26
AX_WIDTH = .42
AX_TOP = .75
ax_height = AX_WIDTH*w2h_ratio
GRIDSPEC_KW = dict(left=AX_LEFT, right=AX_LEFT+AX_WIDTH,
    top=AX_TOP, bottom=AX_TOP-ax_height)

SIG_XLOC = 1.05
SIG_YLOC = .5

# palette = utils.load_config(as_object=False)["colors"]
palette = {
    label_legend[colB][0]: "red",
    label_legend[colB][1]: "green",
}

PROPS = lambda key: { # ("True", "True") strings(?) tuple in key_order
    "color": palette[key[1]], "alpha": 1,
}

############### Draw.

# Open figure.
fig, ax = plt.subplots(figsize=FIGSIZE, gridspec_kw=GRIDSPEC_KW)

# Draw boxes.
_, rects = mosaic(
    data=observed,
    properties=PROPS,
    # labelizer=lambda x: None,
    # horizontal=True,
    # axes_label=True,
    gap=.05,
    ax=ax,
)

# Aesthetics.
ax.set_xlabel(colA)
ax.set_ylabel("Relative frequency")
ax.yaxis.set(major_locator=plt.MultipleLocator(.5),
    minor_locator=plt.MultipleLocator(.1),
    major_formatter=plt.matplotlib.ticker.PercentFormatter(xmax=1))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_position(("outward", 5))
ax.spines["bottom"].set_position(("outward", 5))

ax2 = ax.twiny()
ax2.spines["top"].set_position(("outward", 5))
ax2.set_xlabel("Relative frequency", labelpad=6)
ax2.xaxis.set(major_locator=plt.MultipleLocator(.5),
    minor_locator=plt.MultipleLocator(.1),
    major_formatter=plt.matplotlib.ticker.PercentFormatter(xmax=1))

# # ax.tick_params(left=False, bottom=False)
# # for ch in ax.get_children():
# #     if isinstance(ch, plt.Text):
# #         ch.set_horizontalalignment("left")

handles = [ plt.matplotlib.patches.Patch(
        edgecolor="none", facecolor=c, label=l)
    for l, c in palette.items() ]
legend = ax.legend(handles=handles,
    title=colB,
    loc="upper left", bbox_to_anchor=(1, 1), borderaxespad=0,
    frameon=False, labelspacing=.1, handletextpad=.2)
# legend._legend_box.sep = 2 # brings title up farther on top of handles/labels
legend._legend_box.align = "left"


# Add significance text.
sigchars = "*" * sum([ pval<cutoff for cutoff in (.05, .01, .001) ])
ptxt = r"p<0.001" if pval < .001 else fr"$p={pval:.2f}$"
ptxt = ptxt.replace("0", "", 1)
chi2txt = fr"$\chi^2={chi2val:.0f}$"
stats_txt = chi2txt + "\n" + ptxt + sigchars
ax.text(SIG_XLOC, SIG_YLOC, stats_txt, transform=ax.transAxes,
    ha="left", va="top", linespacing=1)

# Export!
observed.to_csv(export_path_ctab, sep="\t", index=True)
stats.to_json(export_path_stats, orient="index", indent=4)
plt.savefig(export_path_plot, dpi=300)