"""Helper functions."""
import json
from pathlib import Path
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat


def load_config():
    """Return the configuration file."""
    with open("./config.json", "r", encoding="utf-8") as jsonfile:
        return json.load(jsonfile)

def load_raw(trim=False):
    """Load raw data tsv and sidecar json files.

    If `trim` is True, reduce to only participants who completed part 2 and remove excess columns.
    """
    config = load_config()
    root_dir = Path(config["root_directory"])
    import_path_data = root_dir / "derivatives" / "data.tsv"
    import_path_sidecar = import_path_data.with_suffix(".json")

    df = pd.read_csv(import_path_data, sep="\t")
    with open(import_path_sidecar, "r", encoding="utf-8") as fp:
        sidecar = json.load(fp)

    if trim:
        # Reduce to only those who participated in the second part and completed the second part task.
        df = df.query("Completed_part2.eq(True)").query("Task_completion.eq(3)")
        # Reduce to desired columns.
        KEEP_COLUMNS = [
            "ParticipantID",
            "Condition",
            "age",
            "gender",
            "recruitment",
            "Dream_recall",
            "Nightmare_recall",
            "Lucid_recall",
            "LUSK",  # derived
            "Multiple_attempts",
            "Task_lucid",
            "Dream_LUSK",  # derived
            "Wakeup",
            "Wakeup_impact",
            "Lucidity",
            "Nightmare",
            "Sleep_paralysis",
            "PANAS_pos",  # derived
            "PANAS_neg",  # derived
            "Dream_report",
            "Free_response",
        ]
        df = df[KEEP_COLUMNS]
        sidecar = {k: v for k, v in sidecar.items() if k in df or k == "MeasurementToolMetadata"}
    return df, sidecar

def load_qualtrics_source(which):
    """Return raw qualtrics SPSS data."""
    assert which in ["initial", "morning"]

    root_dir = Path(load_config()["root_directory"])
    source_dir = root_dir / "sourcedata"
    if which == "initial":
        potential_paths = list(source_dir.glob("*Initial*questionnaire*.sav"))
    elif which == "morning":
        potential_paths = list(source_dir.glob("*Morning*report*form*.sav"))
    
    # Find most recent filename.
    date_strings = [ x.stem.split("_", 1)[1] for x in potential_paths ]
    date_times = [ time.strptime(x, "%B+%d,+%Y_%H.%M") for x in date_strings ]
    recent_date = max(date_times)
    recent_index = date_times.index(recent_date)
    
    filepath = potential_paths[recent_index]

    df, meta = pyreadstat.read_sav(filepath)

    return df, meta


def standard_qualtrics_clean(df, keep_columns=[]):
    """The qualtrics file comes baked with some columns we don't need.
    Make sure they are all "in order" or as expected,
    and then take them off the dataframe.
    Nothing is specific to this study here.

    Removes non-anonymous links (pilot participants)
    and those who didn't finish (actually not sure about the latter).
    """

    # Exclude any submissions prior to the original study advertisement.
    # Convert to the Qualtrics timestamps from MST to CST since that's the time I have it in.
    for col in ["StartDate", "EndDate", "RecordedDate"]:
        df[col] = df[col].dt.tz_localize("US/Mountain").dt.tz_convert("US/Central")

    # Sort for readability
    df = df.sort_values("StartDate")

    ################################# Handle Qualtrics-specific columns.
    ## These have nothing to do with out data.
    ## Check all the Qualtrics columns and make sure they look as expected.
    ## Then remove them for cleanliness.

    ##### Remove piloting/testing data.
    # That should handle all the "previews" from this column, but check.
    df = df.query("DistributionChannel=='anonymous'")
    # assert df["DistributionChannel"].eq("anonymous").all(), "All surveys should have come from the anonymous link."
    # This is also redundnat but make sure "IP Address" is here (just indicates normal response, IP was not collected).
    # df = df.query("Status=='IP Address'")
    # assert df["Status"].eq("IP Address").all(), "All surveys should have come from the anonymous link."
    assert df["Status"].eq(0).all(), "All surveys should have come from the anonymous link."

    ##### Remove unfinished surveys.
    ##### (This only catches those that left early,
    #####  if they just skipped some non-required Qs they will stay.)
    # "Finished" is binary, True if they didn't manually exit (ie, True even if screedn out early).
    # "Progress" is percentage of completion, even if screened out, so a more useful measure.
    # BUT I think bc I screened w/ branching rather than skipping, they all say 100% even if they get screened out.
    # So this can be handled another way. Some questions were
    # required so check for this. The last question was required,
    # so use that as the measure of completion.
    # Still make sure Finished and Progress are both full (as I'm expecting)
    # I think there's a way to export with incomplete I probably didn't check that.
    # Or they might be "in progress"?
    df = df.query("Finished==1")
    df = df.query("Progress==100") # redundant I think

    # Can't see how these would be off but w/e just check
    assert df["ResponseId"].is_unique, "These should all be unique."
    assert df["UserLanguage"].eq("EN").all(), "All languages should be English."

    ## Description of Qualtrics default columns
    ## https://www.qualtrics.com/support/survey-platform/data-and-analysis-module/data/download-data/understanding-your-dataset/

    ################################# Handle Qualtrics-specific columns.
    ## These have nothing to do with out data.
    ## Check all the Qualtrics columns and make sure they look as expected.
    ## Then remove them for cleanliness.

    # Remove default Qualtrics columns
    drop_columns = [
        "StartDate", "EndDate", "RecordedDate",         # Qualtrics stuff we're done with.
        "Status", "DistributionChannel", "Progress",    # Qualtrics stuff we're done with.
        "Finished", "ResponseId", "UserLanguage",       # Qualtrics stuff we're done with.
        "Duration__in_seconds_",
    ]
    for c in keep_columns:
        drop_columns.remove(c)

    df = df.drop(columns=drop_columns)
    return df


