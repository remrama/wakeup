######### Make a condensed file with only those who completed 2nd part
######### and essentials variables.
######### Some slight manipulation too (e.g., binarizing some responses).

import json
from pathlib import Path

import pandas as pd

import utils


config = utils.load_config()

# Choose filepaths.
root_dir = Path(config["root_directory"])
import_path_data = root_dir / "derivatives" / "data.tsv"
import_path_sidecar = import_path_data.with_suffix(".json")
export_path_data = import_path_data.with_stem("data_trimmed")
export_path_sidecar = export_path_data.with_suffix(".json")

# Load data.
df = pd.read_csv(import_path_data, sep="\t")
with open(import_path_sidecar, "r", encoding="utf-8") as fp:
    full_sidecar = json.load(fp)

CONDENSE_KEEP_COLUMNS = [
    "ParticipantID",
    "Condition",
    "Multiple_attempts",
    "Task_lucid",
    "Wakeup",
    "Wakeup_immediately", # derived
    "Wakeup_shortly", # derived
    "Wakeup_impact",
    "Lucidity",
    "Sleep_paralysis",
    "PANAS_pos",
    "PANAS_neg",
    "Dream_report",
    "Free_response",
]

# Reduce to only those who completed the second part.
# Reduce to only those who completed the task.
df = df.query("Completed_part2.eq(True)")
df = df.query("Task_completion.eq(3)")

# Bin the wakeup column by two different cutoffs.
df["Wakeup_immediately"] = df["Wakeup"].le(2).astype(int)
df["Wakeup_shortly"] = df["Wakeup"].le(3).astype(int)

# Reduce to desired columns.
df = df[CONDENSE_KEEP_COLUMNS]

# Build sidecar.
derived_info = {
    "Wakeup_immediately": {
        "Levels": {
            "0": "Responded 3 or more to Wakeup probe.",
            "1": "Responded 2 or less to Wakeup probe."
        }
    },
    "Wakeup_shortly": {
        "Levels": {
            "0": "Responded 4 or more to Wakeup probe.",
            "1": "Responded 3 or less to Wakeup probe."
        }
    }
}
sidecar = {
    "MeasurementToolMetadata": {
        "Description": "Series of custom questionnaires"
    }
}
for c in CONDENSE_KEEP_COLUMNS:
    if c in full_sidecar:
        sidecar.update({c: full_sidecar[c]})
    elif c in derived_info:
        sidecar.update({c: derived_info[c]})

# Export.
df.to_csv(export_path_data, sep="\t", index=False, na_rep="n/a")
with open(export_path_sidecar, "w", encoding="utf-8") as fp:
    json.dump(sidecar, fp, indent=4, sort_keys=False, ensure_ascii=True)