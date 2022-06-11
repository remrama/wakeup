######### Make a condensed file with only those who completed 2nd part
######### and essentials variables.

from pathlib import Path

import pandas as pd

import utils


config = utils.load_config()

# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path = root_dir / "derivatives" / "data.tsv"
export_path = import_path.with_stem("data_trimmed")

# Load data.
df = pd.read_csv(import_path, sep="\t")

CONDENSE_KEEP_COLUMNS = [
    "ParticipantID",
    "Condition",
    "Morning_recall",
    "Task_completion",
    "Multiple_attempts",
    "Task_lucid",
    "Wakeup",
    "Wakeup_impact",
    "Lucidity",
    "Sleep_paralysis",
    "PANAS_pos",
    "PANAS_neg",
    "Dream_report",
    "Free_response",
]

# Reduce to only those who completed the second part.
df = df.query("Completed_part2.eq(True)")

# Reduce to desired columns.
df = df[CONDENSE_KEEP_COLUMNS]

# Export.
df.to_csv(export_path, sep="\t", index=False, na_rep="n/a")