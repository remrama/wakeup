"""Export contacts list for Qualtrics.

Some participants requested a weekly reminder up till either
the end of they study or they finish the second part.
This finds those people and saves a csv that can be loaded
into Qualtrics with the necessary info for each participant.

When sending the email, use a Qualtrics contact list.
    - From name: Paller Cognitive Neuroscience Lab
    - Reply-To email: remington.mallett@northwestern.edu
    - Subject: Northwestern LD Study Reminder
    - Message: in Qualtrics library (have to copy/paste)

Grab freshest data and rerun right before sending.
"""

from pathlib import Path

import utils


root_dir = Path("../")

export_path = root_dir / "derivatives" / "email_contacts_reminders.csv"


# Get a list of those who submitted the final report.
morning_df, _ = utils.load_qualtrics_source("morning")
completed_pids = morning_df["ParticipantID"].astype(int).tolist()


# Load all data and metadata.
df, meta = utils.load_qualtrics_source("initial")

df = df.dropna(subset=["ParticipantID"])
df = df[df["ParticipantID"].str.len() == 6]

df["ParticipantID"] = df["ParticipantID"].astype(int)

# Remove those who already completed 2nd part
df = df[~df["ParticipantID"].isin(completed_pids)]

# Get people who want the reminders
df = df.dropna(subset=["Email_other_4"])
assert df["Email_other_4"].eq(1).all()

# Catch empties
df = df[df["Email"].str.contains("@")]

# Export
df = df[["Email", "ParticipantID", "TaskInstructions"]]
df = df.sort_values("ParticipantID")
df.to_csv(export_path, index=False)