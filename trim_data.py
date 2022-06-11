######### Make a condensed file with only those who completed 2nd part
######### and essentials variables.

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
    sidecar = json.load(fp)

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
sidecar = { k: v for k, v in sidecar.items() if k in CONDENSE_KEEP_COLUMNS }

# Export.
df.to_csv(export_path_data, sep="\t", index=False, na_rep="n/a")
with open(export_path_sidecar, "w", encoding="utf-8") as fp:
    json.dump(sidecar, fp, indent=4, sort_keys=False, ensure_ascii=True)