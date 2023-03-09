"""Get some general summary statistics of the whole sample."""
from pathlib import Path

import pandas as pd

import utils


# Load custom plot settings and grab configuration file.
utils.load_matplotlib_settings()
config = utils.load_config()

# Choose filepaths.
root_dir = Path(config["root_directory"])
export_path = root_dir / "derivatives" / "sample_desc.tsv"

# Load data.
df, meta = utils.load_raw(trim=False)

# Add a new column that identifies varying levels of study completion.
def participation_level(row):
    level = "pt1_finished"
    if row["Completed_part2"]:
        level = "pt2_finished"
    if row["Task_completion"] == 3:
        level = "pt2_finished_task"
    return level
df["completion"] = df.apply(participation_level, axis=1)

# Pick variables to include in frequency table.
variables = ["age", "gender", "Condition", "recruitment"]

# Get full text labels.
for c in variables:
    if c != "Condition":
        response_legend = {int(k): v.split()[0] for k, v in meta[c]["Levels"].items()}
        df[c] = df[c].map(response_legend)


freqs = (df
    .set_index("completion")[variables]
    .stack()
    .groupby(level=[0,1])
    .value_counts()
    .unstack(0)
    .fillna(0)
    .astype(int)
    .rename_axis(None, axis=1)
    .rename_axis(["response", "probe"])
)

# # Messy/lazy concatenation.
# df_list = [
#     (df
#         .groupby("Completed_part2")[v]
#         .value_counts()
#         .unstack(0, fill_value=0)
#         .rename_axis(None, axis=1)
#         .rename_axis("response")
#         .assign(probe=v)
#         .set_index("probe", append=True)
#         .swaplevel()
#     ) for v in variables
# ]

# df = pd.concat(pd.DataFrame(x) for x in df_list)

# desc = (df
#     .groupby("Completed_part2")[variables].describe()
#     .stack(0)[["count", "unique", "top", "freq"]]
#     .reset_index(0)
#     .rename_axis("variable")
#     .sort_index()
# )

# feature = "gender"
# ser = df[feature].value_counts().rename("count").rename_axis(feature).sort_index()


# # Draw plot.
# fig, ax = plt.subplots(figsize=(3.5, 3.5))
# bars = ax.bar(
#     ser.index, ser.values,
#     color="white", edgecolor="black", linewidth=1,
# )

# # Aesthetics.
# ax.set_xlabel(feature.capitalize())
# ax.set_ylabel("Count")

# # Export.
# plt.savefig(export_path_plot)
# ser.to_csv(export_path_data, sep="\t")
