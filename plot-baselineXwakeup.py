"""Visualize the relationship between
baseline LD experience and wakeup success.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pingouin as pg
import seaborn as sns

import utils

plt.rcParams["savefig.dpi"] = 600
# plt.rcParams["interactive"] = True
plt.rcParams["figure.constrained_layout.use"] = True
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 8
plt.rcParams["axes.titlesize"] = 8
plt.rcParams["axes.labelsize"] = 8
plt.rcParams["axes.labelsize"] = 8
plt.rcParams["xtick.labelsize"] = 8
plt.rcParams["ytick.labelsize"] = 8
plt.rcParams["axes.linewidth"] = 0.8 # edge line width

config = utils.load_config()

x_var = "Lucid_recall"
y_var = "Wakeup"



# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data_trimmed.tsv"
export_path_plot = root_dir / "results" / "baselineXwakeup.png"

# Load data.
df, sidecar = utils.load_data_and_sidecar(import_path)

# Group all the wakeup conditions together.
df = df.replace({"Condition":
    {
        "Clench": "Clench fists",
        "Visual": "Wakeup variant",
        "Verbal": "Wakeup variant",
        "Tholey": "Wakeup variant",
    }
})

hue_order = ["Clench fists", "Wakeup variant"]
palette = {
    "Clench fists": "gainsboro",
    "Wakeup variant": "royalblue",
}


data_kwargs = dict(
    data=df, x=x_var, y="Wakeup", hue="Condition",
    palette=palette, hue_order=hue_order)

fig, ax = plt.subplots(figsize=(4.5, 3))

sns.barplot(**data_kwargs, ax=ax, ci=None)
sns.swarmplot(**data_kwargs, ax=ax,
    dodge=True, linewidth=.5, s=3, edgecolor="white")

x_levels = sidecar[x_var]["Levels"]
y_levels = sidecar[y_var]["Levels"]

x_ticks, x_labels = zip(*{ int(k): v for k, v in x_levels.items() }.items())
x_ticks = [ x-1 for x in x_ticks ] # bc seaborn starts at 0 always
ax.set_xticks(x_ticks)
ax.set_xticklabels(x_labels, rotation=33, ha="right")
ax.set_xlim(min(x_ticks)-1, max(x_ticks)+1)

y_ticks, y_labels = zip(*{ int(k): v for k, v in y_levels.items() }.items())
y_labels = []
for k, v in y_levels.items():
    if "while" in v:
        y_labels.append("during")
    else:
        y_labels.append(v.split("(")[1].split(")")[0])
ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels)
ax.set_ylim(min(y_ticks)-1, max(y_ticks)+1)

ax.set_xlabel("Baseline Lucid Dreaming Frequency")
ax.set_ylabel("Time between task\ncompletion and waking up")
# if x_var.endswith("_recall"):
#     ax.invert_xaxis()

# if y_var == "Wakeup":
#     ax.invert_yaxis()

handles = [ plt.matplotlib.patches.Patch(
        edgecolor="none", facecolor=c, label=l)
    for l, c in palette.items() ]
legend = ax.legend(handles=handles,
    title="Task assignment",
    loc="upper right", bbox_to_anchor=(1, 1), borderaxespad=0,
    frameon=False, labelspacing=.1, handletextpad=.2)
# legend._legend_box.sep = 2 # brings title up farther on top of handles/labels
legend._legend_box.align = "left"


# Export.
plt.savefig(export_path_plot)