def validate_likert_scales(meta, vars_to_validate):
    """Sometimes when the Qualtrics question is edited
    the scale gets changed "unknowingly". Here, check
    to make sure everything starts at 1 and increases by 1.
    Could be remapped but it's easier and safer to fix
    the source of the problem in Qualtrics.
    """
    if isinstance(vars_to_validate, str):
        vars_to_validate = [vars_to_validate]
    assert isinstance(vars_to_validate, list)
    for var in vars_to_validate:
        if var in meta.variable_value_labels:
            levels = meta.variable_value_labels[var]
            values = list(levels.keys())
            assert values[0] == 1, f"{var} scale doesn't start at 1. Recode values in Qualtrics and re-export."
            assert values == sorted(values), f"{var} scale is not in increasing order. Recode values in Qualtrics and re-export."
            assert not np.any(np.diff(values) != 1), f"{var} scale is not linear. Recode values in Qualtrics and re-export."

def vertical_sigbar(ax, y1, y2, x, p, width=0.1, linewidth=1, caplength=None):
    """significance bar vertical, with hooks to the left.
    y1, y2 in data coordinates because makes more sense, and x in data_coords
    """
    stars = "*" * sum(p < cutoff for cutoff in (0.05, 0.01, 0.001))
    color = "black" if stars else "gainsboro"
    x_coords = [x - width, x, x, x - width]
    y_coords = [y1, y1, y2, y2]
    ax.plot(
        x_coords, y_coords, color=color, linewidth=linewidth, transform=ax.get_yaxis_transform()
    )
    if caplength is not None:
        for y in [y1, y2]:
            cap_x = [x - width, x - width]
            cap_y = [y - caplength/2, y + caplength/2]
            ax.plot(
                cap_x, cap_y, color=color, linewidth=linewidth, transform=ax.get_yaxis_transform()
            )
    if stars:
        y_txt = (y1 + y2) / 2
        ax.text(
            x, y_txt, stars, fontsize=10, color=color,
            rotation=270, ha="center", va="center", transform=ax.get_yaxis_transform()
        )

def load_matplotlib_settings():
    plt.rcParams["savefig.dpi"] = 1200
    plt.rcParams["interactive"] = True
    plt.rcParams["figure.constrained_layout.use"] = True
    plt.rcParams["font.family"] = "Times New Roman"
    # plt.rcParams["font.sans-serif"] = "Arial"
    plt.rcParams["mathtext.fontset"] = "custom"
    plt.rcParams["mathtext.rm"] = "Times New Roman"
    plt.rcParams["mathtext.cal"] = "Times New Roman"
    plt.rcParams["mathtext.it"] = "Times New Roman:italic"
    plt.rcParams["mathtext.bf"] = "Times New Roman:bold"
    plt.rcParams["font.size"] = 8
    plt.rcParams["axes.titlesize"] = 8
    plt.rcParams["axes.labelsize"] = 8
    plt.rcParams["axes.labelsize"] = 8
    plt.rcParams["xtick.labelsize"] = 8
    plt.rcParams["ytick.labelsize"] = 8
    plt.rcParams["axes.linewidth"] = 0.8  # Edge linewidth
    plt.rcParams["axes.axisbelow"] = True
    plt.rcParams["axes.grid"] = True
    plt.rcParams["axes.grid.axis"] = "y"
    plt.rcParams["axes.grid.which"] = "major"
    plt.rcParams["axes.labelpad"] = 4
    plt.rcParams["xtick.top"] = True
    plt.rcParams["ytick.right"] = True
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["ytick.direction"] = "in"
    plt.rcParams["grid.color"] = "gainsboro"
    plt.rcParams["grid.linewidth"] = 1
    plt.rcParams["grid.alpha"] = 1
    plt.rcParams["legend.frameon"] = False
    plt.rcParams["legend.edgecolor"] = "black"
    plt.rcParams["legend.fontsize"] = 8
    plt.rcParams["legend.title_fontsize"] = 8
    plt.rcParams["legend.borderpad"] = 0.4
    plt.rcParams["legend.labelspacing"] = 0.2  # the vertical space between the legend entries
    plt.rcParams["legend.handlelength"] = 2  # the length of the legend lines
    plt.rcParams["legend.handleheight"] = 0.7  # the height of the legend handle
    plt.rcParams["legend.handletextpad"] = 0.2  # the space between the legend line and legend text
    plt.rcParams["legend.borderaxespad"] = 0.5  # the border between the axes and legend edge
    plt.rcParams["legend.columnspacing"] = 1  # the space between the legend line and legend text
