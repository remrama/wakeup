## Run all scripts in sequence to reproduce results.
##
## $ bash runall.sh

set -e

# Clean and aggregate raw Qualtrics output.
python source2raw.py

# Describe the sample.
python demographics.py

# Inspect correlated measures.
python corr_table.py

# Did participants think the wakeup tasks impacted their awakening?
python wakeup_impact.py

# Did participants wake up sooner after the wakeup tasks?
python wakeup_timing.py

# Did lucidity levels during wakeup tasks predict success?
python wakeup_lucidity.py

# Did dream control (more generally) predict a change in dream emotion?
python control_emotion.py
