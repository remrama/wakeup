"""Helper functions."""

import json
from pathlib import Path

import pyreadstat

def load_config():
    """Return the configuration file."""
    with open("./config.json", "r", encoding="utf-8") as jsonfile:
        return json.load(jsonfile)


def load_qualtrics_source(which):
    """Return raw qualtrics SPSS data."""
    assert which in ["initial", "morning"]

    root_dir = Path(load_config()["root_directory"])
    source_dir = root_dir / "sourcedata"
    if which == "initial":
        potential_paths = list(source_dir.glob("*Initial*questionnaire*.sav"))
    elif which == "morning":
        potential_paths = list(source_dir.glob("*Morning*report*form*.sav"))
    
    assert len(potential_paths) == 1
    filepath = potential_paths[0]

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
