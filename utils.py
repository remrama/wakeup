"""Helper functions."""
import json
from pathlib import Path
import time

import pandas as pd
import pyreadstat


def load_config():
    """Return the configuration file."""
    with open("./config.json", "r", encoding="utf-8") as jsonfile:
        return json.load(jsonfile)

def load_data_and_sidecar(import_path_data):
    import_path_sidecar = import_path_data.with_suffix(".json")
    df = pd.read_csv(import_path_data, sep="\t")
    with open(import_path_sidecar, "r", encoding="utf-8") as fp:
        sidecar = json.load(fp)
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


def load_matplotlib_settings():
    import matplotlib.pyplot as plt
    # plt.rcParams["figure.dpi"] = 600
    plt.rcParams["savefig.dpi"] = 600
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
    plt.rcParams["axes.linewidth"] = 0.8 # edge line width
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
    plt.rcParams["legend.borderpad"] = .4
    plt.rcParams["legend.labelspacing"] = .2 # the vertical space between the legend entries
    plt.rcParams["legend.handlelength"] = 2 # the length of the legend lines
    plt.rcParams["legend.handleheight"] = .7 # the height of the legend handle
    plt.rcParams["legend.handletextpad"] = .2 # the space between the legend line and legend text
    plt.rcParams["legend.borderaxespad"] = .5 # the border between the axes and legend edge
    plt.rcParams["legend.columnspacing"] = 1 # the space between the legend line and legend text
