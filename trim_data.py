"""
Take raw data file and:
    - reduce to only participants who reported completing the part 2 task
    - remove excess columns
    - add binary "Wakeup_immediately" column
    - add binary "Wakeup_shortly" column
"""
import json
from pathlib import Path

import utils


# Choose filepaths for importing/exporting.
config = utils.load_config()
root_dir = Path(config["root_directory"])
import_path_data = root_dir / "derivatives" / "data.tsv"
export_path_data = import_path_data.with_stem("data_trimmed")
export_path_sidecar = export_path_data.with_suffix(".json")

# Load data.
df, full_sidecar = utils.load_data_and_sidecar(import_path_data)

# Reduce to only those who participated in the second part and completed the second part task.
df = df.query("Completed_part2.eq(True)").query("Task_completion.eq(3)")

# Add new columns that binarize the wakeup column by two different cutoffs.
IMMEDIATE_CUTOFF = 2
SHORTLY_CUTOFF = 3
df["Wakeup_immediately"] = df["Wakeup"].le(IMMEDIATE_CUTOFF).astype(int)
df["Wakeup_shortly"] = df["Wakeup"].le(SHORTLY_CUTOFF).astype(int)

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
    "Wakeup_immediately",  # derived
    "Wakeup_shortly", # derived
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

# Build sidecar.
derived_info = {
    "Wakeup_immediately": {
        "Levels": {
            "0": f"Responded higher than {IMMEDIATE_CUTOFF} on `Wakeup` probe.",
            "1": f"Responded {IMMEDIATE_CUTOFF} or lower on `Wakeup` probe."
        }
    },
    "Wakeup_shortly": {
        "Levels": {
            "0": f"Responded higher than {SHORTLY_CUTOFF} on `Wakeup` probe.",
            "1": f"Responded {SHORTLY_CUTOFF} or lower on `Wakeup` probe."
        }
    }
}
sidecar = {
    "MeasurementToolMetadata": {
        "Description": "Series of custom questionnaires"
    }
}
for c in KEEP_COLUMNS:
    if c in full_sidecar:
        sidecar.update({c: full_sidecar[c]})
    elif c in derived_info:
        sidecar.update({c: derived_info[c]})

# Export.
df.to_csv(export_path_data, index=False, na_rep="n/a", sep="\t")
with open(export_path_sidecar, "w", encoding="utf-8") as fp:
    json.dump(sidecar, fp, indent=4, sort_keys=False, ensure_ascii=True)
