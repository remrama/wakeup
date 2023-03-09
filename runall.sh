## Run all scripts in sequence to reproduce results.
##
## $ bash runall.sh

set -e

# Clean and aggregate raw Qualtrics output.
python source2raw.py                #=> data.tsv

# Describe the sample.
python sample.py -f age             #=> sample_age.tsv
python sample.py -f gender          #=> sample_gender.tsv
python sample.py -f Condition       #=> sample_condition.tsv
python sample.py -f recruitment     #=> sample_recruitment.tsv

# Inspect survey responses.
python inspection.py                #=> results/inspection.png

# Did participants think the wakeup tasks impacted their awakening?
python wakeup_impact.py

# Did participants wake up sooner after the wakeup tasks?
python wakeup_timing.py

# Visualize baseline LD frequency and wakeup success.
python plot-baselineXwakeup.py      #=> results/baselineXwakeup.png
