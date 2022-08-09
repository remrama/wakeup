"""Export email lists for those who checked a box
to get notified of future studies (participation)
and information about publication of this work (publication).
"""
from pathlib import Path

import utils

config = utils.load_config()


# Choose filepaths.
root_dir = Path(config["root_directory"])
export_path_participation = root_dir / "email_lists" / "listserve_participation.txt"
export_path_publication = root_dir / "email_lists" / "listserve_publication.txt"

# Load source data.
df, meta = utils.load_qualtrics_source("initial")

# Identify relevant columns.
participation_key = "Email_other_1"
publication_key = "Email_other_2"

# Make sure the keys/columns are correct.
participation_probe = "Similar lucid dreaming study opportunities in the future"
publication_probe = "Any published work that comes from this current study"
assert meta.column_names_to_labels[participation_key].endswith(participation_probe)
assert meta.column_names_to_labels[publication_key].endswith(publication_probe)

# Remove non-emails.
df = df[df["Email"].str.contains("@")]

# Get the participants for each list.
participation_ser = df.loc[df[participation_key].eq(1), "Email"]
publication_ser = df.loc[df[publication_key].eq(1), "Email"]

# Sort for readability.
participation_ser = participation_ser.sort_values()
publication_ser = publication_ser.sort_values()

# Export.
participation_ser.to_csv(export_path_participation, index=False, header=False)
publication_ser.to_csv(export_path_publication, index=False, header=False)